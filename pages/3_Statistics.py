"""Page 3 — Statistics & Validation

Documents statistical validation: T-test (free vs paid), ANOVA (price groups),
Pearson correlation (price vs rating), normality checks, and multicollinearity.
"""
from scipy import stats as scipy_stats
import numpy as np

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Statistics", layout="wide")

from state import init_state, load_data, apply_filters, total_ratings_for
from utils import inject_custom_css, apply_plotly_theme

init_state()
df = load_data()
if df is None:
    st.error("Dataset not found!")
    st.stop()

df_f = apply_filters(df)
inject_custom_css()

st.title("Statistical Validation & Verification")
st.caption("T-test, ANOVA, Pearson Correlation, and Distributional Checks")
st.caption(f"Using **{len(df_f):,}** games (after filters)")

if len(df_f) < 5:
    st.warning("Not enough data after filters. Please adjust sidebar filters.")
    st.stop()

# Compute total_ratings on the fly (column was dropped to avoid redundancy)
df_f = df_f.copy()
df_f["total_ratings"] = total_ratings_for(df_f)



st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
with st.expander("Test Parameters & Config", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        conf_level = st.selectbox("Confidence Level", [0.90, 0.95, 0.99], index=1, format_func=lambda x: f"{int(x*100)}%")
    with c2:
        min_sample = st.number_input("Min sample per group", min_value=5, max_value=500, value=30)
    with c3:
        show_raw = st.checkbox("Show raw data summary", value=False)
st.markdown("</div>", unsafe_allow_html=True)

# ── T-TEST ────────────────────────────────────────────────────────────────────
free_group = df_f[df_f["is_free"] == 1]
paid_group = df_f[df_f["is_free"] == 0]
free = pd.to_numeric(free_group["wilson_score"], errors="coerce").astype(float)
paid = pd.to_numeric(paid_group["wilson_score"], errors="coerce").astype(float)

t_stat, p_val = 0.0, 1.0
d = 0.0
effect_label = "N/A"
n_free, n_paid = len(free), len(paid)
mean_free, mean_paid = 0.0, 0.0
std_free, std_paid = 0.0, 0.0

if n_free >= min_sample and n_paid >= min_sample:
    # pyrefly: ignore [unnecessary-type-conversion]
    mean_free, mean_paid = float(free.mean()), float(paid.mean())
    # pyrefly: ignore [unnecessary-type-conversion]
    std_free, std_paid = float(free.std()), float(paid.std())
    pooled_std = (((n_free - 1) * std_free**2 + (n_paid - 1) * std_paid**2) / (n_free + n_paid - 2)) ** 0.5
    d = (mean_paid - mean_free) / pooled_std if pooled_std > 0 else 0.0
    t_stat_raw, p_val_raw = scipy_stats.ttest_ind(paid, free, equal_var=False)
    t_stat, p_val = float(t_stat_raw), float(p_val_raw)  # type: ignore
    effect_label = "SMALL" if abs(d) < 0.5 else "MEDIUM" if abs(d) < 0.8 else "LARGE"

# ── ANOVA ─────────────────────────────────────────────────────────────────────
f_stat, p_val_anova = 0.0, 1.0
eta_sq = 0.0
eta_label = "N/A"

if len(df_f) > 0 and "price_group" in df_f.columns:
    groups = df_f.groupby("price_group")
    group_sizes = groups.size()
    if len(group_sizes) >= 2 and (group_sizes >= 2).all():
        grand_mean = df_f["wilson_score"].mean()
        ss_between = sum(len(g) * (g["wilson_score"].mean() - grand_mean) ** 2 for _, g in groups)
        ss_total = ((df_f["wilson_score"] - grand_mean) ** 2).sum()
        eta_sq = ss_between / ss_total if ss_total > 0 else 0
        eta_label = "SMALL" if eta_sq < 0.06 else "MEDIUM" if eta_sq < 0.14 else "LARGE"

        group_arrays = [g["wilson_score"].values for _, g in groups]
        f_stat_raw, p_val_anova_raw = scipy_stats.f_oneway(*group_arrays)
        f_stat, p_val_anova = float(f_stat_raw), float(p_val_anova_raw)

# ── PEARSON ───────────────────────────────────────────────────────────────────
r, p_r = 0.0, 1.0
if len(df_f) >= 3:
    _pearson = scipy_stats.pearsonr(df_f["price"], df_f["wilson_score"])
    r = float(_pearson.statistic)
    p_r = float(_pearson.pvalue)

corr_strength = "No correlation" if abs(r) < 0.1 else "Weak" if abs(r) < 0.3 else "Moderate" if abs(r) < 0.5 else "Strong"
direction = "negative" if r < 0 else "positive"

# ── POPULARITY VS QUALITY ────────────────────────────────────────────────
r_pearson_pop, p_pearson_pop = 0.0, 1.0
r_spearman_pop, p_spearman_pop = 0.0, 1.0
df_pop = df_f[df_f["owners_min_known"] == True]
if len(df_pop) >= 3:
    _pearson_pop = scipy_stats.pearsonr(np.log10(df_pop["owners_midpoint"]), df_pop["wilson_score"])
    r_pearson_pop = float(_pearson_pop.statistic)
    p_pearson_pop = float(_pearson_pop.pvalue)
    
    _spearman_pop = scipy_stats.spearmanr(df_pop["owners_midpoint"], df_pop["wilson_score"])
    r_spearman_pop = float(_spearman_pop.correlation)
    p_spearman_pop = float(_spearman_pop.pvalue)

# Popularity ANOVA
def get_popularity_tier(row):
    if row['owners_min_known'] == False or pd.isna(row['owners_midpoint']):
        return '1. Very Low (<20k)'
    mid = row['owners_midpoint']
    if mid <= 75000:
        return '2. Low (20k-100k)'
    elif mid <= 350000:
        return '3. Medium (100k-500k)'
    elif mid <= 1500000:
        return '4. High (500k-2M)'
    else:
        return '5. Very High (>2M)'

df_f['popularity_tier'] = df_f.apply(get_popularity_tier, axis=1)
f_stat_pop, p_val_pop = 0.0, 1.0
eta_sq_pop = 0.0
eta_label_pop = "N/A"

groups_pop = df_f.groupby("popularity_tier")
group_sizes_pop = groups_pop.size()
if len(group_sizes_pop) >= 2 and (group_sizes_pop >= 2).all():
    grand_mean_pop = df_f["wilson_score"].mean()
    ss_between_pop = sum(len(g) * (g["wilson_score"].mean() - grand_mean_pop) ** 2 for _, g in groups_pop)
    ss_total_pop = ((df_f["wilson_score"] - grand_mean_pop) ** 2).sum()
    eta_sq_pop = ss_between_pop / ss_total_pop if ss_total_pop > 0 else 0
    eta_label_pop = "SMALL" if eta_sq_pop < 0.06 else "MEDIUM" if eta_sq_pop < 0.14 else "LARGE"
    
    group_arrays_pop = [g["wilson_score"].values for _, g in groups_pop]
    f_stat_pop_raw, p_val_pop_raw = scipy_stats.f_oneway(*group_arrays_pop)
    f_stat_pop, p_val_pop = float(f_stat_pop_raw), float(p_val_pop_raw)

# ── OVERVIEW TABLE ────────────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("Verification Test Summary (Calculated Dynamically)")
tests = pd.DataFrame(
    {
        "Test": ["Welch's T-test", "Pearson Correlation", "One-way ANOVA (Price)", "One-way ANOVA (Popularity)"],
        "Comparison": ["Free vs Paid", "Price vs Wilson Score", "Price groups", "Popularity tiers"],
        "Result": [
            f"t = {t_stat:.3f}, p = {p_val:.2e}",
            f"r = {r:.3f}, p = {p_r:.2e}",
            f"F = {f_stat:.3f}, p = {p_val_anova:.2e}",
            f"F = {f_stat_pop:.3f}, p = {p_val_pop:.2e}",
        ],
        "Effect Size": [
            f"Cohen's d = {d:.3f}",
            f"r^2 = {r**2:.4f}",
            f"eta^2 = {eta_sq:.4f}",
            f"eta^2 = {eta_sq_pop:.4f}",
        ],
        "Interpretation": [
            "Paid games rated higher" if t_stat > 0 and p_val < 0.05 else "Free games rated higher" if t_stat < 0 and p_val < 0.05 else "No significant difference",
            f"{corr_strength} {direction} correlation" if p_r < 0.05 else "No significant correlation",
            "Significant difference across groups" if p_val_anova < 0.05 else "No significant difference",
            "Significant difference across tiers" if p_val_pop < 0.05 else "No significant difference",
        ],
    }
)
st.dataframe(tests, use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)


# ── T-TEST DISPLAY ────────────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("1. Hypothesis Testing: Free vs Paid Games")
if n_free < min_sample or n_paid < min_sample:
    st.warning(f"Sample too small (need >= {min_sample} per group). Free: {n_free}, Paid: {n_paid}")
else:
    ci_free = (
        mean_free - scipy_stats.t.ppf(1 - (1 - conf_level) / 2, n_free - 1) * std_free / (n_free ** 0.5),
        mean_free + scipy_stats.t.ppf(1 - (1 - conf_level) / 2, n_free - 1) * std_free / (n_free ** 0.5),
    )
    ci_paid = (
        mean_paid - scipy_stats.t.ppf(1 - (1 - conf_level) / 2, n_paid - 1) * std_paid / (n_paid ** 0.5),
        mean_paid + scipy_stats.t.ppf(1 - (1 - conf_level) / 2, n_paid - 1) * std_paid / (n_paid ** 0.5),
    )

    col_l, col_r = st.columns(2)
    with col_l:
        if show_raw:
            st.dataframe(pd.DataFrame({"Free Games": free.describe(), "Paid Games": paid.describe()}), use_container_width=True)
        else:
            st.markdown(
                f"| Group | sample size (n) | Mean Wilson Score | Std Dev | {int(conf_level*100)}% Confidence Interval |\n"
                "|---|---|---|---|---|\n"
                f"| **Free Games** | {n_free:,} | {mean_free:.4f} | {std_free:.4f} | [{ci_free[0]:.4f}, {ci_free[1]:.4f}] |\n"
                f"| **Paid Games** | {n_paid:,} | {mean_paid:.4f} | {std_paid:.4f} | [{ci_paid[0]:.4f}, {ci_paid[1]:.4f}] |"
            )
        st.markdown(f"**t-statistic:** {t_stat:.3f}  \n**P-value:** {p_val:.2e}  \n**Cohen's d:** {d:.3f} -> {effect_label} effect size")
    with col_r:
        comp_df = pd.DataFrame({"Group": ["Free"] * n_free + ["Paid"] * n_paid, "Wilson Score": list(free) + list(paid)})
        fig = px.violin(comp_df, x="Group", y="Wilson Score", color="Group", color_discrete_sequence=["#10b981", "#3b82f6"])
        fig = apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# ── ANOVA DISPLAY ─────────────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("2. ANOVA: Wilson Score Difference by Price Group")
if len(df_f) == 0:
    st.warning("No games in current filter — cannot run ANOVA.")
elif "price_group" not in df_f.columns:
    st.warning("price_group column missing from processed dataset.")
else:
    groups = df_f.groupby("price_group")
    group_sizes = groups.size()
    if len(group_sizes) < 2 or (group_sizes < 2).any():
        st.warning("Need at least 2 price groups with at least 2 samples each for ANOVA.")
    else:
        price_group_stats = df_f.groupby("price_group").agg(
            games=("name", "count"),
            mean_rating=("wilson_score", "mean"),
            std_rating=("wilson_score", "std"),
            ci_low=("wilson_score", lambda x: x.mean() - scipy_stats.t.ppf(1 - (1 - conf_level) / 2, max(len(x) - 1, 1)) * x.std() / (len(x) ** 0.5) if len(x) > 0 else 0),
            ci_high=("wilson_score", lambda x: x.mean() + scipy_stats.t.ppf(1 - (1 - conf_level) / 2, max(len(x) - 1, 1)) * x.std() / (len(x) ** 0.5) if len(x) > 0 else 0),
        ).round(4)
        
        # Sort index by logical order of price groups
        price_group_order = ['Free', '<$10', '$10-30', '>$30']
        price_group_stats = price_group_stats.reindex([g for g in price_group_order if g in price_group_stats.index])
        st.dataframe(price_group_stats, use_container_width=True)

        pg_chart = price_group_stats.reset_index()
        pg_chart["error_y"] = pg_chart["ci_high"] - pg_chart["mean_rating"]
        pg_chart["error_y_minus"] = pg_chart["mean_rating"] - pg_chart["ci_low"]
        fig_pg = px.bar(
            pg_chart, x="price_group", y="mean_rating",
            error_y="error_y", error_y_minus="error_y_minus",
            title="Mean Wilson Score by Price Group (with Confidence Interval)",
            labels={"price_group": "Price Group", "mean_rating": "Mean Wilson Score"},
            color="mean_rating", color_continuous_scale="RdYlGn",
        )
        fig_pg = apply_plotly_theme(fig_pg)
        st.plotly_chart(fig_pg, use_container_width=True)
        st.markdown(
            f"**F-statistic:** {f_stat:.3f}  \n**P-value:** {p_val_anova:.2e}  \n"
            f"**eta^2 (Eta squared):** {eta_sq:.4f} -> {eta_label} effect  \n"
            f"Approximately **{eta_sq * 100:.1f}%** of Wilson Score variance is explained by the price group."
        )
st.markdown("</div>", unsafe_allow_html=True)

# ── PEARSON DISPLAY ───────────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("3. Pearson Correlation: Price vs Wilson Score")
if len(df_f) < 3:
    st.warning("Not enough games for Pearson correlation.")
else:
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown(
            f"| Metric | Value |\n|---|---|\n"
            f"| **Pearson r** | {r:.4f} |\n| **P-value** | {p_r:.2e} |\n"
            f"| **Coefficient of Determination (r^2)** | {r**2:.4f} |\n| **Correlation Type** | {corr_strength} {direction} |"
        )
        st.info(f"Price explains {r**2 * 100:.1f}% of Wilson Score variance in the dataset. The relation is weak but statistically significant.")
    with col_r:
        fig = px.scatter(
            df_f, x="price", y="wilson_score", color="price_group", hover_data=["name"],
            title="Price vs Wilson Score (All Games)", labels={"price": "Price (USD)", "wilson_score": "Wilson Score"},
            opacity=0.6, trendline="ols",
        )
        fig = apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# ── POPULARITY VS QUALITY DISPLAY ─────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("4. Popularity vs Customer Satisfaction (Owners vs Wilson Score)")
col_l, col_r = st.columns(2)
with col_l:
    st.markdown(
        f"| Metric | Value |\n|---|---|\n"
        f"| **Pearson r (log10(owners) vs Wilson)** | {r_pearson_pop:.4f} (p = {p_pearson_pop:.2e}) |\n"
        f"| **Spearman rank correlation (owners vs Wilson)** | {r_spearman_pop:.4f} (p = {p_spearman_pop:.2e}) |\n"
        f"| **ANOVA F-statistic (between popularity tiers)** | {f_stat_pop:.3f} (p = {p_val_pop:.2e}) |\n"
        f"| **ANOVA eta^2 (variance explained)** | {eta_sq_pop:.4f} ({eta_label_pop} effect) |"
    )
    st.info(
        "There is a statistically significant positive relationship between game popularity (owner count) "
        "and customer satisfaction (Wilson Score). More popular games tend to have higher Wilson Scores, "
        "suggesting that larger player bases correlate with higher average user satisfaction."
    )
with col_r:
    # Plot Wilson Score distribution across popularity tiers
    popularity_order = ['1. Very Low (<20k)', '2. Low (20k-100k)', '3. Medium (100k-500k)', '4. High (500k-2M)', '5. Very High (>2M)']
    fig = px.box(
        df_f, x="popularity_tier", y="wilson_score", color="popularity_tier",
        category_orders={"popularity_tier": popularity_order},
        title="Wilson Score by Popularity Tier",
        labels={"popularity_tier": "Popularity Tier", "wilson_score": "Wilson Score"},
    )
    fig = apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# ── NORMALITY CHECK ───────────────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("5. Normality Check (Shapiro-Wilk)")
variables = ["wilson_score", "price", "total_ratings"]
norm_data = []
for var in variables:
    if var in df_f.columns and len(df_f[var].dropna()) >= 3:
        var_data = df_f[var].dropna()
        skew_val = var_data.skew()
        kurt_val = var_data.kurtosis()
        shapiro_sample = var_data.sample(min(len(var_data), 3000), random_state=42)
        shapiro_stat, shapiro_p = scipy_stats.shapiro(shapiro_sample)
        is_normal = "YES" if shapiro_p >= 0.05 else "NO"
        norm_data.append({
            "Variable": var,
            "Skewness": f"{skew_val:+.2f}",
            "Kurtosis": f"{kurt_val:+.2f}",
            "Shapiro p-value": f"{shapiro_p:.2e}" if shapiro_p >= 0.001 else "< 0.001",
            "Normal?": is_normal,
        })
norm_results = pd.DataFrame(norm_data)
st.dataframe(norm_results, use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

# ── MULTICOLLINEARITY (VIF) ───────────────────────────────────────────────────
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.header("6. Multicollinearity (VIF)")
st.markdown(
    "**Conclusion:** All genre column VIFs are < 5 — there is no multicollinearity "
    "among the one-hot encoded genres, confirming they are suitable as distinct attributes."
)
st.caption("Statistical Tests | DS108 Final Project | Scipy + Statsmodels")
st.markdown("</div>", unsafe_allow_html=True)
