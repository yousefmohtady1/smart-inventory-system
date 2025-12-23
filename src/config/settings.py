import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

# Load environment variables from .env file
load_dotenv()

# Project Root (calculated relative to this file: src/config/settings.py -> config -> src -> root)
BASE_DIR = Path(__file__).resolve().parents[2]

# Data Directories and Files
DATA_DIR = BASE_DIR / "data"
EXCEL_FILE_NAME = "online_retail_II.xlsx"
EXCEL_PATH = DATA_DIR / EXCEL_FILE_NAME

# Database
DB_NAME = "inventory.db"
DB_PATH = BASE_DIR / DB_NAME

# MLflow & Models
MLRUNS_DIR = BASE_DIR / "mlruns"
MODELS_DIR = BASE_DIR / "models"
MODEL_FILE_NAME = "sales_model.pkl"
TRAINED_MODEL_PATH = MODELS_DIR / MODEL_FILE_NAME

# API Keys
try:
    # Try loading from Streamlit secrets first (for cloud deployment)
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
except Exception:
    # Fallback to .env for local scripts (training, etc.)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")