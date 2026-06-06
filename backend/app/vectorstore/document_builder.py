from langchain_core.documents import Document

def document_builder(
        chunks,
        source_file
    ):
    docs=[]
    for chunk in chunks:
        docs.append(
            Document(
                page_content=chunk,
                metadata={
                    "source":source_file
                }
            )
        )

    return docs