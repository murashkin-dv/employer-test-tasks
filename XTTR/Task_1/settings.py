import os

if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    DATABASE_URL = f"sqlite:///./database/test/test_telegram_summary.db"
