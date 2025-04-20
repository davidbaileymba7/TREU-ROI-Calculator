# app.py
import streamlit as st
import pandas as pd
import numpy as np
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
BROKER_FEE_PCT = 5  # Brokerage fee percentage of total annual benefit
OPP_COST_RATE = 0.20  # Opportunity cost as % of subscription spend

# In-House Assumptions (Fixed, not editable)
OPP_MULTIPLIER = 3  # Opportunity cost multiplier applied to base hourly rate
BASE_HOURLY_RATE = 125.0  # Avg base pay ($/hr) for IT/Procurement/Legal roles
OPP_COST_PER_HOUR = BASE_HOURLY_RATE * OPP_MULTIPLIER  # Actual cost per diverted hour
INHOUSE_HOURS = 200  # Hours spent in-house per sourcing project
SUPPLIER_MGMT_PCT = 25  # % of annual time spent on supplier management
SUPPLIER_HOURLY_RATE = 135.0  # Avg rate ($/hr) for supplier management activities

# Service Categories & Industry Rates (License vs. Implementation savings)
CATEGORY_PARAMS = {
    "Software Licensing": {"license_rate": 0.50, "implementation_rate": 0.30},
    "SaaS Subscriptions": {"license_rate": 0.45, "implementation_rate": 0.25},
    "Cloud Services": {"license_rate": 0.40, "implementation_rate": 0.20},
    "Telecom Services": {"license_rate": 0.35, "implementation_rate": 0.15},
    "Hardware Maintenance": {"license_rate": 0.30, "implementation_rate": 0.10},
    "Mobility & IoT": {"license_rate": 0.40, "implementation_rate": 0.20},
    "Security": {"license_rate": 0.55, "implementation_rate": 0.35},
    "ITAM/ITSM": {"license_rate": 0.45, "implementation_rate": 0.25}
}

# Streamlit Page Setup
st.set_page_config(page_title="TREU ROI Calculator", layout="wide")

# Sidebar Inputs
with st.sidebar:
    st.header("🔧 Inputs")
    category = st.selectbox(
        "Service Category", list(CATEGORY_PARAMS.keys()),
        help="Select the service area; savings rates are based on industry benchmarks for licensing and implementation costs."
    )
    annual_spend = st.number_input(
        "Annual Spend ($)", min_value=0.0, value=100000.0,
        help="Enter the total annual budget for the chosen service category; this drives license and implementation savings calculations."
    )
    st.markdown("---")
    st.caption("Fixed assumptions (not editable):")
    st.markdown(
        f"- **Forecast Horizon:** {YEARS} years\n"
        f"- **Discount Rate:** {int(DISCOUNT_RATE*100)}% for NPV\n"
        f"- **Broker Fee:** {BROKER_FEE_PCT}% of the *total annual benefit* (license + implementation + productivity savings)\n"
        f"- **Opportunity Cost:** {int(OPP_COST_RATE*100)}% of subscription spend (value of alternative investments)\n"
        f"- **Opportunity Cost Multiplier:** {OPP_MULTIPLIER}× base hourly rate (${BASE_HOURLY_RATE}/hr) = ${OPP_COST_PER_HOUR}/hr lost per diversion\n"
        f"- **In-House Sourcing Hours:** {INHOUSE_HOURS} hrs per project spent by internal teams\n"
        f"- **Supplier Mgmt Time:** {SUPPLIER_MGMT_PCT}% of annual hours at ${SUPPLIER_HOURLY_RATE}/hr for ongoing supplier relationships\n"
    )

# Retrieve Rates and Compute Savings
rates = CATEGORY_PARAMS[category]
license_rate = rates["license_rate"]
impl_rate = rates["implementation_rate"]
license_savings = annual_spend * license_rate
implementation_savings = annual_spend * impl_rate
productivity_savings = PRODUCTIVITY_GAIN_PCT/100 * SALARY_PER_EMPLOYEE * NUM_EMPLOYEES
annual_benefit = license_savings + implementation_savings + productivity_savings

# Outsourced Scenario Calculations
subscription_cost = annual_spend
broker_fee_value = annual_benefit * BROKER_FEE_PCT/100
opp_cost_value = subscription_cost * OPP_COST_RATE
net_out = annual_benefit - subscription_cost - broker_fee_value - opp_cost_value

# In-House Scenario Calculations
inhouse_cost = (
    OPP_COST_PER_HOUR * INHOUSE_HOURS +
    (SUPPLIER_MGMT_PCT/100) * 2080 * SUPPLIER_HOURLY_RATE
)
net_in = annual_benefit - inhouse_cost

# Metrics Calculation
cf_out = [net_out] * YEARS
cf_in = [net_in] * YEARS
npv_out = sum(cf/((1+DISCOUNT_RATE)**i) for i,cf in enumerate(cf_out,1))
npv_in = sum(cf/((1+DISCOUNT_RATE)**i) for i,cf in enumerate(cf_in,1))
roi_out = (sum(cf_out) - subscription_cost) / subscription_cost * 100
roi_in = (sum(cf_in) - inhouse_cost) / inhouse_cost * 100
payback_out = next((i for i,cum in enumerate(np.cumsum(cf_out),1) if cum>subscription_cost), None)
payback_in = next((i for i,cum in enumerate(np.cumsum(cf_in),1) if cum>inhouse_cost), None)

# Main Interface
def main():
    st.title(f"🚀 ROI Calculator — {category}")
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary","📈 Breakdown","🔍 Compare","📥 Export"])

    with tab1:
        st.subheader("Key Metrics")
        c1, c2 = st.columns(2)
        c1.metric("Outsourced NPV", f"${npv_out:,.0f}", help="Net present value of outsourcing scenario using a 10% discount rate.")
        c1.metric("Outsourced ROI", f"{roi_out:.1f}%", help="Return on investment calculated as total net benefit divided by subscription cost.")
        c1.metric("Payback Period", f"{payback_out or '> Horizon'} yrs", help="Number of years to recover subscription cost from net benefits.")
        c2.metric("In-House NPV", f"${npv_in:,.0f}", help="NPV of maintaining in-house processes with fixed assumption costs.")
        c2.metric("In-House ROI", f"{roi_in:.1f}%", help="ROI for in-house scenario based on fixed time and cost assumptions.")
        c2.metric("Payback Period", f"{payback_in or '> Horizon'} yrs", help="Years to recover in-house costs from net in-house benefits.")

    with tab2:
        st.subheader("Annual Net Benefit: Outsourced")
        df_out = pd.DataFrame({"Year": range(1, YEARS+1), "Net Benefit": cf_out}).set_index('Year')
        st.bar_chart(df_out['Net Benefit'], use_container_width=True)

    with tab3:
        st.subheader("Scenario Comparison")
        df_comp = pd.DataFrame({"In-House": cf_in, "Outsourced": cf_out}, index=range(1, YEARS+1))
        df_comp.index.name = 'Year'
        st.bar_chart(df_comp, use_container_width=True)

    with tab4:
        st.subheader("Download Results")
        df_export = df_comp.copy()
        df_export['NPV Outsourced'] = npv_out
        df_export['NPV In-House'] = npv_in
        st.download_button("Download CSV", df_export.to_csv(index=False).encode(), "roi_results.csv")

if __name__ == '__main__':
    main()
