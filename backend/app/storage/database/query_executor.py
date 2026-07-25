from app.storage.database.factory import DatabaseFactory


def run_query(query: str):
    db = DatabaseFactory.create()
    return db.fetch_all(query)