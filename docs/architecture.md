Pipeline Architecture

Overview

The Retail Sales ETL Pipeline is designed for scalability and reliability, using modern data engineering tools.

Components





Data Ingestion: Reads retail_sales.csv and publishes file paths to RabbitMQ.



Message Queue (RabbitMQ): Handles asynchronous processing of CSV files.



Data Processing: Validates data quality and transforms data using Pandas.



Storage: Loads data into PostgreSQL with SQLAlchemy.



Orchestration (Airflow): Schedules and manages ETL tasks.



Monitoring (Prometheus/Grafana): Tracks pipeline metrics (e.g., ETL runtime, rows processed).



Visualization (Streamlit): Displays processed data with interactive charts.

Architecture Diagram

[CSV Files] --> [RabbitMQ] --> [ETL (Pandas, SQLAlchemy)] --> [PostgreSQL]
   |              |                    |                        |
   v              v                    v                        v
[Airflow]   [Prometheus/Grafana]   [Streamlit Dashboard]

Data Flow





Airflow triggers ETL tasks daily.



CSV file paths are published to RabbitMQ.



ETL consumer processes files, validates data, and loads to PostgreSQL.



Prometheus collects metrics; Grafana visualizes them.



Streamlit dashboard queries PostgreSQL for visualizations.