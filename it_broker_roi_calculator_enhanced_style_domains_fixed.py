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

# In-House Assumptions
OPP_MULTIPLIER = 3
BASE_HOURLY_RATE = 125.0
OPP_COST_PER_HOUR = BASE_HOURLY_RATE * OPP_MULTIPLIER
INHOUSE_HOURS = 200
SUPPLIER_MGMT_PCT = 25
SUPPLIER_HOURLY_RATE = 135.0

# Service Categories & Industry Rates
# Sources: Flexera, IDC, Gartner, Forrester, ABI Research, SiriusDecisions
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

# Page Setup
st.set_page_config(page_title="TREU ROI Calculator", layout="wide")
st.markdown("<style>.stTabs [data-baseweb] {font-size:1.1rem;}</style>", unsafe_allow_html=True)

# Sidebar Inputs
with st.sidebar:
    st.header("🔧 Inputs")
    category = st.selectbox("Select Service Category", list(CATEGORY_PARAMS.keys()), help="Choose the spend category.")
    annual_spend = st.number_input("Annual Spend ($)", min_value=0.0, value=100000.0)
    with st.expander("ℹ️ View All Assumptions"):
        st.markdown(f"- **Forecast Horizon:** {YEARS} years\n- **Discount Rate:** {int(DISCOUNT_RATE*100)}%\n- **Broker Fee:** {BROKER_FEE_PCT}%\n- **Opportunity Cost:** {int(OPP_COST_RATE*100)}% of spend\n")
        st.markdown(f"- **Opportunity Cost Multiplier:** {OPP_MULTIPLIER}× base rate at ${BASE_HOURLY_RATE}/hr = ${OPP_COST_PER_HOUR}/hr\n- **In-House Sourcing Hours:** {INHOUSE_HOURS} hrs/project\n- **Supplier Mgmt Time:** {SUPPLIER_MGMT_PCT}% of annual hours at ${SUPPLIER_HOURLY_RATE}/hr\n")

# Compute Rates
rates = CATEGORY_PARAMS[category]
license_rate = rates["license_rate"]
impl_rate = rates["implementation_rate"]

# Calculations
license_savings = annual_spend * license_rate
implementation_savings = annual_spend * impl_rate
prod_savings = PRODUCTIVITY_GAIN_PCT/100 * SALARY_PER_EMPLOYEE * NUM_EMPLOYEES
annual_benefit = license_savings + implementation_savings + prod_savings
broker_fee = annual_benefit * BROKER_FEE_PCT/100
opp_cost = annual_spend * OPP_COST_RATE
net_out = annual_benefit - annual_spend - broker_fee - opp_cost
inhouse_cost = OPP_COST_PER_HOUR * INHOUSE_HOURS + (SUPPLIER_MGMT_PCT/100)*2080*SUPPLIER_HOURLY_RATE
net_in = annual_benefit - inhouse_cost

# Cash Flows
cf_out = [net_out]*YEARS
cf_in = [net_in]*YEARS
npv_out = sum(cf/((1+DISCOUNT_RATE)**i) for i,cf in enumerate(cf_out,1))
npv_in = sum(cf/((1+DISCOUNT_RATE)**i) for i,cf in enumerate(cf_in,1))
roi_out = (sum(cf_out)-annual_spend)/annual_spend*100
roi_in = (sum(cf_in)-inhouse_cost)/inhouse_cost*100
payback_out = next((i for i,cum in enumerate(np.cumsum(cf_out),1) if cum>annual_spend), None)
payback_in = next((i for i,cum in enumerate(np.cumsum(cf_in),1) if cum>inhouse_cost), None)

# Plot Function
def plot_bar(data, name):
    df = pd.DataFrame({"Year":range(1,YEARS+1),"Net Benefit":data})
    fig = go.Figure(data=[go.Bar(x=df.Year,y=df["Net Benefit"],name=name)])
    fig.update_layout(xaxis_title="Year",yaxis_title="Net Benefit ($)",legend=dict(orientation="h"),plot_bgcolor="#FFFFFF")
    return fig

# Main UI
st.title(f"🚀 ROI Calculator — {category}")
t1,t2,t3,t4 = st.tabs(["📊 Summary","📈 Breakdown","🔍 Compare","📥 Export"])

with t1:
    st.subheader("Key Metrics")
    c1,c2 = st.columns(2)
    c1.metric("Outsourced NPV",f"${npv_out:,.0f}",help="Net present value of outsourcing scenario.")
    c1.metric("Outsourced ROI",f"{roi_out:.1f}%")
    c1.metric("Payback Period",f"{payback_out or '> Horizon'} yrs")
    c2.metric("In-House NPV",f"${npv_in:,.0f}")
    c2.metric("In-House ROI",f"{roi_in:.1f}%")
    c2.metric("Payback Period",f"{payback_in or '> Horizon'} yrs")

with t2:
    st.subheader("Annual Net Benefit: Outsourced")
    st.plotly_chart(plot_bar(cf_out,'Outsourced'),use_container_width=True)

with t3:
    st.subheader("Scenario Comparison")
    fig=go.Figure()
    fig.add_trace(go.Bar(x=list(range(1,YEARS+1)),y=cf_in,name='In-House'))
    fig.add_trace(go.Bar(x=list(range(1,YEARS+1)),y=cf_out,name='Outsourced'))
    fig.update_layout(barmode='group',xaxis={'title':'Year'},yaxis={'title':'Net Benefit ($)'},legend=dict(orientation='h'))
    st.plotly_chart(fig,use_container_width=True)

with t4:
    st.subheader("Download Options")
    # CSV
    df_export = pd.DataFrame({"Year":range(1,YEARS+1),"Outsourced":cf_out,"In-House":cf_in})
    st.download_button("Download CSV",df_export.to_csv(index=False).encode(),'roi.csv')
    # PDF
    pdf_buffer=BytesIO()
    pdf=FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,f"ROI Report — {category}",ln=True)
    pdf.ln(5)
    for label,val in [("Outsourced NPV",f"${npv_out:,.0f}"),
                      ("In-House NPV",f"${npv_in:,.0f}")]:
        pdf.set_font("Arial","",12)
        pdf.cell(60,8,label+":",border=0)
        pdf.cell(40,8,val,ln=True)
    pdf.output(pdf_buffer)
    st.download_button("Download PDF",pdf_buffer.getvalue(),'roi_report.pdf')

st.markdown("---")
st.caption("*Values are estimates. Contact TREU Partners for tailored insights.*")
