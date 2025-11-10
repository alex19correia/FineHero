# Retrieval-Augmented Generation (RAG) Module

This directory contains the core components for the FineHero AI's Retrieval-Augmented Generation (RAG) system. The RAG module is designed to enhance the AI-powered contestation of traffic fines by combining structured knowledge retrieval with generative AI, ensuring legal accuracy and reducing hallucinations.

## Purpose

The primary goal of this module is to:
- Ingest and index legal documents, traffic regulations, and example defenses.
- Retrieve relevant legal context for a given traffic fine.
- Inject this context into prompts for the Gemini CLI to generate accurate and legally grounded administrative defenses.

## Components

### `rag/ingest.py`

This script is responsible for processing raw legal documents, splitting them into manageable chunks, generating vector embeddings, and storing these embeddings in a local FAISS vector store.

**How it works:**
1.  **Document Loading:** Reads `.txt` files from the `knowledge_base/` directory.
2.  **Text Splitting:** Uses `RecursiveCharacterTextSplitter` to break down documents into chunks (currently ~500 tokens with 50 token overlap).
3.  **Embedding Generation:** Utilizes `HuggingFaceEmbeddings` (model: `all-MiniLM-L6-v2`) to create vector representations of each chunk.
4.  **Vector Store Creation & Storage:** Builds a FAISS vector store from the chunks and their embeddings, saving it to the `vector_store/` directory.

**To run the ingestion process:**
```bash
python rag/ingest.py --ingest
```

### `rag/retriever.py`

This module provides functionality to load the pre-built FAISS vector store and perform similarity searches to retrieve the most relevant legal document chunks for a given query.

**How it works:**
1.  **Vector Store Loading:** Loads the FAISS index and the associated embedding model from the `vector_store/` directory.
2.  **Similarity Search:** Takes a natural language query and returns the top-K most semantically similar document chunks from the vector store.

**Example Usage (within another Python script):**
```python
from rag.retriever import RAGRetriever

retriever = RAGRetriever()
query = "notificação de multas de trânsito"
relevant_docs = retriever.retrieve(query, k=3)
for doc_content in relevant_docs:
    print(doc_content)
```

## Integration

The `RAGRetriever` is integrated into `backend/services/defense_generator.py`. Before generating a prompt for the Gemini CLI, the `DefenseGenerator` uses the retriever to fetch relevant legal context based on the fine details. This context is then included in the prompt, enabling the AI to generate more informed and legally accurate defenses.

## Current Status & Future Enhancements

The core RAG mechanism is established. Future enhancements include:

*   **Metadata and Filtering:** Implement advanced filtering of retrieved documents based on legal type, date, and jurisdiction.
*   **PDF Ingestion:** Extend `rag/ingest.py` to directly process PDF documents from the `knowledge_base/` directory.
*   **CLI for RAG Testing:** Add dedicated CLI commands for testing RAG functionality.
*   **Prompt Refinement:** Further refine the system prompt to enforce strict legal structure and citation.
*   **Active Learning Loop:** Fully develop the active learning loop to incorporate user feedback for continuous improvement of RAG and defense generation.
*   **Database Integration:** Integrate storage of extracted data, generated defenses, and user history with the database.
*   **Comprehensive Logging:** Implement detailed logging across all RAG components.
