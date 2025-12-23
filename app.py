import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import mlflow
import mlflow.sklearn
from datetime import timedelta
import joblib
from src.config.settings import DB_PATH, MLRUNS_DIR, TRAINED_MODEL_PATH
from src.agents.sql_agent import get_sql_agent, input_guardrail
from src.ml.data_preparation import load_and_prepare_data

st.set_page_config(
    page_title="Smart Inventory System",
    page_icon="🤖",
    layout="wide"
)

@st.cache_data
def load_raw_data_for_dashboard():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        t.InvoiceDate, p.Description, t.Quantity, t.Price, 
        (t.Quantity * t.Price) as TotalAmount, t.Invoice, t."Customer ID" as CustomerID
    FROM transactions t
    JOIN products p ON t.StockCode = p.StockCode
    WHERE t.Quantity > 0
    """

    df = pd.read_sql(query, conn)
    conn.close()
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

    ignore_list = [
        'POSTAGE', 'DOTCOM POSTAGE', 'CRUK Commission', 
        'Manual', 'Bank Charges', 'Discount', 'SAMPLES',
        'AMAZON FEE', 'Adjust bad debt', 'CARRIAGE'
    ]

    df_clean = df[~df['Description'].isin(ignore_list)]
    return df_clean

def load_best_model_from_mlflow():
    try:
        mlflow.set_tracking_uri(MLRUNS_DIR.as_uri())
        experiment = mlflow.get_experiment_by_name("Smart_Inventory_Sales_Forecast")
        if experiment is None:
            return None, "No MLflow experiment found. Run the training script first."

        runs = mlflow.search_runs(
            experiment_ids=experiment.experiment_id,
            order_by=["metrics.mae ASC"],
            max_results=1
        )

        if runs.empty:
            return None, "No runs found in the experiment."

        best_run_id = runs.iloc[0].run_id
        best_mae = runs.iloc[0]["metrics.mae"]
        model_uri = f"runs:/{best_run_id}/random_forest_model"
        model = mlflow.sklearn.load_model(model_uri)

        return model, f"Best Model Loaded (Run: {best_run_id[:7]} | MAE: {best_mae:,.0f})"

    except Exception as e:
        return None, str(e)

# Navigation Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard Overview", "AI Sales Forecast", "Smart Assistant"])

df = load_raw_data_for_dashboard()

# Page 1: Dashboard Overview
if page == "Dashboard Overview":
    st.title("Dashboard Overview")

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    total_revenue = df['TotalAmount'].sum()
    total_orders = df['Invoice'].nunique()
    total_items = df['Quantity'].sum()
    avg_order_value = total_revenue / total_orders
    
    col1.metric("Total Revenue", f"${total_revenue:,.0f}")
    col2.metric("Total Orders", total_orders)
    col3.metric("Items Sold", total_items)
    col4.metric("Average Order Value", f"${avg_order_value:,.0f}")

    st.divider()

    # Charts
    st.subheader("Monthly Sales Trend")
    monthly_Sales = df.set_index('InvoiceDate').resample('ME')['TotalAmount'].sum().reset_index()
    fig_line = px.line(monthly_Sales, x='InvoiceDate', y='TotalAmount', markers=True, template="plotly_white")
    fig_line.update_traces(line_color = "blue", line_width = 2)
    st.plotly_chart(fig_line, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Customer Spending Distribution")
        customer_sales = df.groupby('CustomerID')['TotalAmount'].sum()
        # Filter < 5000 to focus on main distribution as requested
        filtered_sales = customer_sales[customer_sales < 5000]
        fig_hist = px.histogram(filtered_sales, nbins=50, template="plotly_white")
        fig_hist.update_layout(showlegend=False, xaxis_title="Total Spent", yaxis_title="Count")
        st.plotly_chart(fig_hist, use_container_width=True)

    with c2:
        st.subheader("Top 10 Best Selling Products")
        top_prod = df.groupby('Description')['TotalAmount'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_bar = px.bar(top_prod, x='TotalAmount', y='Description', orientation='h', template="plotly_white")
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

# Page 2: AI Sales Forecasting
elif page == "AI Sales Forecast":
    st.title("AI Demand Forecasting")
    st.markdown("Predicting next month's sales using **Machine Learning (Random Forest)** powered by MLflow.")
    
    col_left, col_right = st.columns([2, 1])
    model_data = load_and_prepare_data()

    with col_left:
        st.subheader("Historical Sales Data (Model Input)")
        fig = px.area(model_data, x='ds', y='y', title="Sales History")
        st.plotly_chart(fig, use_container_width=True)
        
    with col_right:
        st.subheader("Next Month Prediction")

        if TRAINED_MODEL_PATH.exists():
            try:
                model = joblib.load(TRAINED_MODEL_PATH)
                st.success("Model loaded successfully.")
                
                last_date = model_data['ds'].max()
                next_month_date = last_date + pd.DateOffset(months=1)
                last_month_sales = model_data.iloc[-1]['y']
                
                next_features = pd.DataFrame({
                    'month': [next_month_date.month],
                    'year': [next_month_date.year],
                    'prev_month_sales': [last_month_sales]
                })
                
                prediction = model.predict(next_features)[0]
                growth = ((prediction - last_month_sales) / last_month_sales) * 100
                
                st.metric(
                    label=f"Forecast for {next_month_date.strftime('%B %Y')}",
                    value=f"£{prediction:,.2f}",
                    delta=f"{growth:+.2f}% vs Last Month"
                )
            except Exception as e:
                st.error(f"Error loading model: {e}")
        else:
            st.warning("Model file not found. Please run training script locally and push the 'models' folder.")

# Page 3: Smart Assistant (Chatbot)
elif page == "Smart Assistant":
    st.title("AI Data Analyst")
    st.markdown("Ask complex questions about your inventory, sales, or customers.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! I can analyze your database. Ask me anything like: 'What are the top 5 products?'"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask your data..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        if not input_guardrail(prompt):
            error_msg = "**Security Alert:** This query contains restricted keywords (e.g., DROP, DELETE) and cannot be executed."
            st.chat_message("assistant").markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing Database..."):
                    try:
                        agent = get_sql_agent()
                        if agent:
                            response = agent.invoke(prompt)
                            output = response['output']
                            st.markdown(output)
                            st.session_state.messages.append({"role": "assistant", "content": output})
                        else:
                            st.error("Agent Initialization Failed. Check API Key.")
                    except Exception as e:
                        st.error(f"Error: {e}")