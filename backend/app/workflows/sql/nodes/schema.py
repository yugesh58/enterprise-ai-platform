from app.storage.database.schema_retriever import get_schema


def retrieve_schema_node(state):

    schema = get_schema()

    return {
        "schema": schema
    }