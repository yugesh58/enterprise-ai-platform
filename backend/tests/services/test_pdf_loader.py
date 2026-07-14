from app.loaders.pdf_loader import load_pdf

text=load_pdf("app/uploads/Leave-Policy.pdf")

print(text[3000:])