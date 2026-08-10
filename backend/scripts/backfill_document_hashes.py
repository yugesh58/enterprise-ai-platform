import hashlib
from pathlib import Path

from sqlalchemy import text

from app.storage.database.connection import engine


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 for a file without loading the
    entire file into memory.
    """

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


def main() -> None:

    print("=" * 100)
    print("DOCUMENT HASH BACKFILL")
    print("=" * 100)

    with engine.begin() as connection:

        documents = connection.execute(
            text(
                """
                SELECT
                    id,
                    filename,
                    storage_path,
                    content_hash
                FROM documents
                ORDER BY created_at
                """
            )
        ).mappings().all()

        print(f"Documents found: {len(documents)}")

        successful = 0
        missing = 0

        for document in documents:

            document_id = document["id"]
            storage_path = Path(document["storage_path"])

            print("\n" + "-" * 100)
            print(f"Document : {document['filename']}")
            print(f"ID       : {document_id}")
            print(f"Path     : {storage_path}")

            if not storage_path.exists():

                print("❌ File does not exist")

                missing += 1
                continue

            content_hash = calculate_sha256(
                storage_path
            )

            connection.execute(
                text(
                    """
                    UPDATE documents
                    SET content_hash = :content_hash
                    WHERE id = :document_id
                    """
                ),
                {
                    "content_hash": content_hash,
                    "document_id": document_id,
                },
            )

            print(f"SHA-256  : {content_hash}")
            print("✅ Hash populated")

            successful += 1

    print("\n" + "=" * 100)
    print("BACKFILL COMPLETE")
    print("=" * 100)
    print(f"Documents found : {len(documents)}")
    print(f"Successful      : {successful}")
    print(f"Missing files   : {missing}")


if __name__ == "__main__":
    main()