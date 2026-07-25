from app.storage.database.factory import DatabaseFactory

db = DatabaseFactory.create()

print(type(db).__name__)