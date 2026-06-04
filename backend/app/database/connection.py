from sqlalchemy import create_engine
from pathlib import Path

# Database file path
DB_PATH = Path(__file__).parent / "company.db"

# SQLite connection URL
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)