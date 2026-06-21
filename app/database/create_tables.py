"""Create all currently defined database tables."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.database.connection import engine
from app.database.models import Base


def _ensure_advisor_message_columns() -> None:
    inspector = inspect(engine)
    if "advisor_messages" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("advisor_messages")}
    alter_statements = []

    if "task_type" not in existing_columns:
        alter_statements.append("ALTER TABLE advisor_messages ADD COLUMN task_type VARCHAR")
    if "task_label" not in existing_columns:
        alter_statements.append("ALTER TABLE advisor_messages ADD COLUMN task_label VARCHAR")
    if "tool_trace" not in existing_columns:
        alter_statements.append("ALTER TABLE advisor_messages ADD COLUMN tool_trace TEXT")

    if not alter_statements:
        return

    with engine.begin() as connection:
        for statement in alter_statements:
            connection.execute(text(statement))


def main() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_advisor_message_columns()
    print("Created database tables successfully.")


if __name__ == "__main__":
    main()
