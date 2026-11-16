import sqlite3
from pathlib import Path

# The database file sits in the main project folder.
# This file is src/db/connection.py, so the project folder is 2 levels up.
DB_PATH = Path(__file__).resolve().parents[2] / "customer_support.db"


def get_connection(db_path=None):
    """Open the database. Rows come back like dictionaries, e.g. row["balance"]."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn