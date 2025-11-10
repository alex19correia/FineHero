"""
This script is responsible for ingesting raw legal documents from the knowledge_base directory,
processing them into chunks, generating vector embeddings, and storing these embeddings
in a local FAISS vector store. This forms the foundation of the Retrieval-Augmented Generation (RAG) system.
"""
import os
import argparse
from typing import Dict, Any
from datetime import datetime

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LangchainDocument

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models import Base, LegalDocument as DB_Document # Renamed to avoid conflict

# Define constants
KNOWLEDGE_BASE_DIR = "knowledge_base"
VECTOR_STORE_DIR = "vector_store"
DATABASE_URL = "sqlite:///./sql_app.db" # Use the same DB as backend

# Setup database engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables are created
Base.metadata.create_all(bind=engine)

def calculate_quality_scores(document_content: str, metadata: Dict[str, Any]) -> Dict[str, float]:
    """
    Placeholder function to calculate quality scores for a document.
    This will be expanded with actual logic later.
    """
    # Dummy scores for now
    relevance = 0.7 + (len(document_content) % 100) / 1000.0 # Example: longer docs slightly more relevant
    freshness = 1.0 # Assume fresh for now
    authority = 0.8 # Assume reasonable authority

    # Example: Adjust scores based on metadata
    if metadata.get("document_type") == "law":
        authority = 0.95
    elif metadata.get("document_type") == "precedent":
        authority = 0.9

    return {
        "relevance_score": relevance,
        "freshness_score": freshness,
        "authority_score": authority,
        "quality_score": (relevance + freshness + authority) / 3.0
    }

def ingest_document_with_metadata(
    document_data: Dict[str, Any],
    vector_store_dir: str = VECTOR_STORE_DIR
):
    """
    Ingests a single document with associated metadata into the database and FAISS vector store.

    Args:
        document_data (Dict[str, Any]): A dictionary containing:
            - 'content': The text content of the document.
            - 'title': The title of the document.
            - 'document_type': Type of document (e.g., 'law', 'precedent').
            - 'jurisdiction': Geographic jurisdiction.
            - 'publication_date': Date of publication (datetime.date object).
            - 'source_url': URL where the document was sourced.
            - 'file_path': Local path if saved as a file.
            - 'case_outcome_id': (Optional) ID of the CaseOutcome if applicable.
            - 'legal_arguments': (Optional) Legal arguments if applicable.
        vector_store_dir (str): The directory where the FAISS vector store will be saved.
    """
    db = SessionLocal()
    try:
        # Calculate quality scores
        quality_scores = calculate_quality_scores(document_data['content'], document_data)
        
        # Create and save document metadata to the database
        db_document = DB_Document(
            title=document_data['title'],
            document_type=document_data['document_type'],
            jurisdiction=document_data['jurisdiction'],
            publication_date=document_data.get('publication_date'),
            source_url=document_data['source_url'],
            file_path=document_data.get('file_path'),
            extracted_text=document_data['content'],
            case_outcome_id=document_data.get('case_outcome_id'), # Now a foreign key
            quality_score=quality_scores['quality_score'],
            relevance_score=quality_scores['relevance_score'],
            freshness_score=quality_scores['freshness_score'],
            authority_score=quality_scores['authority_score']
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        print(f"Document metadata saved to DB with ID: {db_document.id}")

        # Prepare document for FAISS
        # Langchain Document expects page_content and metadata
        lc_document = LangchainDocument(
            page_content=document_data['content'],
            metadata={
                "document_id": db_document.id, # Link to our DB document
                "title": db_document.title,
                "document_type": db_document.document_type,
                "jurisdiction": db_document.jurisdiction,
                "source_url": db_document.source_url,
                "quality_score": db_document.quality_score,
                "relevance_score": db_document.relevance_score,
                "freshness_score": db_document.freshness_score,
                "authority_score": db_document.authority_score,
                "publication_date": db_document.publication_date.isoformat() if db_document.publication_date else None,
                "case_outcome_id": db_document.case_outcome_id,
            }
        )

        # Split document into chunks
        print("Splitting document into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        texts = text_splitter.split_documents([lc_document])
        print(f"Split into {len(texts)} chunks.")

        # Create embeddings
        print("Creating embeddings... (This may take a while on the first run)")
        embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Load existing vector store or create a new one
        if os.path.exists(vector_store_dir) and os.listdir(vector_store_dir):
            print(f"Loading existing vector store from '{vector_store_dir}'...")
            vector_store = FAISS.load_local(vector_store_dir, embedding_model, allow_dangerous_deserialization=True)
            vector_store.add_documents(texts)
            print("Documents added to existing vector store.")
        else:
            print("Creating new FAISS vector store...")
            vector_store = FAISS.from_documents(texts, embedding_model)
            print("New vector store created.")

        # Save the vector store locally
        if not os.path.exists(vector_store_dir):
            os.makedirs(vector_store_dir)
            
        vector_store.save_local(vector_store_dir)
        print(f"Vector store saved to '{vector_store_dir}'.")
        print("\nIngestion complete! ✅")

    except Exception as e:
        db.rollback()
        print(f"Error during ingestion: {e}")
        raise
    finally:
        db.close()

def ingest_documents_from_directory(knowledge_base_dir: str = KNOWLEDGE_BASE_DIR):
    """
    Ingests documents from the specified knowledge base directory.
    This function is for existing local files without rich metadata.
    It will create basic metadata for them.
    """
    print(f"Loading documents from '{knowledge_base_dir}'...")

    # Use TextLoader to load all .txt files
    # For now, we'll assume basic metadata for files loaded this way
    for root, _, files in os.walk(knowledge_base_dir):
        for file_name in files:
            if file_name.endswith(".txt"):
                file_path = os.path.join(root, file_name)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Basic metadata for existing files
                document_data = {
                    "content": content,
                    "title": os.path.basename(file_path),
                    "document_type": "unknown", # Can be improved with file content analysis
                    "jurisdiction": "Portugal",
                    "publication_date": datetime.now().date(), # Placeholder
                    "source_url": f"file://{os.path.abspath(file_path)}",
                    "file_path": os.path.abspath(file_path),
                    "case_outcome_id": None # Default for directory ingestion
                }
                print(f"Ingesting file: {file_name}")
                ingest_document_with_metadata(document_data)
