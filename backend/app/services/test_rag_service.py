from app.loaders.pdf_loader import load_pdf
from app.services.chunker import create_chunks
from app.vectorstore.faiss_manager import create_vectorstore,retrieve_chunk
from app.services.rag_service import generate_rag_answer

text = load_pdf(
    "app/uploads/Leave-Policy.pdf"
)

chunks = create_chunks(text)

vectorstore = create_vectorstore(chunks)

docs=retrieve_chunk(vectorstore,"What is the leave policy")

result = generate_rag_answer(
    docs,
    "What is the leave policy"
)

print("\nAnswer:\n")

print(result["answer"])

print("\nSources:\n")

for source in result["sources"]:
    print(source)
