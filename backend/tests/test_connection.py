from pprint import pprint

from app.storage.database import DatabaseFactory


def main():
    db = DatabaseFactory.create()

    pprint(db.get_schema())

    db.close()


if __name__ == "__main__":
    main()