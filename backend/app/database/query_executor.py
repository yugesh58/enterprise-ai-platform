from sqlalchemy import text
from app.database.connection import engine


def run_query(query: str):

    try:

        with engine.connect() as connection:

            result = connection.execute(text(query))

            rows = result.fetchall()

            return [dict(row._mapping) for row in rows]

    except Exception as e:

        return {
            "error": str(e)
        }