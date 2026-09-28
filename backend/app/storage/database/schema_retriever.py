from app.storage.database.factory import DatabaseFactory


def get_schema():
    db = DatabaseFactory.create("sqlite")
    return db.get_schema()