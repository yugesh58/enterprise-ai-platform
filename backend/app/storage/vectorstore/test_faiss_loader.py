from app.loaders.pdf_loader import load_pdf
from app.services.chunker import create_chunks
from app.vectorstore.document_builder import document_builder
from app.vectorstore.faiss_manager import create_vectorstore,retrieve_chunk,save_vectorstore

text = load_pdf(
    "app/uploads/Leave-Policy.pdf"
)

chunks = create_chunks(text)

documents = document_builder(
    chunks,
    "leave_policy.pdf"
)

vectorstore = create_vectorstore(documents)

save_vectorstore(vectorstore)

result=retrieve_chunk(vectorstore=vectorstore,question="What is the leave policy")

for doc in result:

    print("\n=================\n")

    print(doc.page_content)