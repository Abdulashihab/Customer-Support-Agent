import shutil

import pytest

from src.db.connection import DB_PATH


@pytest.fixture
def db_copy(tmp_path):
    """Give every test its own throwaway copy of the database."""
    copy = tmp_path / "test.db"
    shutil.copy(DB_PATH, copy)
    return copy