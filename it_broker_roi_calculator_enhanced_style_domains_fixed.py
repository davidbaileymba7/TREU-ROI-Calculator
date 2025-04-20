# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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

# Streamlit Page Configuration
st.set_page_config(page_title="TREU ROI Calculator", layout="wide")

# Sidebar: Only Editable Fields
with st.sidebar:
    st.header("Inputs")
    category = st.selectbox(
        "Service Category", list(CATEGORY_PARAMS.keys()),
        help="Choose the spend category to evaluate."
    )
    annual_spend = st.number_input(
        "Annual Spend ($)", min_value=0.0, value=100000.0,
        help="Total annual budget in the selected category."
    )
    st.markdown("---")
    st.caption("Fixed assumptions displayed here are not editable:")
    st.markdown(
        f"- Forecast Horizon: {YEARS} yrs  \
        - Discount Rate: {int(DISCOUNT_RATE*100)}%  \
        - Broker Fee: {BROKER_FEE_PCT}%  \
        - Opportunity Cost: {int(OPP_COST_RATE*100)}% of spend  \
        - Opportunity Cost Multiplier: {OPP_MULTIPLIER}× base rate at ${BASE_HOURLY_RATE}/hr = ${OPP_COST_PER_HOUR}/hr  \
        - In-House Sourcing Hours: {INHOUSE_HOURS} hrs/project  \
        - Supplier Mgmt Time: {SUPPLIER_MGMT_PCT}% of annual hrs at ${SUPPLIER_HOURLY_RATE}/hr"
    )

# Retrieve Selected Category Rates
rates = CATEGORY_PARAMS[category]
license_rate = rates["license_rate"]
impl_rate = rates["implementation_rate"]

# ROI Calculations
license_savings = annual_spend * license_rate
implementation_savings = annual_spend * impl_rate
productivity_savings = PRODUCTIVITY_GAIN_PCT/100 * SALARY_PER_EMPLOYEE * NUM_EMPLOYEES
annual_benefit = license_savings + implementation_savings + productivity_savings
broker_fee = annual_benefit * BROKER_FEE_PCT/100
opp_cost_value = annual_spend * OPP_COST_RATE
net_out = annual_benefit - annual_spend - broker_fee - opp_cost_value
inhouse_cost = OPP_COST_PER_HOUR * INHOUSE_HOURS + (SUPPLIER_MGMT_PCT/100) * 2080 * SUPPLIER_HOURLY_RATE
net_in = annual_benefit - inhouse_cost

# Cash Flows and Metrics
cf_out = [net_out] * YEARS
cf_in = [net_in] * YEARS
npv_out = sum(cf/((1+DISCOUNT_RATE)**i) for i,cf in enumerate(cf_out,1))
npv_in = sum(cf/((1+DISCOUNT_RATE)**i) for i,cf in enumerate(cf_in,1))
roi_out = (sum(cf_out)-annual_spend)/annual_spend*100
roi_in = (sum(cf_in)-inhouse_cost)/inhouse_cost*100
payback_out = next((i for i,cum in enumerate(np.cumsum(cf_out),1) if cum>annual_spend), None)
payback_in = next((i for i,cum in enumerate(np.cumsum(cf_in),1) if cum>inhouse_cost), None)

# Plot Helper
import pandas as pd

def plot_benefit(data, label):
    df = pd.DataFrame({"Year": range(1, YEARS+1), "Net Benefit": data})
    fig = go.Figure(go.Bar(x=df.Year, y=df["Net Benefit"], name=label))
    fig.update_layout(xaxis_title="Year", yaxis_title="Net Benefit ($)", plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
    return fig

# Main UI
st.title(f"ROI Calculator — {category}")
tab1, tab2, tab3, tab4 = st.tabs(["Summary","Breakdown","Compare","Export"])

with tab1:
    st.subheader("Key Metrics")
    col1, col2 = st.columns(2)
    col1.metric("Outsourced NPV", f"${npv_out:,.0f}", help="NPV of outsourcing scenario.")
    col1.metric("Outsourced ROI", f"{roi_out:.1f}%")
    col1.metric("Payback", f"{payback_out or '> Horizon'} yrs")
    col2.metric("In-House NPV", f"${npv_in:,.0f}")
    col2.metric("In-House ROI", f"{roi_in:.1f}%")
    col2.metric("Payback", f"{payback_in or '> Horizon'} yrs")

with tab2:
    st.subheader("Annual Net Benefit: Outsourced")
    st.plotly_chart(plot_benefit(cf_out, 'Outsourced'), use_container_width=True)

with tab3:
    st.subheader("Scenario Comparison")
    df_comp = pd.DataFrame({"Year": range(1, YEARS+1), "Outsourced": cf_out, "In-House": cf_in})
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_comp.Year, y=df_comp["In-House"], name="In-House"))
    fig.add_trace(go.Bar(x=df_comp.Year, y=df_comp["Outsourced"], name="Outsourced"))
    fig.update_layout(barmode='group', xaxis_title='Year', yaxis_title='Net Benefit ($)', plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF')
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Download Results")
    df_exp = pd.DataFrame({"Year": range(1, YEARS+1), "Outsourced": cf_out, "In-House": cf_in})
    st.download_button("Download CSV", df_exp.to_csv(index=False).encode(), "roi.csv")
    # PDF Export (requires fpdf install: pip install fpdf)
    try:
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
        pdf_output = pdf.output(dest="S").encode('latin-1')
        st.download_button("Download PDF", pdf_output, "roi_report.pdf")
    except Exception as e:
        st.error("PDF export failed. Ensure 'fpdf' is installed. Error: " + str(e))

st.markdown("---")
st.caption("*Estimates based on fixed industry assumptions.*")
