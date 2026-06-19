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

# --- KPI CARD CALCULATIONS ---
kpis = {"metric_val": 0, "volume_val": 0, "amount_val": 0}

if domain == "Transactions" or domain == "Insurance":
    tbl = "agg_trans" if domain == "Transactions" else "agg_insurance"
    type_col = "transaction_type" if domain == "Transactions" else "insurance_type"
    
    # Base query for totals
    q_filter = list(filter_params)
    q_clauses = list(filter_clauses)
    q_clauses.append("state = ?")
    q_filter.append(state_filter)
    
    if category_selection != "All Categories":
        q_clauses.append(f"{type_col} = ?")
        q_filter.append(category_selection)
        
    query_kpi = f"SELECT SUM(count) as total_count, SUM(amount) as total_amount FROM {tbl} WHERE " + " AND ".join(q_clauses)
    kpi_df = query_db(query_kpi, tuple(q_filter))
    
    if not kpi_df.empty and kpi_df["total_count"].iloc[0] is not None:
        cnt = kpi_df["total_count"].iloc[0]
        amt = kpi_df["total_amount"].iloc[0]
        kpis["volume_val"] = cnt
        kpis["amount_val"] = amt
        if metric == "Total Amount (Rs.)":
            kpis["metric_val"] = format_indian_currency(amt)
        elif metric == "Total Transaction Count":
            kpis["metric_val"] = format_indian_count(cnt)
        else:
            kpis["metric_val"] = format_indian_currency(amt / cnt if cnt > 0 else 0)
    else:
        kpis["metric_val"] = "Rs. 0" if "Amount" in metric or "Value" in metric else "0"

elif domain == "Users":
    q_filter = list(filter_params)
    q_clauses = list(filter_clauses)
    q_clauses.append("state = ?")
    q_filter.append(state_filter)
    
    query_kpi = f"SELECT MAX(registered_users) as reg_users, SUM(app_opens) as app_ops FROM agg_user WHERE " + " AND ".join(q_clauses)
    kpi_df = query_db(query_kpi, tuple(q_filter))
    
    if not kpi_df.empty and kpi_df["reg_users"].iloc[0] is not None:
        reg = kpi_df["reg_users"].iloc[0]
        ops = kpi_df["app_ops"].iloc[0]
        kpis["volume_val"] = reg
        kpis["amount_val"] = ops if ops else 0
        if metric == "Registered Users":
            kpis["metric_val"] = format_indian_count(reg)
        else:
            kpis["metric_val"] = format_indian_count(ops) if ops else "Data N/A"
    else:
        kpis["metric_val"] = "0"

# Render KPIs Layout
kpi_cols = st.columns(3)
with kpi_cols[0]:
    # Card 1: Selected Metric
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Selected Metric: {metric}</div>
        <div class="metric-value">{kpis["metric_val"]}</div>
        <div class="metric-subtext">Filters: {state_selection} | {year} | {quarter}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[1]:
    # Card 2: Domain Volume
    label = "Total Transactions" if domain in ["Transactions", "Insurance"] else "Registered Users"
    val = format_indian_count(kpis["volume_val"])
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:var(--accent);">{val}</div>
        <div class="metric-subtext">Cumulative sum or maximum state boundary count</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[2]:
    # Card 3: Domain Secondary Metric (Amount or App Opens)
    if domain in ["Transactions", "Insurance"]:
        label = "Total Payment Volume"
        val = format_indian_currency(kpis["amount_val"])
    else:
        label = "Total App Opens"
        val = format_indian_count(kpis["amount_val"]) if kpis["amount_val"] > 0 else "Data N/A"
        
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{val}</div>
        <div class="metric-subtext">Aggregated financial value or app open events</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

# --- VISUALIZATION DRAWING ---
main_viz_col, side_viz_col = st.columns([7, 5])

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
                # Map colors using accent theme
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

# Add a secondary metrics row for deep insights
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

# Footer info
st.markdown(f"""
<div style="text-align:center; padding: 1.5rem 0 0.5rem; color:var(--text-dim); font-size:0.75rem;">
    Phonepe Pulse Geovisualization Dashboard &bull; Designed with Zinc aesthetics &bull; Data licensed under CDLA-Permissive-2.0
</div>
""", unsafe_allow_html=True)
