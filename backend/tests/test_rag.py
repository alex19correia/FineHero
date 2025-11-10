import os
import shutil
import unittest
from unittest.mock import MagicMock, patch

# Adjust the path to import modules from the rag directory
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from rag.ingest import ingest_documents
from rag.retriever import RAGRetriever

# Mock the HuggingFaceEmbeddings to prevent model download during tests
class MockEmbeddings(MagicMock):
    def embed_documents(self, texts):
        # Return dummy embeddings for testing
        return [[0.1] * 384 for _ in texts] # all-MiniLM-L6-v2 has 384 dimensions

    def embed_query(self, text):
        return [0.1] * 384

@patch('langchain_huggingface.HuggingFaceEmbeddings', new=MockEmbeddings)
class TestRAG(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create a temporary knowledge base directory for testing
        cls.test_knowledge_base_dir = "test_knowledge_base"
        cls.test_vector_store_dir = "test_vector_store"
        os.makedirs(os.path.join(cls.test_knowledge_base_dir, "legal_articles"), exist_ok=True)
        
        # Create a dummy document
        with open(os.path.join(cls.test_knowledge_base_dir, "legal_articles", "test_article.txt"), "w", encoding="utf-8") as f:
            f.write("This is a test legal article about traffic laws. It has multiple sentences. This is another sentence.")
            f.write("This is a second paragraph. It also has multiple sentences. More content here.")

    @classmethod
    def tearDownClass(cls):
        # Clean up temporary directories
        if os.path.exists(cls.test_knowledge_base_dir):
            shutil.rmtree(cls.test_knowledge_base_dir)
        if os.path.exists(cls.test_vector_store_dir):
            shutil.rmtree(cls.test_vector_store_dir)
        
        # Remove the added path from sys.path
        sys.path.remove(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

    def setUp(self):
        # Ensure a clean state for each test
        if os.path.exists(self.test_vector_store_dir):
            shutil.rmtree(self.test_vector_store_dir)

    def test_ingest_documents(self):
        ingest_documents(knowledge_base_dir=self.test_knowledge_base_dir, vector_store_dir=self.test_vector_store_dir)
        self.assertTrue(os.path.exists(self.test_vector_store_dir))
        self.assertTrue(os.path.exists(os.path.join(self.test_vector_store_dir, "index.faiss")))
        self.assertTrue(os.path.exists(os.path.join(self.test_vector_store_dir, "index.pkl")))

    def test_retriever_load_and_retrieve(self):
        # Ensure ingestion has run to create the vector store for this test
        ingest_documents(knowledge_base_dir=self.test_knowledge_base_dir, vector_store_dir=self.test_vector_store_dir)

        retriever = RAGRetriever(vector_store_dir=self.test_vector_store_dir)
        self.assertIsNotNone(retriever.vector_store)

        # Use a Portuguese query that is present in the dummy document
        query = "notificação por contacto pessoal" 
        relevant_docs = retriever.retrieve(query, k=1)
        self.assertEqual(len(relevant_docs), 1)
        self.assertIn("test legal article", relevant_docs[0].lower()) # Check for content from the dummy article

    def test_retriever_file_not_found(self):
        # The setUp method ensures the vector store is removed before this test
        with self.assertRaises(FileNotFoundError):
            RAGRetriever(vector_store_dir=self.test_vector_store_dir)

if __name__ == '__main__':
    unittest.main()
