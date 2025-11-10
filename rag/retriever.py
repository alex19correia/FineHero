"""
This module provides the RAGRetriever class, which is responsible for loading a
FAISS vector store and performing similarity searches to retrieve relevant
document chunks based on a given query. This retrieved context is then used
to augment prompts for AI defense generation.
"""
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Define constants
VECTOR_STORE_DIR = "vector_store"

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
        Initializes the retriever by loading the FAISS vector store.

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

    def retrieve(self, query: str, k: int = 3) -> list:
        """
        Retrieves the top-k most relevant document chunks for a given query.

        Args:
            query (str): The query string to search for relevant documents.
            k (int): The number of top relevant document chunks to retrieve.

        Returns:
            list: A list of strings, where each string is the content of a
                  retrieved document chunk.
        """
        print(f"Retrieving top-{k} documents for query: '{query}'...")
        docs = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]

if __name__ == "__main__":
    # Example usage:
    # This block demonstrates how to use the RAGRetriever to fetch relevant
    # legal documents for a sample query.
    try:
        retriever = RAGRetriever()
        query = "notificação de multas de trânsito"
        relevant_docs = retriever.retrieve(query)
        print("\n--- Retrieved Documents ---")
        for i, doc in enumerate(relevant_docs):
            print(f"Document {i+1}:\n{doc}\n---")
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")
