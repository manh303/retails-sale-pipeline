import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import logging
from sqlalchemy.exc import ProgrammingError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database connection
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "retail_db")
DB_PORT = os.getenv("DB_PORT", "5432")

# Create database engine
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Streamlit app
st.title("Retail Sales Dashboard")

# Check if sales table exists
def table_exists():
    try:
        pd.read_sql("SELECT 1 FROM sales LIMIT 1", engine)
        return True
    except ProgrammingError:
        return False

if not table_exists():
    st.error("The 'sales' table does not exist. Please ensure the ETL process has run successfully.")
else:
    # Sidebar for filters
    st.sidebar.header("Filters")
    try:
        query = "SELECT MIN(date), MAX(date) FROM sales"
        min_date, max_date = pd.read_sql(query, engine).iloc[0]
        start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
        end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
    except Exception as e:
        st.error(f"Error fetching date range: {e}")
        st.stop()

    query = "SELECT DISTINCT product_category FROM sales"
    categories = pd.read_sql(query, engine)["product_category"].tolist()
    selected_categories = st.sidebar.multiselect("Product Category", categories, default=categories)

    query = "SELECT DISTINCT gender FROM sales"
    genders = pd.read_sql(query, engine)["gender"].tolist()
    selected_genders = st.sidebar.multiselect("Gender", genders, default=genders)

    # Load filtered data
    query = """
    SELECT transaction_id, date, product_category, total_amount, customer_id, gender, age, quantity, price_per_unit
    FROM sales
    WHERE date BETWEEN %s AND %s
    AND product_category = ANY(%s)
    AND gender = ANY(%s)
    """
    df = pd.read_sql(query, engine, params=(start_date, end_date, selected_categories, selected_genders))

    if df.empty:
        st.error("No data available for the selected filters. Please adjust the filters.")
    else:
        st.write(f"Displaying {len(df)} transactions")

        # Key Metrics
        st.header("Key Metrics")
        col1, col2, col3 = st.columns(3)
        total_amount = df["total_amount"].sum()
        total_transactions = df["transaction_id"].nunique()
        avg_total_amount = df["total_amount"].mean() if total_transactions > 0 else 0
        col1.metric("Total total_amount", f"${total_amount:,.2f}")
        col2.metric("Total Transactions", total_transactions)
        col3.metric("Average total_amount per Transaction", f"${total_amount:,.2f}")

        # Revenue by Category
        st.subheader("Revenue by Category")
        category_revenue = df.groupby("product_category")["total_amount"].sum().reset_index()
        fig = px.bar(category_revenue, x="product_category", y="total_amount", title="total_amount by Category", template="plotly_dark")
        st.plotly_chart(fig)

        # Monthly Revenue Trend
        st.subheader("Monthly Revenue Trend")
        df = pd.read_sql(query, engine, params=(start_date, end_date, selected_categories, selected_genders))
        df["date"] = pd.to_datetime(df["date"])  # Chuyển đổi cột 'date' sang kiểu datetime
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if df["date"].isnull().any():
            st.error("Some rows have invalid date values. Please check your data.")
            st.stop()
        df["month"] = df["date"].dt.to_period("M").astype(str)
        monthly_total_amount = df.groupby("month")["total_amount"].sum().reset_index()
        fig = px.line(monthly_total_amount, x="month", y="total_amount", title="Monthly Revenue Trend", template="plotly_dark")
        st.plotly_chart(fig)

        # Revenue by Gender
        st.subheader("Revenue by Gender")
        gender_total_amount = df.groupby("gender")["total_amount"].sum().reset_index()
        fig = px.pie(gender_total_amount, names="gender", values="total_amount", title="Revenue by Gender", template="plotly_dark")
        st.plotly_chart(fig)

        # Export Data
        st.subheader("Export Data")
        if st.button("Export Filtered Data as CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="filtered_sales_data.csv",
                mime="text/csv"
            )

        # Export Report as PDF
        def generate_pdf_report(df):
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.drawString(100, 750, "Retail Sales Report")
            y = 700
            for i, row in df.head(10).iterrows():
                c.drawString(100, y, f"Transaction {row['transaction_id']}: {row['product_category']} - ${row['total_amount']}")
                y -= 20
            c.showPage()
            c.save()
            buffer.seek(0)
            return buffer

        if st.button("Export Report as PDF"):
            pdf_buffer = generate_pdf_report(df)
            st.download_button(
                label="Download PDF",
                data=pdf_buffer,
                file_name="sales_report.pdf",
                mime="application/pdf"
            )