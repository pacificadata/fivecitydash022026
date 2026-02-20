import pandas as pd
import streamlit as st

# --------------------------------------------------
# App configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Property Price Trend Dashboard",
    layout="wide"
)

st.title("📈 Property Price Trend Dashboard")
st.caption("Median Sale Price by Property Type and Selected Period")

# --------------------------------------------------
# Load local data
# --------------------------------------------------
DATA_PATH = "data/CITYDATA_feb2026.csv"  # Adjust path if needed
df = pd.read_csv(DATA_PATH)

# Parse date column
df["PERIOD_END"] = pd.to_datetime(df["PERIOD_END"], errors="coerce")

# Drop rows with invalid dates
df = df.dropna(subset=["PERIOD_END"])

# --------------------------------------------------
# Sidebar controls
# --------------------------------------------------
st.sidebar.header("Filters")

# PROPERTY_TYPE selector
property_types = sorted(df["PROPERTY_TYPE"].dropna().unique().tolist())
selected_property_type = st.sidebar.selectbox(
    "Select Property Type",
    property_types
)

# --------------------------------------------------
# Date range slider
# --------------------------------------------------
min_date = df["PERIOD_END"].min().to_pydatetime()
max_date = df["PERIOD_END"].max().to_pydatetime()

default_start = max_date - pd.DateOffset(months=11)

start_date, end_date = st.sidebar.slider(
    "Select Period",
    min_value=min_date,
    max_value=max_date,
    value=(default_start.to_pydatetime(), max_date),
    format="YYYY-MM"
)

# --------------------------------------------------
# Apply filters
# --------------------------------------------------
filtered_df = df[
    (df["PROPERTY_TYPE"] == selected_property_type) &
    (df["PERIOD_END"].between(start_date, end_date))
].copy()

# --------------------------------------------------
# Aggregate to monthly trend
# (If multiple rows exist per month, take the average)
# --------------------------------------------------
monthly_trend = (
    filtered_df
    .groupby("PERIOD_END", as_index=False)["MEDIAN_SALE_PRICE"]
    .mean()
    .sort_values("PERIOD_END")
)

# --------------------------------------------------
# Display chart
# --------------------------------------------------
st.subheader(
    f"Median Sale Price Trend — {selected_property_type}"
)

st.line_chart(
    monthly_trend.set_index("PERIOD_END")["MEDIAN_SALE_PRICE"]
)

# --------------------------------------------------
# Optional data preview
# --------------------------------------------------
with st.expander("Show underlying aggregated data"):
    st.dataframe(monthly_trend, use_container_width=True)
