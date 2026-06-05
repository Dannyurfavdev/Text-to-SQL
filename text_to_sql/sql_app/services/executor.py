from django.db import connection


def execute_query(sql: str) -> dict:
    """
    Execute a pre-validated SELECT query and return columns + rows.
    Uses Django's connection so it respects the configured database.
    """
    with connection.cursor() as cursor:
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

    return {
        "columns": columns,
        "rows": [list(row) for row in rows],
        "row_count": len(rows),
    }