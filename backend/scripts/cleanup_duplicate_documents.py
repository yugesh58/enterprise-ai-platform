from uuid import UUID

from sqlalchemy import delete, text

from app.core.config import settings
from app.storage.database.connection import engine
from app.storage.vectorstore.factory import VectorStoreFactory
from app.models.document import documents


STALE_DOCUMENT_IDS = [
    UUID("caf18d06-ae30-4681-94df-640e93714505"),
    UUID("613b6751-e52a-4164-b62f-f1d9da8e07ac"),
]

CURRENT_DOCUMENT_ID = UUID(
    "fca77fcc-a0ce-46c9-bec5-414e23014ad5"
)


def main() -> None:

    print("=" * 100)
    print("DOCUMENT DUPLICATE CLEANUP")
    print("=" * 100)

    provider = VectorStoreFactory.get_provider()

    # ------------------------------------------------------
    # Verify current document
    # ------------------------------------------------------

    with engine.connect() as connection:

        current = connection.execute(
            text(
                """
                SELECT
                    id,
                    filename,
                    storage_path,
                    content_hash
                FROM documents
                WHERE id = :document_id
                """
            ),
            {
                "document_id": CURRENT_DOCUMENT_ID,
            },
        ).mappings().first()

    if current is None:
        raise RuntimeError(
            f"Current document {CURRENT_DOCUMENT_ID} was not found."
        )

    print("\nCURRENT DOCUMENT")
    print("-" * 100)
    print(f"ID           : {current['id']}")
    print(f"Filename     : {current['filename']}")
    print(f"Storage path : {current['storage_path']}")
    print(f"Content hash : {current['content_hash']}")

    if not current["content_hash"]:
        raise RuntimeError(
            "Current document does not have a content hash."
        )

    # ------------------------------------------------------
    # Remove stale Qdrant points
    # ------------------------------------------------------

    for document_id in STALE_DOCUMENT_IDS:

        print("\n" + "-" * 100)
        print(f"PROCESSING STALE DOCUMENT: {document_id}")

        results = provider.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=[0.0] * 1536,
            limit=100,
            filters={
                "document_id": str(document_id),
            },
        )

        point_ids = [
            result["id"]
            for result in results
        ]

        print(f"Qdrant points found: {len(point_ids)}")

        if point_ids:

            provider.delete(
                collection_name=settings.QDRANT_COLLECTION,
                point_ids=point_ids,
            )

            print(
                f"Deleted {len(point_ids)} Qdrant points."
            )

        else:

            print("No Qdrant points to delete.")

    # ------------------------------------------------------
    # Remove stale PostgreSQL metadata
    # ------------------------------------------------------

    with engine.begin() as connection:

        result = connection.execute(
            delete(documents).where(
                documents.c.id.in_(STALE_DOCUMENT_IDS)
            )
        )

        print(
            f"\nDeleted PostgreSQL records: {result.rowcount}"
        )

    # ------------------------------------------------------
    # Verify
    # ------------------------------------------------------

    print("\n" + "=" * 100)
    print("VERIFICATION")
    print("=" * 100)

    for document_id in STALE_DOCUMENT_IDS:

        results = provider.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=[0.0] * 1536,
            limit=100,
            filters={
                "document_id": str(document_id),
            },
        )

        print(
            f"{document_id} → "
            f"{len(results)} Qdrant points"
        )

    with engine.connect() as connection:

        remaining = connection.execute(
            text(
                """
                SELECT
                    id,
                    filename,
                    content_hash
                FROM documents
                ORDER BY created_at
                """
            )
        ).mappings().all()

    print("\nRemaining PostgreSQL documents:")

    for document in remaining:

        print(
            f"{document['id']} | "
            f"{document['filename']} | "
            f"{document['content_hash']}"
        )

    print("\nCleanup complete.")


if __name__ == "__main__":
    main()