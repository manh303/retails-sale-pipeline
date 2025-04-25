import unittest
import pandas as pd
from scripts.etl import load_data
from scripts.data_quality import validate_data

class TestETL(unittest.TestCase):
    def test_load_data(self):
        csv_file = "/app/data/retail_sales.csv"
        df = load_data(csv_file)
        expected_columns = [
            "order_id", "date", "category", "revenue", "customer_id",
            "gender", "age", "quantity", "price_per_unit"
        ]
        for col in expected_columns:
            self.assertIn(col, df.columns)
    
    def test_data_quality(self):
        data = pd.DataFrame({
            "order_id": ["1", "2"],
            "date": [pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-02")],
            "category": ["Electronics", "Clothing"],
            "revenue": [100.0, 50.0],
            "customer_id": ["C1", "C2"],
            "gender": ["Male", "Female"],
            "age": [30, 25],
            "quantity": [2, 1],
            "price_per_unit": [50.0, 50.0]
        })
        self.assertTrue(validate_data(data))

if __name__ == "__main__":
    unittest.main()