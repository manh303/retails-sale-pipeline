#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
/opt/airflow/wait-for-it.sh postgres:5432 -t 60

echo "Initializing Airflow database..."
airflow db init

echo "Creating Airflow admin user..."
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

echo "Starting Airflow scheduler..."
airflow scheduler &

echo "Starting Airflow webserver..."
exec airflow webserver