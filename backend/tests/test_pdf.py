from app.services.pdf_processing_service import PDFProcessingService

service = PDFProcessingService()

result = service.extract_document(
    "/Users/yugesh/Desktop/GenAI/enterprise-ai-platform/backend/uploads/2026/07/22/89b3cd77-7a76-4b9f-bec8-61c5fc492449.pdf"
)

print(result.model_dump())