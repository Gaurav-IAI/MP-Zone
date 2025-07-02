import pymysql
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT")),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'xlsx'

def safe_parse_datetime(val):
    if pd.isna(val) or isinstance(val, str) and val.strip() in ['', '*']:
        return None
    try:
        return pd.to_datetime(val)
    except Exception:
        return None

def safe_parse_int(val):
    if pd.isna(val):
        return None
    try:
        return int(val)
    except Exception:
        return None
