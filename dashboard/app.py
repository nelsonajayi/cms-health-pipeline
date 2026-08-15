"""
CMS Healthcare Analytics Dashboard
Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import snowflake.connector
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="CMS Healthcare Analytics",
    page_icon="🏥",
    layout="wide"
)


@st.cache_data(ttl=3600)
def load_readmissions_data():
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        role=os.getenv('SNOWFLAKE_ROLE')
    )
    df = pd.read_sql(
        "SELECT * FROM CMS_HEALTH.MARTS.MART_HOSPITAL_READMISSIONS",
        conn
    )
    conn.close()
    return df


@st.cache_data(ttl=3600)
def load_drug_data():
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        role=os.getenv('SNOWFLAKE_ROLE')
    )
    df = pd.read_sql(
        "SELECT * FROM CMS_HEALTH.MARTS.MART_DRUG_ANALYSIS LIMIT 500",
        conn
    )
    conn.close()
    return df


st.title("🏥 CMS Medicare Population Health Analytics")

tab1, tab2 = st.tabs(["Hospital Readmissions", "Drug Prescribing"])

with tab1:
    with st.spinner("Loading from Snowflake..."):
        try:
            df = load_readmissions_data()
        except Exception as e:
            st.error(f"Connection failed: {e}")
            st.stop()

    conditions = sorted(df['MEASURE_NAME'].unique())
    selected = st.selectbox("Select Condition", conditions)
    filtered = df[df['MEASURE_NAME'] == selected]

    col1, col2, col3 = st.columns(3)
    col1.metric("States", filtered['STATE'].nunique())
    col2.metric("Avg Excess Ratio",
                f"{filtered['AVG_EXCESS_READMISSION_RATIO'].mean():.3f}")
    col3.metric("Total Readmissions",
                f"{filtered['TOTAL_READMISSIONS'].sum():,.0f}")

    fig = px.choropleth(
        filtered,
        locations='STATE',
        locationmode='USA-states',
        color='AVG_EXCESS_READMISSION_RATIO',
        scope='usa',
        color_continuous_scale='RdBu_r',
        color_continuous_midpoint=1.0,
        title=f"Excess Readmission Ratio — {selected}"
    )
    st.plotly_chart(fig, use_container_width=True)

    top20 = filtered.nlargest(20, 'AVG_EXCESS_READMISSION_RATIO')
    fig2 = px.bar(
        top20,
        x='STATE',
        y='AVG_EXCESS_READMISSION_RATIO',
        color='STATE_RISK_CATEGORY',
        color_discrete_map={
            'HIGH RISK': 'red',
            'ABOVE EXPECTED': 'orange',
            'BELOW EXPECTED': 'steelblue',
            'LOW RISK': 'green'
        }
    )
    fig2.add_hline(y=1.0, line_dash="dash", annotation_text="Expected = 1.0")
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    with st.spinner("Loading drug data..."):
        try:
            drug_df = load_drug_data()
        except Exception as e:
            st.error(f"Connection failed: {e}")
            st.stop()

    col1, col2 = st.columns(2)
    col1.metric("Unique Drugs", f"{drug_df['BRAND_DRUG_NAME'].nunique():,}")
    col2.metric("Total Cost",
                f"${drug_df['NATIONAL_TOTAL_COST'].sum()/1e9:.1f}B")

    top_drugs = drug_df.nlargest(20, 'NATIONAL_TOTAL_COST')
    fig3 = px.bar(
        top_drugs,
        x='NATIONAL_TOTAL_COST',
        y='BRAND_DRUG_NAME',
        orientation='h',
        title="Top 20 Highest Cost Drugs"
    )
    st.plotly_chart(fig3, use_container_width=True)