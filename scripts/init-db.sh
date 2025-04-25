#!/bin/bash
set -e

# Create retail_db and airflow databases
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE retail_db;
    CREATE DATABASE airflow;
EOSQL

# Create sales table in retail_db
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname retail_db <<-EOSQL
    CREATE TABLE sales (
        transaction_id INTEGER PRIMARY KEY,
        date DATE,
        customer_id VARCHAR(50),
        gender VARCHAR(10),
        age INTEGER,
        product_category VARCHAR(50),
        quantity INTEGER,
        price_per_unit FLOAT,
        total_amount FLOAT
    );
EOSQL

echo "Databases and sales table created successfully"