from app.core.config import settings
from app.storage.database.factory import DatabaseFactory


def run_query(query: str):
    db = DatabaseFactory.create("sqlite")

    query = query.strip().rstrip(";")

    limited_query = f"""
    SELECT *
    FROM (
        {query}
    )
    LIMIT {settings.SQL_MAX_RESULT_ROWS}
    """

    try:
        result = db.fetch_all(limited_query)

        return {
            "result": result,
            "execution_error": "",
        }

    except Exception as exc:
        return {
            "result": [],
            "execution_error": str(exc),
        }