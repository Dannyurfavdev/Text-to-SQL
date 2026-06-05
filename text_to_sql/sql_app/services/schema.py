import sqlite3
from django.db import connection
from django.conf import settings


def get_schema_description() -> str:
    """
    Introspect the database and return a plain-English schema description
    that the LLM can use to write accurate SQL.
    """
    allowed = set(settings.ALLOWED_TABLES)
    lines = ["You have access to a SQLite database with the following tables:\n"]

    with connection.cursor() as cursor:
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        all_tables = [row[0] for row in cursor.fetchall()]

        for table in all_tables:
            if table not in allowed:
                continue

            lines.append(f"Table: {table}")

            # Get column info
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            # PRAGMA returns: (cid, name, type, notnull, default, pk)
            for col in columns:
                pk_marker = " [PRIMARY KEY]" if col[5] else ""
                null_marker = " NOT NULL" if col[3] else ""
                lines.append(f"  - {col[1]} ({col[2]}{null_marker}{pk_marker})")

            # Show a sample row so the LLM understands real values
            cursor.execute(f"SELECT * FROM {table} LIMIT 1;")
            sample = cursor.fetchone()
            if sample:
                col_names = [col[1] for col in columns]
                sample_str = ", ".join(f"{k}={v}" for k, v in zip(col_names, sample))
                lines.append(f"  Sample row: {sample_str}")

            lines.append("")

    lines.append(
        "Rules:\n"
        "- Only write SELECT statements.\n"
        "- Only reference the tables listed above.\n"
        "- Always include a LIMIT clause (max 100 rows).\n"
        "- Return ONLY the raw SQL — no markdown, no explanation.\n"
    )
    return "\n".join(lines)