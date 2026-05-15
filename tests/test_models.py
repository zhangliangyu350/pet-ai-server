from sqlalchemy import create_engine, inspect

from app.models import Base


def test_metadata_contains_core_tables():
    table_names = set(Base.metadata.tables.keys())

    assert {
        "users",
        "image_assets",
        "analyses",
        "health_records",
    }.issubset(table_names)


def test_models_can_create_sqlite_schema():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    table_names = set(inspect(engine).get_table_names())
    assert "users" in table_names
    assert "image_assets" in table_names
    assert "analyses" in table_names
    assert "health_records" in table_names

