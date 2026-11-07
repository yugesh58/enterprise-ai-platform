import logging

from sqlalchemy.exc import DBAPIError, OperationalError

from app.core.config import settings
from app.core.enums import ExecutionErrorType
from app.storage.database.factory import DatabaseFactory

logger = logging.getLogger(__name__)


def run_query(query: str):
    try:
        # Include provider creation so connection failures are handled.
        if not isinstance(query, str) or not query.strip():
            return {
                "result": [],
                "execution_error": "SQL query is empty or invalid.",
                "error_type": ExecutionErrorType.UNKNOWN,
            }

        query = query.strip().rstrip(";")
        db = DatabaseFactory.create("postgres")
        limited_query = f"""
        SELECT *
        FROM (
            {query}
        ) AS query_result
        LIMIT {settings.SQL_MAX_RESULT_ROWS}
        """

        result = db.fetch_all(limited_query)

        return {
            "result": result,
            "execution_error": "",
            "error_type": None,
        }

    except OperationalError as exc:
        error_message = str(exc).lower()

        if "statement timeout" in error_message:
            error_type = ExecutionErrorType.TIMEOUT
            safe_message = "The SQL query exceeded the execution time limit."
        elif "permission denied" in error_message:
            error_type = ExecutionErrorType.PERMISSION
            safe_message = "The SQL query was denied due to insufficient permissions."
        else:
            error_type = ExecutionErrorType.DATABASE
            safe_message = "A database operation failed."

        logger.warning(
            "SQL query execution failed: %s",
            error_type.value,
        )

        return {
            "result": [],
            "execution_error": safe_message,
            "error_type": error_type,
        }

    except DBAPIError:
        logger.exception("SQL database driver error.")

        return {
            "result": [],
            "execution_error": "A database error occurred while executing the query.",
            "error_type": ExecutionErrorType.DATABASE,
        }

    except Exception:
        logger.exception("Unexpected SQL query execution error.")

        return {
            "result": [],
            "execution_error": "An unexpected error occurred while executing the query.",
            "error_type": ExecutionErrorType.UNKNOWN,
        }