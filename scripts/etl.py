import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
from data_quality import validate_data
import logging
import os
import pika
import json
from prometheus_client import Counter, Histogram

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "retail_db")
DB_PORT = os.getenv("DB_PORT", "5432")

# Prometheus metrics
etl_runs = Counter("etl_runs_total", "Total number of ETL runs")
etl_duration = Histogram("etl_duration_seconds", "Duration of ETL runs")
data_rows_processed = Counter("data_rows_processed_total", "Total number of rows processed")

# Create SQLAlchemy engine
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Path to CSV file
csv_file = "/app/data/retail_sales.csv"

def load_data(file_path):
    """Load data from CSV file."""
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} records from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

def transform_data(df):
    """Transform data and validate."""
    try:
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
        publish_to_queue(df.to_dict('records'))
        # Validate data
        validated_df = validate_data(df)
        logger.info(f"Transformed and validated {len(validated_df)} records")
        return validated_df
    except Exception as e:
        logger.error(f"Error transforming data: {e}")
        raise

def save_to_db(df):
    """Save data to PostgreSQL."""
    try:
        # Tạo kết nối trực tiếp đến cơ sở dữ liệu
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


def publish_to_queue(data):
    credentials = pika.PlainCredentials('admin', 'admin')
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq', 5672, '/', credentials))
    channel = connection.channel()
    channel.queue_declare(queue='sales_data_queue', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='sales_data_queue',
        body=json.dumps(data),
        properties=pika.BasicProperties(delivery_mode=2)  # Persistent
    )
    connection.close()
    logging.info("Published data to sales_data_queue")

def callback(ch, method, properties, body):
    try:
        file_path = body.decode()
        logger.info(f"Received {file_path} from queue")
        etl_runs.inc()
        with etl_duration.time():
            sales_data = load_data(file_path)
            save_to_db(sales_data)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

def main():
    """Main ETL pipeline."""
    try:
        # Load data
        df = load_data(csv_file)
        
        # Transform and validate
        df = transform_data(df)
        
        # Save to database
        save_to_db(df)
        
        logger.info("ETL pipeline completed successfully")
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()