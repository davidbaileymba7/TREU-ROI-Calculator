# app.py
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from fpdf import FPDF

# =====================
# TREU Partners ROI Calculator
# =====================

# Fixed Assumptions
YEARS = 3
DISCOUNT_RATE = 0.10
PRODUCTIVITY_GAIN_PCT = 15
SALARY_PER_EMPLOYEE = 80000
NUM_EMPLOYEES = 50
BROKER_FEE_PCT = 5
OPP_COST_RATE = 0.20

# In-House Assumptions (Fixed, not editable)
OPP_MULTIPLIER = 3
BASE_HOURLY_RATE = 125.0
OPP_COST_PER_HOUR = BASE_HOURLY_RATE * OPP_MULTIPLIER
INHOUSE_HOURS = 200
SUPPLIER_MGMT_PCT = 25
SUPPLIER_HOURLY_RATE = 135.0

# Service Categories & Industry Rates
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
    st.header("Inputs")
    category = st.selectbox("Service Category", list(CATEGORY_PARAMS.keys()), help="Choose the spend category to evaluate.")
    annual_spend = st.number_input("Annual Spend ($)", min_value=0.0, value=100000.0, help="Total annual budget in the selected category.")
    st.markdown("---")
    st.caption("Fixed assumptions (not editable):")
    st.markdown(
        f"- Forecast Horizon: {YEARS} yrs  \
        - Discount Rate: {int(DISCOUNT_RATE*100)}%  \
        - Broker Fee: {BROKER_FEE_PCT}%  \
        - Opportunity Cost: {int(OPP_COST_RATE*100)}% of spend  \
        - Opportunity Cost Multiplier: {OPP_MULTIPLIER}× base rate at ${BASE_HOURLY_RATE}/hr = ${OPP_COST_PER_HOUR}/hr  \
        - In-House Sourcing Hours: {INHOUSE_HOURS} hrs/project  \
        - Supplier Mgmt Time: {SUPPLIER_MGMT_PCT}% of annual hrs at ${SUPPLIER_HOURLY_RATE}/hr"
    )

# Retrieve Rates and Compute Savings
rates = CATEGORY_PARAMS[category]
license_rate = rates["license_rate"]
impl_rate = rates["implementation_rate"]
license_savings = annual_spend * license_rate
implementation_savings = annual_spend * impl_rate
productivity_savings = PRODUCTIVITY_GAIN_PCT/100 * SALARY_PER_EMPLOYEE * NUM_EMPLOYEES
annual_benefit = license_savings + implementation_savings + productivity_savings

# Outsourced Scenario
subscription_cost = annual_spend
broker_fee_value = annual_benefit * BROKER_FEE_PCT/100
opp_cost_value = subscription_cost * OPP_COST_RATE
net_out = annual_benefit - subscription_cost - broker_fee_value - opp_cost_value

# In-House Scenario
inhouse_cost = OPP_COST_PER_HOUR * INHOUSE_HOURS + (SUPPLIER_MGMT_PCT/100) * 2080 * SUPPLIER_HOURLY_RATE
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
st.title(f"🚀 ROI Calculator — {category}")
tab1, tab2, tab3, tab4 = st.tabs(["Summary","Breakdown","Compare","Export"])

with tab1:
    st.subheader("Key Metrics")
    col1, col2 = st.columns(2)
    col1.metric("Outsourced NPV", f"${npv_out:,.0f}")
    col1.metric("Outsourced ROI", f"{roi_out:.1f}%")
    col1.metric("Payback Period", f"{payback_out or '> Horizon'} yrs")
    col2.metric("In-House NPV", f"${npv_in:,.0f}")
    col2.metric("In-House ROI", f"{roi_in:.1f}%")
    col2.metric("Payback Period", f"{payback_in or '> Horizon'} yrs")

with tab2:
    st.subheader("Annual Net Benefit: Outsourced")
    df_out = pd.DataFrame({'Year': range(1, YEARS+1), 'Net Benefit': cf_out}).set_index('Year')
    st.bar_chart(df_out['Net Benefit'])

with tab3:
    st.subheader("Scenario Comparison")
    df_comp = pd.DataFrame({'In-House': cf_in, 'Outsourced': cf_out}, index=range(1, YEARS+1))
    df_comp.index.name = 'Year'
    st.bar_chart(df_comp)

with tab4:
    st.subheader("Download Results")
    df_export = df_comp.copy()
    df_export['NPV Outsourced'] = npv_out
    df_export['NPV In-House'] = npv_in
    st.download_button("Download CSV", df_export.to_csv().encode(), "roi_results.csv")
    
    # PDF Export (optional)
    try:
        buffer = BytesIO()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"ROI Report — {category}", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"Outsourced NPV: ${npv_out:,.0f}", ln=True)
        pdf.cell(0, 8, f"In-House NPV: ${npv_in:,.0f}", ln=True)
        pdf.cell(0, 8, f"Outsourced ROI: {roi_out:.1f}%", ln=True)
        pdf.cell(0, 8, f"In-House ROI: {roi_in:.1f}%", ln=True)
        pdf.output(buffer)
        st.download_button("Download PDF", buffer.getvalue(), "roi_report.pdf")
    except Exception as e:
        st.error("PDF export failed; install fpdf. Error: " + str(e))

st.markdown("---")
st.caption("*Estimates based on fixed industry assumptions.*")
