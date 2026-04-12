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
    "API Ispat": "Raipur",
    "SKA Ispat": "Raipur",
    "Aditya Industries": "Mandi Gobindgarh",
    "ASUL-Gwalior": "Delhi/NCR",
    "Amba Shakti": "Delhi/NCR",
    "Real Ispat": "Raipur",
    "German Steel": "Ahmedabad",
    "N N Ispat": "Durgapur",
}

GRADES = ["Fe 550", "Fe 550D-LRF"]

# SteelMint price adjustment per plant (e.g. ASUL-Gwalior = Delhi/NCR price - 800)
PLANT_PRICE_ADJUSTMENT = {
    "ASUL-Gwalior": -800,
}

# Per-plant costs: BIS, Loading Charges, JSW PMC (keyed by "Plant|Grade")
# Falls back to "Plant|*" if exact grade not found
PLANT_COSTS = {
    "Amba Shakti|Fe 550":             {"bis": 1200, "loading": 200, "jsw_pmc": 500},
    "API Ispat|Fe 550":               {"bis": 2150, "loading": 265, "jsw_pmc": 500},
    "Aditya Industries|Fe 550":       {"bis": 400,  "loading": 250, "jsw_pmc": 500},
    "SKA Ispat|Fe 550":               {"bis": 1800, "loading": 275, "jsw_pmc": 500},
    "ASUL-Gwalior|Fe 550":            {"bis": 1200, "loading": 200, "jsw_pmc": 500},
    "ASUL-Gwalior|Fe 550D-LRF":       {"bis": 3200, "loading": 200, "jsw_pmc": 500},
    "German Steel|Fe 550":            {"bis": 2500, "loading": 200, "jsw_pmc": 500},
    "N N Ispat|Fe 550":               {"bis": 2700, "loading": 270, "jsw_pmc": 500},
    "Real Ispat|Fe 550D-LRF":         {"bis": 4235, "loading": 265, "jsw_pmc": 500},
}


def get_plant_costs(plant: str, grade: str) -> dict:
    """Get BIS, Loading, JSW PMC for a plant+grade combo."""
    key = f"{plant}|{grade}"
    if key in PLANT_COSTS:
        return PLANT_COSTS[key]
    # Fallback: try any grade for this plant
    for k, v in PLANT_COSTS.items():
        if k.startswith(f"{plant}|"):
            return v
    return {"bis": 0, "loading": 0, "jsw_pmc": 500}

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
    st.caption("Actual: FOR - Freight - Inventory Cost - PMF | SteelMint: FOR - Freight - SteelMint - BIS - Loading - PMF")

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

    # User inputs - Row 1: FOR Price, Freight, Plant
    mc1, mc2, mc3 = st.columns(3)

    with mc1:
        for_price = st.number_input("FOR Price (INR)", min_value=0, value=0, step=100)
    with mc2:
        freight = st.number_input("Freight (INR)", min_value=0, value=0, step=100)
    with mc3:
        freight_plant = st.selectbox(
            "Freight is from which Plant?",
            options=list(PLANT_CITY_MAP.keys()),
            disabled=(freight == 0),
            help="Enter freight first" if freight == 0 else "Select the plant",
        ) if True else None

    # Row 2: Grade
    mc4, _, _ = st.columns(3)
    with mc4:
        selected_grade = st.selectbox("Grade", options=GRADES)

    # Auto-fill plant costs (BIS, Loading, JSW PMC)
    plant_for_cost = freight_plant if freight_plant else list(PLANT_CITY_MAP.keys())[0]
    pcosts = get_plant_costs(plant_for_cost, selected_grade)
    bis_cost = pcosts["bis"]
    loading_cost = pcosts["loading"]
    jsw_pmc = pcosts["jsw_pmc"]

    # Auto-fill inventory cost from JSON
    lookup_key = f"{plant_for_cost}|{selected_grade}"
    auto_cost = inv_costs.get(lookup_key, 0)
    if auto_cost == 0:
        auto_cost = grade_avgs.get(selected_grade, 0)
    actual_inventory_cost = auto_cost

    # Show auto-filled costs
    st.divider()

    # Ex-Works Price
    ex_works = for_price - freight if for_price > 0 else 0
    ew1, ew2, _ = st.columns(3)
    with ew1:
        if ex_works > 0:
            st.metric("Ex-Works Price (FOR - Freight)", f"INR {ex_works:,}")
        else:
            st.markdown("**Ex-Works Price:** Enter FOR Price and Freight above")

    st.divider()
    st.markdown(f"**Auto-filled costs for {plant_for_cost} ({selected_grade}):**")
    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1:
        st.metric("BIS", f"INR {bis_cost:,}")
    with ac2:
        st.metric("Loading Charges", f"INR {loading_cost:,}")
    with ac3:
        st.metric("JSW Project Mgmt Cost", f"INR {jsw_pmc:,}")
    with ac4:
        if actual_inventory_cost > 0:
            st.metric("Inventory Cost (from image)", f"INR {actual_inventory_cost:,}")
        else:
            actual_inventory_cost = st.number_input("Inventory Cost (INR)", min_value=0, value=0, step=100)

    # Get SteelMint price for the freight plant's city
    plant_city = PLANT_CITY_MAP.get(freight_plant, "Delhi/NCR") if freight_plant else "Delhi/NCR"

    # Last 15 calendar days avg SteelMint price (today - 15 to today)
    city_data_all = df.dropna(subset=[plant_city]).copy()
    last_available_date = city_data_all.iloc[-1]["Date"] if len(city_data_all) > 0 else pd.Timestamp.now()
    cal_15_start = last_available_date - pd.Timedelta(days=14)  # 15 days inclusive
    last15_mask = (df["Date"] >= cal_15_start) & (df["Date"] <= last_available_date)
    last15_data = df[last15_mask][plant_city].dropna()
    price_adj = PLANT_PRICE_ADJUSTMENT.get(plant_for_cost, 0)
    avg_steelmint_15 = (last15_data.mean() + price_adj) if len(last15_data) > 0 else 0
    avg_15_start_str = cal_15_start.strftime("%d %b")
    avg_15_end_str = last_available_date.strftime("%d %b %Y")

    # SteelMint date selection dropdown
    if len(city_data_all) > 0:
        # Get last 30 available dates for the dropdown
        available_dates = city_data_all.tail(30)["Date"].dt.strftime("%d %b %Y").tolist()
        available_dates.reverse()  # Most recent first

        sd1, sd2, _ = st.columns(3)
        with sd1:
            selected_sm_date = st.selectbox(
                "SteelMint Date (for Section 3)",
                options=available_dates,
                index=0,
                help="Select a date for SteelMint price comparison",
            )

        # Get price for selected date
        from datetime import datetime as dt_cls
        sel_date_parsed = pd.to_datetime(selected_sm_date, format="%d %b %Y")
        sel_row = city_data_all[city_data_all["Date"] == sel_date_parsed]
        if len(sel_row) > 0:
            selected_steelmint_price = float(sel_row.iloc[0][plant_city]) + price_adj
        else:
            selected_steelmint_price = 0
    else:
        selected_sm_date = "N/A"
        selected_steelmint_price = 0

    if price_adj != 0:
        st.caption(f"Note: {plant_for_cost} uses {plant_city} SteelMint price {price_adj:+,} adjustment")

    st.divider()

    # Calculate margins
    # Actual: FOR - Freight - Base Cost - PMF (no BIS/Loading, already in inventory cost)
    # SteelMint: FOR - Freight - SteelMint - BIS - Loading - PMF
    if for_price > 0:
        margin_actual = for_price - freight - actual_inventory_cost - jsw_pmc if actual_inventory_cost > 0 else None
        margin_15day = for_price - freight - avg_steelmint_15 - bis_cost - loading_cost - jsw_pmc
        margin_selected = for_price - freight - selected_steelmint_price - bis_cost - loading_cost - jsw_pmc

        plant_label = freight_plant if freight_plant else "N/A"
        st.markdown(f"**Plant:** {plant_label} | **Grade:** {selected_grade} | **SteelMint City:** {plant_city}")

        # Three columns for the three margin sections
        s1, s2, s3 = st.columns(3)

        with s1:
            st.markdown("#### 1. Actual Inventory")
            if margin_actual is not None:
                st.metric(
                    label=f"Inventory Cost: INR {actual_inventory_cost:,.0f}",
                    value=f"INR {margin_actual:,.0f}",
                    delta=f"{'Profit' if margin_actual >= 0 else 'Loss'}",
                    delta_color="normal" if margin_actual >= 0 else "inverse",
                )
            else:
                st.info("Enter Actual Inventory Cost above")

        with s2:
            st.markdown(f"#### 2. SteelMint 15-Day Avg")
            st.metric(
                label=f"{avg_15_start_str} to {avg_15_end_str}: INR {avg_steelmint_15:,.0f}",
                value=f"INR {margin_15day:,.0f}",
                delta=f"{'Profit' if margin_15day >= 0 else 'Loss'}",
                delta_color="normal" if margin_15day >= 0 else "inverse",
            )

        with s3:
            st.markdown(f"#### 3. SteelMint ({selected_sm_date})")
            st.metric(
                label=f"Price: INR {selected_steelmint_price:,.0f}",
                value=f"INR {margin_selected:,.0f}",
                delta=f"{'Profit' if margin_selected >= 0 else 'Loss'}",
                delta_color="normal" if margin_selected >= 0 else "inverse",
            )

        # Breakdown table
        st.divider()
        st.subheader("Breakdown")

        # Actual: no BIS/Loading
        actual_components = [
            "FOR Price",
            "- Freight",
            "- Base Cost (Avg Inventory 12-32MM)",
            "- JSW Project Mgmt Cost",
            "= Margin",
        ]
        actual_vals = [
            f"{for_price:,.0f}",
            f"{freight:,.0f}",
            f"{actual_inventory_cost:,.0f}" if actual_inventory_cost > 0 else "-",
            f"{jsw_pmc:,.0f}",
            f"{margin_actual:+,.0f}" if margin_actual is not None else "-",
        ]

        # SteelMint: includes BIS + Loading
        sm_components = [
            "FOR Price",
            "- Freight",
            "- Base Cost (SteelMint Price)",
            "- BIS",
            "- Loading Charges",
            "- JSW Project Mgmt Cost",
            "= Margin",
        ]
        sm15_vals = [
            f"{for_price:,.0f}",
            f"{freight:,.0f}",
            f"{avg_steelmint_15:,.0f}",
            f"{bis_cost:,.0f}",
            f"{loading_cost:,.0f}",
            f"{jsw_pmc:,.0f}",
            f"{margin_15day:+,.0f}",
        ]
        smsel_vals = [
            f"{for_price:,.0f}",
            f"{freight:,.0f}",
            f"{selected_steelmint_price:,.0f}",
            f"{bis_cost:,.0f}",
            f"{loading_cost:,.0f}",
            f"{jsw_pmc:,.0f}",
            f"{margin_selected:+,.0f}",
        ]

        # Show tables side by side
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.markdown("**Actual**")
            st.dataframe(
                pd.DataFrame({"Component": actual_components, "Value (INR)": actual_vals}),
                use_container_width=True, hide_index=True,
            )
        with bc2:
            st.markdown("**SteelMint 15-Day Avg**")
            st.dataframe(
                pd.DataFrame({"Component": sm_components, "Value (INR)": sm15_vals}),
                use_container_width=True, hide_index=True,
            )
        with bc3:
            st.markdown(f"**SteelMint ({selected_sm_date})**")
            st.dataframe(
                pd.DataFrame({"Component": sm_components, "Value (INR)": smsel_vals}),
                use_container_width=True, hide_index=True,
            )

    else:
        st.info("Enter a FOR Price to calculate margins.")

# --- Footer ---

st.divider()
st.caption(f"Data range: {min_date.strftime('%d %b %Y')} to {max_date.strftime('%d %b %Y')}")
