"""Helper utilities for global dashboard styling and themes."""
import streamlit as st

def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        /* Global Styles */
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Outfit', sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
            color: #334155 !important;
        }
        
        [data-testid="stHeader"] {
            background: rgba(248, 250, 252, 0.5) !important;
            backdrop-filter: blur(10px);
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid rgba(0, 0, 0, 0.08);
        }
        
        /* Custom Sidebar Title and Widgets */
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: #1e293b !important;
        }
        
        /* Glassmorphism Cards */
        .glass-card {
            background: rgba(255, 255, 255, 0.8) !important;
            backdrop-filter: blur(12px) saturate(160%);
            border: 1px solid rgba(255, 255, 255, 0.6) !important;
            border-radius: 16px !important;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.06);
        }
        
        /* Headings */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif;
            font-weight: 600 !important;
            color: #0f172a !important;
            letter-spacing: -0.02em;
        }
        
        /* Metrics Styling */
        [data-testid="stMetricValue"] {
            font-family: 'Outfit', sans-serif;
            font-size: 30px !important;
            font-weight: 700 !important;
            color: #0284c7 !important;
            text-shadow: 0 0 10px rgba(2, 132, 199, 0.1);
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 13px !important;
            font-weight: 500 !important;
            color: #64748b !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Buttons */
        .stButton>button {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 10px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.15);
        }
        
        .stButton>button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px 0 rgba(37, 99, 235, 0.25) !important;
            border-color: rgba(255, 255, 255, 0.4) !important;
        }
        
        .stButton>button:active {
            transform: translateY(0) !important;
        }
        
        /* Selectboxes & inputs */
        .stSelectbox div, .stMultiSelect div, .stSlider div {
            color: #0f172a !important;
        }
        
        /* Tables and Dataframe overrides */
        [data-testid="stTable"], [data-testid="stDataFrame"] {
            background-color: rgba(255, 255, 255, 0.6) !important;
            border-radius: 12px;
            border: 1px solid rgba(0, 0, 0, 0.05);
        }
        
        /* Info/Success/Warning blocks override */
        .element-container div.stAlert {
            background-color: rgba(241, 245, 249, 0.9) !important;
            border: 1px solid rgba(0, 0, 0, 0.05) !important;
            border-left: 6px solid #3b82f6 !important;
            color: #1e293b !important;
            border-radius: 10px;
        }
        
        .element-container div.stAlert[data-baseweb="notification"] {
            background-color: rgba(241, 245, 249, 0.9) !important;
        }
        
        /* Tabs */
        button[data-baseweb="tab"] {
            color: #64748b !important;
            font-size: 15px !important;
            font-weight: 500 !important;
            padding: 12px 18px !important;
        }
        
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #0284c7 !important;
            border-bottom-color: #0284c7 !important;
        }
        
        /* Scrollbars custom styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.05);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(0, 0, 0, 0.1);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 0, 0, 0.2);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def apply_plotly_theme(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#334155', family='Outfit'),
        xaxis=dict(
            gridcolor='rgba(0,0,0,0.05)',
            zerolinecolor='rgba(0,0,0,0.1)',
            linecolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            gridcolor='rgba(0,0,0,0.05)',
            zerolinecolor='rgba(0,0,0,0.1)',
            linecolor='rgba(0,0,0,0.1)'
        ),
        legend=dict(
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='rgba(0,0,0,0.08)',
            borderwidth=1
        ),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig

