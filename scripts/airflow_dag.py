from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
from sqlalchemy import create_engine
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "retail_db")
DB_PORT = os.getenv("DB_PORT", "5432")
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Path to CSV file
CSV_FILE = "/opt/airflow/dags/data/retail_sales.csv"

def load_data():
    """Load data from CSV file."""
    try:
        df = pd.read_csv(CSV_FILE)
        logger.info(f"Loaded {len(df)} records from {CSV_FILE}")
        return df
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

def transform_data():
    """Transform and validate data."""
    try:
        df = load_data()
        # Rename columns to match sales table schema
        column_mapping = {
            "Transaction ID": "transaction_id",
            "Date": "date",
            "Customer ID": "customer_id",
            "Gender": "gender",
            "Age": "age",
            "Product Category": "product_category",
            "Quantity": "quantity",
            "Price per Unit": "price_per_unit",
            "Total Amount": "total_amount"
        }
        df = df.rename(columns=column_mapping)
        
        # Validate data
        required_columns = list(column_mapping.values())
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing columns: {missing_columns}")
            raise ValueError(f"Missing columns: {missing_columns}")
        
        # Check for null values
        null_counts = df[required_columns].isnull().sum()
        if null_counts.any():
            logger.warning(f"Null values found:\n{null_counts[null_counts > 0]}")
            df = df.dropna(subset=required_columns)
        
        # Validate data types and constraints
        if not pd.api.types.is_integer_dtype(df['transaction_id']):
            logger.error("transaction_id must be integer")
            raise ValueError("transaction_id must be integer")
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            logger.warning("Converting date to datetime")
            df['date'] = pd.to_datetime(df['date'])
        if (df['quantity'] <= 0).any():
            logger.warning("Removing rows with quantity <= 0")
            df = df[df['quantity'] > 0]
        
        logger.info(f"Transformed and validated {len(df)} records")
        return df
    except Exception as e:
        logger.error(f"Error transforming data: {e}")
        raise

def save_to_db():
    """Save data to PostgreSQL."""
    try:
        df = transform_data()
        with engine.connect() as conn:
            for index, row in df.iterrows():
                query = """
                INSERT INTO sales (transaction_id, date, customer_id, gender, age, product_category, quantity, price_per_unit, total_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (transaction_id) DO NOTHING
                """
                conn.execute(query, (
                    row['transaction_id'], row['date'], row['customer_id'], row['gender'],
                    row['age'], row['product_category'], row['quantity'], row['price_per_unit'], row['total_amount']
                ))
        logger.info(f"Saved {len(df)} records to sales table")
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        raise
    
# Define DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'retail_sales_etl',
    default_args=default_args,
    description='ETL pipeline for retail sales data',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 4, 25),
    catchup=False,
) as dag:
    
    transform_task = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
    )
    
    save_task = PythonOperator(
        task_id='save_to_db',
        python_callable=save_to_db,
    )
    
    transform_task >> save_task