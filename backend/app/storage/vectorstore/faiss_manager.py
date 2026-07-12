from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv


load_dotenv()
FAISS_PATH = "app/vectorstore/faiss_index"

def create_vectorstore(documents):
    embeddings=OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    vector_store=FAISS.from_documents(
    documents,
    embedding=embeddings
    )

    return vector_store

def add_documents_to_vectorstore(
    vectorstore,
    documents
):

    vectorstore.add_documents(
        documents
    )

    return vectorstore

def save_vectorstore(vectorstore):
    vectorstore.save_local(
        FAISS_PATH
    )

def load_vectorstore():
    embeddings=OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    return FAISS.load_local(  
        FAISS_PATH,
        embeddings,
        allow_dangerous_deserialization=True)

def retrieve_chunk(
        vectorstore,
        question,
        k=3
):
    docs=vectorstore.similarity_search(
        question,
        k=k
    )

    return docs
