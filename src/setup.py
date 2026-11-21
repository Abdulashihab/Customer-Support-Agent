import json
from pathlib import Path

from src.db.connection import DB_PATH

# This file is src/setup.py, so the project folder is 1 level up.
PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_DIR / "data" / "customer_support_data.json"


def ensure_database(db_path=None, data_file=None):
    """Build the database from the JSON file if it does not exist yet."""
    from seed import build, validate   # seed.py sits in the project folder

    db_path = Path(db_path or DB_PATH)
    if db_path.exists() and db_path.stat().st_size > 0:
        return False

    data = json.loads(Path(data_file or DATA_FILE).read_text(encoding="utf-8"))
    errors, _warnings = validate(data)
    if errors:
        raise RuntimeError("The data file has errors: " + "; ".join(errors[:3]))
    build(data, db_path).close()
    return True


def ensure_search_index():
    """Build the document search if the chroma_db folder does not exist yet."""
    from src.rag.ingest import CHROMA_DIR, ingest

    if CHROMA_DIR.exists():
        return False
    ingest()
    return True


def ensure_ready():
    """Make sure the database and the document search exist. Safe to call every time."""
    built_database = ensure_database()
    built_index = ensure_search_index()
    return {"database_built": built_database, "search_index_built": built_index}