import os
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-restaurant-secret-key-2026")
    DB_TYPE = os.getenv("DB_TYPE", "sqlite") # 'mysql' or 'sqlite'
    
    # MySQL config
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "restaurant_db")
    
    # SQLite config (for local dev / testing)
    SQLITE_PATH = os.getenv("SQLITE_PATH", os.path.join(os.path.dirname(__file__), "restaurant_dev.db"))
    
    # Business Rules Defaults (See docs/DECISIONS.md)
    MEAL_DURATION_MINUTES = int(os.getenv("MEAL_DURATION_MINUTES", 90))
    CLEANING_BUFFER_MINUTES = int(os.getenv("CLEANING_BUFFER_MINUTES", 15))
    MAX_RESERVATION_DAYS = int(os.getenv("MAX_RESERVATION_DAYS", 30))
    MIN_ADVANCE_MINUTES = int(os.getenv("MIN_ADVANCE_MINUTES", 30))
    MAX_PARTY_SIZE = int(os.getenv("MAX_PARTY_SIZE", 10))
    
    # Business Hours (24-hour format)
    OPENING_TIME = os.getenv("OPENING_TIME", "11:00")
    CLOSING_TIME = os.getenv("CLOSING_TIME", "21:30")

class TestingConfig(Config):
    TESTING = True
    DB_TYPE = "sqlite"
    SQLITE_PATH = "file:restaurant_test?mode=memory&cache=shared"
