import os
import sqlite3
from dotenv import load_dotenv
import psycopg
from psycopg import sql

load_dotenv()

SOURCE_DB = "students.db"

# Tables are copied in foreign-key dependency order.
TABLES = {
    "students": [
        "id", "name", "email", "password",
        "department", "level", "bio"
    ],
    "quiz_results": [
        "id", "student_id", "score", "percentage", "date_taken"
    ],
    "materials": [
        "id", "title", "description", "link"
    ],
    "lesson_progress": [
        "id", "student_id", "topic", "lesson_index", "completed_at"
    ],
    "reviews": [
        "id", "student_id", "rating", "review_text", "date_submitted"
    ],
}

OPTIONAL_DEFAULTS = {
    "department": "",
    "level": "",
    "bio": "",
}

def main():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing from your .env file."
        )

    if not os.path.isfile(SOURCE_DB):
        raise FileNotFoundError(
            "students.db was not found in the project folder."
        )

    source = sqlite3.connect(
        f"file:{os.path.abspath(SOURCE_DB)}?mode=ro",
        uri=True
    )
    source.row_factory = sqlite3.Row

    try:
        source_tables = {
            row["name"]
            for row in source.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        for table in TABLES:
            if table not in source_tables:
                raise RuntimeError(
                    f"Source table is missing: {table}"
                )

        data = {}

        for table, target_columns in TABLES.items():
            source_columns = {
                row["name"]
                for row in source.execute(
                    f'PRAGMA table_info("{table}")'
                )
            }

            missing = [
                column for column in target_columns
                if column not in source_columns
                and column not in OPTIONAL_DEFAULTS
            ]

            if missing:
                raise RuntimeError(
                    f"{table} is missing source columns: {missing}"
                )

            selected_columns = [
                column for column in target_columns
                if column in source_columns
            ]

            query = (
                f'SELECT {", ".join(selected_columns)} '
                f'FROM "{table}" ORDER BY id'
            )

            rows = []
            for record in source.execute(query):
                row = dict(record)

                for column in target_columns:
                    if column not in row:
                        row[column] = OPTIONAL_DEFAULTS[column]

                rows.append(row)

            data[table] = rows

        expected_counts = {
            "students": 2,
            "quiz_results": 11,
            "materials": 1,
            "lesson_progress": 24,
            "reviews": 1,
        }

        actual_counts = {
            table: len(rows) for table, rows in data.items()
        }

        if actual_counts != expected_counts:
            raise RuntimeError(
                "Source counts differ from the previously checked "
                f"counts. Expected {expected_counts}; found {actual_counts}. "
                "Stop and review before migrating."
            )

        for table, rows in data.items():
            for row in rows:
                for column in TABLES[table]:
                    if row[column] is None and column in (
                        "id", "name", "email", "password",
                        "student_id", "score", "percentage",
                        "title", "description", "link", "topic",
                        "lesson_index", "rating", "review_text"
                    ):
                        raise RuntimeError(
                            f"Unexpected NULL in {table}.{column}. "
                            "Review the source data before migrating."
                        )

    finally:
        source.close()

    with psycopg.connect(database_url) as target:
        with target.cursor() as cur:
            # Safety check: never append to an already populated database.
            for table in TABLES:
                cur.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}").format(
                        sql.Identifier("public", table)
                    )
                )
                count = cur.fetchone()[0]

                if count != 0:
                    raise RuntimeError(
                        f"Neon table {table} is not empty ({count} rows). "
                        "No data was copied. Review the database first."
                    )

            # Insert all rows in one transaction.
            for table, columns in TABLES.items():
                rows = data[table]

                if not rows:
                    continue

                insert_query = sql.SQL(
                    "INSERT INTO {} ({}) VALUES ({})"
                ).format(
                    sql.Identifier("public", table),
                    sql.SQL(", ").join(
                        sql.Identifier(column) for column in columns
                    ),
                    sql.SQL(", ").join(
                        sql.Placeholder() for _ in columns
                    )
                )

                values = [
                    tuple(row[column] for column in columns)
                    for row in rows
                ]

                cur.executemany(insert_query, values)

            # Update identity counters so future IDs don't collide.
            for table in TABLES:
                cur.execute(
                    sql.SQL(
                        "SELECT setval("
                        "pg_get_serial_sequence(%s, 'id'), "
                        "COALESCE(MAX(id), 1), "
                        "MAX(id) IS NOT NULL"
                        ") FROM {}"
                    ).format(sql.Identifier("public", table)),
                    (f"public.{table}",)
                )

            # Verify counts before the transaction commits.
            for table, expected in expected_counts.items():
                cur.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}").format(
                        sql.Identifier("public", table)
                    )
                )
                actual = cur.fetchone()[0]

                if actual != expected:
                    raise RuntimeError(
                        f"Verification failed for {table}: "
                        f"expected {expected}, found {actual}."
                    )

    print("Migration completed successfully!")
    print("Verified record counts:")
    for table, count in expected_counts.items():
        print(f"  {table}: {count}")
    print("Total records copied: 39")
    print("Your original students.db was not modified.")


if __name__ == "__main__":
    main()