import sqlite3
import pandas as pd
import logging
from src.config.settings import DB_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_and_prepare_data():
    logger.info("Loading and cleaning data...")

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT 
        t.InvoiceDate,
        t.Quantity,
        t.Price,
        p.Description,
        (t.Quantity * t.Price) as TotalAmount
        FROM transactions t
        JOIN products p ON t.StockCode = p.StockCode
    """

    df = pd.read_sql(query, conn)
    conn.close()

    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

    df = df[df['Quantity'] > 0]
    
    non_product = [
        'POSTAGE', 'DOTCOM POSTAGE', 'CRUK Commission', 
        'Manual', 'Bank Charges', 'Discount', 'SAMPLES',
        'AMAZON FEE', 'Adjust bad debt', 'CARRIAGE' 
    ]

    df = df[~df['Description'].isin(non_product)]

    df = df[df['InvoiceDate'] < '2011-12-01']

    df_monthly = df.set_index('InvoiceDate').resample('ME')['TotalAmount'].sum().reset_index()

    df_monthly.columns = ['ds', 'y']

    logger.info("Applying Feature Engineering...")

    df_monthly['month'] = df_monthly['ds'].dt.month
    df_monthly['year'] = df_monthly['ds'].dt.year
    df_monthly['prev_month_sales'] = df_monthly['y'].shift(1)

    df_monthly = df_monthly.dropna()

    logger.info(f"✅ Data Ready for Training. Shape: {df_monthly.shape}")

    return df_monthly

if __name__ == "__main__":
    data = load_and_prepare_data()
    print(data.head())
