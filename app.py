"""
Rebar & Billet Price Trend Dashboard v1.1

Streamlit app that reads the 12MM sheet from the main Excel file and displays:
  - Dashboard 1: Price trend line chart for Raipur, Delhi/NCR, Durgapur
  - Dashboard 2: Price delta bar chart between start and end date

Deploy: https://share.streamlit.io
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta

# --- Config ---

EXCEL_PATH = "daily rebar prices/Rebar & Billet price trend (2).xlsx"
SHEET_NAME = "12MM"
HEADER_ROW = 19  # 0-indexed: row 20 in Excel has city names
DATA_START_ROW = 20  # 0-indexed: row 21 in Excel is first data row

CITY_COLUMNS = {
    "Raipur": 16,
    "Delhi/NCR": 3,
    "Durgapur": 4,
}

CITY_COLORS = {
    "Raipur": "#4f46e5",
    "Delhi/NCR": "#059669",
    "Durgapur": "#dc2626",
}


# --- Data Loading ---

@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    """Load 12MM sheet data for the three cities."""
    df = pd.read_excel(
        EXCEL_PATH,
        sheet_name=SHEET_NAME,
        header=None,
        skiprows=DATA_START_ROW,
        engine="openpyxl",
    )

    records = []
    for _, row in df.iterrows():
        date_val = row.iloc[0]
        if pd.isna(date_val):
            continue
        try:
            date = pd.to_datetime(date_val)
        except (ValueError, TypeError):
            continue

        record = {"Date": date}
        for city, col_idx in CITY_COLUMNS.items():
            val = row.iloc[col_idx] if col_idx < len(row) else None
            if pd.isna(val) or val in ("-", "H", "", "#DIV/0!", "#REF!"):
                record[city] = None
            else:
                try:
                    record[city] = float(val)
                except (ValueError, TypeError):
                    record[city] = None
        records.append(record)

    result = pd.DataFrame(records)
    result = result.sort_values("Date").reset_index(drop=True)
    return result


def get_trading_days(df: pd.DataFrame, n: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Get start and end dates for last N trading days with data."""
    valid = df.dropna(subset=list(CITY_COLUMNS.keys()), how="all")
    if len(valid) < n:
        return valid.iloc[0]["Date"], valid.iloc[-1]["Date"]
    return valid.iloc[-n]["Date"], valid.iloc[-1]["Date"]


# --- Page Config ---

st.set_page_config(
    page_title="Rebar & Billet Price Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Rebar & Billet Price Dashboard")
st.caption("12MM rebar prices for Raipur, Delhi/NCR, and Durgapur")

# --- Load Data ---

try:
    df = load_data()
except FileNotFoundError:
    st.error(f"Excel file not found: `{EXCEL_PATH}`")
    st.stop()

if df.empty:
    st.warning("No data found in the 12MM sheet.")
    st.stop()

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

# --- Controls ---

st.divider()

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    frequency = st.selectbox(
        "Frequency",
        options=["Last 5 Days", "Last 10 Days", "Last 15 Days", "Custom Range"],
        index=1,
    )

if frequency == "Custom Range":
    with col2:
        start_date = st.date_input("Start Date", value=max_date - timedelta(days=15), min_value=min_date, max_value=max_date)
    with col3:
        end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)
else:
    n_days = {"Last 5 Days": 5, "Last 10 Days": 10, "Last 15 Days": 15}[frequency]
    s, e = get_trading_days(df, n_days)
    start_date = s.date()
    end_date = e.date()
    with col2:
        st.date_input("Start Date", value=start_date, disabled=True)
    with col3:
        st.date_input("End Date", value=end_date, disabled=True)

# Filter data
mask = (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
filtered = df[mask].copy()

# --- Tabs ---

tab1, tab2 = st.tabs(["📈 Price Trend", "📊 Price Delta"])

# --- Dashboard 1: Price Trend ---

with tab1:
    st.subheader(f"Price Trend — {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}")

    if filtered.empty:
        st.info("No data available for the selected range.")
    else:
        fig = go.Figure()

        for city, color in CITY_COLORS.items():
            city_data = filtered.dropna(subset=[city])
            fig.add_trace(go.Scatter(
                x=city_data["Date"],
                y=city_data[city],
                name=city,
                mode="lines",
                line=dict(color=color, width=2.5),
                hovertemplate=f"<b>{city}</b><br>Date: %{{x|%d %b %Y}}<br>Price: ₹%{{y:,.0f}}<extra></extra>",
            ))

        fig.update_layout(
            yaxis_title="Price (INR)",
            xaxis_title="Date",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            margin=dict(l=60, r=20, t=40, b=40),
            height=500,
            template="plotly_white",
        )
        fig.update_layout(yaxis_tickformat=",")

        st.plotly_chart(fig, use_container_width=True)

        st.caption(f"Showing {len(filtered)} trading days")

# --- Dashboard 2: Price Delta ---

with tab2:
    st.subheader("Price Change (Delta)")
    st.write(
        f"Price change from **{start_date.strftime('%d %b %Y')}** to **{end_date.strftime('%d %b %Y')}**"
    )

    if filtered.empty or len(filtered) < 2:
        st.info("Need at least 2 data points to calculate delta.")
    else:
        delta_data = []
        for city in CITY_COLUMNS:
            city_valid = filtered.dropna(subset=[city])
            if len(city_valid) < 2:
                continue
            start_price = float(city_valid.iloc[0][city])
            end_price = float(city_valid.iloc[-1][city])
            delta = end_price - start_price
            pct = (delta / start_price) * 100 if start_price != 0 else 0
            delta_data.append({
                "City": city,
                "Start Price (INR)": start_price,
                "End Price (INR)": end_price,
                "Delta": delta,
                "Change %": pct,
            })

        if not delta_data:
            st.warning("No valid price data for the selected range.")
        else:
            delta_df = pd.DataFrame(delta_data)

            # Bar chart
            bar_colors = ["#059669" if d >= 0 else "#dc2626" for d in delta_df["Delta"]]

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=delta_df["City"],
                y=delta_df["Delta"],
                marker=dict(color=bar_colors),
                text=[f"INR {d:+,.0f}" for d in delta_df["Delta"]],
                textposition="outside",
            ))

            fig2.update_layout(
                yaxis_title="Price Change (INR)",
                xaxis_title="City",
                height=400,
                template="plotly_white",
                margin=dict(l=60, r=20, t=20, b=40),
                showlegend=False,
            )

            st.plotly_chart(fig2, use_container_width=True)

            # Summary table
            st.subheader("Summary")

            display_df = delta_df.copy()
            display_df["Start Price (INR)"] = display_df["Start Price (INR)"].apply(lambda x: f"{x:,.0f}")
            display_df["End Price (INR)"] = display_df["End Price (INR)"].apply(lambda x: f"{x:,.0f}")
            display_df["Delta"] = display_df["Delta"].apply(lambda x: f"{x:+,.0f}")
            display_df["Change %"] = display_df["Change %"].apply(lambda x: f"{x:+.2f}%")

            st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- Footer ---

st.divider()
st.caption(f"Data range: {min_date.strftime('%d %b %Y')} to {max_date.strftime('%d %b %Y')}")
