"""
Rebar & Billet Price Trend Dashboard v1.1

Streamlit app that reads the 12MM sheet from the main Excel file and displays:
  - Dashboard 1: Price trend line chart for 10 cities (SteelMint data)
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

# Fixed cities — always shown on the chart
FIXED_CITIES = {
    "Delhi/NCR": 3,
    "Raipur": 16,
    "Durgapur": 4,
}

# Optional cities — selectable via dropdown
OPTIONAL_CITIES = {
    "Mandi Gobindgarh": 11,
    "Jaipur": 8,
    "Muzaffarnagar": 13,
    "Rourkela": 17,
    "Ahmedabad": 1,
    "Mumbai": 12,
    "Hyderabad": 7,
}

# All cities combined (for data loading)
CITY_COLUMNS = {**FIXED_CITIES, **OPTIONAL_CITIES}

CITY_COLORS = {
    "Delhi/NCR": "#4f46e5",
    "Raipur": "#059669",
    "Durgapur": "#dc2626",
    "Mandi Gobindgarh": "#7c3aed",
    "Jaipur": "#db2777",
    "Muzaffarnagar": "#ea580c",
    "Rourkela": "#0d9488",
    "Ahmedabad": "#2563eb",
    "Mumbai": "#9333ea",
    "Hyderabad": "#ca8a04",
}


# --- Data Loading ---

@st.cache_data(ttl=60)
def load_data(city_names: tuple[str, ...], city_indices: tuple[int, ...]) -> pd.DataFrame:
    """Load 12MM sheet data for all configured cities."""
    city_map = dict(zip(city_names, city_indices))
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
        for city, col_idx in city_map.items():
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
st.caption("12MM rebar prices across 10 cities (SteelMint)")

# --- Load Data ---

try:
    df = load_data(tuple(CITY_COLUMNS.keys()), tuple(CITY_COLUMNS.values()))
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
        options=["Yesterday", "Last 5 Days", "Last 10 Days", "Last 15 Days", "Custom Range"],
        index=2,
    )

if frequency == "Custom Range":
    with col2:
        start_date = st.date_input("Start Date", value=max_date - timedelta(days=15), min_value=min_date, max_value=max_date)
    with col3:
        end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)
elif frequency == "Yesterday":
    s, e = get_trading_days(df, 2)
    start_date = s.date()
    end_date = e.date()
    with col2:
        st.date_input("Start Date", value=start_date, disabled=True)
    with col3:
        st.date_input("End Date", value=end_date, disabled=True)
else:
    n_days = {"Last 5 Days": 5, "Last 10 Days": 10, "Last 15 Days": 15}[frequency]
    s, e = get_trading_days(df, n_days)
    start_date = s.date()
    end_date = e.date()
    with col2:
        st.date_input("Start Date", value=start_date, disabled=True)
    with col3:
        st.date_input("End Date", value=end_date, disabled=True)

# City selection
extra_cities = st.multiselect(
    "Add more cities (Delhi/NCR, Raipur, Durgapur are always shown)",
    options=list(OPTIONAL_CITIES.keys()),
    default=[],
)

# Build active city list: fixed + selected optional
active_cities = list(FIXED_CITIES.keys()) + extra_cities

# Filter data
mask = (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
filtered = df[mask].copy()

# --- Tabs ---

tab1, tab2, tab3 = st.tabs(["📈 Price Trend", "📊 Price Delta", "💰 Margin Calculator"])

# --- Dashboard 1: Price Trend ---

with tab1:
    st.subheader(f"Price Trend — {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}")

    if filtered.empty:
        st.info("No data available for the selected range.")
    else:
        fig = go.Figure()

        for city in active_cities:
            color = CITY_COLORS.get(city, "#64748b")
            is_fixed = city in FIXED_CITIES
            city_data = filtered.dropna(subset=[city])
            fig.add_trace(go.Scatter(
                x=city_data["Date"],
                y=city_data[city],
                name=city,
                mode="lines+markers",
                line=dict(color=color, width=2.5 if is_fixed else 1.5, dash="solid" if is_fixed else "dot"),
                marker=dict(size=6 if is_fixed else 4),
                hovertemplate=f"<b>{city}</b><br>Date: %{{x|%d %b %Y}}<br>Price: INR %{{y:,.0f}}<extra></extra>",
            ))

        fig.update_layout(
            yaxis_title="Price (INR)",
            xaxis_title="Date",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            margin=dict(l=60, r=20, t=40, b=40),
            height=500,
            template="plotly_white",
            yaxis_tickformat=",",
            xaxis=dict(
                type="date",
                tickformat="%d %b %Y",
                dtick="D1",
            ),
        )

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
        for city in active_cities:
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

# --- Dashboard 3: Margin Calculator ---

# Plant-to-city mapping for SteelMint prices
PLANT_CITY_MAP = {
    "API Ispat": "Delhi/NCR",
    "SKA Ispat": "Delhi/NCR",
    "Aditya Industries": "Raipur",
    "ASUL-Gwalior": "Delhi/NCR",
    "Amba Shakti": "Raipur",
    "Real Ispat": "Raipur",
    "German Steel": "Durgapur",
    "N N Ispat": "Ahmedabad",
}

GRADES = ["Fe 550", "Fe 550D"]

MARGIN_IMAGE_PATH = "daily rebar prices/margin dashboard/12th Apr'26.png"
INVENTORY_JSON_PATH = "daily rebar prices/margin dashboard/inventory_costs.json"


@st.cache_data(ttl=60)
def load_inventory_costs() -> dict:
    """Load inventory costs from JSON (extracted from uploaded image)."""
    import json
    if os.path.exists(INVENTORY_JSON_PATH):
        with open(INVENTORY_JSON_PATH) as f:
            return json.load(f)
    return {"costs": {}, "grade_averages": {}, "image_date": "N/A"}


import os

with tab3:
    st.subheader("Margin Calculator")
    st.caption("Margin = Avg Inventory Cost + JSW Project Management Cost - FOR Price - Freight")

    # Load inventory costs from JSON
    inv_data = load_inventory_costs()
    inv_costs = inv_data.get("costs", {})
    inv_date = inv_data.get("image_date", "N/A")
    grade_avgs = inv_data.get("grade_averages", {})

    # Show the uploaded inventory cost image for reference
    if os.path.exists(MARGIN_IMAGE_PATH):
        with st.expander(f"View Actual Inventory Cost Image — {inv_date} (reference)", expanded=False):
            st.image(MARGIN_IMAGE_PATH, use_container_width=True)

    st.divider()

    # User inputs - Row 1: Grade, FOR Price
    mc1, mc2, mc3 = st.columns(3)

    with mc1:
        selected_grade = st.selectbox("Grade", options=GRADES)
    with mc2:
        for_price = st.number_input("FOR Price (INR)", min_value=0, value=0, step=100)
    with mc3:
        jsw_pmc = st.number_input("JSW Project Management Cost (INR)", min_value=0, value=0, step=100)

    # Row 2: Freight and Plant (freight depends on plant)
    mc4, mc5, mc6 = st.columns(3)

    with mc4:
        freight = st.number_input("Freight (INR)", min_value=0, value=0, step=100)
    with mc5:
        freight_plant = st.selectbox(
            "Freight is from which Plant?",
            options=list(PLANT_CITY_MAP.keys()),
            help="Select the plant from which this freight cost applies",
        ) if freight > 0 else None
        if freight == 0:
            freight_plant = st.selectbox(
                "Freight is from which Plant?",
                options=list(PLANT_CITY_MAP.keys()),
                disabled=True,
                help="Enter freight first",
            )

    # Auto-fill inventory cost from JSON based on plant + grade
    plant_for_cost = freight_plant if freight_plant else list(PLANT_CITY_MAP.keys())[0]
    lookup_key = f"{plant_for_cost}|{selected_grade}"
    auto_cost = inv_costs.get(lookup_key, 0)

    # Fallback to grade average if exact plant+grade not found
    if auto_cost == 0:
        auto_cost = grade_avgs.get(selected_grade, 0)

    with mc6:
        if auto_cost > 0:
            st.markdown(f"**Actual Inventory Cost** (auto from image)")
            st.markdown(f"### INR {auto_cost:,.0f}")
            st.caption(f"Source: {inv_date} | {plant_for_cost} | {selected_grade}")
            actual_inventory_cost = auto_cost
        else:
            actual_inventory_cost = st.number_input(
                "Actual Inventory Cost (INR)",
                min_value=0, value=0, step=100,
                help="No auto-fill available for this plant+grade. Enter manually."
            )

    # Get SteelMint price for the freight plant's city
    plant_city = PLANT_CITY_MAP.get(freight_plant, "Delhi/NCR") if freight_plant else "Delhi/NCR"

    # Last 15 days avg SteelMint price
    last15_start, last15_end = get_trading_days(df, 15)
    last15_mask = (df["Date"] >= last15_start) & (df["Date"] <= last15_end)
    last15_data = df[last15_mask][plant_city].dropna()
    avg_steelmint_15 = last15_data.mean() if len(last15_data) > 0 else 0

    # Last date SteelMint price
    last_date_data = df.dropna(subset=[plant_city])
    last_steelmint_price = float(last_date_data.iloc[-1][plant_city]) if len(last_date_data) > 0 else 0
    last_steelmint_date = last_date_data.iloc[-1]["Date"].strftime("%d %b %Y") if len(last_date_data) > 0 else "N/A"

    st.divider()

    # Calculate margins
    if for_price > 0:
        margin_actual = actual_inventory_cost + jsw_pmc - for_price - freight if actual_inventory_cost > 0 else None
        margin_15day = avg_steelmint_15 + jsw_pmc - for_price - freight
        margin_last = last_steelmint_price + jsw_pmc - for_price - freight

        plant_label = freight_plant if freight_plant else "N/A"
        st.markdown(f"**Plant:** {plant_label} | **Grade:** {selected_grade} | **SteelMint City:** {plant_city}")

        # Three columns for the three margin sections
        s1, s2, s3 = st.columns(3)

        with s1:
            st.markdown("#### 1. Actual Inventory")
            if margin_actual is not None:
                st.metric(
                    label=f"Cost: INR {actual_inventory_cost:,.0f}",
                    value=f"INR {margin_actual:,.0f}",
                    delta=f"{'Profit' if margin_actual >= 0 else 'Loss'}",
                    delta_color="normal" if margin_actual >= 0 else "inverse",
                )
            else:
                st.info("Enter Actual Inventory Cost above")

        with s2:
            st.markdown("#### 2. SteelMint (15-Day Avg)")
            st.metric(
                label=f"Avg Price: INR {avg_steelmint_15:,.0f}",
                value=f"INR {margin_15day:,.0f}",
                delta=f"{'Profit' if margin_15day >= 0 else 'Loss'}",
                delta_color="normal" if margin_15day >= 0 else "inverse",
            )

        with s3:
            st.markdown(f"#### 3. SteelMint ({last_steelmint_date})")
            st.metric(
                label=f"Price: INR {last_steelmint_price:,.0f}",
                value=f"INR {margin_last:,.0f}",
                delta=f"{'Profit' if margin_last >= 0 else 'Loss'}",
                delta_color="normal" if margin_last >= 0 else "inverse",
            )

        # Breakdown table
        st.divider()
        st.subheader("Breakdown")

        breakdown = {
            "Component": ["Base Cost", "+ JSW Project Mgmt Cost", "- FOR Price", "- Freight", "= Margin"],
            "Actual": [
                f"{actual_inventory_cost:,.0f}" if actual_inventory_cost > 0 else "-",
                f"{jsw_pmc:,.0f}",
                f"{for_price:,.0f}",
                f"{freight:,.0f}",
                f"{margin_actual:+,.0f}" if margin_actual is not None else "-",
            ],
            "SteelMint 15-Day Avg": [
                f"{avg_steelmint_15:,.0f}",
                f"{jsw_pmc:,.0f}",
                f"{for_price:,.0f}",
                f"{freight:,.0f}",
                f"{margin_15day:+,.0f}",
            ],
            f"SteelMint ({last_steelmint_date})": [
                f"{last_steelmint_price:,.0f}",
                f"{jsw_pmc:,.0f}",
                f"{for_price:,.0f}",
                f"{freight:,.0f}",
                f"{margin_last:+,.0f}",
            ],
        }

        st.dataframe(pd.DataFrame(breakdown), use_container_width=True, hide_index=True)

    else:
        st.info("Enter a FOR Price to calculate margins.")

# --- Footer ---

st.divider()
st.caption(f"Data range: {min_date.strftime('%d %b %Y')} to {max_date.strftime('%d %b %Y')}")
