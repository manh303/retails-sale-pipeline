Retail Sales ETL Pipeline

This project builds an ETL pipeline to process retail sales data from CSV files, store it in PostgreSQL, and visualize insights via a Streamlit dashboard. The entire application is containerized using Docker.

Features





Extracts and cleans sales data using Pandas.



Loads data into PostgreSQL.



Visualizes revenue trends with Streamlit.



Containerized with Docker for consistent deployment.

Prerequisites





Docker



Dataset: Place retail_sales.csv in the data/ folder.

Setup





Clone the repository:

git clone <your-repo-url>
cd retail-sales-pipeline



Run the ETL pipeline:

docker-compose up --build



Run the Streamlit dashboard:

docker-compose up --build

Open http://localhost:8501 in your browser.

Technologies





Python (Pandas, SQLAlchemy)



PostgreSQL



Streamlit



Docker# retails-sale-pipeline
