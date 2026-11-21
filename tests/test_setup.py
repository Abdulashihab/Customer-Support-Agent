from src.setup import ensure_database


def test_database_is_built_when_it_is_missing(tmp_path):
    path = tmp_path / "new.db"
    assert ensure_database(db_path=path) is True
    assert path.exists() and path.stat().st_size > 0


def test_an_existing_database_is_left_alone(tmp_path):
    path = tmp_path / "old.db"
    path.write_text("not really a database")
    assert ensure_database(db_path=path) is False
    assert path.read_text() == "not really a database"