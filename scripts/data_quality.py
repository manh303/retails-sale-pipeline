import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_data(df):
    """Validate DataFrame for required columns and data quality."""
    try:
        # Define required columns
        required_columns = [
            'transaction_id', 'date', 'customer_id', 'gender', 'age',
            'product_category', 'quantity', 'price_per_unit', 'total_amount'
        ]
        
        # Check for missing columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing columns: {missing_columns}")
            raise ValueError(f"Missing columns: {missing_columns}")
        
        # Check for null values
        null_counts = df[required_columns].isnull().sum()
        if null_counts.any():
            logger.warning(f"Null values found:\n{null_counts[null_counts > 0]}")
            df = df.dropna(subset=required_columns)
        
        if not pd.api.types.is_float_dtype(df['price_per_unit']):
            logger.warning("Converting price_per_unit to float")
            try:
                df['price_per_unit'] = pd.to_numeric(df['price_per_unit'], errors='coerce')
                invalid_rows = df[df['price_per_unit'].isnull()]
                if not invalid_rows.empty:
                    logger.warning(f"Removing rows with invalid price_per_unit values:\n{invalid_rows}")
                    df = df.dropna(subset=['price_per_unit'])
            except Exception as e:
                logger.error(f"Failed to convert price_per_unit to float: {e}")
                raise ValueError("price_per_unit must be float")
        
        # Validate logical constraints
        if (df['quantity'] <= 0).any():
            logger.warning("Removing rows with quantity <= 0")
            df = df[df['quantity'] > 0]
        if (df['price_per_unit'] <= 0).any():
            logger.warning("Removing rows with price_per_unit <= 0")
            df = df[df['price_per_unit'] > 0]
        if (df['total_amount'] <= 0).any():
            logger.warning("Removing rows with total_amount <= 0")
            df = df[df['total_amount'] > 0]
        
        logger.info(f"Validated {len(df)} records")
        return df
    
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise