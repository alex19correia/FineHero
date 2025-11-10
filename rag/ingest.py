"""
This script is responsible for ingesting raw legal documents from the knowledge_base directory,
processing them into chunks, generating vector embeddings, and storing these embeddings
in a local FAISS vector store. This forms the foundation of the Retrieval-Augmented Generation (RAG) system.
"""
import os
import argparse
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Define constants
KNOWLEDGE_BASE_DIR = "knowledge_base"
VECTOR_STORE_DIR = "vector_store"

def ingest_documents(knowledge_base_dir: str = KNOWLEDGE_BASE_DIR, vector_store_dir: str = VECTOR_STORE_DIR):
    """
    Ingests documents from the specified knowledge base directory, creates embeddings,
    and saves them to a FAISS vector store.

    Args:
        knowledge_base_dir (str): The directory containing the source documents.
                                  Defaults to KNOWLEDGE_BASE_DIR.
        vector_store_dir (str): The directory where the FAISS vector store will be saved.
                                Defaults to VECTOR_STORE_DIR.

    The process involves:
    1. Loading text files using DirectoryLoader.
    2. Splitting the loaded documents into smaller, manageable chunks
       using RecursiveCharacterTextSplitter to optimize retrieval granularity.
    3. Generating vector embeddings for each chunk using HuggingFaceEmbeddings.
    4. Creating and saving a FAISS vector store locally, which allows for
       efficient similarity search and retrieval of relevant document parts.
    """
    print(f"Loading documents from '{knowledge_base_dir}'...")

    # Use DirectoryLoader to load all .txt files
    loader = DirectoryLoader(
        knowledge_base_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()

    if not documents:
        print("No documents found to ingest.")
        return

    print(f"Loaded {len(documents)} document(s).")

    # Split documents into chunks
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)
    print(f"Split into {len(texts)} chunks.")

    # Create embeddings
    print("Creating embeddings... (This may take a while on the first run)")
    # Using a smaller, faster model for the MVP
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Create a FAISS vector store from the documents and embeddings
    print("Creating FAISS vector store...")
    vector_store = FAISS.from_documents(texts, embedding_model)

    # Save the vector store locally
    if not os.path.exists(vector_store_dir):
        os.makedirs(vector_store_dir)
        
    vector_store.save_local(vector_store_dir)
    print(f"Vector store saved to '{vector_store_dir}'.")
    print("\nIngestion complete! ✅")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents for FineHero RAG.")
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Run the ingestion process."
    )
    args = parser.parse_args()

    if args.ingest:
        ingest_documents()
    else:
        print("Please specify the action to perform. Use --ingest to start the ingestion process.")
