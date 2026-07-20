from app.storage.database.base import DatabaseProvider


class PostgreSQLProvider(DatabaseProvider):

    def connect(self):
        raise NotImplementedError

    def execute(self, query, params=None):
        raise NotImplementedError

    def fetch_one(self, query, params=None):
        raise NotImplementedError

    def fetch_all(self, query, params=None):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError