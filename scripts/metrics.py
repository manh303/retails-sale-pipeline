from prometheus_client import start_http_server, Counter, Gauge
from time import sleep

# Define Prometheus metrics
etl_records_processed = Counter('etl_records_processed_total', 'Total records processed by ETL pipeline')
etl_errors = Counter('etl_errors_total', 'Total errors in ETL pipeline')
etl_processing_time = Gauge('etl_processing_time_seconds', 'Time taken for ETL processing')

def start_metrics_server():
    """Start a Prometheus metrics server on port 8000."""
    start_http_server(8000)
    print("Prometheus metrics server started on port 8000")

if __name__ == "__main__":
    start_metrics_server()
    while True:
        sleep(60)  # Keep the server running