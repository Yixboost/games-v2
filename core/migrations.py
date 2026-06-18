from sqlalchemy import text

from core.database import engine


USER_COLUMNS = {
    "username": "VARCHAR",
    "email": "VARCHAR",
    "oauth_provider": "VARCHAR",
    "oauth_subject": "VARCHAR",
    "role": "VARCHAR NOT NULL DEFAULT 'user'",
    "created_at": "DATETIME",
    "updated_at": "DATETIME",
}


def run_core_migrations() -> None:
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        existing_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(users)"))
        }

        for column_name, column_type in USER_COLUMNS.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                )
