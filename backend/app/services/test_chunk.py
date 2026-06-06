from app.loaders.pdf_loader import load_pdf
from app.services.chunker import create_chunk


text=load_pdf(file_path="app/uploads/Leave-Policy.pdf")

chunks=create_chunk(text)

print(f"Total chunks: {len(chunks)} \n First chunk:{chunks[0:]}")