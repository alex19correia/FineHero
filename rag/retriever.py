"""
This module provides the RAGRetriever class, which is responsible for loading a
FAISS vector store and performing similarity searches to retrieve relevant
document chunks based on a given query. This retrieved context is then used
to augment prompts for AI defense generation.
"""
import os
from typing import List, Dict, Any, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models import LegalDocument # Import the new LegalDocument model

# Define constants
VECTOR_STORE_DIR = "vector_store"
DATABASE_URL = "sqlite:///./sql_app.db" # Use the same DB as backend

class RAGRetriever:
    """
    A class to retrieve relevant documents from the FAISS vector store.

    This retriever loads a pre-built FAISS index containing embeddings of
    legal documents and traffic regulations. It allows for efficient
    similarity search to find the most relevant document chunks for a given query,
    which can then be used to provide context to a language model.
    """
    def __init__(self, vector_store_dir: str = VECTOR_STORE_DIR):
        """
        Initializes the retriever by loading the FAISS vector store and setting up DB session.

        Args:
            vector_store_dir (str): The directory where the FAISS vector store is located.
                                    Defaults to VECTOR_STORE_DIR.

        Raises:
            FileNotFoundError: If the vector store directory does not exist,
                               indicating that the ingestion script has not been run.
        """
        if not os.path.exists(vector_store_dir):
            raise FileNotFoundError(f"Vector store not found at '{vector_store_dir}'. Please run ingest.py first.")

        print(f"Loading vector store from '{vector_store_dir}'...")
        # The embedding model used for loading must be the same as the one used for ingestion.
        embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = FAISS.load_local(vector_store_dir, embedding_model, allow_dangerous_deserialization=True)
        print("Vector store loaded successfully.")

        # Setup database engine and session
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def retrieve(self, query: str, k: int = 3, metadata_filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Retrieves the top-k most relevant document chunks for a given query,
        optionally filtered by metadata.

        Args:
            query (str): The query string to search for relevant documents.
            k (int): The number of top relevant document chunks to retrieve.
            metadata_filters (Optional[Dict[str, Any]]): A dictionary of metadata
                                                        to filter the retrieved documents.
                                                        E.g., {"document_type": "law", "jurisdiction": "Portugal"}

        Returns:
            List[str]: A list of strings, where each string is the content of a
                       retrieved document chunk.
        """
        print(f"Retrieving top-{k} documents for query: '{query}' with filters: {metadata_filters}...")
        
        # Perform similarity search first
        docs_with_scores = self.vector_store.similarity_search_with_score(query, k=k*5) # Retrieve more to filter down

        filtered_docs_content = []
        db = self.SessionLocal()
        try:
            for doc, score in docs_with_scores:
                # Each doc.metadata contains "document_id" which links to our LegalDocument model
                document_id = doc.metadata.get("document_id")
                if document_id:
                    db_document = db.query(LegalDocument).filter(LegalDocument.id == document_id).first()
                    
                    if db_document:
                        # Apply metadata filters
                        if metadata_filters:
                            match = True
                            for key, value in metadata_filters.items():
                                if not hasattr(db_document, key) or getattr(db_document, key) != value:
                                    match = False
                                    break
                            if not match:
                                continue # Skip this document if filters don't match

                        # If filters match or no filters provided, add document content
                        filtered_docs_content.append(doc.page_content)
                        if len(filtered_docs_content) >= k:
                            break # Stop once we have enough documents after filtering
        finally:
            db.close()

        return filtered_docs_content

if __name__ == "__main__":
    # Example usage:
    # This block demonstrates how to use the RAGRetriever to fetch relevant
    # legal documents for a sample query.
    try:
        retriever = RAGRetriever()
        query = "notificação de multas de trânsito"
        
        print("\n--- Retrieving without filters ---")
        relevant_docs = retriever.retrieve(query, k=2)
        for i, doc in enumerate(relevant_docs):
            print(f"Document {i+1}:\n{doc}\n---")

        print("\n--- Retrieving with filters (document_type='law') ---")
        filtered_docs = retriever.retrieve(query, k=2, metadata_filters={"document_type": "law"})
        for i, doc in enumerate(filtered_docs):
            print(f"Document {i+1}:\n{doc}\n---")

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")
