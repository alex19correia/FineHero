# Knowledge Base Automation Instructions

## Objective
Automate the discovery, collection, and organization of Portuguese traffic fine data including fines, complaints, winning/losing cases, and successful defense letters to build a comprehensive RAG knowledge base.

## Current Status
- Basic RAG infrastructure exists with FAISS vector store and HuggingFace embeddings.
- Single legal article (artigo_135.txt) in knowledge base.
- Initial web scraping infrastructure (`backend/services/web_scraper.py`) is in place, with a base `WebScraper` class and a placeholder for ANSR.
- Database models (`backend/app/models.py`) have been extended with a `Document` model for metadata and quality tracking.
- `rag/ingest.py` has been enhanced to support metadata tagging and initial quality scoring, and to ingest documents into the database and vector store.
- CLI commands (`cli/main.py`) for web scraping and knowledge base ingestion are implemented.

## Implementation Steps

### 1. Web Scraping Infrastructure (Ongoing)
- **Libraries**: requests, beautifulsoup4, selenium (for JavaScript-heavy sites)
- **Target Sources**:
  - ANSR official website and databases (initial placeholder implemented)
  - **Implement specific scrapers for:**
    - Diario da Republica (Government gazettes for new regulations)
    - Portuguese court decision databases (Citius, DGSI)
  - Legal forums and attorney resources (Future)
- **Rate Limiting**: Respectful scraping with delays and user-agent rotation (Implemented in base `WebScraper`)
- **Error Handling**: Robust retry mechanisms and failure logging (Implemented in base `WebScraper`)

### 2. Data Collection Pipeline (Ongoing)
- **Document Discovery**: Automated crawling of legal websites and databases (Integrated with CLI)
- **Content Extraction**: PDF download, HTML parsing, and text extraction (PDF download implemented, text extraction from PDFs needs to be integrated)
- **Deduplication**: Remove duplicate documents and cases (Future)
- **Language Filtering**: Focus on Portuguese content with optional English translations (Future)

### 3. Metadata Enrichment (Ongoing)
- **Automatic Tagging**:
  - Document type (law, precedent, defense, regulation)
  - Jurisdiction (Portugal, specific regions)
  - Date and legal period
  - Case outcome (successful defense, fine upheld, etc.)
  - Legal arguments and citations used
- **Quality Scoring**: Relevance to traffic fines, recency, authority level (Initial implementation in `rag/ingest.py`)

### 4. RAG Enhancement (Next Focus)
- **Advanced Chunking**: Legal document-aware text splitting (preserve article/paragraph structure)
- **Multi-modal Embeddings**: Consider domain-specific legal embeddings
- **Metadata Filtering**: Enable retrieval based on case outcomes, jurisdictions, dates
- **Hybrid Search**: Combine semantic search with keyword filtering

### 5. Integration with Existing System (Ongoing)
- **Database Storage**: Extend models to include document metadata and quality scores (Initial `Document` model implemented)
  - **Extend `backend/app/models.py` with `LegalDocument`, `CaseOutcome`, and `DefenseTemplate` models.**
  - **Create corresponding database migration scripts.**
- **API Endpoints**: Add endpoints for knowledge base management and statistics (Future)
- **CLI Commands**: Add commands for manual data ingestion and automated collection (Implemented)
- **Monitoring Dashboard**: Track knowledge base growth and quality metrics (Future)

## Expected Outcomes
- **Comprehensive Knowledge Base**: Thousands of legal documents, cases, and defense examples
- **High-Quality RAG**: Accurate, contextually relevant legal information retrieval
- **Automated Maintenance**: Self-updating knowledge base with new legal developments
- **Scalable Architecture**: Easy addition of new data sources and document types

## Legal and Ethical Considerations
- **Data Usage Rights**: Ensure compliance with website terms and copyright laws
- **Rate Limiting**: Respectful scraping practices to avoid service disruption
- **Data Privacy**: Handle personal information appropriately in court documents
- **Attribution**: Maintain source attribution for legal documents

## Testing and Validation
- **Data Quality**: Automated checks for document completeness and relevance
- **RAG Performance**: A/B testing of retrieval accuracy with expanded knowledge base
- **Legal Accuracy**: Validation of retrieved information against official sources
- **Performance Monitoring**: Track ingestion speed, storage efficiency, and query response times

## Success Metrics
- **Coverage**: Percentage of common traffic violations with precedent data
- **Accuracy**: Reduction in hallucinations and improvement in legal citation accuracy
- **Freshness**: Average age of documents in knowledge base
- **Usage**: Query success rate and user satisfaction with retrieved information