#!/bin/bash
set -e

echo "Starting app service..."

# Check retail_sales.csv
echo "Checking retail_sales.csv..."
if [ ! -f /app/data/retail_sales.csv ]; then
    echo "Error: /app/data/retail_sales.csv not found"
    exit 1
fi
echo "retail_sales.csv found"

# Check dependencies
echo "Checking PostgreSQL..."
if ! /app/scripts/wait-for-it.sh postgres:5432 -t 120; then
    echo "PostgreSQL check failed"
    PGPASSWORD=password psql -h postgres -U postgres -c "\l" || echo "Failed to list databases"
    exit 1
fi
# Verify retail_db
echo "Verifying retail_db..."
PGPASSWORD=password psql -h postgres -U postgres -d retail_db -c "\d" || { echo "retail_db verification failed"; exit 1; }

echo "Checking RabbitMQ..."
if ! /app/scripts/wait-for-it.sh rabbitmq:5672 -t 120; then
    echo "RabbitMQ check failed"
    nc -z rabbitmq 5672 || echo "Failed to check RabbitMQ status"
    exit 1
fi

# Start metrics server
echo "Starting metrics server..."
python /app/scripts/metrics.py &> /app/logs/metrics.log &
METRICS_PID=$!
echo "Metrics server PID: $METRICS_PID"

# Run ETL pipeline
echo "Running ETL pipeline..."
python /app/scripts/etl.py &> /app/logs/etl.log || { echo "ETL pipeline failed"; cat /app/logs/etl.log; exit 1; }

# Start Streamlit dashboard
echo "Starting Streamlit dashboard..."
streamlit run /app/scripts/dashboard.py --server.port 8501 &> /app/logs/dashboard.log || { echo "Streamlit dashboard failed"; cat /app/logs/dashboard.log; exit 1; }

echo "App service started successfully"
tail -f /app/logs/metrics.log /app/logs/etl.log /app/logs/dashboard.log