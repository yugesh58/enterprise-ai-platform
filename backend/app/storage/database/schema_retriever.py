from app.storage.database.factory import DatabaseFactory


def get_schema():
    db = DatabaseFactory.create()
    return db.get_schema()