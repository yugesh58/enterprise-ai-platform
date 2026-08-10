from collections import Counter

from sqlalchemy import text

from app.core.config import settings
from app.storage.database.connection import engine
from app.storage.vectorstore.factory import VectorStoreFactory


def main() -> None:
    print("=" * 100)
    print("QDRANT / POSTGRES CONSISTENCY AUDIT")
    print("=" * 100)

    # --------------------------------------------------
    # Get document IDs from PostgreSQL
    # --------------------------------------------------

    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT id FROM documents")
        ).all()

    postgres_ids = {
        str(row[0])
        for row in rows
    }

    print(f"\nPostgreSQL documents : {len(postgres_ids)}")

    for document_id in sorted(postgres_ids):
        print(f"  ✅ {document_id}")

    # --------------------------------------------------
    # Retrieve Qdrant points
    # --------------------------------------------------

    provider = VectorStoreFactory.get_provider()

    # We use a zero vector only to inspect the collection.
    results = provider.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=[0.0] * 1536,
        limit=10000,
    )

    print(f"\nQdrant points         : {len(results)}")

    # --------------------------------------------------
    # Group points by document_id
    # --------------------------------------------------

    points_by_document = {}

    for result in results:
        payload = result["payload"]

        document_id = payload.get("document_id")

        if document_id is None:
            document_id = "<MISSING_DOCUMENT_ID>"

        points_by_document.setdefault(
            str(document_id),
            [],
        ).append(result["id"])

    # --------------------------------------------------
    # Audit
    # --------------------------------------------------

    print("\n" + "=" * 100)
    print("DOCUMENT CONSISTENCY")
    print("=" * 100)

    orphaned_ids = []

    for document_id, point_ids in sorted(
        points_by_document.items()
    ):
        point_count = len(point_ids)

        if document_id in postgres_ids:
            print(
                f"✅ {document_id} "
                f"| Qdrant points: {point_count} "
                f"| PostgreSQL: EXISTS"
            )
        else:
            print(
                f"❌ {document_id} "
                f"| Qdrant points: {point_count} "
                f"| PostgreSQL: MISSING"
            )

            orphaned_ids.append(
                document_id
            )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    orphaned_point_count = sum(
        len(points_by_document[document_id])
        for document_id in orphaned_ids
    )

    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)

    print(
        f"PostgreSQL documents : {len(postgres_ids)}"
    )

    print(
        f"Qdrant documents     : "
        f"{len(points_by_document)}"
    )

    print(
        f"Valid Qdrant points  : "
        f"{len(results) - orphaned_point_count}"
    )

    print(
        f"Orphaned Qdrant points: "
        f"{orphaned_point_count}"
    )

    if orphaned_ids:
        print("\nORPHANED DOCUMENT IDS:")
        for document_id in orphaned_ids:
            print(
                f"  - {document_id} "
                f"({len(points_by_document[document_id])} points)"
            )

    print("\nNo data was modified.")


if __name__ == "__main__":
    main()
