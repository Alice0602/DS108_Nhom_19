import os
import ast
import pandas as pd
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / 'data' / 'processed' / 'steam_games_with_genres.csv'
SCHEMA_PAGE = PROJECT_ROOT / 'pages' / '4_Data_Curation_Schema.py'
REPORT_MD = PROJECT_ROOT / 'audit_report.md'
REPORT_CSV = PROJECT_ROOT / 'audit_report.csv'

def load_data():
    # Import state's load_data to ensure on-the-fly calculated columns are present during audit
    import sys
    sys.path.append(str(PROJECT_ROOT))
    from state import load_data as state_load_data
    from state import total_ratings_for
    df = state_load_data()
    if df is not None:
        df['total_ratings'] = total_ratings_for(df)
    return df

def load_schema():
    # Safely extract the `schema_data` literal using AST to avoid regex truncation on brackets.
    import ast
    with open(SCHEMA_PAGE, 'r', encoding='utf-8') as f:
        content = f.read()
    tree = ast.parse(content)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'schema_data':
                    return ast.literal_eval(node.value)
    raise ValueError('schema_data not found in schema page')

def compare_types(df, schema):
    mismatches = []
    for col in df.columns:
        actual_dtype = str(df[col].dtype)
        # Find documented entry, fallback to genre_X pattern for one-hot columns
        doc = next((s for s in schema if s.get('Column') == col), None)
        if not doc and col.startswith('genre_'):
            doc = next((s for s in schema if 'genre_X' in s.get('Column', '')), None)
            
        doc_type = doc.get('Type') if doc else None
        if doc_type:
            # Normalise actual dtypes
            actual_norm = actual_dtype.lower()
            if actual_norm.startswith('object') or actual_norm.startswith('string'):
                actual_norm = 'string'
            elif 'datetime' in actual_norm or 'date' in actual_norm:
                actual_norm = 'date'
            elif 'int' in actual_norm:
                actual_norm = 'int64'
            elif 'float' in actual_norm:
                actual_norm = 'float64'
            elif 'bool' in actual_norm:
                actual_norm = 'boolean'
            
            # Normalise documented types
            doc_norm = doc_type.lower()
            if 'int' in doc_norm:
                doc_norm = 'int64'
            elif 'float' in doc_norm:
                doc_norm = 'float64'
            elif 'bool' in doc_norm:
                doc_norm = 'boolean'
            elif 'date' in doc_norm:
                doc_norm = 'date'
            elif 'categorical' in doc_norm:
                doc_norm = 'string'
            elif 'list' in doc_norm:
                # If first element is a list, treat actual norm as list
                is_list_val = len(df) > 0 and isinstance(df[col].dropna().iloc[0], list)
                actual_norm = 'list' if is_list_val else actual_norm
                doc_norm = 'list'
                
            if actual_norm != doc_norm:
                mismatches.append({
                    'column': col,
                    'actual': actual_dtype,
                    'documented': doc_type,
                    'description': doc.get('Description') if doc is not None else None
                })
    return mismatches

def logical_inconsistencies(df):
    issues = []
    # 1. Free flag vs price
    free_price = df[(df['is_free'] == 1) & (df['price'] > 0)]
    if not free_price.empty:
        issues.append({'type': 'Free but price > 0', 'count': len(free_price), 'sample': free_price.head(3).to_dict('records')})
    price_free = df[(df['is_free'] == 0) & (df['price'] == 0)]
    if not price_free.empty:
        issues.append({'type': 'Paid but price == 0', 'count': len(price_free), 'sample': price_free.head(3).to_dict('records')})
    # 2. Rating thresholds
    total_ratings = df['positive_ratings'] + df['negative_ratings']
    low_ratings = df[total_ratings < 100]
    if not low_ratings.empty:
        issues.append({'type': 'Total ratings < 100', 'count': len(low_ratings), 'sample': low_ratings.head(3).to_dict('records')})
    # 3. Year bounds
    year_out = df[~df['year'].between(2022, 2026, inclusive='both')]
    if not year_out.empty:
        issues.append({'type': 'Year out of range', 'count': len(year_out), 'sample': year_out.head(3).to_dict('records')})
    # 4. Owners consistency
    if 'owners_min' in df.columns and 'owners_max' in df.columns:
        wrong_order = df[df['owners_min'] > df['owners_max']]
        if not wrong_order.empty:
            issues.append({'type': 'owners_min > owners_max', 'count': len(wrong_order), 'sample': wrong_order.head(3).to_dict('records')})
    if 'owners_midpoint' in df.columns and 'owners_min' in df.columns and 'owners_max' in df.columns:
        expected_mid = ((df['owners_min'] + df['owners_max']) // 2).astype('Int64')
        diff = (df['owners_midpoint'] != expected_mid)
        if diff.any():
            bad = df[diff]
            issues.append({'type': 'owners_midpoint mismatch', 'count': len(bad), 'sample': bad.head(3).to_dict('records')})
    # 5. One‑hot genre columns should be 0/1 only
    genre_onehot = [c for c in df.columns if c.startswith('genre_') and c not in ('genre_X (22 columns)', 'genres')]
    for col in genre_onehot:
        invalid = df[~df[col].isin([0,1])]
        if not invalid.empty:
            issues.append({'type': f'Invalid one‑hot values in {col}', 'count': len(invalid), 'sample': invalid.head(2).to_dict('records')})
    return issues

def static_code_analysis(root_path):
    warnings = []
    for py_path in root_path.rglob('*.py'):
        if py_path.parts[-1].startswith('__'):
            continue
        try:
            tree = ast.parse(py_path.read_text(encoding='utf-8'), filename=str(py_path))
        except SyntaxError as e:
            warnings.append({'file': str(py_path), 'issue': f'SyntaxError: {e}'} )
            continue
        # Look for eval/exec usage
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec'):
                warnings.append({'file': str(py_path), 'line': node.lineno, 'issue': f'Use of dangerous function {node.func.id}'} )
        # Look for hard‑coded column names that no longer exist in the dataset
        # Collect all string literals used as attribute/index keys
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                col_name = node.slice.value
                # We'll compare later against actual df columns
                warnings.append({'file': str(py_path), 'line': node.lineno, 'issue': f'Column literal "{col_name}" used'} )
    return warnings

def generate_reports(df, schema, type_mismatches, logic_issues, code_warnings):
    # Markdown report
    with open(REPORT_MD, 'w', encoding='utf-8') as md:
        md.write('# 📊 Audit Report\n\n')
        md.write('## 1️⃣ Data Type Mismatches\n')
        if not type_mismatches:
            md.write('✅ All documented types match actual pandas dtypes.\n\n')
        else:
            md.write('| Column | Actual | Documented | Description |\n')
            md.write('|--------|--------|------------|-------------|\n')
            for m in type_mismatches:
                md.write(f"| {m['column']} | {m['actual']} | {m['documented']} | {m['description']} |\n")
            md.write('\n')
        md.write('## 2️⃣ Logical Inconsistencies\n')
        if not logic_issues:
            md.write('✅ No logical inconsistencies detected.\n\n')
        else:
            for issue in logic_issues:
                md.write(f"- **{issue['type']}** – Count: {issue['count']}\n")
                for s in issue['sample']:
                    md.write(f"  - Sample: {s}\n")
            md.write('\n')
        md.write('## 3️⃣ Static Code Warnings\n')
        if not code_warnings:
            md.write('✅ No static analysis warnings.\n\n')
        else:
            for w in code_warnings:
                line = f" (line {w['line']})" if 'line' in w else ''
                md.write(f"- **{w['file']}{line}** – {w['issue']}\n")
            md.write('\n')
    # CSV report – a compact version
    rows = []
    for m in type_mismatches:
        rows.append({
            'category': 'type_mismatch',
            'detail': m['column'],
            'actual': m['actual'],
            'documented': m['documented'],
            'description': m['description']
        })
    for issue in logic_issues:
        rows.append({
            'category': 'logic',
            'detail': issue['type'],
            'count': issue['count'],
            'sample': json.dumps(issue['sample'], ensure_ascii=False)
        })
    for w in code_warnings:
        rows.append({
            'category': 'code',
            'file': w['file'],
            'line': w.get('line'),
            'issue': w['issue']
        })
    if rows:
        pd.DataFrame(rows).to_csv(REPORT_CSV, index=False)
    else:
        pd.DataFrame([{'category': 'summary', 'message': 'All checks passed'}]).to_csv(REPORT_CSV, index=False)

def main():
    df = load_data()
    schema = load_schema()
    type_mismatches = compare_types(df, schema)
    logic_issues = logical_inconsistencies(df)
    code_warnings = static_code_analysis(PROJECT_ROOT)
    generate_reports(df, schema, type_mismatches, logic_issues, code_warnings)
    print('✅ Audit completed. Reports written to', REPORT_MD, 'and', REPORT_CSV)

if __name__ == '__main__':
    main()
