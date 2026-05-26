"""Schema contract tests for generated rule provenance fields."""

from sqlalchemy import create_engine, inspect

import de_forge.models  # noqa: F401
from de_forge.db.base import Base


def test_generated_rules_has_provenance_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("generated_rules")}

    assert "generation_source" in columns
    assert "detection_ast_id" in columns
    assert "compiled_sigma_id" in columns
