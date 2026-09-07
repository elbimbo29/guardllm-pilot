import json
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text


# Page Configuration
st.set_page_config(
    page_title="GuardLLM Observability Portal",
    page_icon="🛡️",
    layout="wide",
)

# Database Connection Helper
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgrespassword@guardllm-timescaledb:5432/guardllm",
)


@st.cache_resource
def get_db_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True)


engine = get_db_engine()

# Header
st.title("🛡️ GuardLLM Proxy Observability & Audit Portal")
st.markdown(
    "Real-time evaluation logs, action analytics, and rule execution details from TimescaleDB."
)


# Sidebar Filters
st.sidebar.header("🔍 Audit Filters")

action_filter = st.sidebar.multiselect(
    "Filter by Action:",
    options=["PASS", "MASK", "BLOCK"],
    default=["PASS", "MASK", "BLOCK"],
)

limit = st.sidebar.slider("Max Logs to Fetch:", 10, 500, 100)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# Data Fetching
try:
    query = text("""
        SELECT 
            time, 
            request_id, 
            passed, 
            overall_action, 
            execution_time_ms, 
            rule_results 
        FROM guardrail_evaluations
        WHERE overall_action = ANY(:actions)
        ORDER BY time DESC
        LIMIT :limit;
    """)

    with engine.connect() as conn:
        df = pd.read_sql_query(
            query,
            conn,
            params={"actions": action_filter, "limit": limit},
        )

except Exception as e:
    st.error(f"Failed to connect to TimescaleDB or query evaluations: {e}")
    st.stop()

if df.empty:
    st.warning("No guardrail evaluations found matching the selected filters.")
    st.stop()

# Key Performance Indicators (KPIs)
total_requests = len(df)
block_count = len(df[df["overall_action"] == "BLOCK"])
mask_count = len(df[df["overall_action"] == "MASK"])
avg_latency = df["execution_time_ms"].mean() if not df.empty else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Evaluated Logs", total_requests)
col2.metric("Blocked Requests", block_count, delta_color="inverse")
col3.metric("Masked Requests", mask_count)
col4.metric("Avg Latency", f"{avg_latency:.2f} ms")

st.markdown("---")

# Visual Analytics Section
tab1, tab2 = st.tabs(["📊 Analytics Overview", "🔍 Audit Log Inspector"])

with tab1:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Action Distribution")
        action_counts = df["overall_action"].value_counts().reset_index()
        action_counts.columns = ["Action", "Count"]
        fig_pie = px.pie(
            action_counts,
            values="Count",
            names="Action",
            color="Action",
            color_discrete_map={
                "PASS": "#2ECC71",
                "MASK": "#F1C40F",
                "BLOCK": "#E74C3C",
            },
            hole=0.4,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_col2:
        st.subheader("Execution Latency Distribution (ms)")
        fig_hist = px.histogram(
            df,
            x="execution_time_ms",
            nbins=20,
            color="overall_action",
            color_discrete_map={
                "PASS": "#2ECC71",
                "MASK": "#F1C40F",
                "BLOCK": "#E74C3C",
            },
            labels={"execution_time_ms": "Latency (ms)"},
        )
        st.plotly_chart(fig_hist, use_container_width=True)

with tab2:
    st.subheader("Evaluation Audit Logs")

    # Display DataFrame without raw rule_results
    display_df = df[
        ["time", "request_id", "passed", "overall_action", "execution_time_ms"]
    ].copy()
    st.dataframe(display_df, use_container_width=True)

    st.markdown("---")
    st.subheader("Inspect JSONB Rule Execution Details")

    selected_req_id = st.selectbox(
        "Select Request ID to expand rule details:",
        options=df["request_id"].tolist(),
    )

    if selected_req_id:
        selected_row = df[df["request_id"] == selected_req_id].iloc[0]

        st.write(f"**Request ID:** `{selected_row['request_id']}`")
        st.write(f"**Timestamp:** `{selected_row['time']}`")
        st.write(f"**Action:** `{selected_row['overall_action']}`")
        st.write(f"**Latency:** `{selected_row['execution_time_ms']} ms`")

        raw_rules = selected_row["rule_results"]

        # Parse rule details
        if isinstance(raw_rules, str):
            rule_list = json.loads(raw_rules)
        else:
            rule_list = raw_rules

        if rule_list:
            st.markdown("#### Executed Rules Detail")
            st.json(rule_list)
        else:
            st.info("No rules were triggered or recorded for this request.")
