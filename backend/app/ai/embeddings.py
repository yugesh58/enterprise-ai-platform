from langchain_openai import OpenAIEmbeddings

from app.core.config import settings


embeddings = OpenAIEmbeddings(
    model=settings.OPENAI_EMBEDDING_MODEL,
    api_key=settings.OPENAI_API_KEY,
)