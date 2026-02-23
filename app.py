import pandas as pd
import streamlit as st
import altair as alt
from pathlib import Path

# G-TAG (GA)
import streamlit.components.v1 as components

GA_ID = "G-5LPCWEZNT3"  # replace with your real ID

st.html(
    f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_ID}', {{ debug_mode: true }});
    </script>
    """,
    unsafe_allow_javascript=True,
)

# --------------------------------------------------
# App configuration
# --------------------------------------------------
st.set_page_config(page_title="Metro Market Dashboard", layout="wide")
st.title("🏙️ Metro Market Dashboard")
st.caption("Property Type • Geography • Period slider • Metric selector • KPI cards • YoY overlay • Smoothing")

# --------------------------------------------------
# Load data (local CSV)
# --------------------------------------------------
# If you run locally, keep the file next to app.py and use: DATA_PATH = "ALLMETRO_jan2026.csv"
# In this chat environment, the uploaded file lives here:
DATA_PATH = "data/ALLMETRO_jan2026.csv"

if not Path(DATA_PATH).exists():
    st.error(f"Data file not found at: {DATA_PATH}")
    st.stop()

df = pd.read_csv(DATA_PATH)

# Parse dates
df["PERIOD_END"] = pd.to_datetime(df["PERIOD_END"], errors="coerce")
df = df.dropna(subset=["PERIOD_END"]).copy()

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def guess_base_metric_columns(frame: pd.DataFrame):
    """
    Return numeric metric columns, excluding *_MOM and *_YOY, plus obvious ID fields.
    """
    numeric_cols = [c for c in frame.columns if pd.api.types.is_numeric_dtype(frame[c])]
    base = []
    for c in numeric_cols:
        if c.endswith("_MOM") or c.endswith("_YOY"):
            continue
        if c.endswith("_ID") or c in ["TABLE_ID", "REGION_TYPE_ID", "PROPERTY_TYPE_ID"]:
            continue
        base.append(c)
    return sorted(base)

def is_count_like(metric_name: str) -> bool:
    """
    Aggregation rule when multiple geos are selected:
      - Count-like → sum
      - Price/ratio-like → mean
    """
    count_like = {
        "HOMES_SOLD",
        "PENDING_SALES",
        "NEW_LISTINGS",
        "INVENTORY",
        "PRICE_DROPS",
    }
    return metric_name in count_like

def agg_func(metric_name: str) -> str:
    return "sum" if is_count_like(metric_name) else "mean"

def fmt_number(x):
    if x is None or pd.isna(x):
        return "—"
    try:
        x = float(x)
        if abs(x) >= 1000:
            return f"{x:,.0f}"
        return f"{x:,.2f}"
    except Exception:
        return str(x)

# --------------------------------------------------
# Sidebar controls
# --------------------------------------------------
st.sidebar.header("Filters")

# PROPERTY_TYPE selector
property_types = sorted(df["PROPERTY_TYPE"].dropna().unique().tolist())
selected_property_type = st.sidebar.selectbox("Property Type", property_types)

# Geography selector (this dataset supports both REGION (metro area label) and CITY)
geo_field = st.sidebar.selectbox(
    "Geography Level",
    options=["REGION (Metro Area)", "CITY"],
    index=0
)
geo_col = "REGION" if geo_field.startswith("REGION") else "CITY"

# List of geographies (filtered by property type)
geo_options = sorted(
    df.loc[df["PROPERTY_TYPE"] == selected_property_type, geo_col]
      .dropna()
      .unique()
      .tolist()
)

default_geos = geo_options[:1] if geo_options else []
selected_geos = st.sidebar.multiselect(
    f"Select {geo_col}(s)",
    options=geo_options,
    default=default_geos
)

# Metric selector
base_metrics = guess_base_metric_columns(df)
default_metric = "MEDIAN_SALE_PRICE" if "MEDIAN_SALE_PRICE" in base_metrics else (base_metrics[0] if base_metrics else None)
selected_metric = st.sidebar.selectbox(
    "Metric",
    options=base_metrics,
    index=(base_metrics.index(default_metric) if default_metric in base_metrics else 0)
)

# Period slider
min_date = df["PERIOD_END"].min().to_pydatetime()
max_date = df["PERIOD_END"].max().to_pydatetime()
default_start = (pd.Timestamp(max_date) - pd.DateOffset(months=11)).to_pydatetime()

start_date, end_date = st.sidebar.slider(
    "Period (drag to select range)",
    min_value=min_date,
    max_value=max_date,
    value=(default_start, max_date),
    format="YYYY-MM",
)

# Smoothing
st.sidebar.header("Smoothing")
use_smoothing = st.sidebar.toggle("Apply rolling average", value=False)
window = 3
if use_smoothing:
    window = st.sidebar.slider("Rolling window (months)", min_value=2, max_value=6, value=3)

# YoY overlay
show_yoy = st.sidebar.toggle("Show YoY % change", value=True)

# --------------------------------------------------
# Apply filters
# --------------------------------------------------
filtered = df[
    (df["PROPERTY_TYPE"] == selected_property_type) &
    (df["PERIOD_END"].between(start_date, end_date))
].copy()

if selected_geos:
    filtered = filtered[filtered[geo_col].isin(selected_geos)].copy()

if filtered.empty:
    st.warning("No data matches your filters. Adjust selections and try again.")
    st.stop()

multi_geo = len(selected_geos) > 1

# --------------------------------------------------
# Build monthly series
# --------------------------------------------------
group_cols = ["PERIOD_END"]
if multi_geo:
    group_cols.append(geo_col)

metric_agg = agg_func(selected_metric)

trend = (
    filtered
    .groupby(group_cols, as_index=False)[selected_metric]
    .agg(metric_agg)
    .rename(columns={selected_metric: "value"})
    .sort_values(group_cols)
)

# Smoothing (rolling average)
if use_smoothing:
    if multi_geo:
        trend["value"] = trend.groupby(geo_col)["value"].transform(
            lambda s: s.rolling(window=window, min_periods=1).mean()
        )
    else:
        trend["value"] = trend["value"].rolling(window=window, min_periods=1).mean()

# MoM / YoY (prefer provided *_MOM / *_YOY columns if they exist; else compute)
mom_col = f"{selected_metric}_MOM"
yoy_col = f"{selected_metric}_YOY"

if mom_col in filtered.columns and pd.api.types.is_numeric_dtype(filtered[mom_col]):
    mom_trend = (
        filtered.groupby(group_cols, as_index=False)[mom_col]
        .agg(metric_agg)
        .rename(columns={mom_col: "mom"})
        .sort_values(group_cols)
    )
else:
    mom_trend = trend.copy()
    if multi_geo:
        mom_trend["mom"] = mom_trend.groupby(geo_col)["value"].pct_change() * 100
    else:
        mom_trend["mom"] = mom_trend["value"].pct_change() * 100
    mom_trend = mom_trend[group_cols + ["mom"]]

if yoy_col in filtered.columns and pd.api.types.is_numeric_dtype(filtered[yoy_col]):
    yoy_trend = (
        filtered.groupby(group_cols, as_index=False)[yoy_col]
        .agg(metric_agg)
        .rename(columns={yoy_col: "yoy"})
        .sort_values(group_cols)
    )
else:
    yoy_trend = trend.copy()
    if multi_geo:
        yoy_trend["yoy"] = yoy_trend.groupby(geo_col)["value"].pct_change(12) * 100
    else:
        yoy_trend["yoy"] = yoy_trend["value"].pct_change(12) * 100
    yoy_trend = yoy_trend[group_cols + ["yoy"]]

chart_df = (
    trend.merge(mom_trend, on=group_cols, how="left")
         .merge(yoy_trend, on=group_cols, how="left")
)

# --------------------------------------------------
# KPI Cards (latest period in range)
# --------------------------------------------------
latest_period = chart_df["PERIOD_END"].max()
latest_slice = chart_df[chart_df["PERIOD_END"] == latest_period].copy()

if multi_geo:
    # KPI aggregates across selected geos
    latest_value = latest_slice["value"].sum() if is_count_like(selected_metric) else latest_slice["value"].mean()
    latest_mom = latest_slice["mom"].mean()
    latest_yoy = latest_slice["yoy"].mean()
    scope_label = f"{len(selected_geos)} {geo_col.lower()}s"
else:
    latest_value = latest_slice["value"].iloc[0] if not latest_slice.empty else None
    latest_mom = latest_slice["mom"].iloc[0] if not latest_slice.empty else None
    latest_yoy = latest_slice["yoy"].iloc[0] if not latest_slice.empty else None
    scope_label = selected_geos[0] if selected_geos else "—"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest Period", latest_period.strftime("%Y-%m"))
c2.metric("Metric", selected_metric)
c3.metric("Latest Value", fmt_number(latest_value))
c4.metric("Scope", scope_label)

k1, k2, k3 = st.columns(3)
k1.metric("MoM %", "—" if latest_mom is None or pd.isna(latest_mom) else f"{latest_mom:,.2f}%")
k2.metric("YoY %", "—" if latest_yoy is None or pd.isna(latest_yoy) else f"{latest_yoy:,.2f}%")
k3.metric("Filtered Rows", f"{len(filtered):,}")

st.divider()

# --------------------------------------------------
# Charts (Altair)
# --------------------------------------------------
st.subheader("Trend Chart")

base = alt.Chart(chart_df).encode(
    x=alt.X("PERIOD_END:T", title="Period End")
)

if multi_geo:
    value_line = base.mark_line().encode(
        y=alt.Y("value:Q", title=selected_metric),
        color=alt.Color(f"{geo_col}:N", title=geo_col),
        tooltip=[
            alt.Tooltip("PERIOD_END:T", title="Period"),
            alt.Tooltip(f"{geo_col}:N", title=geo_col),
            alt.Tooltip("value:Q", title=selected_metric, format=",.2f"),
            alt.Tooltip("mom:Q", title="MoM %", format=",.2f"),
            alt.Tooltip("yoy:Q", title="YoY %", format=",.2f"),
        ],
    ).properties(height=380)

    st.altair_chart(value_line, use_container_width=True)

    if show_yoy:
        st.caption("YoY is shown as a separate chart when comparing multiple geographies (for readability).")
        yoy_line = alt.Chart(chart_df).mark_line(strokeDash=[6, 4]).encode(
            x=alt.X("PERIOD_END:T", title="Period End"),
            y=alt.Y("yoy:Q", title="YoY %"),
            color=alt.Color(f"{geo_col}:N", title=geo_col),
            tooltip=[
                alt.Tooltip("PERIOD_END:T", title="Period"),
                alt.Tooltip(f"{geo_col}:N", title=geo_col),
                alt.Tooltip("yoy:Q", title="YoY %", format=",.2f"),
            ],
        ).properties(height=260)

        st.altair_chart(yoy_line, use_container_width=True)

else:
    value_line = base.mark_line().encode(
        y=alt.Y("value:Q", title=selected_metric),
        tooltip=[
            alt.Tooltip("PERIOD_END:T", title="Period"),
            alt.Tooltip("value:Q", title=selected_metric, format=",.2f"),
            alt.Tooltip("mom:Q", title="MoM %", format=",.2f"),
            alt.Tooltip("yoy:Q", title="YoY %", format=",.2f"),
        ],
    )

    if show_yoy:
        yoy_line = base.mark_line(strokeDash=[6, 4]).encode(
            y=alt.Y("yoy:Q", title="YoY %"),
            tooltip=[
                alt.Tooltip("PERIOD_END:T", title="Period"),
                alt.Tooltip("yoy:Q", title="YoY %", format=",.2f"),
            ],
        )
        layered = alt.layer(value_line, yoy_line).resolve_scale(y="independent").properties(height=420)
        st.altair_chart(layered, use_container_width=True)
    else:
        st.altair_chart(value_line.properties(height=420), use_container_width=True)

# --------------------------------------------------
# Data preview + download
# --------------------------------------------------
with st.expander("Show aggregated chart data"):
    cols = ["PERIOD_END"] + ([geo_col] if multi_geo else []) + ["value", "mom", "yoy"]
    st.dataframe(chart_df[cols].sort_values(["PERIOD_END"] + ([geo_col] if multi_geo else [])), use_container_width=True)

st.download_button(
    "Download aggregated CSV",
    data=chart_df[["PERIOD_END"] + ([geo_col] if multi_geo else []) + ["value", "mom", "yoy"]]
        .to_csv(index=False)
        .encode("utf-8"),
    file_name="aggregated_trend.csv",
    mime="text/csv",
)
