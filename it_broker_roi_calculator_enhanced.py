import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# App Configuration and Theming
st.set_page_config(page_title="TREU Partners IT Broker ROI Calculator", layout="wide")
st.markdown(
    """
    <style>
    .reportview-container {
        background-color: #FFFFFF;
    }
    .sidebar .sidebar-content {
        background-color: #000000;
        color: #FFFFFF;
    }
    .css-1d391kg {  /* Streamlit header class */
        color: #D80016;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title and Description
st.title("IT Broker vs. In-House Value & Opportunity Cost Calculator")
st.markdown(
    """
Adjust the sliders to compare **In-House** outcomes versus engaging an **IT Broker**, with multi-year forecasts, sensitivity ranges, and branded visuals.
"""
)

# Sidebar Inputs
st.sidebar.header("Broker Inputs")
baseline_spend = st.sidebar.number_input("Baseline Annual IT Spend ($)", min_value=0, value=1_000_000, step=50_000)
savings_pct = st.sidebar.slider("Expected Broker Savings (%)", min_value=0, max_value=100, value=30)
fee_pct = st.sidebar.slider("Broker Fee (%)", min_value=0, max_value=50, value=10)
baseline_hours = st.sidebar.number_input("Annual Procurement Hours", min_value=0, value=500, step=50)
time_saved_pct = st.sidebar.slider("Time Saved by Broker (%)", min_value=0, max_value=100, value=50)
cost_per_hour = st.sidebar.number_input("Staff Cost per Hour ($)", min_value=0, value=150, step=10)
opp_value_per_hour = st.sidebar.number_input("Opportunity Value per Hour ($)", min_value=0, value=250, step=10)
forecast_years = st.sidebar.slider("Forecast Duration (Years)", min_value=1, max_value=10, value=3)

# Sensitivity Analysis Inputs
st.sidebar.header("Sensitivity Analysis")
savings_range = st.sidebar.slider("Savings % Range", min_value=0, max_value=100, value=(10, 50))
fee_range = st.sidebar.slider("Fee % Range", min_value=0, max_value=50, value=(8, 12))

# Calculation Function
def calculate_metrics(spend, savings_pct, fee_pct, hours, time_saved_pct, cost_hr, opp_hr):
    gross_savings = spend * savings_pct / 100
    fee_cost = spend * fee_pct / 100
    net_savings = gross_savings - fee_cost
    hours_saved = hours * time_saved_pct / 100
    time_value = hours_saved * cost_hr
    opp_value = hours_saved * opp_hr
    total_benefit = net_savings + time_value + opp_value
    financial_roi = net_savings / fee_cost if fee_cost else np.nan
    total_roi = total_benefit / fee_cost if fee_cost else np.nan
    return {
        "Gross Savings ($)": gross_savings,
        "Broker Fee Cost ($)": fee_cost,
        "Net Savings ($)": net_savings,
        "Hours Saved": hours_saved,
        "Time Savings Value ($)": time_value,
        "Opportunity Value ($)": opp_value,
        "Total Benefit ($)": total_benefit,
        "Financial ROI (x)": financial_roi,
        "Total ROI (x)": total_roi
    }

# Metrics for In-House vs. Broker
inhouse = calculate_metrics(baseline_spend, 0, 0, baseline_hours, 0, cost_per_hour, opp_value_per_hour)
broker = calculate_metrics(baseline_spend, savings_pct, fee_pct, baseline_hours, time_saved_pct, cost_per_hour, opp_value_per_hour)

# Side-by-Side Tables
st.subheader("Side-by-Side Metrics")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**In-House**")
    st.table(pd.DataFrame.from_dict(inhouse, orient='index', columns=["Value"]))
with col2:
    st.markdown("**IT Broker**")
    st.table(pd.DataFrame.from_dict(broker, orient='index', columns=["Value"]))

# Multi-Year Forecast
years = list(range(1, forecast_years + 1))
cumulative_benefits = [broker["Total Benefit ($)"] * y for y in years]
st.subheader("Multi-Year Benefit Projection")
fig1, ax1 = plt.subplots()
ax1.plot(years, cumulative_benefits, marker='o', color="#D80016")
ax1.set_xlabel("Year")
ax1.set_ylabel("Cumulative Benefit ($)")
ax1.set_title("Over " + str(forecast_years) + " Years")
st.pyplot(fig1)

# Sensitivity Analysis Chart
st.subheader("Sensitivity Analysis")
x_vals = list(range(savings_range[0], savings_range[1] + 1, 5))
fig2, ax2 = plt.subplots()
for fee in fee_range:
    roi_vals = [calculate_metrics(baseline_spend, x, fee, baseline_hours, time_saved_pct, cost_per_hour, opp_value_per_hour)["Total ROI (x)"] for x in x_vals]
    ax2.plot(x_vals, roi_vals, marker='o', label=f"Fee {fee}%")
ax2.axhline(1, linestyle='--', color="#000000", linewidth=1)
ax2.set_xlabel("Savings (%)")
ax2.set_ylabel("Total ROI (x)")
ax2.set_title("ROI Sensitivity to Savings & Fees")
ax2.legend()
st.pyplot(fig2)

# Download
st.markdown("### Download Data")
df_compare = pd.concat([pd.Series(inhouse, name="In-House"), pd.Series(broker, name="IT Broker")], axis=1)
st.download_button("Download CSV", df_compare.to_csv(), file_name='broker_vs_inhouse.csv', mime='text/csv')

st.markdown("© TREU Partners • Strategic Advocacy in IT Sourcing")
