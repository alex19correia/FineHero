from sqlalchemy import create_engine
from backend.app.models import Base
import os

DATABASE_URL = "sqlite:///./sql_app.db"

def run_migrations():
    """
    Drops all existing tables and recreates them based on the current models.
    WARNING: This will delete all data in the database.
    """
    engine = create_engine(DATABASE_URL)
    
    # Check if the database file exists and delete it
    db_file = DATABASE_URL.replace("sqlite:///./", "")
    if os.path.exists(db_file):
        print(f"Deleting existing database file: {db_file}")
        os.remove(db_file)

    print("Dropping all existing tables (if any) and recreating them...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Database migration complete: Tables recreated.")

if __name__ == "__main__":
    run_migrations()
