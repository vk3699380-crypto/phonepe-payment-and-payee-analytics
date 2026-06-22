import json
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Phonepe Pulse Insights",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- SESSION STATE FOR THEME ---
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

IS_DARK = st.session_state.theme == "dark"

def inject_custom_css(accent_color, is_dark):
    bg = "#09090b" if is_dark else "#ffffff"
    bg_subtle = "#0c0c0f" if is_dark else "#f9fafb"
    card = "#0c0c0f" if is_dark else "#ffffff"
    card_hover = "#131316" if is_dark else "#f4f4f5"
    border = "#1e1e24" if is_dark else "#e4e4e7"
    border_subtle = "#16161a" if is_dark else "#f0f0f2"
    text = "#fafafa" if is_dark else "#09090b"
    text_dim = "#52525b" if is_dark else "#a1a1aa"
    text_muted = "#71717a"
    shadow = "none" if is_dark else "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)"
    
    css = f"""
    <style>
    :root {{
        --bg: {bg};
        --bg-subtle: {bg_subtle};
        --card: {card};
        --card-hover: {card_hover};
        --border: {border};
        --border-subtle: {border_subtle};
        --text: {text};
        --text-muted: {text_muted};
        --text-dim: {text_dim};
        --accent: {accent_color};
        --shadow: {shadow};
        --radius: 10px;
    }}
    
    header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
    div[data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
    }}
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'DM Sans', -apple-system, sans-serif !important;
    }}
    
    .block-container {{
        padding: 1.5rem 2rem 2rem !important;
        max-width: 1360px !important;
    }}
    
    .brand {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding-bottom: 1rem;
    }}
    .brand-name {{
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.04em;
        color: var(--text);
    }}
    
    /* Control Center Card */
    .control-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.25rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow);
    }}
    .control-title {{
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    
    /* KPI Cards */
    .metric-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.25rem 1.4rem;
        box-shadow: var(--shadow);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .metric-label {{
        font-size: 0.75rem;
        color: var(--text-muted);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .metric-value {{
        font-size: 1.85rem;
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.03em;
        margin: 0.25rem 0;
    }}
    .metric-subtext {{
        font-size: 0.7rem;
        color: var(--text-dim);
    }}
    
    /* Chart and Table Wraps */
    .chart-wrap {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.25rem;
        box-shadow: var(--shadow);
        margin-bottom: 1.25rem;
        height: 100%;
    }}
    .chart-title {{
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text);
    }}
    .chart-subtitle {{
        font-size: 0.72rem;
        color: var(--text-dim);
        margin-bottom: 0.75rem;
    }}
    
    /* Data Table Styling */
    .data-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.78rem;
    }}
    .data-table th {{
        text-align: left;
        padding: 0.6rem 0.8rem;
        color: var(--text-muted);
        font-weight: 600;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-bottom: 1px solid var(--border);
    }}
    .data-table td {{
        padding: 0.65rem 0.8rem;
        color: var(--text);
        border-bottom: 1px solid var(--border-subtle);
    }}
    .data-table tr:last-child td {{
        border-bottom: none;
    }}
    .data-table tr:hover td {{
        background: var(--bg-subtle);
    }}
    
    /* Badge styling */
    .badge {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 500;
    }}
    .badge-accent {{
        color: var(--accent);
        background: rgba(37,99,235,0.08);
    }}
    .delta-up {{
        color: #10b981 !important;
        background: rgba(16,185,129,0.1) !important;
    }}
    .delta-down {{
        color: #ef4444 !important;
        background: rgba(239,68,68,0.1) !important;
    }}
    
    /* Pill Tabs styling */
    button[data-baseweb="tab"] {{
        background: transparent !important;
        color: var(--text-muted) !important;
        font-size: 0.835rem !important;
        font-weight: 500 !important;
        padding: 0.55rem 1rem !important;
        border: 1px solid transparent !important;
        border-radius: 7px !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: var(--text) !important;
        background: var(--card) !important;
        border-color: var(--border) !important;
    }}
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
        display: none !important;
    }}
    [data-baseweb="tab-list"] {{
        gap: 4px !important;
        background: var(--bg-subtle) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 3px;
        margin-bottom: 1.5rem !important;
    }}
    
    /* Layout Gap override */
    [data-testid="stHorizontalBlock"] {{
        gap: 1.25rem !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
DB_FILE = "phonepe_pulse.db"
GEOJSON_FILE = "states_india.geojson"

# --- THEME ACCENT COLOR CODES ---
ACCENTS = {
    "Classic Blue": {"hex": "#2563eb", "scale": "Blues"},
    "Forest Emerald": {"hex": "#10b981", "scale": "Greens"},
    "Sunset Amber": {"hex": "#f59e0b", "scale": "Oranges"},
    "Royal Purple": {"hex": "#8b5cf6", "scale": "Purples"}
}

# --- DATABASE UTILITIES ---
def query_db(query, params=()):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql_query(query, conn, params=params)

def get_unique_states():
    df = query_db("SELECT DISTINCT state FROM agg_trans WHERE state != 'India' ORDER BY state")
    return df["state"].tolist()

def fetch_top_performers(table_name, entity_col, metric_col, sort_col, year, quarter_num, state_selection, limit):
    clauses = []
    params = []
    
    if year:
        clauses.append("year = ?")
        params.append(year)
    if quarter_num is not None:
        clauses.append("quarter = ?")
        params.append(quarter_num)
        
    is_all_india = (state_selection == "All India")
    if not is_all_india:
        clauses.append("state = ?")
        params.append(state_selection)
        
    select_fields = f"state, {entity_col}" if is_all_india else entity_col
    group_fields = f"state, {entity_col}" if is_all_india else entity_col
    
    query = f"SELECT {select_fields}, {metric_col} FROM {table_name} WHERE " + " AND ".join(clauses) + f" GROUP BY {group_fields} ORDER BY {sort_col} DESC LIMIT {limit}"
    return query_db(query, tuple(params))

# --- HELPER FORMATTING FUNCTIONS ---
def format_indian_currency(val):
    if val is None or np.isnan(val):
        return "Rs. 0"
    if val >= 10_000_000:
        return f"Rs. {val / 10_000_000:.2f} Cr"
    elif val >= 100_000:
        return f"Rs. {val / 100_000:.2f} Lk"
    else:
        return f"Rs. {val:,.2f}"

def format_indian_count(val):
    if val is None or np.isnan(val):
        return "0"
    if val >= 10_000_000:
        return f"{val / 10_000_000:.2f} Cr"
    elif val >= 100_000:
        return f"{val / 100_000:.2f} Lk"
    else:
        return f"{val:,}"

# --- SHAPEFILE / GEOJSON LOAD ---
@st.cache_data
def load_geojson():
    if Path(GEOJSON_FILE).exists():
        with open(GEOJSON_FILE, "r") as f:
            return json.load(f)
    return None

geojson_data = load_geojson()

# --- STATE MATCHING FOR MAP ---
def prepare_map_df(df, metric_col):
    # Mapping table-level names to GeoJSON st_nm properties
    mapping = {
        "Andaman & Nicobar Islands": ["Andaman & Nicobar Island"],
        "Arunachal Pradesh": ["Arunanchal Pradesh"],
        "Delhi": ["NCT of Delhi"],
        "Dadra & Nagar Haveli & Daman & Diu": ["Dadara & Nagar Havelli", "Daman & Diu"]
    }
    
    new_rows = []
    for _, row in df.iterrows():
        state = row['state']
        if state in mapping:
            for mapped_name in mapping[state]:
                new_row = row.copy()
                new_row['st_nm'] = mapped_name
                new_rows.append(new_row)
        else:
            new_row = row.copy()
            new_row['st_nm'] = state
            new_rows.append(new_row)
            
    return pd.DataFrame(new_rows)

# --- 10 DROPDOWN SELECTION SYSTEM ---
# Fetch dynamic filters
states = get_unique_states()

# Dashboard control panel block wrapper
st.markdown("""
<div style='margin-bottom: 0.5rem;'></div>
""", unsafe_allow_html=True)

# Main Branding Header Row
head_left, head_right = st.columns([9, 1])
with head_left:
    st.markdown(f"""
    <div class="brand">
        <span class="brand-name">Phonepe <span style="color:var(--accent)">Pulse</span> Insights</span>
        <span class="badge badge-accent" style="margin-left:10px;">Live Geovisualization</span>
    </div>
    """, unsafe_allow_html=True)
with head_right:
    theme_label = "☀️ Light" if IS_DARK else "🌙 Dark"
    st.button(theme_label, on_click=toggle_theme, use_container_width=True)

# Grid Card containing the 10 dropdowns
st.markdown("""
<div class="control-card">
    <div class="control-title">⚙️ Dashboard Control Center (10 Filter Dropdowns)</div>
</div>
""", unsafe_allow_html=True)

row1_cols = st.columns(5)
row2_cols = st.columns(5)

# Row 1 Dropdowns
with row1_cols[0]:
    domain = st.selectbox(
        "1. Insight Domain",
        ["Transactions", "Users", "Insurance"],
        help="Select the data domain to analyze."
    )

with row1_cols[1]:
    mode = st.selectbox(
        "2. Analysis Mode",
        ["Aggregated Summary", "Map Analysis", "Top Performance"],
        help="Select the granular scope of the analysis."
    )

with row1_cols[2]:
    year = st.selectbox(
        "3. Select Year",
        [2018, 2019, 2020, 2021, 2022, 2023, 2024],
        index=5,
        help="Filter the analysis by year."
    )

with row1_cols[3]:
    quarter = st.selectbox(
        "4. Select Quarter",
        ["All Quarters", "Q1", "Q2", "Q3", "Q4"],
        index=0,
        help="Filter the analysis by quarter."
    )

with row1_cols[4]:
    # Insurance is only available for a subset of states/pincodes or categories, 
    # adjust the selector states accordingly if needed.
    state_selection = st.selectbox(
        "5. Select State",
        ["All India"] + states,
        index=0,
        help="Analyze specific regions or All India."
    )

# Determine valid Categories based on Domain Selection
if domain == "Transactions":
    categories = ["All Categories", "Merchant payments", "Peer-to-peer payments", "Recharge & bill payments", "Financial Services", "Others"]
elif domain == "Insurance":
    categories = ["All Categories", "Insurance"]
else: # Users
    categories = ["All Categories"]

# Determine valid Metrics based on Domain Selection
if domain == "Transactions" or domain == "Insurance":
    metric_options = ["Total Amount (Rs.)", "Total Transaction Count", "Average Value per Transaction (Rs.)"]
else: # Users
    metric_options = ["Registered Users", "App Opens"]

# Row 2 Dropdowns
with row2_cols[0]:
    category_selection = st.selectbox(
        "6. Category Filter",
        categories,
        index=0,
        help="Filter by payment transaction category."
    )

with row2_cols[1]:
    metric = st.selectbox(
        "7. Select Metric",
        metric_options,
        index=0,
        help="Metric value to plot and visualize."
    )

with row2_cols[2]:
    limit = st.selectbox(
        "8. Top N Limit",
        [5, 10, 15, 20],
        index=1,
        help="Limit for top charts and tables."
    )

with row2_cols[3]:
    accent_selection = st.selectbox(
        "9. Visual Accent Palette",
        list(ACCENTS.keys()),
        index=0,
        help="Change the primary highlighting color of the UI."
    )
    ACCENT_COLOR = ACCENTS[accent_selection]["hex"]
    COLOR_SCALE = ACCENTS[accent_selection]["scale"]

with row2_cols[4]:
    viz_style = st.selectbox(
        "10. Visualization Style",
        ["Choropleth Map", "Bar Chart", "Trend Line", "Pie Chart"],
        index=0,
        help="Select the default primary rendering chart style."
    )

# Inject Custom Style Sheet with theme variables
inject_custom_css(ACCENT_COLOR, IS_DARK)

# --- PLOTLY CHART THEME CONFIG ---
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#71717a" if not IS_DARK else "#a1a1aa", size=11),
    margin=dict(l=0, r=0, t=25, b=0),
    xaxis=dict(
        gridcolor="rgba(0,0,0,0.04)" if not IS_DARK else "rgba(255,255,255,0.04)",
        zerolinecolor="rgba(0,0,0,0.04)" if not IS_DARK else "rgba(255,255,255,0.04)",
        tickfont=dict(size=10, color="#71717a"),
    ),
    yaxis=dict(
        gridcolor="rgba(0,0,0,0.04)" if not IS_DARK else "rgba(255,255,255,0.04)",
        zerolinecolor="rgba(0,0,0,0.04)" if not IS_DARK else "rgba(255,255,255,0.04)",
        tickfont=dict(size=10, color="#71717a"),
    ),
)

# --- DATA QUERYING LOGIC ---
quarter_num = None if quarter == "All Quarters" else int(quarter[1])

# Build Base Filters
filter_clauses = ["year = ?"]
filter_params = [year]

if quarter_num is not None:
    filter_clauses.append("quarter = ?")
    filter_params.append(quarter_num)

# Resolve state-wise vs country-level filtering
is_all_india = (state_selection == "All India")
state_filter = "India" if is_all_india else state_selection

# --- KPI QUERYING HELPERS ---
def fetch_kpi_data(tbl, count_col, amount_col, year, quarter_num, state_filter, category_col=None, category_val=None):
    # current year
    clauses_curr = ["year = ?", "state = ?"]
    params_curr = [year, state_filter]
    if quarter_num is not None:
        clauses_curr.append("quarter = ?")
        params_curr.append(quarter_num)
    if category_col and category_val and category_val != "All Categories":
        clauses_curr.append(f"{category_col} = ?")
        params_curr.append(category_val)
        
    query_curr = f"SELECT SUM({count_col}) as cnt, SUM({amount_col}) as amt FROM {tbl} WHERE " + " AND ".join(clauses_curr)
    res_curr = query_db(query_curr, tuple(params_curr))
    
    # prev year
    clauses_prev = ["year = ?", "state = ?"]
    params_prev = [year - 1, state_filter]
    if quarter_num is not None:
        clauses_prev.append("quarter = ?")
        params_prev.append(quarter_num)
    if category_col and category_val and category_val != "All Categories":
        clauses_prev.append(f"{category_col} = ?")
        params_prev.append(category_val)
        
    query_prev = f"SELECT SUM({count_col}) as cnt, SUM({amount_col}) as amt FROM {tbl} WHERE " + " AND ".join(clauses_prev)
    res_prev = query_db(query_prev, tuple(params_prev))
    
    curr_cnt = res_curr["cnt"].iloc[0] if not res_curr.empty else None
    curr_amt = res_curr["amt"].iloc[0] if not res_curr.empty else None
    prev_cnt = res_prev["cnt"].iloc[0] if not res_prev.empty else None
    prev_amt = res_prev["amt"].iloc[0] if not res_prev.empty else None
    
    return curr_cnt, curr_amt, prev_cnt, prev_amt

def fetch_user_kpi_data(year, quarter_num, state_filter):
    # current year
    clauses_curr = ["year = ?", "state = ?"]
    params_curr = [year, state_filter]
    if quarter_num is not None:
        clauses_curr.append("quarter = ?")
        params_curr.append(quarter_num)
    
    query_curr = f"SELECT MAX(registered_users) as reg, SUM(app_opens) as opens FROM agg_user WHERE " + " AND ".join(clauses_curr)
    res_curr = query_db(query_curr, tuple(params_curr))
    
    # prev year
    clauses_prev = ["year = ?", "state = ?"]
    params_prev = [year - 1, state_filter]
    if quarter_num is not None:
        clauses_prev.append("quarter = ?")
        params_prev.append(quarter_num)
        
    query_prev = f"SELECT MAX(registered_users) as reg, SUM(app_opens) as opens FROM agg_user WHERE " + " AND ".join(clauses_prev)
    res_prev = query_db(query_prev, tuple(params_prev))
    
    curr_reg = res_curr["reg"].iloc[0] if not res_curr.empty else None
    curr_opens = res_curr["opens"].iloc[0] if not res_curr.empty else None
    prev_reg = res_prev["reg"].iloc[0] if not res_prev.empty else None
    prev_opens = res_prev["opens"].iloc[0] if not res_prev.empty else None
    
    return curr_reg, curr_opens, prev_reg, prev_opens

def calc_yoy_growth(curr, prev):
    if curr is None or prev is None or prev == 0:
        return None
    return ((curr - prev) / prev) * 100

def render_kpi_card(title, value, yoy, subtext, sub_yoy=None):
    yoy_html = ""
    if yoy is not None:
        cls = "delta-up" if yoy >= 0 else "delta-down"
        arrow = "↑" if yoy >= 0 else "↓"
        yoy_html = f'<span class="badge {cls}" style="margin-left: 8px; vertical-align: middle;">{arrow} {abs(yoy):.1f}% YoY</span>'
    
    sub_yoy_html = ""
    if sub_yoy is not None:
        cls = "delta-up" if sub_yoy >= 0 else "delta-down"
        arrow = "↑" if sub_yoy >= 0 else "↓"
        sub_yoy_html = f' <span class="badge {cls}" style="font-size:0.65rem; padding: 1px 4px; line-height: 1;">{arrow} {abs(sub_yoy):.1f}%</span>'
        
    return f"""
    <div class="metric-card">
        <div class="metric-label">{title}</div>
        <div style="display: flex; align-items: center; flex-wrap: wrap; margin: 0.15rem 0;">
            <span class="metric-value" style="margin-right: 2px;">{value}</span>
            {yoy_html}
        </div>
        <div class="metric-subtext" style="font-size:0.75rem; color:var(--text-dim); display:flex; align-items:center; gap:4px;">
            <span>{subtext}</span>{sub_yoy_html}
        </div>
    </div>
    """

# --- BUSINESS EXECUTIVE SUMMARY GENERATOR ---
def generate_business_summary(domain, year, quarter_num, state_selection, category_selection):
    is_all_india = (state_selection == "All India")
    state_filter = "India" if is_all_india else state_selection
    
    if domain in ["Transactions", "Insurance"]:
        tbl = "agg_trans" if domain == "Transactions" else "agg_insurance"
        type_col = "transaction_type" if domain == "Transactions" else "insurance_type"
        
        # 1. Total & Previous totals
        clauses_curr = ["year = ?", "state = ?"]
        params_curr = [year, state_filter]
        if quarter_num is not None:
            clauses_curr.append("quarter = ?")
            params_curr.append(quarter_num)
        
        query_curr = f"SELECT SUM(count) as cnt, SUM(amount) as amt FROM {tbl} WHERE " + " AND ".join(clauses_curr)
        res_curr = query_db(query_curr, tuple(params_curr))
        
        curr_cnt = res_curr["cnt"].iloc[0] if (not res_curr.empty and res_curr["cnt"].iloc[0] is not None) else 0
        curr_amt = res_curr["amt"].iloc[0] if (not res_curr.empty and res_curr["amt"].iloc[0] is not None) else 0
        
        # Dominant category
        query_cat = f"SELECT {type_col} as cat, SUM(amount) as amt FROM {tbl} WHERE " + " AND ".join(clauses_curr) + f" GROUP BY cat ORDER BY amt DESC LIMIT 1"
        res_cat = query_db(query_cat, tuple(params_curr))
        dom_cat = res_cat["cat"].iloc[0] if not res_cat.empty else "N/A"
        dom_amt = res_cat["amt"].iloc[0] if (not res_cat.empty and res_cat["amt"].iloc[0] is not None) else 0
        dom_share = (dom_amt / curr_amt * 100) if curr_amt > 0 else 0
        
        # Average Ticket Size (ATS)
        ats = (curr_amt / curr_cnt) if curr_cnt > 0 else 0
        
        # YoY Growth
        clauses_prev = ["year = ?", "state = ?"]
        params_prev = [year - 1, state_filter]
        if quarter_num is not None:
            clauses_prev.append("quarter = ?")
            params_prev.append(quarter_num)
            
        query_prev = f"SELECT SUM(amount) as amt FROM {tbl} WHERE " + " AND ".join(clauses_prev)
        res_prev = query_db(query_prev, tuple(params_prev))
        prev_amt = res_prev["amt"].iloc[0] if (not res_prev.empty and res_prev["amt"].iloc[0] is not None) else 0
        yoy_val = calc_yoy_growth(curr_amt, prev_amt)
        
        yoy_str = f"growing by {yoy_val:.1f}% YoY" if yoy_val is not None else "with baseline YoY data unavailable"
        ats_str = format_indian_currency(ats)
        
        summary_text = f"""
        💼 <strong>Executive Summary ({state_selection})</strong>:<br/>
        In <strong>{year}{f" Q{quarter_num}" if quarter_num else ""}</strong>, {state_selection} recorded a total digital payment volume of <strong>{format_indian_currency(curr_amt)}</strong> over <strong>{format_indian_count(curr_cnt)}</strong> transactions, {yoy_str}. 
        The <strong>Average Ticket Size (ATS)</strong> stood at <strong>{ats_str}</strong> per transaction. 
        <strong>{dom_cat}</strong> emerged as the dominant payment type, driving <strong>{dom_share:.1f}%</strong> of total payment value (Rs. {format_indian_count(dom_amt)}).
        """
        
    else: # Users
        clauses_curr = ["year = ?", "state = ?"]
        params_curr = [year, state_filter]
        if quarter_num is not None:
            clauses_curr.append("quarter = ?")
            params_curr.append(quarter_num)
            
        query_curr = f"SELECT MAX(registered_users) as reg, SUM(app_opens) as opens FROM agg_user WHERE " + " AND ".join(clauses_curr)
        res_curr = query_db(query_curr, tuple(params_curr))
        curr_reg = res_curr["reg"].iloc[0] if (not res_curr.empty and res_curr["reg"].iloc[0] is not None) else 0
        curr_opens = res_curr["opens"].iloc[0] if (not res_curr.empty and res_curr["opens"].iloc[0] is not None) else 0
        
        # Dom brand
        query_brand = f"SELECT brand, SUM(count) as cnt FROM agg_user_device WHERE " + " AND ".join(clauses_curr) + " GROUP BY brand ORDER BY cnt DESC LIMIT 1"
        res_brand = query_db(query_brand, tuple(params_curr))
        dom_brand = res_brand["brand"].iloc[0] if not res_brand.empty else "N/A"
        dom_cnt = res_brand["cnt"].iloc[0] if (not res_brand.empty and res_brand["cnt"].iloc[0] is not None) else 0
        dom_brand_share = (dom_cnt / curr_reg * 100) if curr_reg > 0 else 0
        
        # YoY Registered
        clauses_prev = ["year = ?", "state = ?"]
        params_prev = [year - 1, state_filter]
        if quarter_num is not None:
            clauses_prev.append("quarter = ?")
            params_prev.append(quarter_num)
        query_prev = f"SELECT MAX(registered_users) as reg FROM agg_user WHERE " + " AND ".join(clauses_prev)
        res_prev = query_db(query_prev, tuple(params_prev))
        prev_reg = res_prev["reg"].iloc[0] if (not res_prev.empty and res_prev["reg"].iloc[0] is not None) else 0
        yoy_reg = calc_yoy_growth(curr_reg, prev_reg)
        yoy_str = f"expanding by {yoy_reg:.1f}% YoY" if yoy_reg is not None else "with baseline YoY data unavailable"
        
        summary_text = f"""
        💼 <strong>Executive Summary ({state_selection})</strong>:<br/>
        In <strong>{year}{f" Q{quarter_num}" if quarter_num else ""}</strong>, the active user ecosystem in {state_selection} reached <strong>{format_indian_count(curr_reg)}</strong> registered users, {yoy_str}. 
        App Opens reached <strong>{format_indian_count(curr_opens)}</strong> events, showing healthy user engagement frequency. 
        <strong>{dom_brand}</strong> remains the primary device manufacturer, accounting for <strong>{dom_brand_share:.1f}%</strong> of active accounts.
        """
        
    return summary_text

# --- KPI CARD CALCULATIONS ---
curr_reg, curr_opens, prev_reg, prev_opens = fetch_user_kpi_data(year, quarter_num, state_filter)
yoy_reg = calc_yoy_growth(curr_reg, prev_reg)
yoy_opens = calc_yoy_growth(curr_opens, prev_opens)

if domain == "Transactions":
    curr_vol, curr_val, prev_vol, prev_val = fetch_kpi_data(
        "agg_trans", "count", "amount", year, quarter_num, state_filter,
        category_col="transaction_type", category_val=category_selection
    )
    yoy_vol = calc_yoy_growth(curr_vol, prev_vol)
    yoy_val = calc_yoy_growth(curr_val, prev_val)
    ats_val = curr_val / curr_vol if (curr_vol and curr_val and curr_vol > 0) else 0
    
    kpi1_html = render_kpi_card("Transaction Volume", format_indian_count(curr_vol), yoy_vol, "transaction count")
    kpi2_html = render_kpi_card("Transaction Value (Revenue)", format_indian_currency(curr_val), yoy_val, f"total volume | ATS: {format_indian_currency(ats_val)}")
    kpi3_html = render_kpi_card("Registered Users", format_indian_count(curr_reg), yoy_reg, f"App Opens: {format_indian_count(curr_opens)}" if curr_opens else "App Opens: N/A", yoy_opens)

elif domain == "Insurance":
    curr_vol, curr_val, prev_vol, prev_val = fetch_kpi_data(
        "agg_insurance", "count", "amount", year, quarter_num, state_filter,
        category_col="insurance_type", category_val=category_selection
    )
    yoy_vol = calc_yoy_growth(curr_vol, prev_vol)
    yoy_val = calc_yoy_growth(curr_val, prev_val)
    ats_val = curr_val / curr_vol if (curr_vol and curr_val and curr_vol > 0) else 0
    
    kpi1_html = render_kpi_card("Insurance Volume", format_indian_count(curr_vol), yoy_vol, "policies count")
    kpi2_html = render_kpi_card("Insurance Value (Revenue)", format_indian_currency(curr_val), yoy_val, f"total volume | ATS: {format_indian_currency(ats_val)}")
    kpi3_html = render_kpi_card("Registered Users", format_indian_count(curr_reg), yoy_reg, f"App Opens: {format_indian_count(curr_opens)}" if curr_opens else "App Opens: N/A", yoy_opens)

else: # Users
    kpi1_html = render_kpi_card("Registered Users", format_indian_count(curr_reg), yoy_reg, "cumulative user base")
    kpi2_html = render_kpi_card("App Opens (Engagement)", format_indian_count(curr_opens) if curr_opens else "Data N/A", yoy_opens, "total app open events")
    
    if curr_reg and curr_opens:
        curr_ratio = curr_opens / curr_reg
        prev_ratio = prev_opens / prev_reg if (prev_reg and prev_opens) else None
        yoy_ratio = calc_yoy_growth(curr_ratio, prev_ratio)
        kpi3_html = render_kpi_card("Avg Opens per User", f"{curr_ratio:.2f}", yoy_ratio, "engagement frequency ratio")
    else:
        kpi3_html = render_kpi_card("Avg Opens per User", "N/A", None, "engagement frequency ratio")

# Render KPIs Layout
kpi_cols = st.columns(3)
with kpi_cols[0]:
    st.markdown(kpi1_html, unsafe_allow_html=True)
with kpi_cols[1]:
    st.markdown(kpi2_html, unsafe_allow_html=True)
with kpi_cols[2]:
    st.markdown(kpi3_html, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:1.25rem;'></div>", unsafe_allow_html=True)

# --- EXECUTIVE BUSINESS SUMMARY ---
summary_text = generate_business_summary(domain, year, quarter_num, state_selection, category_selection)
st.markdown(f"""
<div class="control-card" style="margin-bottom: 1.5rem; border-left: 4px solid var(--accent); background: var(--bg-subtle);">
    <div style="font-size: 0.8rem; line-height: 1.5; color: var(--text);">{summary_text}</div>
</div>
""", unsafe_allow_html=True)

# Determine database metric columns to fetch
def get_metric_column_name():
    if domain in ["Transactions", "Insurance"]:
        if metric == "Total Amount (Rs.)":
            return "SUM(amount) as val"
        elif metric == "Total Transaction Count":
            return "SUM(count) as val"
        else:
            return "(SUM(amount) / SUM(count)) as val"
    else:
        if metric == "Registered Users":
            return "MAX(registered_users) as val"
        else:
            return "SUM(app_opens) as val"

metric_expr = get_metric_column_name()

# --- MAIN TABS ROUTING ---
tab1, tab2, tab3 = st.tabs(["📍 Geovisualization Explorer", "🏆 Top Performers", "📈 Growth & CAGR Analytics"])

with tab1:
    main_viz_col, side_viz_col = st.columns([7, 5])
    
    # 1. PRIMARY VISUALIZATION COMPONENT
    with main_viz_col:
        st.markdown(f"""
        <div class="chart-wrap">
            <div class="chart-title">Primary Visualization ({viz_style})</div>
            <div class="chart-subtitle">Current Selection: {metric} of {domain} in {state_selection} ({year})</div>
        """, unsafe_allow_html=True)
        
        fig = None
        
        # --- STYLE: CHOROPLETH MAP ---
        if viz_style == "Choropleth Map":
            if not geojson_data:
                st.error("GeoJSON mapping file states_india.geojson is missing. Cannot render Choropleth Map.")
            elif not is_all_india:
                st.warning("State level district mapping selected. Choropleth Map displays country wide state distributions. Switch Select State to 'All India' to view the map.")
            else:
                # Query state-level transaction or user data for all states
                tbl = "agg_trans" if domain == "Transactions" else ("agg_insurance" if domain == "Insurance" else "agg_user")
                clauses = list(filter_clauses)
                clauses.append("state != 'India'")
                
                grp_col = "state"
                if domain == "Transactions" and category_selection != "All Categories":
                    clauses.append("transaction_type = ?")
                elif domain == "Insurance" and category_selection != "All Categories":
                    clauses.append("insurance_type = ?")
                    
                query = f"SELECT state, {metric_expr} FROM {tbl} WHERE " + " AND ".join(clauses) + " GROUP BY state"
                map_data = query_db(query, tuple(filter_params + ([category_selection] if category_selection != "All Categories" else [])))
                
                if map_data.empty:
                    st.info("No state level records found matching current filter values.")
                else:
                    # Prepare names matching GeoJSON
                    plot_df = prepare_map_df(map_data, "val")
                    
                    fig = px.choropleth(
                        plot_df,
                        geojson=geojson_data,
                        locations="st_nm",
                        featureidkey="properties.st_nm",
                        color="val",
                        color_continuous_scale=COLOR_SCALE,
                        hover_name="state",
                        labels={"val": metric}
                    )
                    fig.update_geos(fitbounds="locations", visible=False)
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=0, r=0, t=10, b=0),
                        coloraxis_colorbar=dict(
                            title=dict(text="", font=dict(size=10)),
                            tickfont=dict(size=9),
                            thickness=15
                        )
                    )
    
        # --- STYLE: BAR CHART ---
        elif viz_style == "Bar Chart":
            if is_all_india:
                # Query top states
                tbl = "agg_trans" if domain == "Transactions" else ("agg_insurance" if domain == "Insurance" else "agg_user")
                clauses = list(filter_clauses)
                clauses.append("state != 'India'")
                
                if domain == "Transactions" and category_selection != "All Categories":
                    clauses.append("transaction_type = ?")
                elif domain == "Insurance" and category_selection != "All Categories":
                    clauses.append("insurance_type = ?")
                    
                query = f"SELECT state, {metric_expr} FROM {tbl} WHERE " + " AND ".join(clauses) + f" GROUP BY state ORDER BY val DESC LIMIT {limit}"
                plot_data = query_db(query, tuple(filter_params + ([category_selection] if category_selection != "All Categories" else [])))
                
                if not plot_data.empty:
                    fig = px.bar(
                        plot_data, x="state", y="val",
                        labels={"state": "State", "val": metric}
                    )
                    fig.update_traces(marker_color=ACCENT_COLOR)
            else:
                # Query district wise map records
                tbl = "map_trans" if domain == "Transactions" else ("map_insurance" if domain == "Insurance" else "map_user")
                clauses = list(filter_clauses)
                clauses.append("state = ?")
                params = list(filter_params) + [state_selection]
                
                query = f"SELECT district, {metric_expr} FROM {tbl} WHERE " + " AND ".join(clauses) + f" GROUP BY district ORDER BY val DESC LIMIT {limit}"
                plot_data = query_db(query, tuple(params))
                
                if not plot_data.empty:
                    fig = px.bar(
                        plot_data, x="district", y="val",
                        labels={"district": "District", "val": metric}
                    )
                    fig.update_traces(marker_color=ACCENT_COLOR)
                else:
                    st.info("No district level data found for state selection.")
    
        # --- STYLE: TREND LINE ---
        elif viz_style == "Trend Line":
            # Group metrics by Year + Quarter
            tbl = "agg_trans" if domain == "Transactions" else ("agg_insurance" if domain == "Insurance" else "agg_user")
            clauses = ["state = ?"]
            params = [state_filter]
            
            if domain == "Transactions" and category_selection != "All Categories":
                clauses.append("transaction_type = ?")
                params.append(category_selection)
            elif domain == "Insurance" and category_selection != "All Categories":
                clauses.append("insurance_type = ?")
                params.append(category_selection)
                
            query = f"SELECT year, quarter, {metric_expr} FROM {tbl} WHERE " + " AND ".join(clauses) + " GROUP BY year, quarter ORDER BY year, quarter"
            plot_data = query_db(query, tuple(params))
            
            if not plot_data.empty:
                plot_data["period"] = plot_data["year"].astype(str) + " Q" + plot_data["quarter"].astype(str)
                fig = px.line(
                    plot_data, x="period", y="val",
                    labels={"period": "Time Period", "val": metric}
                )
                fig.update_traces(line=dict(color=ACCENT_COLOR, width=3), marker=dict(size=6, color=ACCENT_COLOR))
            else:
                st.info("No temporal records available for trend charts.")
    
        # --- STYLE: PIE CHART ---
        elif viz_style == "Pie Chart":
            if domain == "Users":
                # For Users, we show brand distribution from device table
                tbl = "agg_user_device"
                clauses = list(filter_clauses)
                clauses.append("state = ?")
                params = list(filter_params) + [state_filter]
                
                query = f"SELECT brand, SUM(count) as val FROM {tbl} WHERE " + " AND ".join(clauses) + f" GROUP BY brand ORDER BY val DESC LIMIT {limit}"
                plot_data = query_db(query, tuple(params))
                
                if not plot_data.empty:
                    fig = px.pie(plot_data, values="val", names="brand", hole=0.4)
                else:
                    st.info("No brand distribution data found for user selections.")
            else:
                # For Transactions/Insurance, we show category distribution
                tbl = "agg_trans" if domain == "Transactions" else "agg_insurance"
                type_col = "transaction_type" if domain == "Transactions" else "insurance_type"
                clauses = list(filter_clauses)
                clauses.append("state = ?")
                params = list(filter_params) + [state_filter]
                
                query = f"SELECT {type_col} as category, {metric_expr} FROM {tbl} WHERE " + " AND ".join(clauses) + " GROUP BY category"
                plot_data = query_db(query, tuple(params))
                
                if not plot_data.empty:
                    fig = px.pie(plot_data, values="val", names="category", hole=0.4)
                    fig.update_traces(marker=dict(colors=px.colors.sequential.Aggrnyl))
                else:
                    st.info("No transactional category records available for pie charts.")
    
        if fig is not None:
            fig.update_layout(**PLOT_LAYOUT)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown("<div style='height:280px; display:flex; align-items:center; justify-content:center; color:var(--text-muted);'>Chart cannot be rendered for this selection combination.</div>", unsafe_allow_html=True)
    
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 2. SIDEBAR / SECONDARY BREAKDOWN PANEL
    with side_viz_col:
        st.markdown("""
        <div class="chart-wrap">
            <div class="chart-title">Leaderboards & Tabular Rankings</div>
            <div class="chart-subtitle">Top regions sorted by the selected metric</div>
        """, unsafe_allow_html=True)
        
        # Query rankings based on selections
        rank_df = pd.DataFrame()
        
        if mode == "Aggregated Summary" or is_all_india:
            # Show top States
            tbl = "agg_trans" if domain == "Transactions" else ("agg_insurance" if domain == "Insurance" else "agg_user")
            clauses = list(filter_clauses)
            clauses.append("state != 'India'")
            params = list(filter_params)
            
            if domain in ["Transactions", "Insurance"] and category_selection != "All Categories":
                type_col = "transaction_type" if domain == "Transactions" else "insurance_type"
                clauses.append(f"{type_col} = ?")
                params.append(category_selection)
                
            query = f"SELECT state as Name, {metric_expr} FROM {tbl} WHERE " + " AND ".join(clauses) + f" GROUP BY state ORDER BY val DESC LIMIT {limit}"
            rank_df = query_db(query, tuple(params))
        else:
            # Show top Districts inside the selected State
            tbl = "map_trans" if domain == "Transactions" else ("map_insurance" if domain == "Insurance" else "map_user")
            clauses = list(filter_clauses)
            clauses.append("state = ?")
            params = list(filter_params) + [state_selection]
            
            query = f"SELECT district as Name, {metric_expr} FROM {tbl} WHERE " + " AND ".join(clauses) + f" GROUP BY district ORDER BY val DESC LIMIT {limit}"
            rank_df = query_db(query, tuple(params))
            
        if rank_df.empty:
            st.markdown("<div style='height:180px; display:flex; align-items:center; justify-content:center; color:var(--text-muted);'>No rankings available for selected filters.</div>", unsafe_allow_html=True)
        else:
            # Format the ranking data
            rank_df.index = range(1, len(rank_df) + 1)
            rank_df.columns = ["Region/Area Name", "Metric Value"]
            
            # Format the metric value neatly
            is_money = "Amount" in metric or "Value" in metric
            if is_money:
                rank_df["Metric Value"] = rank_df["Metric Value"].apply(format_indian_currency)
            else:
                rank_df["Metric Value"] = rank_df["Metric Value"].apply(format_indian_count)
                
            # Draw custom HTML table
            rows_html = ""
            for idx, row in rank_df.iterrows():
                badge_class = "badge-accent" if idx == 1 else "badge-blue"
                rows_html += f"""
                <tr>
                    <td><span class="badge {badge_class}">{idx}</span></td>
                    <td>{row['Region/Area Name']}</td>
                    <td style="font-family:'JetBrains Mono', monospace; text-align:right;">{row['Metric Value']}</td>
                </tr>
                """
                
            st.markdown(f"""
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 50px;">Rank</th>
                        <th>Region Name</th>
                        <th style="text-align: right;">Metric Value</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            """, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Add secondary metrics row
    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)
    bot_cols = st.columns(2)
    
    with bot_cols[0]:
        st.markdown("""
        <div class="chart-wrap">
            <div class="chart-title">Payment Category / User Segmentation Share</div>
            <div class="chart-subtitle">Percentage contribution breakdown</div>
        """, unsafe_allow_html=True)
        
        # Query category share
        sub_df = pd.DataFrame()
        if domain in ["Transactions", "Insurance"]:
            tbl = "agg_trans" if domain == "Transactions" else "agg_insurance"
            type_col = "transaction_type" if domain == "Transactions" else "insurance_type"
            
            clauses = list(filter_clauses)
            clauses.append("state = ?")
            params = list(filter_params) + [state_filter]
            
            query = f"SELECT {type_col} as category, SUM(amount) as amount_sum FROM {tbl} WHERE " + " AND ".join(clauses) + " GROUP BY category"
            sub_df = query_db(query, tuple(params))
            
            if not sub_df.empty:
                sub_df["Percentage"] = (sub_df["amount_sum"] / sub_df["amount_sum"].sum()) * 100
                sub_df["Amount Formatted"] = sub_df["amount_sum"].apply(format_indian_currency)
                sub_df.columns = ["Category", "Raw", "Share (%)", "Amount"]
                
                fig2 = px.bar(
                    sub_df, y="Category", x="Share (%)", orientation="h",
                    text=sub_df["Share (%)"].apply(lambda x: f"{x:.1f}%")
                )
                fig2.update_traces(marker_color=ACCENT_COLOR, textposition="inside")
                fig2.update_layout(**PLOT_LAYOUT)
                fig2.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No distribution breakdown available.")
        else:
            # User Brand Share
            tbl = "agg_user_device"
            clauses = list(filter_clauses)
            clauses.append("state = ?")
            params = list(filter_params) + [state_filter]
            
            query = f"SELECT brand as Brand, SUM(count) as user_count FROM {tbl} WHERE " + " AND ".join(clauses) + " GROUP BY Brand"
            sub_df = query_db(query, tuple(params))
            
            if not sub_df.empty:
                sub_df["Share (%)"] = (sub_df["user_count"] / sub_df["user_count"].sum()) * 100
                
                fig2 = px.bar(
                    sub_df, y="Brand", x="Share (%)", orientation="h",
                    text=sub_df["Share (%)"].apply(lambda x: f"{x:.1f}%")
                )
                fig2.update_traces(marker_color=ACCENT_COLOR, textposition="inside")
                fig2.update_layout(**PLOT_LAYOUT)
                fig2.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No device distribution records available.")
                
        st.markdown("</div>", unsafe_allow_html=True)
    
    with bot_cols[1]:
        st.markdown("""
        <div class="chart-wrap">
            <div class="chart-title">Quarterly Performance Comparisons</div>
            <div class="chart-subtitle">Quarter-on-quarter growth indices</div>
        """, unsafe_allow_html=True)
        
        # Query Q1-Q4 comparison for selected year
        tbl = "agg_trans" if domain == "Transactions" else ("agg_insurance" if domain == "Insurance" else "agg_user")
        clauses = ["year = ?", "state = ?"]
        params = [year, state_filter]
        
        if domain in ["Transactions", "Insurance"] and category_selection != "All Categories":
            type_col = "transaction_type" if domain == "Transactions" else "insurance_type"
            clauses.append(f"{type_col} = ?")
            params.append(category_selection)
            
        query = f"SELECT quarter, {metric_expr} FROM {tbl} WHERE " + " AND ".join(clauses) + " GROUP BY quarter ORDER BY quarter"
        q_df = query_db(query, tuple(params))
        
        if q_df.empty or len(q_df) < 2:
            st.markdown("<div style='height:230px; display:flex; align-items:center; justify-content:center; color:var(--text-muted);'>Insufficient quarterly data points in selected year.</div>", unsafe_allow_html=True)
        else:
            q_df["Quarter"] = "Q" + q_df["quarter"].astype(str)
            fig3 = px.bar(
                q_df, x="Quarter", y="val",
                labels={"val": metric}
            )
            fig3.update_traces(marker_color=ACCENT_COLOR)
            fig3.update_layout(**PLOT_LAYOUT)
            fig3.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
    top_col1, top_col2 = st.columns(2)
    
    if domain in ["Transactions", "Insurance"]:
        tbl_dist = "top_trans_district" if domain == "Transactions" else "top_insurance_district"
        tbl_pin = "top_trans_pincode" if domain == "Transactions" else "top_insurance_pincode"
        
        sort_field = "amount" if "Amount" in metric or "Value" in metric else "count"
        metric_sql = "SUM(count) as count, SUM(amount) as amount"
        
        dist_df = fetch_top_performers(tbl_dist, "district", metric_sql, sort_field, year, quarter_num, state_selection, limit)
        pin_df = fetch_top_performers(tbl_pin, "pincode", metric_sql, sort_field, year, quarter_num, state_selection, limit)
        
        with top_col1:
            st.markdown(f"""
            <div class="chart-wrap">
                <div class="chart-title">🏆 Top {limit} Districts (Transactions)</div>
                <div class="chart-subtitle">Ranked by {metric} for {state_selection} ({year} {quarter if quarter_num else ""})</div>
            """, unsafe_allow_html=True)
            
            if dist_df.empty:
                st.markdown("<div style='height:180px; display:flex; align-items:center; justify-content:center; color:var(--text-muted);'>No district data found.</div>", unsafe_allow_html=True)
            else:
                dist_df["val"] = dist_df[sort_field]
                fig_top_dist = px.bar(dist_df, x="district", y="val", labels={"district": "District", "val": metric})
                fig_top_dist.update_traces(marker_color=ACCENT_COLOR)
                fig_top_dist.update_layout(**PLOT_LAYOUT)
                st.plotly_chart(fig_top_dist, use_container_width=True, config={"displayModeBar": False})
                
                rows_html = ""
                for idx, row in enumerate(dist_df.itertuples(), 1):
                    badge_class = "badge-accent" if idx == 1 else "badge-blue"
                    val_fmt = format_indian_currency(row.val) if sort_field == "amount" else format_indian_count(row.val)
                    loc_name = f"{row.state} - {row.district}" if is_all_india else row.district
                    rows_html += f"""
                    <tr>
                        <td><span class="badge {badge_class}">{idx}</span></td>
                        <td>{loc_name}</td>
                        <td style="font-family:'JetBrains Mono', monospace; text-align:right;">{val_fmt}</td>
                    </tr>
                    """
                st.markdown(f"""
                <table class="data-table">
                    <thead><tr><th style='width:50px;'>Rank</th><th>District</th><th style='text-align:right;'>{metric}</th></tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with top_col2:
            st.markdown(f"""
            <div class="chart-wrap">
                <div class="chart-title">🏆 Top {limit} Pincodes (Transactions)</div>
                <div class="chart-subtitle">Ranked by {metric} for {state_selection} ({year} {quarter if quarter_num else ""})</div>
            """, unsafe_allow_html=True)
            
            if pin_df.empty:
                st.markdown("<div style='height:180px; display:flex; align-items:center; justify-content:center; color:var(--text-muted);'>No pincode data found.</div>", unsafe_allow_html=True)
            else:
                pin_df["val"] = pin_df[sort_field]
                fig_top_pin = px.bar(pin_df, x="pincode", y="val", labels={"pincode": "Pincode", "val": metric})
                fig_top_pin.update_traces(marker_color=ACCENT_COLOR)
                fig_top_pin.update_layout(**PLOT_LAYOUT)
                st.plotly_chart(fig_top_pin, use_container_width=True, config={"displayModeBar": False})
                
                rows_html = ""
                for idx, row in enumerate(pin_df.itertuples(), 1):
                    badge_class = "badge-accent" if idx == 1 else "badge-blue"
                    val_fmt = format_indian_currency(row.val) if sort_field == "amount" else format_indian_count(row.val)
                    loc_name = f"{row.state} - {row.pincode}" if is_all_india else row.pincode
                    rows_html += f"""
                    <tr>
                        <td><span class="badge {badge_class}">{idx}</span></td>
                        <td>{loc_name}</td>
                        <td style="font-family:'JetBrains Mono', monospace; text-align:right;">{val_fmt}</td>
                    </tr>
                    """
                st.markdown(f"""
                <table class="data-table">
                    <thead><tr><th style='width:50px;'>Rank</th><th>Pincode</th><th style='text-align:right;'>{metric}</th></tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
    else: # Users Domain
        sort_field = "registered_users"
        metric_sql = "MAX(registered_users) as registered_users"
        
        dist_df = fetch_top_performers("top_user_district", "district", metric_sql, sort_field, year, quarter_num, state_selection, limit)
        pin_df = fetch_top_performers("top_user_pincode", "pincode", metric_sql, sort_field, year, quarter_num, state_selection, limit)
        
        with top_col1:
            st.markdown(f"""
            <div class="chart-wrap">
                <div class="chart-title">🏆 Top {limit} Districts (Users)</div>
                <div class="chart-subtitle">Ranked by Registered Users for {state_selection} ({year} {quarter if quarter_num else ""})</div>
            """, unsafe_allow_html=True)
            
            if dist_df.empty:
                st.markdown("<div style='height:180px; display:flex; align-items:center; justify-content:center; color:var(--text-muted);'>No district user data found.</div>", unsafe_allow_html=True)
            else:
                dist_df["val"] = dist_df[sort_field]
                fig_top_dist = px.bar(dist_df, x="district", y="val", labels={"district": "District", "val": "Registered Users"})
                fig_top_dist.update_traces(marker_color=ACCENT_COLOR)
                fig_top_dist.update_layout(**PLOT_LAYOUT)
                st.plotly_chart(fig_top_dist, use_container_width=True, config={"displayModeBar": False})
                
                rows_html = ""
                for idx, row in enumerate(dist_df.itertuples(), 1):
                    badge_class = "badge-accent" if idx == 1 else "badge-blue"
                    val_fmt = format_indian_count(row.val)
                    loc_name = f"{row.state} - {row.district}" if is_all_india else row.district
                    rows_html += f"""
                    <tr>
                        <td><span class="badge {badge_class}">{idx}</span></td>
                        <td>{loc_name}</td>
                        <td style="font-family:'JetBrains Mono', monospace; text-align:right;">{val_fmt}</td>
                    </tr>
                    """
                st.markdown(f"""
                <table class="data-table">
                    <thead><tr><th style='width:50px;'>Rank</th><th>District</th><th style='text-align:right;'>Registered Users</th></tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with top_col2:
            st.markdown(f"""
            <div class="chart-wrap">
                <div class="chart-title">🏆 Top {limit} Pincodes (Users)</div>
                <div class="chart-subtitle">Ranked by Registered Users for {state_selection} ({year} {quarter if quarter_num else ""})</div>
            """, unsafe_allow_html=True)
            
            if pin_df.empty:
                st.markdown("<div style='height:180px; display:flex; align-items:center; justify-content:center; color:var(--text-muted);'>No pincode user data found.</div>", unsafe_allow_html=True)
            else:
                pin_df["val"] = pin_df[sort_field]
                fig_top_pin = px.bar(pin_df, x="pincode", y="val", labels={"pincode": "Pincode", "val": "Registered Users"})
                fig_top_pin.update_traces(marker_color=ACCENT_COLOR)
                fig_top_pin.update_layout(**PLOT_LAYOUT)
                st.plotly_chart(fig_top_pin, use_container_width=True, config={"displayModeBar": False})
                
                rows_html = ""
                for idx, row in enumerate(pin_df.itertuples(), 1):
                    badge_class = "badge-accent" if idx == 1 else "badge-blue"
                    val_fmt = format_indian_count(row.val)
                    loc_name = f"{row.state} - {row.pincode}" if is_all_india else row.pincode
                    rows_html += f"""
                    <tr>
                        <td><span class="badge {badge_class}">{idx}</span></td>
                        <td>{loc_name}</td>
                        <td style="font-family:'JetBrains Mono', monospace; text-align:right;">{val_fmt}</td>
                    </tr>
                    """
                st.markdown(f"""
                <table class="data-table">
                    <thead><tr><th style='width:50px;'>Rank</th><th>Pincode</th><th style='text-align:right;'>Registered Users</th></tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # Historical Time Series query
    tbl_ts = "agg_trans" if domain == "Transactions" else ("agg_insurance" if domain == "Insurance" else "agg_user")
    clauses_ts = ["state = ?"]
    params_ts = [state_filter]
    
    if domain in ["Transactions", "Insurance"] and category_selection != "All Categories":
        type_col = "transaction_type" if domain == "Transactions" else "insurance_type"
        clauses_ts.append(f"{type_col} = ?")
        params_ts.append(category_selection)
        
    query_ts = f"SELECT year, quarter, {metric_expr} FROM {tbl_ts} WHERE " + " AND ".join(clauses_ts) + " GROUP BY year, quarter ORDER BY year, quarter"
    df_ts = query_db(query_ts, tuple(params_ts))
    
    if df_ts.empty or len(df_ts) < 2:
        st.markdown("<div style='height:180px; display:flex; align-items:center; justify-content:center; color:var(--text-muted);'>Insufficient historical data points to perform growth analysis for this selection.</div>", unsafe_allow_html=True)
    else:
        df_yoy = df_ts.copy()
        df_prev = df_ts.copy()
        df_prev["year"] = df_prev["year"] + 1
        df_prev = df_prev.rename(columns={"val": "prev_val"})
        df_merged = pd.merge(df_yoy, df_prev, on=["year", "quarter"], how="inner")
        df_merged["yoy_growth"] = ((df_merged["val"] - df_merged["prev_val"]) / df_merged["prev_val"]) * 100
        df_merged["period"] = df_merged["year"].astype(str) + " Q" + df_merged["quarter"].astype(str)
        
        df_sorted = df_ts.sort_values(["year", "quarter"]).reset_index(drop=True)
        n_quarters = len(df_sorted) - 1
        start_val = df_sorted["val"].iloc[0]
        end_val = df_sorted["val"].iloc[-1]
        
        cagr = None
        if n_quarters > 0 and start_val > 0 and end_val > 0:
            q_cagr = (end_val / start_val) ** (1 / n_quarters) - 1
            cagr = ((1 + q_cagr) ** 4 - 1) * 100
            
        avg_yoy = df_merged["yoy_growth"].mean() if not df_merged.empty else None
        peak_idx = df_merged["yoy_growth"].idxmax() if not df_merged.empty else None
        peak_row = df_merged.loc[peak_idx] if peak_idx is not None else None
        peak_period = peak_row["period"] if peak_row is not None else "N/A"
        peak_val = peak_row["yoy_growth"] if peak_row is not None else None
        
        # Render Growth cards
        g_col1, g_col2, g_col3 = st.columns(3)
        with g_col1:
            cagr_fmt = f"{cagr:.1f}%" if cagr is not None else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Compound Annual Growth Rate (CAGR)</div>
                <div class="metric-value" style="color:var(--accent);">{cagr_fmt}</div>
                <div class="metric-subtext">Overall growth rate from {df_sorted['year'].iloc[0]} Q{df_sorted['quarter'].iloc[0]} to {df_sorted['year'].iloc[-1]} Q{df_sorted['quarter'].iloc[-1]}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with g_col2:
            avg_yoy_fmt = f"{avg_yoy:.1f}%" if avg_yoy is not None else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Average YoY Growth Rate</div>
                <div class="metric-value">{avg_yoy_fmt}</div>
                <div class="metric-subtext">Mean of all quarterly YoY growth records</div>
            </div>
            """, unsafe_allow_html=True)
            
        with g_col3:
            peak_fmt = f"+{peak_val:.1f}%" if peak_val is not None else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Peak YoY Growth Quarter</div>
                <div class="metric-value">{peak_fmt}</div>
                <div class="metric-subtext">Highest YoY growth recorded in {peak_period}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)
        
        # Trend line and YoY charts side-by-side
        g_chart1, g_chart2 = st.columns(2)
        
        with g_chart1:
            st.markdown(f"""
            <div class="chart-wrap">
                <div class="chart-title">Historical Timeline Trend ({metric})</div>
                <div class="chart-subtitle">Raw metric values in {state_selection} (2018-2024)</div>
            """, unsafe_allow_html=True)
            
            df_sorted["period"] = df_sorted["year"].astype(str) + " Q" + df_sorted["quarter"].astype(str)
            fig_ts = px.line(df_sorted, x="period", y="val", labels={"period": "Period", "val": metric})
            fig_ts.update_traces(line=dict(color=ACCENT_COLOR, width=3), marker=dict(size=6, color=ACCENT_COLOR))
            fig_ts.update_layout(**PLOT_LAYOUT)
            st.plotly_chart(fig_ts, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
            
        with g_chart2:
            st.markdown(f"""
            <div class="chart-wrap">
                <div class="chart-title">Year-over-Year Growth Rate (%) by Quarter</div>
                <div class="chart-subtitle">Comparison against corresponding quarter of the previous year</div>
            """, unsafe_allow_html=True)
            
            if df_merged.empty:
                st.markdown("<div style='height:180px; display:flex; align-items:center; justify-content:center; color:var(--text-muted);'>No YoY comparison points available.</div>", unsafe_allow_html=True)
            else:
                fig_yoy = px.bar(df_merged, x="period", y="yoy_growth", labels={"period": "Period", "yoy_growth": "YoY Growth (%)"})
                colors = ['#10b981' if x >= 0 else '#ef4444' for x in df_merged["yoy_growth"]]
                fig_yoy.update_traces(marker_color=colors)
                fig_yoy.update_layout(**PLOT_LAYOUT)
                st.plotly_chart(fig_yoy, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

# Footer info
st.markdown(f"""
<div style="text-align:center; padding: 1.5rem 0 0.5rem; color:var(--text-dim); font-size:0.75rem;">
    Phonepe Pulse Geovisualization Dashboard &bull; Designed with Zinc aesthetics &bull; Data licensed under CDLA-Permissive-2.0
</div>
""", unsafe_allow_html=True)
