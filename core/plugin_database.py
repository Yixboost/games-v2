import re
from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection


IDENTIFIER = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)


def _validate_identifier(
    identifier: str,
) -> str:

    if not IDENTIFIER.fullmatch(identifier):
        raise RuntimeError(
            f"Invalid database identifier: {identifier}"
        )

    return identifier



class PluginDatabase:

    def __init__(
        self,
        engine: Engine,
    ):
        self.engine = engine



    @contextmanager
    def connection(self) -> Iterator[Connection]:

        with self.engine.begin() as connection:
            yield connection



    def execute(
        self,
        query: str,
        params: dict | None = None,
        connection: Connection | None = None,
    ):

        if connection:

            return connection.execute(
                text(query),
                params or {},
            )


        with self.connection() as connection:

            return connection.execute(
                text(query),
                params or {},
            )



    def fetch_all(
        self,
        query: str,
        params: dict | None = None,
        connection: Connection | None = None,
    ):

        return self.execute(
            query,
            params,
            connection,
        ).mappings().all()



    def fetch_one(
        self,
        query: str,
        params: dict | None = None,
        connection: Connection | None = None,
    ):

        return self.execute(
            query,
            params,
            connection,
        ).mappings().first()



    def require_table(
        self,
        table_name: str,
        columns: dict[str, str],
    ) -> None:

        if self.engine.dialect.name != "sqlite":
            return


        table_name = _validate_identifier(
            table_name
        )


        definitions = ", ".join(
            f"{_validate_identifier(name)} {value}"
            for name, value in columns.items()
        )


        with self.connection() as connection:

            connection.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table_name}
                    (
                        {definitions}
                    )
                    """
                )
            )


            existing = {
                row[1]
                for row in connection.execute(
                    text(
                        f"PRAGMA table_info({table_name})"
                    )
                )
            }


            for name, column_type in columns.items():

                name = _validate_identifier(
                    name
                )

                if name not in existing:

                    connection.execute(
                        text(
                            f"""
                            ALTER TABLE {table_name}
                            ADD COLUMN {name} {column_type}
                            """
                        )
                    )



    def require_columns(
        self,
        table_name: str,
        columns: dict[str, str],
    ) -> None:

        if self.engine.dialect.name != "sqlite":
            return


        table_name = _validate_identifier(
            table_name
        )


        with self.connection() as connection:

            existing = {
                row[1]
                for row in connection.execute(
                    text(
                        f"PRAGMA table_info({table_name})"
                    )
                )
            }


            for name, column_type in columns.items():

                name = _validate_identifier(
                    name
                )

                if name not in existing:

                    connection.execute(
                        text(
                            f"""
                            ALTER TABLE {table_name}
                            ADD COLUMN {name} {column_type}
                            """
                        )
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