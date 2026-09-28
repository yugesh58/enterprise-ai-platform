from app.storage.database.factory import DatabaseFactory


def run_query(query: str):
    db = DatabaseFactory.create("sqlite")
    return db.fetch_all(query)