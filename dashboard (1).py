import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
import os
warnings.filterwarnings('ignore')

# ── FIND CSV AUTOMATICALLY ────────────────────────────────────────────────────
CSV_NAME = "Nassau Candy Distributor.csv"

def find_csv():
    # 1. Same folder as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(script_dir, CSV_NAME)
    if os.path.exists(candidate):
        return candidate
    # 2. Current working directory
    candidate = os.path.join(os.getcwd(), CSV_NAME)
    if os.path.exists(candidate):
        return candidate
    return None

CSV_PATH = find_csv()
if CSV_PATH is None:
    st.error(f"❌ Cannot find **{CSV_NAME}**. Please place it in the same folder as dashboard.py and restart.")
    st.stop()

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nassau Candy | Logistics Dashboard",
    page_icon="🍫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background - light */
    .stApp { background-color: #ffffff; color: #1a202c; }

    /* Sidebar - dark navy */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a202c 0%, #2d3748 100%);
        border-right: 3px solid #4a5568;
    }
    section[data-testid="stSidebar"] * { color: #ffffff !important; }

    /* Metric cards - dark with bright white text */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        border: 2px solid #4299e1;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.25);
    }
    [data-testid="metric-container"] label {
        color: #90cdf4 !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 28px !important;
        font-weight: 800 !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricDelta"] {
        color: #68d391 !important;
        font-size: 12px !important;
        font-weight: 700 !important;
    }

    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #2d3748, #4a5568);
        border-left: 5px solid #4299e1;
        padding: 12px 20px;
        margin: 28px 0 18px 0;
        border-radius: 0 10px 10px 0;
        font-size: 16px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.5px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #2d3748;
        border-radius: 12px;
        padding: 6px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #a0aec0 !important;
        font-weight: 700;
        font-size: 14px;
        padding: 10px 22px;
    }
    .stTabs [aria-selected="true"] {
        background: #4299e1 !important;
        color: #ffffff !important;
    }

    /* Dataframe */
    .stDataFrame { border-radius: 10px; overflow: hidden; }

    /* Alert boxes */
    .stAlert { border-radius: 10px; font-weight: 600; }

    /* Title */
    .main-title {
        background: linear-gradient(90deg, #2b6cb0, #e53e3e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 36px;
        font-weight: 900;
    }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        margin: 2px;
    }
    .badge-green  { background: #c6f6d5; color: #22543d; border: 1px solid #9ae6b4; }
    .badge-red    { background: #fed7d7; color: #742a2a; border: 1px solid #fc8181; }
    .badge-yellow { background: #fefcbf; color: #744210; border: 1px solid #f6e05e; }

    /* Plotly chart */
    .js-plotly-plot { border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }

    /* Divider */
    hr { border-color: #4a5568; border-width: 2px; }
</style>
""", unsafe_allow_html=True)

# ── PLOTLY DARK THEME ─────────────────────────────────────────────────────────
PLOT_THEME = dict(
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    font=dict(color="#1a202c", family="Arial", size=13),
    xaxis=dict(gridcolor="#e2e8f0", zerolinecolor="#cbd5e0", color="#1a202c"),
    yaxis=dict(gridcolor="#e2e8f0", zerolinecolor="#cbd5e0", color="#1a202c"),
    margin=dict(l=40, r=20, t=50, b=40),
    title_font=dict(color="#1a202c", size=15, family="Arial"),
)
COLORS = {
    "teal":   "#0694a2",
    "purple": "#7e3af2",
    "red":    "#e02424",
    "orange": "#d97706",
    "yellow": "#f59e0b",
    "blue":   "#1c64f2",
    "green":  "#057a55",
    "pink":   "#e74694",
}
PALETTE = list(COLORS.values())

# ── DATA LOADING ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH)
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d-%m-%Y")
    df["Ship Date"]  = pd.to_datetime(df["Ship Date"],  format="%d-%m-%Y")
    df["Lead Time (Days)"] = (df["Ship Date"] - df["Order Date"]).dt.days
    df["Order Month"] = df["Order Date"].dt.to_period("M").astype(str)
    df["Order Year"]  = df["Order Date"].dt.year
    df["Profit Margin %"] = (df["Gross Profit"] / df["Sales"] * 100).round(2)
    p90 = df["Lead Time (Days)"].quantile(0.90)
    df["Is_Delayed"] = df["Lead Time (Days)"] > p90
    return df

df = load_data()
overall_mean = df["Lead Time (Days)"].mean()
p90_threshold = df["Lead Time (Days)"].quantile(0.90)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🍫 Nassau Candy")
    st.markdown("**Logistics Intelligence Dashboard**")
    st.markdown("---")

    st.markdown("### 🔎 Filters")

    # Region filter
    all_regions = sorted(df["Region"].unique().tolist())
    sel_regions = st.multiselect("Region", all_regions, default=all_regions)

    # Ship Mode filter
    all_modes = sorted(df["Ship Mode"].unique().tolist())
    sel_modes = st.multiselect("Ship Mode", all_modes, default=all_modes)

    # Division filter
    all_divs = sorted(df["Division"].unique().tolist())
    sel_divs = st.multiselect("Division", all_divs, default=all_divs)

    # Lead time range slider
    lt_min = int(df["Lead Time (Days)"].min())
    lt_max = int(df["Lead Time (Days)"].max())
    lt_range = st.slider("Lead Time Range (Days)", lt_min, lt_max, (lt_min, lt_max))

    # Min shipments threshold
    min_orders = st.slider("Min Shipments (for State Analysis)", 10, 200, 50)

    st.markdown("---")
    st.markdown("### 📊 Dataset")
    st.metric("Total Records", f"{len(df):,}")
    st.metric("Date Range", "Jan 2024 – Dec 2025")
    st.markdown("---")
    st.caption("Analytics & Logistics Division · April 2026")

# ── FILTER DATA ───────────────────────────────────────────────────────────────
fdf = df[
    df["Region"].isin(sel_regions) &
    df["Ship Mode"].isin(sel_modes) &
    df["Division"].isin(sel_divs) &
    df["Lead Time (Days)"].between(lt_range[0], lt_range[1])
].copy()

if fdf.empty:
    st.warning("No data matches the current filters. Please adjust the sidebar filters.")
    st.stop()

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">Nassau Candy Distributor</p>', unsafe_allow_html=True)
st.markdown("##### 🚚 Logistics Route Efficiency & Bottleneck Analytics · Live Dashboard")
st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview", "🗺️ Regional", "🚢 Ship Mode", "📍 State Routes", "⚠️ Bottlenecks", "💰 Financials"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">⚡ KPI Scorecard</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.metric("Total Shipments",    f"{len(fdf):,}",           delta=f"{len(fdf)-len(df):+,} vs unfiltered")
    with c2: st.metric("Avg Lead Time",      f"{fdf['Lead Time (Days)'].mean():.1f}d",  delta=f"{fdf['Lead Time (Days)'].mean()-overall_mean:+.1f}d vs network")
    with c3: st.metric("Median Lead Time",   f"{fdf['Lead Time (Days)'].median():.0f}d")
    with c4: st.metric("Std Dev",            f"{fdf['Lead Time (Days)'].std():.1f}d")
    with c5: st.metric("Total Revenue",      f"${fdf['Sales'].sum():,.0f}")
    with c6: st.metric("Total Profit",       f"${fdf['Gross Profit'].sum():,.0f}",      delta=f"{fdf['Gross Profit'].sum()/fdf['Sales'].sum()*100:.1f}% margin")

    st.markdown("")
    c7, c8, c9, c10 = st.columns(4)
    with c7:  st.metric("Best Lead Time",  f"{fdf['Lead Time (Days)'].min()} days")
    with c8:  st.metric("Worst Lead Time", f"{fdf['Lead Time (Days)'].max()} days")
    with c9:  st.metric("Delayed Orders",  f"{fdf['Is_Delayed'].sum():,}",  delta=f"{fdf['Is_Delayed'].mean()*100:.1f}% of total")
    with c10: st.metric("States Covered",  f"{fdf['State/Province'].nunique()}")

    st.markdown('<div class="section-header">📈 Lead Time Distribution</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns([2, 1])

    with col_a:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=fdf["Lead Time (Days)"], nbinsx=60,
            marker_color=COLORS["teal"], opacity=0.8, name="Shipments"
        ))
        fig_hist.add_vline(x=fdf["Lead Time (Days)"].mean(),   line_dash="dash", line_color=COLORS["red"],    annotation_text=f"Mean: {fdf['Lead Time (Days)'].mean():.0f}")
        fig_hist.add_vline(x=fdf["Lead Time (Days)"].median(), line_dash="dash", line_color=COLORS["yellow"], annotation_text=f"Median: {fdf['Lead Time (Days)'].median():.0f}")
        fig_hist.add_vline(x=p90_threshold, line_dash="dot",   line_color=COLORS["orange"], annotation_text=f"P90: {p90_threshold:.0f}")
        fig_hist.update_layout(**PLOT_THEME, title="Lead Time Frequency Distribution", height=340, showlegend=False)
        st.plotly_chart(fig_hist, width="stretch")

    with col_b:
        fig_box = go.Figure()
        for i, region in enumerate(sorted(fdf["Region"].unique())):
            fig_box.add_trace(go.Box(
                y=fdf[fdf["Region"]==region]["Lead Time (Days)"],
                name=region, marker_color=PALETTE[i], boxmean=True
            ))
        fig_box.update_layout(**PLOT_THEME, title="Lead Time Box Plot by Region", height=340, showlegend=False)
        st.plotly_chart(fig_box, width="stretch")

    st.markdown('<div class="section-header">📅 Monthly Shipment Trends</div>', unsafe_allow_html=True)
    monthly = fdf.groupby("Order Month").agg(
        Orders=("Lead Time (Days)", "count"),
        Avg_LT=("Lead Time (Days)", "mean"),
        Revenue=("Sales", "sum")
    ).reset_index().sort_values("Order Month")

    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    fig_trend.add_trace(go.Bar(x=monthly["Order Month"], y=monthly["Orders"], name="Shipments", marker_color=COLORS["blue"], opacity=0.7), secondary_y=False)
    fig_trend.add_trace(go.Scatter(x=monthly["Order Month"], y=monthly["Avg_LT"], name="Avg Lead Time", line=dict(color=COLORS["teal"], width=3), mode="lines+markers"), secondary_y=True)
    fig_trend.update_layout(**PLOT_THEME, title="Monthly Shipment Volume & Avg Lead Time", height=320, legend=dict(orientation="h", y=1.1))
    fig_trend.update_yaxes(title_text="Shipment Count", secondary_y=False, gridcolor="#2d3250")
    fig_trend.update_yaxes(title_text="Avg Lead Time (Days)", secondary_y=True, gridcolor="#2d3250")
    st.plotly_chart(fig_trend, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — REGIONAL
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">🌎 Regional Performance Overview</div>', unsafe_allow_html=True)

    region_stats = fdf.groupby("Region").agg(
        Orders=("Lead Time (Days)", "count"),
        Avg_LT=("Lead Time (Days)", "mean"),
        Median_LT=("Lead Time (Days)", "median"),
        Std_Dev=("Lead Time (Days)", "std"),
        Min_LT=("Lead Time (Days)", "min"),
        Max_LT=("Lead Time (Days)", "max"),
        Revenue=("Sales", "sum"),
        Profit=("Gross Profit", "sum"),
    ).round(2).reset_index().sort_values("Avg_LT")

    col1, col2 = st.columns(2)

    with col1:
        fig_reg_bar = go.Figure()
        colors_reg = [COLORS["green"] if v <= overall_mean else COLORS["red"] for v in region_stats["Avg_LT"]]
        fig_reg_bar.add_trace(go.Bar(
            x=region_stats["Avg_LT"], y=region_stats["Region"],
            orientation="h", marker_color=colors_reg,
            text=region_stats["Avg_LT"].round(1), textposition="outside",
            error_x=dict(type="data", array=region_stats["Std_Dev"], color="#8892b0")
        ))
        fig_reg_bar.add_vline(x=overall_mean, line_dash="dash", line_color=COLORS["yellow"], annotation_text=f"Network Avg: {overall_mean:.0f}")
        fig_reg_bar.update_layout(**PLOT_THEME, title="Regional Avg Lead Time (± Std Dev)", height=320, showlegend=False)
        st.plotly_chart(fig_reg_bar, width="stretch")

    with col2:
        fig_reg_pie = go.Figure(go.Pie(
            labels=region_stats["Region"], values=region_stats["Orders"],
            hole=0.55, marker_colors=PALETTE[:4],
            textinfo="label+percent", textfont_size=13
        ))
        fig_reg_pie.update_layout(**PLOT_THEME, title="Order Volume Share by Region", height=320,
            annotations=[dict(text=f"{region_stats['Orders'].sum():,}<br>Orders", x=0.5, y=0.5, font_size=14, showarrow=False, font_color="#ccd6f6")])
        st.plotly_chart(fig_reg_pie, width="stretch")

    st.markdown('<div class="section-header">📋 Regional Metrics Table</div>', unsafe_allow_html=True)
    region_display = region_stats.copy()
    region_display["Revenue"] = region_display["Revenue"].apply(lambda x: f"${x:,.2f}")
    region_display["Profit"]  = region_display["Profit"].apply(lambda x: f"${x:,.2f}")
    region_display["Avg_LT"]  = region_display["Avg_LT"].round(2)
    region_display["Std_Dev"] = region_display["Std_Dev"].round(2)
    st.dataframe(region_display.rename(columns={
        "Region":"Region", "Orders":"Orders", "Avg_LT":"Avg Lead Time", "Median_LT":"Median",
        "Std_Dev":"Std Dev", "Min_LT":"Min", "Max_LT":"Max", "Revenue":"Revenue", "Profit":"Profit"
    }), width="stretch", hide_index=True)

    st.markdown('<div class="section-header">🔥 Ship Mode × Region Heatmap</div>', unsafe_allow_html=True)
    heat_data = fdf.groupby(["Region", "Ship Mode"])["Lead Time (Days)"].mean().reset_index()
    heat_pivot = heat_data.pivot(index="Region", columns="Ship Mode", values="Lead Time (Days)").round(1)
    fig_heat = px.imshow(
        heat_pivot, text_auto=True, aspect="auto",
        color_continuous_scale=["#00ff88", "#ffd700", "#ff4162"],
        labels=dict(color="Avg Lead Time"),
        title="Avg Lead Time Heatmap: Region × Ship Mode"
    )
    fig_heat.update_layout(**PLOT_THEME, height=320, coloraxis_colorbar=dict(tickfont=dict(color="#ccd6f6")))
    fig_heat.update_traces(textfont=dict(color="white", size=14))
    st.plotly_chart(fig_heat, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SHIP MODE
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">🚢 Ship Mode Efficiency Analysis</div>', unsafe_allow_html=True)

    mode_stats = fdf.groupby("Ship Mode").agg(
        Orders=("Lead Time (Days)", "count"),
        Avg_LT=("Lead Time (Days)", "mean"),
        Median_LT=("Lead Time (Days)", "median"),
        Std_Dev=("Lead Time (Days)", "std"),
        Revenue=("Sales", "sum"),
        Profit=("Gross Profit", "sum"),
    ).round(2).reset_index().sort_values("Avg_LT")
    mode_stats["Margin %"] = (mode_stats["Profit"] / mode_stats["Revenue"] * 100).round(1)
    mode_stats["Vol %"]    = (mode_stats["Orders"] / mode_stats["Orders"].sum() * 100).round(1)

    c1, c2 = st.columns(2)
    with c1:
        mode_colors = [COLORS["green"] if v <= overall_mean else COLORS["red"] for v in mode_stats["Avg_LT"]]
        fig_mode = go.Figure()
        fig_mode.add_trace(go.Bar(
            x=mode_stats["Ship Mode"], y=mode_stats["Avg_LT"],
            marker_color=mode_colors,
            text=mode_stats["Avg_LT"].round(1), textposition="outside"
        ))
        fig_mode.add_hline(y=overall_mean, line_dash="dash", line_color=COLORS["yellow"], annotation_text=f"Network Avg: {overall_mean:.0f}")
        fig_mode.update_layout(**PLOT_THEME, title="Avg Lead Time by Ship Mode<br><sup>Green = Below Network Avg | Red = Above</sup>", height=360, showlegend=False)
        st.plotly_chart(fig_mode, width="stretch")

    with c2:
        fig_mode_vol = go.Figure()
        fig_mode_vol.add_trace(go.Bar(
            x=mode_stats["Ship Mode"], y=mode_stats["Orders"],
            marker_color=PALETTE[:4],
            text=[f"{v:,}<br>({p:.1f}%)" for v, p in zip(mode_stats["Orders"], mode_stats["Vol %"])],
            textposition="outside"
        ))
        fig_mode_vol.update_layout(**PLOT_THEME, title="Order Volume by Ship Mode", height=360, showlegend=False)
        st.plotly_chart(fig_mode_vol, width="stretch")

    st.markdown('<div class="section-header">📦 Ship Mode Deep Dive</div>', unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        fig_violin = go.Figure()
        for i, mode in enumerate(sorted(fdf["Ship Mode"].unique())):
            fig_violin.add_trace(go.Violin(
                y=fdf[fdf["Ship Mode"]==mode]["Lead Time (Days)"],
                name=mode, fillcolor=PALETTE[i], line_color=PALETTE[i],
                opacity=0.7, box_visible=True, meanline_visible=True
            ))
        fig_violin.update_layout(**PLOT_THEME, title="Lead Time Distribution by Ship Mode (Violin)", height=360)
        st.plotly_chart(fig_violin, width="stretch")

    with c4:
        fig_mode_region = px.bar(
            heat_data, x="Region", y="Lead Time (Days)", color="Ship Mode",
            barmode="group", color_discrete_sequence=PALETTE,
            title="Avg Lead Time: Ship Mode vs Region",
            labels={"Lead Time (Days)": "Avg Lead Time (Days)"}
        )
        fig_mode_region.update_layout(**PLOT_THEME, height=360, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_mode_region, width="stretch")

    st.markdown('<div class="section-header">📊 Ship Mode Metrics Table</div>', unsafe_allow_html=True)
    mode_display = mode_stats.copy()
    mode_display["Revenue"] = mode_display["Revenue"].apply(lambda x: f"${x:,.2f}")
    mode_display["Profit"]  = mode_display["Profit"].apply(lambda x: f"${x:,.2f}")
    st.dataframe(mode_display.rename(columns={
        "Ship Mode":"Ship Mode","Orders":"Orders","Vol %":"Volume %","Avg_LT":"Avg Lead Time",
        "Median_LT":"Median","Std_Dev":"Std Dev","Revenue":"Revenue","Profit":"Profit","Margin %":"Margin %"
    }), width="stretch", hide_index=True)

    # Paradox callout
    best_lt  = mode_stats.iloc[0]["Avg_LT"]
    worst_lt = mode_stats.iloc[-1]["Avg_LT"]
    gap = worst_lt - best_lt
    st.warning(f"⚠️ **Premium Shipping Paradox Detected:** {mode_stats.iloc[-1]['Ship Mode']} is **{gap:.1f} days SLOWER** than {mode_stats.iloc[0]['Ship Mode']} — despite higher classification. Immediate operational audit recommended.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — STATE ROUTES
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">📍 State-Level Route Efficiency</div>', unsafe_allow_html=True)

    state_stats = fdf.groupby("State/Province").agg(
        Orders=("Lead Time (Days)", "count"),
        Avg_LT=("Lead Time (Days)", "mean"),
        Median_LT=("Lead Time (Days)", "median"),
        Std_Dev=("Lead Time (Days)", "std"),
        Revenue=("Sales", "sum"),
        Profit=("Gross Profit", "sum"),
    ).round(2).reset_index()
    state_stats.columns = ["State","Orders","Avg_LT","Median_LT","Std_Dev","Revenue","Profit"]
    state_stats["Efficiency_Score"] = (100 - ((state_stats["Avg_LT"] - overall_mean) / df["Lead Time (Days)"].std() * 10)).round(2)
    state_stats["Margin %"] = (state_stats["Profit"] / state_stats["Revenue"] * 100).round(1)

    sig_states = state_stats[state_stats["Orders"] >= min_orders].copy()

    top10    = sig_states.nsmallest(10, "Avg_LT")
    bottom10 = sig_states.nlargest(10, "Avg_LT").sort_values("Avg_LT", ascending=True)

    c1, c2 = st.columns(2)
    with c1:
        fig_top = go.Figure(go.Bar(
            x=top10["Avg_LT"], y=top10["State"],
            orientation="h", marker_color=COLORS["green"],
            text=top10["Avg_LT"].round(0), textposition="outside"
        ))
        fig_top.add_vline(x=overall_mean, line_dash="dash", line_color=COLORS["yellow"], annotation_text="Network Avg")
        fig_top.update_layout(**PLOT_THEME, title=f"✅ Top 10 Most Efficient Routes<br><sup>(≥{min_orders} shipments)</sup>", height=380, showlegend=False)
        st.plotly_chart(fig_top, width="stretch")

    with c2:
        fig_bot = go.Figure(go.Bar(
            x=bottom10["Avg_LT"], y=bottom10["State"],
            orientation="h", marker_color=COLORS["red"],
            text=bottom10["Avg_LT"].round(0), textposition="outside"
        ))
        fig_bot.add_vline(x=overall_mean, line_dash="dash", line_color=COLORS["yellow"], annotation_text="Network Avg")
        fig_bot.update_layout(**PLOT_THEME, title=f"❌ Bottom 10 Least Efficient Routes<br><sup>(≥{min_orders} shipments)</sup>", height=380, showlegend=False)
        st.plotly_chart(fig_bot, width="stretch")

    st.markdown('<div class="section-header">🔵 Volume vs Efficiency Bubble Chart</div>', unsafe_allow_html=True)
    fig_bubble = px.scatter(
        sig_states, x="Orders", y="Avg_LT",
        size="Revenue", color="Efficiency_Score",
        hover_name="State",
        hover_data={"Orders":True,"Avg_LT":":.1f","Efficiency_Score":":.1f","Revenue":":.2f"},
        color_continuous_scale=["#ff4162","#ffd700","#00ff88"],
        size_max=50,
        title="Shipment Volume vs Avg Lead Time (Bubble Size = Revenue, Color = Efficiency Score)"
    )
    fig_bubble.add_hline(y=overall_mean, line_dash="dash", line_color=COLORS["yellow"], annotation_text=f"Network Avg: {overall_mean:.0f}")
    fig_bubble.update_layout(**PLOT_THEME, height=420)
    st.plotly_chart(fig_bubble, width="stretch")

    st.markdown('<div class="section-header">📋 Full State Performance Table</div>', unsafe_allow_html=True)
    col_search, col_sort = st.columns([3, 1])
    with col_search: search_state = st.text_input("🔍 Search State", "")
    with col_sort:   sort_by = st.selectbox("Sort By", ["Avg_LT", "Orders", "Revenue", "Efficiency_Score"])

    display_states = sig_states.copy()
    if search_state:
        display_states = display_states[display_states["State"].str.contains(search_state, case=False)]
    display_states = display_states.sort_values(sort_by)
    display_states["Revenue"] = display_states["Revenue"].apply(lambda x: f"${x:,.2f}")
    display_states["Profit"]  = display_states["Profit"].apply(lambda x:  f"${x:,.2f}")
    st.dataframe(display_states, width="stretch", hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — BOTTLENECKS
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">⚠️ Bottleneck Detection & Delay Analysis</div>', unsafe_allow_html=True)

    # Delay by state
    delay_by_state = fdf.groupby("State/Province").agg(
        Total_Orders=("Lead Time (Days)", "count"),
        Delayed_Orders=("Is_Delayed", "sum"),
        Avg_LT=("Lead Time (Days)", "mean")
    ).reset_index()
    delay_by_state["Delay_Rate_%"] = (delay_by_state["Delayed_Orders"] / delay_by_state["Total_Orders"] * 100).round(2)
    delay_by_state = delay_by_state[delay_by_state["Total_Orders"] >= min_orders].sort_values("Delay_Rate_%", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        top_delay = delay_by_state.head(12)
        fig_delay = go.Figure(go.Bar(
            x=top_delay["Delay_Rate_%"], y=top_delay["State/Province"],
            orientation="h",
            marker_color=[COLORS["red"] if v > 10 else COLORS["orange"] if v > 7 else COLORS["yellow"] for v in top_delay["Delay_Rate_%"]],
            text=top_delay["Delay_Rate_%"].apply(lambda x: f"{x:.1f}%"), textposition="outside"
        ))
        fig_delay.update_layout(**PLOT_THEME, title="Delay Rate by State<br><sup>% Orders Exceeding 90th Percentile Lead Time</sup>", height=380, showlegend=False)
        st.plotly_chart(fig_delay, width="stretch")

    with c2:
        # High Volume + High LT = critical
        critical = state_stats[
            (state_stats["Orders"] >= min_orders) &
            (state_stats["Avg_LT"] > overall_mean)
        ].sort_values("Orders", ascending=False).head(12)

        fig_crit = px.scatter(
            critical, x="Avg_LT", y="Orders",
            size="Revenue", color="Avg_LT",
            hover_name="State",
            color_continuous_scale=["#ffd700","#ff4162"],
            title="Critical Bottlenecks: High Volume + High Lead Time",
            labels={"Avg_LT":"Avg Lead Time (Days)","Orders":"Order Count"}
        )
        fig_crit.add_vline(x=overall_mean, line_dash="dash", line_color=COLORS["teal"], annotation_text="Network Avg")
        fig_crit.update_layout(**PLOT_THEME, height=380)
        st.plotly_chart(fig_crit, width="stretch")

    st.markdown('<div class="section-header">🗂️ Cluster Analysis</div>', unsafe_allow_html=True)

    clusters = {
        "Southern Zone ✅": {"states": ["Virginia","Mississippi","Arkansas","Alabama","Florida","Texas","Louisiana"], "color": "#00ff88", "status": "BEST PRACTICE"},
        "Northeast Cluster ⚠️": {"states": ["Connecticut","Maryland","New Jersey","New York","Pennsylvania","Massachusetts","Rhode Island"], "color": "#ff8c42", "status": "CONCERN"},
        "Midwest Cluster 🚨": {"states": ["Indiana","Wisconsin","Missouri","Tennessee","Minnesota","Kentucky"], "color": "#ff4162", "status": "CRITICAL"},
        "Pacific Northwest ⚡": {"states": ["Washington","Oregon"], "color": "#ffd700", "status": "WATCH"},
    }

    cols = st.columns(4)
    for i, (cluster_name, info) in enumerate(clusters.items()):
        with cols[i]:
            cluster_data = fdf[fdf["State/Province"].isin(info["states"])]
            if len(cluster_data) > 0:
                avg_lt   = cluster_data["Lead Time (Days)"].mean()
                n_orders = len(cluster_data)
                gap      = avg_lt - overall_mean
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,{info['color']}15,{info['color']}05);
                            border:1px solid {info['color']}40;border-radius:12px;padding:16px;text-align:center;">
                    <div style="color:{info['color']};font-size:11px;font-weight:700;letter-spacing:1px;">{info['status']}</div>
                    <div style="color:#ccd6f6;font-size:13px;font-weight:700;margin:8px 0;">{cluster_name}</div>
                    <div style="color:{info['color']};font-size:22px;font-weight:800;">{avg_lt:.0f}d</div>
                    <div style="color:#8892b0;font-size:11px;">Avg Lead Time</div>
                    <div style="color:#8892b0;font-size:11px;margin-top:4px;">{n_orders:,} orders | {gap:+.1f}d vs avg</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info(f"No data for {cluster_name}")

    st.markdown("")
    st.markdown('<div class="section-header">📋 Delay Analysis Table</div>', unsafe_allow_html=True)
    st.dataframe(
        delay_by_state.rename(columns={"State/Province":"State","Total_Orders":"Total Orders","Delayed_Orders":"Delayed","Delay_Rate_%":"Delay Rate %","Avg_LT":"Avg Lead Time"}),
        width="stretch", hide_index=True
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — FINANCIALS
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-header">💰 Financial Performance Analysis</div>', unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns(4)
    with f1: st.metric("Total Revenue",    f"${fdf['Sales'].sum():,.2f}")
    with f2: st.metric("Total Profit",     f"${fdf['Gross Profit'].sum():,.2f}")
    with f3: st.metric("Avg Profit Margin",f"{fdf['Profit Margin %'].mean():.1f}%")
    with f4: st.metric("Avg Order Value",  f"${fdf['Sales'].mean():.2f}")

    c1, c2 = st.columns(2)
    with c1:
        div_fin = fdf.groupby("Division").agg(Revenue=("Sales","sum"), Profit=("Gross Profit","sum"), Orders=("Sales","count")).reset_index()
        div_fin["Margin %"] = (div_fin["Profit"] / div_fin["Revenue"] * 100).round(1)
        fig_div = go.Figure()
        fig_div.add_trace(go.Bar(x=div_fin["Division"], y=div_fin["Revenue"], name="Revenue", marker_color=COLORS["blue"]))
        fig_div.add_trace(go.Bar(x=div_fin["Division"], y=div_fin["Profit"],  name="Profit",  marker_color=COLORS["teal"]))
        fig_div.update_layout(**PLOT_THEME, title="Revenue & Profit by Division", barmode="group", height=340, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_div, width="stretch")

    with c2:
        mode_fin = fdf.groupby("Ship Mode").agg(Revenue=("Sales","sum"), Profit=("Gross Profit","sum")).reset_index()
        mode_fin["Margin %"] = (mode_fin["Profit"] / mode_fin["Revenue"] * 100).round(1)
        fig_mfin = go.Figure()
        fig_mfin.add_trace(go.Bar(x=mode_fin["Ship Mode"], y=mode_fin["Revenue"], name="Revenue", marker_color=COLORS["purple"]))
        fig_mfin.add_trace(go.Bar(x=mode_fin["Ship Mode"], y=mode_fin["Profit"],  name="Profit",  marker_color=COLORS["pink"]))
        fig_mfin.update_layout(**PLOT_THEME, title="Revenue & Profit by Ship Mode", barmode="group", height=340, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_mfin, width="stretch")

    st.markdown('<div class="section-header">🏆 Top 15 Products by Revenue</div>', unsafe_allow_html=True)
    prod_stats = fdf.groupby("Product Name").agg(
        Orders=("Sales","count"), Revenue=("Sales","sum"), Profit=("Gross Profit","sum"), Units=("Units","sum")
    ).reset_index().sort_values("Revenue", ascending=False).head(15)
    prod_stats["Margin %"] = (prod_stats["Profit"] / prod_stats["Revenue"] * 100).round(1)

    fig_prod = px.bar(
        prod_stats, x="Revenue", y="Product Name",
        orientation="h", color="Margin %",
        color_continuous_scale=["#ff4162","#ffd700","#00ff88"],
        text="Revenue", title="Top 15 Products by Revenue (Color = Profit Margin %)"
    )
    fig_prod.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig_prod.update_layout(**PLOT_THEME, height=480, coloraxis_colorbar=dict(tickfont=dict(color="#ccd6f6")))
    st.plotly_chart(fig_prod, width="stretch")

    st.markdown('<div class="section-header">📊 Revenue & Profit by Region</div>', unsafe_allow_html=True)
    reg_fin = fdf.groupby("Region").agg(Revenue=("Sales","sum"), Profit=("Gross Profit","sum"), Orders=("Sales","count")).reset_index()
    fig_reg_fin = px.sunburst(
        fdf, path=["Region","Ship Mode"], values="Sales",
        color="Sales", color_continuous_scale=["#7b2ff7","#64ffda"],
        title="Revenue Sunburst: Region → Ship Mode"
    )
    fig_reg_fin.update_layout(**PLOT_THEME, height=420)
    st.plotly_chart(fig_reg_fin, width="stretch")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:#8892b0;font-size:12px;">'
    '🍫 Nassau Candy Distributor · Logistics Intelligence Dashboard · '
    'Analytics & Logistics Division · April 2026</p>',
    unsafe_allow_html=True
)
