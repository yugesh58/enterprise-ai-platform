from sqlalchemy import inspect
from app.database.connection import engine

def get_schema():
    inspector=inspect(engine)

    schema_info=[]

    tables=inspector.get_table_names()

    for table in tables:
        columns=inspector.get_columns(table)

        column_names=[
            column["name"] for column in columns
        ]

        schema_info.append(
            f"{table}({", ".join(column_names)})"
        )
    
    return "\n".join(schema_info)