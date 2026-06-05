from openai import OpenAI
from django.conf import settings
from .schema import get_schema_description

_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_sql(question: str) -> str:
    """
    Ask the LLM to convert a natural language question into SQL.
    Returns a raw SQL string — not yet validated or executed.
    """
    schema = get_schema_description()

    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": schema},
            {"role": "user", "content": question},
        ],
        temperature=0,   # deterministic — we want consistent SQL, not creative SQL
    )

    sql = response.choices[0].message.content.strip()

    # Strip markdown fences if the model wrapped the SQL anyway
    if sql.startswith("```"):
        sql = sql.split("```")[1]
        if sql.startswith("sql"):
            sql = sql[3:]
    return sql.strip()