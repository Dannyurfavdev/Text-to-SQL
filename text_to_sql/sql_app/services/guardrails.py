import re
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DDL, DML
from django.conf import settings


class GuardrailError(Exception):
    """Raised when any guardrail blocks a query."""
    pass


# --- Guardrail 1: Forbidden keywords ---

FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "TRUNCATE", "INSERT", "UPDATE",
    "ALTER", "CREATE", "REPLACE", "ATTACH", "DETACH",
    "PRAGMA", "VACUUM", "REINDEX",
}

SENSITIVE_INTENT_KEYWORDS = [
    "password", "passwd", "secret", "token", "auth_user",
    "credentials", "api_key", "private", "hash",
]

def check_forbidden_keywords(sql: str) -> None:
    """
    Block any SQL that contains write or administrative keywords.
    Parses the token stream so it catches multi-statement tricks
    like "SELECT 1; DROP TABLE users".
    """
    parsed = sqlparse.parse(sql)
    for statement in parsed:
        for token in statement.flatten():
            if token.ttype in (Keyword, DDL, DML):
                if token.normalized.upper() in FORBIDDEN_KEYWORDS:
                    raise GuardrailError(
                        f"Forbidden keyword detected: {token.normalized.upper()}. "
                        f"Only SELECT statements are allowed."
                    )


# --- Guardrail 2: Table allowlist ---

def _extract_table_names(sql: str) -> set[str]:
    """
    Parse the SQL and extract all table names referenced in FROM / JOIN clauses.
    Handles aliases and subqueries.
    """
    # Normalise and use regex for a pragmatic extraction
    # (sqlparse's table resolution is incomplete for complex queries)
    sql_upper = sql.upper()
    pattern = re.compile(
        r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        re.IGNORECASE
    )
    return {m.group(1).lower() for m in pattern.finditer(sql)}


def check_allowed_tables(sql: str) -> None:
    """
    Reject queries that reference tables outside the configured allowlist.
    Prevents the LLM from hallucinating tables like 'users' or 'auth_user'.
    """
    allowed = {t.lower() for t in settings.ALLOWED_TABLES}
    referenced = _extract_table_names(sql)

    forbidden_tables = referenced - allowed
    if forbidden_tables:
        raise GuardrailError(
            f"Query references table(s) not in the allowlist: "
            f"{', '.join(sorted(forbidden_tables))}. "
            f"Allowed tables: {', '.join(sorted(allowed))}."
        )


# --- Guardrail 3: Row limit enforcement ---

def check_row_limit(sql: str) -> str:
    """
    Ensure the query has a LIMIT clause, and that it doesn't exceed MAX_RESULT_ROWS.
    If no LIMIT is present, appends one. If the limit is too high, clamps it.
    Returns the (possibly modified) SQL.
    """
    max_rows = settings.MAX_RESULT_ROWS
    sql = sql.rstrip(";").strip()

    limit_pattern = re.compile(r'\bLIMIT\s+(\d+)', re.IGNORECASE)
    match = limit_pattern.search(sql)

    if match:
        requested = int(match.group(1))
        if requested > max_rows:
            # Replace the existing LIMIT with the capped value
            sql = limit_pattern.sub(f"LIMIT {max_rows}", sql)
    else:
        sql = f"{sql} LIMIT {max_rows}"

    return sql

# --- intent check before calling the LLM — a simple keyword scan on the raw question, before any SQL is generated ---
def check_question_intent(question: str) -> None:
    """
    Block questions that show clear malicious or sensitive intent,
    before the LLM even generates SQL.
    """
    question_lower = question.lower()
    for keyword in SENSITIVE_INTENT_KEYWORDS:
        if keyword in question_lower:
            raise GuardrailError(
                f"Question blocked: references sensitive topic '{keyword}'. "
                f"Only questions about allowed business data are permitted."
            )


# --- Run all guardrails in sequence ---

def apply_guardrails(sql: str) -> str:
    """
    Run all three checks. Returns the (possibly modified) safe SQL,
    or raises GuardrailError with a human-readable reason.
    """
    check_forbidden_keywords(sql)
    check_allowed_tables(sql)
    sql = check_row_limit(sql)
    return sql