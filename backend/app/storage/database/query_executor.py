from sqlalchemy.exc import DBAPIError, OperationalError

from app.core.config import settings
from app.core.enums import ExecutionErrorType
from app.storage.database.factory import DatabaseFactory


def run_query(query: str):
    db = DatabaseFactory.create("postgres")

    query = query.strip().rstrip(";")

    limited_query = f"""
    SELECT *
    FROM (
        {query}
    ) AS query_result
    LIMIT {settings.SQL_MAX_RESULT_ROWS}
    """

    try:
        result = db.fetch_all(limited_query)

        return {
            "result": result,
            "execution_error": "",
            "error_type": None,
        }

    except OperationalError as e:
        error_message = str(e)

        if "statement timeout" in error_message.lower():
            error_type = ExecutionErrorType.TIMEOUT
        elif "permission denied" in error_message.lower():
            error_type = ExecutionErrorType.PERMISSION
        else:
            error_type = ExecutionErrorType.DATABASE

        return {
            "result": [],
            "execution_error": error_message,
            "error_type": error_type,
        }

    except DBAPIError as e:
        return {
            "result": [],
            "execution_error": str(e),
            "error_type": ExecutionErrorType.DATABASE,
        }

    except Exception as e:
        return {
            "result": [],
            "execution_error": str(e),
            "error_type": ExecutionErrorType.UNKNOWN,
        }