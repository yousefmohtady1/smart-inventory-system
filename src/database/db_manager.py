import pandas as pd
import sqlite3
import logging
from src.config.settings import DB_PATH, EXCEL_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self):
        self.db_path = DB_PATH
        self.excel_path = EXCEL_PATH

    def create_db(self):
        if not self.excel_path.exists():
            logger.error(f"Excel file not found at {self.excel_path}")
            return
        
        logger.info("Reading sheets...")

        all_sheets = pd.read_excel(self.excel_path, sheet_name=None)
        df = pd.concat(all_sheets.values(), ignore_index=True)
        df.dropna(subset=['Customer ID', 'Description'],inplace=True)
        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

        logger.info("Creating database...")

        conn = sqlite3.connect(self.db_path)

        products = df.groupby('StockCode')['Description'].last().reset_index()
        products.to_sql('products', conn, if_exists='replace', index=False)
        
        transactions = df[['Invoice', 'StockCode', 'Quantity', 'Price', 'InvoiceDate', 'Customer ID']]
        transactions.to_sql('transactions', conn, if_exists='replace', index=False)

        cursor = conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_stock ON transactions (StockCode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_stock ON products (StockCode)")

        conn.close()
        logger.info("Database created successfully")

if __name__ == "__main__":
    manager = DBManager()
    manager.create_db()