from sqlalchemy import text

from app.core.config import settings
from app.storage.database.connection import engine
from app.storage.vectorstore.factory import VectorStoreFactory


def main() -> None:
    print("=" * 100)
    print("CLEANUP ORPHANED QDRANT VECTORS")
    print("=" * 100)

    # --------------------------------------------------
    # PostgreSQL = source of truth
    # --------------------------------------------------

    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT id FROM documents")
        ).all()

    valid_document_ids = {
        str(row[0])
        for row in rows
    }

    print(
        f"\nValid PostgreSQL documents: "
        f"{len(valid_document_ids)}"
    )

    # --------------------------------------------------
    # Retrieve Qdrant points
    # --------------------------------------------------

    provider = VectorStoreFactory.get_provider()

    results = provider.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=[0.0] * 1536,
        limit=10000,
    )

    # --------------------------------------------------
    # Identify orphaned points
    # --------------------------------------------------

    orphaned_points = []

    for result in results:

        payload = result["payload"]

        document_id = str(
            payload.get("document_id")
        )

        if document_id not in valid_document_ids:
            orphaned_points.append(result)

    print(
        f"Total Qdrant points: {len(results)}"
    )

    print(
        f"Orphaned Qdrant points: "
        f"{len(orphaned_points)}"
    )

    if not orphaned_points:
        print("\nNothing to clean.")
        return

    # --------------------------------------------------
    # Group orphaned points
    # --------------------------------------------------

    points_by_document = {}

    for point in orphaned_points:

        document_id = str(
            point["payload"].get("document_id")
        )

        points_by_document.setdefault(
            document_id,
            [],
        ).append(point["id"])

    print("\nORPHANED DOCUMENTS")
    print("-" * 100)

    for document_id, point_ids in sorted(
        points_by_document.items()
    ):
        print(
            f"{document_id} "
            f"→ {len(point_ids)} points"
        )

    # --------------------------------------------------
    # Delete orphaned vectors
    # --------------------------------------------------

    point_ids = [
        point["id"]
        for point in orphaned_points
    ]

    print("\nDeleting orphaned vectors...")

    provider.delete(
        collection_name=settings.QDRANT_COLLECTION,
        point_ids=point_ids,
    )

    print(
        f"✅ Deleted {len(point_ids)} orphaned vectors."
    )

    # --------------------------------------------------
    # Verify
    # --------------------------------------------------

    remaining = provider.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=[0.0] * 1536,
        limit=10000,
    )

    remaining_orphans = [
        result
        for result in remaining
        if str(
            result["payload"].get("document_id")
        ) not in valid_document_ids
    ]

    print("\nVERIFICATION")
    print("-" * 100)

    print(
        f"Remaining Qdrant points: "
        f"{len(remaining)}"
    )

    print(
        f"Remaining orphaned points: "
        f"{len(remaining_orphans)}"
    )

    if remaining_orphans:
        raise RuntimeError(
            "Orphaned Qdrant vectors still remain."
        )

    print("\n✅ Qdrant is now consistent with PostgreSQL.")


if __name__ == "__main__":
    main()