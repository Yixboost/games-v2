import re
from typing import Any

from sqlalchemy import text

from core.database import engine


IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(identifier: str) -> str:
    if not IDENTIFIER.match(identifier):
        raise RuntimeError(
            f"Invalid database identifier: {identifier}"
        )

    return identifier


class PluginDatabase:

    def require_columns(
        self,
        table_name: str,
        columns: dict[str, str],
    ) -> None:
        if engine.dialect.name != "sqlite":
            return

        table_name = _validate_identifier(table_name)

        with engine.begin() as connection:
            existing_columns = {
                row[1]
                for row in connection.execute(
                    text(f"PRAGMA table_info({table_name})")
                )
            }

            for column_name, column_type in columns.items():
                column_name = _validate_identifier(column_name)

                if column_name not in existing_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} {column_type}"
                        )
                    )


    def require_table(
        self,
        table_name: str,
        columns: dict[str, str],
    ) -> None:
        if engine.dialect.name != "sqlite":
            return

        table_name = _validate_identifier(table_name)

        column_sql = []

        for column_name, column_type in columns.items():
            column_sql.append(
                f"{_validate_identifier(column_name)} {column_type}"
            )

        with engine.begin() as connection:
            connection.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table_name}
                    ({", ".join(column_sql)})
                    """
                )
            )

        self.require_columns(
            table_name,
            columns,
        )


    def apply_manifest_requirements(
        self,
        requirements: dict[str, Any],
    ) -> None:

        for table_name, columns in requirements.get(
            "tables",
            {},
        ).items():
            self.require_table(
                table_name,
                columns,
            )

        for table_name, columns in requirements.get(
            "columns",
            {},
        ).items():
            self.require_columns(
                table_name,
                columns,
            )


plugin_database = PluginDatabase()