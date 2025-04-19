
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Domain-specific default parameters (industry standards)
domain_defaults = {
    "Telecom": {"savings_pct": 35, "fee_pct": 10, "baseline_hours": 400},
    "Mobility & IoT": {"savings_pct": 25, "fee_pct": 10, "baseline_hours": 450},
    "Cloud & SaaS": {"savings_pct": 30, "fee_pct": 10, "baseline_hours": 500},
    "Security": {"savings_pct": 20, "fee_pct": 10, "baseline_hours": 350},
    "Governance": {"savings_pct": 15, "fee_pct": 10, "baseline_hours": 300},
    "All": {"savings_pct": 30, "fee_pct": 10, "baseline_hours": 500}
}

# -- App Configuration and Theming --
st.set_page_config(page_title="TREU IT Broker Value Calculator", layout="wide")
st.markdown(
    """
    <style>
    .reportview-container { background-color: #FFFFFF; }
    .sidebar .sidebar-content { background-color: #000000; color: #FFFFFF; }
    .stMetric { padding: 1rem; background: #F0F0F0; border-radius: 0.5rem; }
    .css-1d391kg { color: #D80016; font-size: 2rem; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True
)

# -- Header & Description --
st.title("IT Broker vs. In-House Value Calculator")
st.markdown("**Compare your In-House procurement costs, time, and risk against engaging an IT Broker.**")

# -- Domain Selection --
domain = st.selectbox("Select a Technology Domain:", list(domain_defaults.keys()))
defaults = domain_defaults[domain]

# -- Input Sections --
with st.expander("Financial Inputs", expanded=True):
    col1, col2, col3 = st.columns(3)
    baseline_spend = col1.number_input("Annual IT Spend ($)", value=1_000_000, step=50_000)
    savings_pct = col2.slider(
        "Expected Broker Savings (%)", 0, 100, defaults["savings_pct"],
        help="Typical savings benchmark for selected domain"
    )
    fee_pct = col3.slider(
        "Broker Fee (%)", 0, 50, defaults["fee_pct"],
        help="Standard broker fee for selected domain"
    )

with st.expander("Time & Opportunity Inputs", expanded=False):
    col4, col5, col6 = st.columns(3)
    baseline_hours = col4.number_input(
        "Annual Procurement Hours", value=defaults["baseline_hours"], step=50,
        help="Average hours spent managing sourcing for selected domain"
    )
    time_saved_pct = col5.slider("Time Saved by Broker (%)", 0, 100, 50)
    cost_per_hour = col6.number_input("Staff Cost per Hour ($)", value=150, step=10)
    opp_value_per_hour = st.number_input("Opportunity Value per Hour ($)", value=250, step=10)

# -- Calculation Function --
def calc(spend, save_pct, fee_pct, hrs, time_pct, cost_hr, opp_hr):
    gross = spend * save_pct / 100
    fee = spend * fee_pct / 100
    net = gross - fee
    hrs_saved = hrs * time_pct / 100
    time_val = hrs_saved * cost_hr
    opp_val = hrs_saved * opp_hr
    total_benefit = net + time_val + opp_val
    fin_roi = net / fee if fee else np.nan
    total_roi = total_benefit / fee if fee else np.nan
    return gross, fee, net, hrs_saved, time_val, opp_val, total_benefit, fin_roi, total_roi

# -- Compute Metrics --
gross, fee, net, hrs_saved, time_val, opp_val, total, fin_roi, tot_roi = calc(
    baseline_spend, savings_pct, fee_pct, baseline_hours, time_saved_pct, cost_per_hour, opp_value_per_hour
)

# -- KPI Metrics Cards --
st.markdown("### Key Outcomes")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Net Savings ($)", f"{net:,.0f}")
k2.metric("Total Benefit ($)", f"{total:,.0f}")
k3.metric("Financial ROI (x)", f"{fin_roi:.2f}")
k4.metric("Total ROI (x)", f"{tot_roi:.2f}")

# -- Side-by-Side Metrics Table --
st.subheader("In‑House vs. IT Broker Metrics")
df_compare = pd.DataFrame({
    "Metric": [
        "Gross Savings ($)",
        "Broker Fee Cost ($)",
        "Net Savings ($)",
        "Hours Saved",
        "Time Savings Value ($)",
        "Opportunity Value ($)",
        "Total Benefit ($)",
        "Financial ROI (x)",
        "Total ROI (x)"
    ],
    "In‑House": [
        0,  # gross savings
        0,  # fee cost
        0,  # net savings
        0,  # hours saved
        0,  # time value
        0,  # opportunity value
        0,  # total benefit
        np.nan,  # financial ROI
        np.nan   # total ROI
    ],
    "IT Broker": [
        gross,
        fee,
        net,
        hrs_saved,
        time_val,
        opp_val,
        total,
        fin_roi,
        tot_roi
    ]
}).set_index("Metric")
st.table(df_compare)

# -- Charts --
st.markdown("### Benefit Breakdown")
fig1, ax1 = plt.subplots(figsize=(4,4))
ax1.pie([net, time_val, opp_val], labels=["Net", "Time Value", "Opportunity"], autopct="%1.1f%%", startangle=140)
ax1.set_title("Benefit Distribution")
st.pyplot(fig1, use_container_width=True)

st.markdown("### 3-Year Cumulative Benefit Projection")
years = list(range(1, 4+1))
cum_benefits = [total * y for y in years]
fig2, ax2 = plt.subplots()
ax2.plot(years, cum_benefits, marker='o', color="#D80016")
ax2.set_xlabel("Year"); ax2.set_ylabel("Cumulative Benefit ($)")
st.pyplot(fig2, use_container_width=True)

st.markdown("### ROI Sensitivity Analysis")
s_range = list(range(max(0, savings_pct-10), min(100, savings_pct+10)+1, 5))
fig3, ax3 = plt.subplots()
for f in [max(0, fee_pct-2), fee_pct, min(50, fee_pct+2)]:
    vals = [calc(baseline_spend, s, f, baseline_hours, time_saved_pct, cost_per_hour, opp_value_per_hour)[8] for s in s_range]
    ax3.plot(s_range, vals, marker='o', label=f"Fee {f}%")
ax3.axhline(1, linestyle='--', color="#000000")
ax3.set_xlabel("Savings (%)"); ax3.set_ylabel("Total ROI (x)")
ax3.legend(title="Broker Fee")
st.pyplot(fig3, use_container_width=True)

# -- Download --
st.markdown("### Download Your Results")
df_out = pd.DataFrame({
    "Metric": ["Net Savings", "Total Benefit", "Financial ROI", "Total ROI"],
    "In‑House": [0, 0, np.nan, np.nan],
    "Broker": [net, total, fin_roi, tot_roi]
})
st.download_button("Download CSV", df_out.to_csv(index=False), file_name="broker_vs_inhouse.csv")

st.markdown("© TREU Partners • Strategic Advocacy in IT Sourcing")
