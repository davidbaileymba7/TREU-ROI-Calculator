# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# =====================
# TREU Partners ROI Calculator
# =====================

# Fixed Assumptions
YEARS = 3  # Forecast horizon in years
DISCOUNT_RATE = 0.10  # Annual discount rate for NPV
PRODUCTIVITY_GAIN_PCT = 15  # Productivity gain (%) from outsourcing
SALARY_PER_EMPLOYEE = 80000  # Avg employee salary for productivity savings
NUM_EMPLOYEES = 50  # Headcount impacted by productivity improvements
BROKER_FEE_PCT = 5  # Brokerage fee % of total annual benefit
OPP_COST_RATE = 0.20  # Opportunity cost % of subscription spend

# In-House Assumptions (Fixed)
OPP_MULTIPLIER = 3  # Opportunity cost multiplier on base hourly rate
BASE_HOURLY_RATE = 125.0  # Avg base pay ($/hr)
OPP_COST_PER_HOUR = BASE_HOURLY_RATE * OPP_MULTIPLIER  # Cost per diverted hour
INHOUSE_HOURS = 200  # Hours spent in-house per project
SUPPLIER_MGMT_PCT = 25  # % of annual time on supplier management
SUPPLIER_HOURLY_RATE = 135.0  # $/hr for supplier management

# Service Categories & Savings Rates
CATEGORY_PARAMS = {
    "Software Licensing": {"license_rate": 0.50, "impl_rate": 0.30},
    "SaaS Subscriptions": {"license_rate": 0.45, "impl_rate": 0.25},
    "Cloud Services": {"license_rate": 0.40, "impl_rate": 0.20},
    "Telecom Services": {"license_rate": 0.35, "impl_rate": 0.15},
    "Hardware Maintenance": {"license_rate": 0.30, "impl_rate": 0.10},
    "Mobility & IoT": {"license_rate": 0.40, "impl_rate": 0.20},
    "Security": {"license_rate": 0.55, "impl_rate": 0.35},
    "ITAM/ITSM": {"license_rate": 0.45, "impl_rate": 0.25}
}

# Streamlit setup
st.set_page_config(page_title="TREU ROI Calculator", layout="wide")

# Sidebar: Inputs
with st.sidebar:
    st.header("Inputs")
    category = st.selectbox(
        "Service Category", list(CATEGORY_PARAMS.keys()),
        help="Select the service category. Savings rates are based on industry benchmarks."
    )
    annual_spend = st.number_input(
        "Annual Spend ($)", min_value=0.0, value=100000.0,
        help="Enter total annual budget for the selected category."
    )
    st.markdown("---")
    st.subheader("Fixed Assumptions")
    st.caption(
        "Forecast horizon, discount rate, broker fee, opportunity cost, "
        "and in-house time assumptions are fixed and non-editable."
    )
    st.markdown(
        f"- Forecast Horizon: {YEARS} yrs  \
"
        f"- Discount Rate: {int(DISCOUNT_RATE*100)}% for NPV  \
"
        f"- Broker Fee: {BROKER_FEE_PCT}% of total annual benefit  \
"
        f"- Opportunity Cost: {int(OPP_COST_RATE*100)}% of spend  \
"
        f"- Opportunity Cost Multiplier: {OPP_MULTIPLIER}× base rate (${BASE_HOURLY_RATE}/hr) = ${OPP_COST_PER_HOUR}/hr  \
"
        f"- In-House Sourcing Hours: {INHOUSE_HOURS} hrs/project  \
"
        f"- Supplier Mgmt Time: {SUPPLIER_MGMT_PCT}% of annual hrs at ${SUPPLIER_HOURLY_RATE}/hr"
    )

# Retrieve rates
params = CATEGORY_PARAMS[category]
license_rate = params["license_rate"]
impl_rate = params["impl_rate"]

# Calculate savings
license_savings = annual_spend * license_rate
impl_savings = annual_spend * impl_rate
prod_savings = PRODUCTIVITY_GAIN_PCT/100 * SALARY_PER_EMPLOYEE * NUM_EMPLOYEES
annual_benefit = license_savings + impl_savings + prod_savings

# Outsourced scenario
subscription_cost = annual_spend
broker_fee_val = annual_benefit * BROKER_FEE_PCT/100
opp_cost_val = subscription_cost * OPP_COST_RATE
net_out = annual_benefit - subscription_cost - broker_fee_val - opp_cost_val

# In-house scenario
inhouse_cost = (
    OPP_COST_PER_HOUR * INHOUSE_HOURS +
    (SUPPLIER_MGMT_PCT/100) * 2080 * SUPPLIER_HOURLY_RATE
)
net_in = annual_benefit - inhouse_cost

# Time-value metrics
cf_out = [net_out] * YEARS
cf_in = [net_in] * YEARS
npv_out = sum(cf/((1+DISCOUNT_RATE)**i) for i, cf in enumerate(cf_out, 1))
npv_in = sum(cf/((1+DISCOUNT_RATE)**i) for i, cf in enumerate(cf_in, 1))
roi_out = (sum(cf_out)-subscription_cost)/subscription_cost * 100
roi_in = (sum(cf_in)-inhouse_cost)/inhouse_cost * 100
payback_out = next((i for i, cum in enumerate(np.cumsum(cf_out),1) if cum>subscription_cost), None)
payback_in = next((i for i, cum in enumerate(np.cumsum(cf_in),1) if cum>inhouse_cost), None)

# Plot helpers using matplotlib
def plot_mat(data, title):
    fig, ax = plt.subplots()
    ax.bar(range(1, YEARS+1), data)
    ax.set_xlabel('Year')
    ax.set_ylabel('Net Benefit ($)')
    ax.set_title(title)
    return fig

# Main UI
def main():
    st.title(f"🚀 ROI Calculator — {category}")
    tab1, tab2, tab3, tab4 = st.tabs(["Summary","Breakdown","Compare","Export"])

    with tab1:
        st.subheader("Key Metrics")
        col1, col2 = st.columns(2)
        col1.metric("Outsourced NPV", f"${npv_out:,.0f}", help="NPV of outsourcing at 10% discount rate.")
        col1.metric("Outsourced ROI", f"{roi_out:.1f}%", help="ROI = net benefit ÷ subscription cost.")
        col1.metric("Payback (yrs)", f"{payback_out or '> Horizon'}", help="Years to recover costs.")
        col2.metric("In-House NPV", f"${npv_in:,.0f}", help="NPV of in-house scenario.")
        col2.metric("In-House ROI", f"{roi_in:.1f}%", help="ROI for in-house based on fixed costs.")
        col2.metric("Payback (yrs)", f"{payback_in or '> Horizon'}", help="Years to recover in-house costs.")

    with tab2:
        st.subheader("Annual Net Benefit: Outsourced")
        fig = plot_mat(cf_out, 'Outsourced Net Benefit')
        st.pyplot(fig, use_container_width=True)

    with tab3:
        st.subheader("Scenario Comparison")
        fig, ax = plt.subplots()
        ax.bar(np.arange(1, YEARS+1)-0.2, cf_in, width=0.4, label='In-House')
        ax.bar(np.arange(1, YEARS+1)+0.2, cf_out, width=0.4, label='Outsourced')
        ax.set_xlabel('Year')
        ax.set_ylabel('Net Benefit ($)')
        ax.legend()
        st.pyplot(fig, use_container_width=True)

    with tab4:
        st.subheader("Download Results")
        df = pd.DataFrame({
            'Year': range(1, YEARS+1),
            'Outsourced': cf_out,
            'In-House': cf_in,
            'NPV Outsourced': npv_out,
            'NPV In-House': npv_in
        })
        st.download_button("Download CSV", df.to_csv(index=False).encode(), "roi_results.csv")

if __name__ == '__main__':
    main()
