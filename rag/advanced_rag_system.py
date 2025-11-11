"""
Advanced RAG System for Portuguese Legal Documents
=================================================

This module provides enhanced RAG capabilities specifically designed for Portuguese legal documents:
- Multi-modal embeddings for legal document processing
- Hybrid search (semantic + keyword filtering)
- Metadata filtering based on case outcomes, jurisdictions, dates
- Legal document-aware text chunking
- Advanced similarity scoring and ranking
- Performance optimization for legal queries

Target: 90%+ relevance score for legal case retrieval, <3-second query response
"""

import numpy as np
import re
import json
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from pathlib import Path
import logging
from collections import defaultdict, Counter
import hashlib

# Import existing components
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine, and_, or_, desc
from sqlalchemy.orm import sessionmaker
from backend.app.models import LegalDocument, CaseOutcome

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LegalQueryContext:
    """Context object for legal queries with metadata and filtering."""
    query: str
    document_types: Optional[List[str]] = None
    jurisdictions: Optional[List[str]] = None
    date_range: Optional[Tuple[date, date]] = None
    case_outcomes: Optional[List[str]] = None
    min_quality_score: float = 0.0
    max_results: int = 5

@dataclass
class SearchResult:
    """Enhanced search result with relevance scoring."""
    content: str
    document_id: int
    title: str
    source: str
    document_type: str
    jurisdiction: str
    publication_date: Optional[date]
    relevance_score: float
    semantic_score: float
    keyword_score: float
    metadata_bonus: float
    quality_score: float

class LegalDocumentChunker:
    """
    Legal document-aware text chunking that preserves article/paragraph structure.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the legal document chunker.
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks for context preservation
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Portuguese legal document patterns
        self.article_patterns = [
            r'artigo\s+(\d+(?:-\d+)?)\s*[º°]?',  # "Artigo 123º"
            r'art\.\s*(\d+(?:-\d+)?)',  # "Art. 123"
            r'Artigo\s+(\d+(?:-\d+)?)',  # "Artigo 123"
        ]
        
        self.paragraph_patterns = [
            r'(\d+)\.\s*[–—\-]',  # "1. —"
            r'(\d+)\)\s*[–—\-]',  # "1) —"
            r'(\d+)\.\s',  # "1. "
        ]
        
        self.section_patterns = [
            r'(CAPÍTULO|SECÇÃO|TÍTULO)\s+[IVX\d]+',  # "CAPÍTULO I"
            r'(Secção|Secção)\s+\d+',  # "Secção 1"
        ]

    def chunk_legal_document(self, text: str, document_type: str = "law") -> List[Dict[str, Any]]:
        """
        Split legal document into chunks while preserving structure.
        
        Args:
            text: Full document text
            document_type: Type of legal document
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        # Try structural splitting first
        if document_type in ["law", "regulation", "decree"]:
            chunks = self._chunk_by_legal_structure(text)
        else:
            chunks = self._chunk_by_paragraphs(text)
        
        # Process each chunk
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_text = chunk["text"].strip()
            
            if len(chunk_text) < 50:  # Skip very short chunks
                continue
                
            # Extract legal references
            legal_refs = self._extract_legal_references(chunk_text)
            
            # Calculate chunk importance
            importance = self._calculate_chunk_importance(chunk_text, document_type)
            
            processed_chunks.append({
                "content": chunk_text,
                "chunk_id": f"{hashlib.md5(chunk_text.encode()).hexdigest()[:8]}",
                "start_position": chunk.get("start", 0),
                "end_position": chunk.get("end", len(chunk_text)),
                "document_structure": chunk.get("structure", "unknown"),
                "legal_references": legal_refs,
                "importance_score": importance,
                "chunk_index": i
            })
        
        return processed_chunks

    def _chunk_by_legal_structure(self, text: str) -> List[Dict[str, Any]]:
        """Split text by legal document structure (articles, sections)."""
        chunks = []
        current_chunk = ""
        current_structure = "preamble"
        start_pos = 0
        
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line_pos = text.find(line, start_pos)
            
            # Check for article markers
            is_article = any(re.search(pattern, line, re.IGNORECASE) for pattern in self.article_patterns)
            
            # Check for section markers
            is_section = any(re.search(pattern, line, re.IGNORECASE) for pattern in self.section_patterns)
            
            if is_article or is_section:
                # Save current chunk if it has content
                if current_chunk.strip():
                    chunks.append({
                        "text": current_chunk.strip(),
                        "structure": current_structure,
                        "start": start_pos,
                        "end": line_pos
                    })
                
                # Start new chunk
                current_chunk = line + "\n"
                current_structure = "article" if is_article else "section"
                start_pos = line_pos
            else:
                current_chunk += line + "\n"
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "structure": current_structure,
                "start": start_pos,
                "end": len(text)
            })
        
        return chunks

    def _chunk_by_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        """Split text by paragraphs with intelligent merging."""
        chunks = []
        current_chunk = ""
        start_pos = 0
        
        paragraphs = re.split(r'\n\s*\n', text)
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Check if adding this paragraph would exceed chunk size
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "structure": "paragraph",
                    "start": start_pos,
                    "end": start_pos + len(current_chunk)
                })
                current_chunk = para[:self.chunk_overlap]  # Keep overlap
                start_pos += len(current_chunk) - self.chunk_overlap
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "structure": "paragraph",
                "start": start_pos,
                "end": start_pos + len(current_chunk)
            })
        
        return chunks

    def _extract_legal_references(self, text: str) -> Dict[str, List[str]]:
        """Extract legal references from text."""
        references = {
            "articles": [],
            "laws": [],
            "regulations": [],
            "citations": []
        }
        
        # Extract article references
        for pattern in self.article_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references["articles"].extend(matches)
        
        # Extract law references (e.g., "Lei 23/2006")
        law_pattern = r'lei\s+(\d+(?:\.\d+)*\/\d{4})'
        law_matches = re.findall(law_pattern, text, re.IGNORECASE)
        references["laws"].extend(law_matches)
        
        # Extract regulation references
        reg_pattern = r'(decreto\s+[^\s]+|portaria\s+[^\s]+)'
        reg_matches = re.findall(reg_pattern, text, re.IGNORECASE)
        references["regulations"].extend(reg_matches)
        
        return references

    def _calculate_chunk_importance(self, text: str, document_type: str) -> float:
        """Calculate importance score for a chunk."""
        importance = 0.0
        
        # Base importance on length (longer chunks often more important)
        importance += min(0.3, len(text) / 3000)
        
        # Boost importance for key legal terms
        legal_keywords = {
            "law": ["artigo", "lei", "disposição", "regra"],
            "regulation": ["portaria", "decreto", "norma", "procedimento"],
            "court_decision": ["tribunal", "juiz", "acórdão", "decisão"],
            "defense": ["argumento", "fundamentação", "direito", "violação"]
        }
        
        keywords = legal_keywords.get(document_type, legal_keywords["law"])
        text_lower = text.lower()
        
        keyword_count = sum(1 for keyword in keywords if keyword in text_lower)
        importance += min(0.4, keyword_count * 0.1)
        
        # Boost for structural elements
        if re.search(r'artigo\s+\d+', text_lower):
            importance += 0.2
        
        if re.search(r'art\.\s*\d+', text_lower):
            importance += 0.2
        
        # Boost for specific legal numbers (article, paragraph)
        numbers = re.findall(r'\b\d+\b', text)
        importance += min(0.1, len(numbers) * 0.01)
        
        return min(1.0, importance)

class AdvancedRAGRetriever:
    """
    Advanced RAG system with hybrid search, metadata filtering, and legal-specific processing.
    """
    
    def __init__(self, vector_store_dir: str = "vector_store", 
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the Advanced RAG Retriever.
        
        Args:
            vector_store_dir: Directory containing FAISS vector store
            embedding_model: HuggingFace embedding model name
        """
        self.vector_store_dir = vector_store_dir
        self.embedding_model_name = embedding_model
        
        # Load vector store
        self._load_vector_store()
        
        # Setup database
        self.engine = create_engine("sqlite:///./sql_app.db")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize legal document chunker
        self.chunker = LegalDocumentChunker()
        
        # Setup keyword search
        self._setup_keyword_search()
        
        # Legal query expansion
        self.legal_synonyms = {
            "multa": ["contraordenação", "penalidade", "coima"],
            "estacionamento": ["parque", "paragem"],
            "velocidade": ["rapidez", "limite"],
            "sinal": ["sinalização", "indicação"],
            "veículo": ["automóvel", "carro", "viatura"]
        }

    def _load_vector_store(self):
        """Load FAISS vector store with embeddings."""
        if not Path(self.vector_store_dir).exists():
            raise FileNotFoundError(f"Vector store not found at '{self.vector_store_dir}'")
        
        logger.info(f"Loading vector store from '{self.vector_store_dir}'...")
        self.embedding_model = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
        self.vector_store = FAISS.load_local(
            self.vector_store_dir, 
            self.embedding_model,
            allow_dangerous_deserialization=True
        )
        logger.info("Vector store loaded successfully")

    def _setup_keyword_search(self):
        """Setup keyword-based search capabilities."""
        # Portuguese legal stopwords
        self.stopwords = {
            'a', 'o', 'as', 'os', 'um', 'uma', 'uns', 'umas', 'de', 'da', 'do', 'das', 'dos',
            'em', 'na', 'no', 'nas', 'nos', 'por', 'para', 'com', 'sem', 'por', 'sobre',
            'que', 'qual', 'quais', 'cujo', 'cuja', 'cujos', 'cujas', 'quem', 'onde',
            'quando', 'como', 'porque', 'embora', 'se', 'caso', 'embora', 'pelo', 'pela'
        }

    def _expand_legal_query(self, query: str) -> List[str]:
        """Expand query with legal synonyms and related terms."""
        expanded_queries = [query.lower()]
        query_words = query.lower().split()
        
        for word in query_words:
            if word in self.legal_synonyms:
                for synonym in self.legal_synonyms[word]:
                    new_query = query.lower().replace(word, synonym)
                    if new_query not in expanded_queries:
                        expanded_queries.append(new_query)
        
        return expanded_queries

    def _calculate_keyword_score(self, text: str, query: str) -> float:
        """Calculate keyword-based relevance score."""
        text_lower = text.lower()
        query_lower = query.lower()
        
        # Basic term frequency
        query_words = [word for word in query_lower.split() if word not in self.stopwords]
        if not query_words:
            return 0.0
        
        matches = sum(1 for word in query_words if word in text_lower)
        base_score = matches / len(query_words)
        
        # Boost for exact phrases
        if query_lower in text_lower:
            base_score += 0.3
        
        # Boost for legal terms in legal context
        legal_boost = 0.0
        legal_terms = ['artigo', 'lei', 'decreto', 'portaria', 'multa', 'contraordenação']
        legal_matches = sum(1 for term in legal_terms if term in text_lower)
        legal_boost = legal_matches * 0.1
        
        return min(1.0, base_score + legal_boost)

    def _apply_metadata_filters(self, documents: List[LegalDocument], 
                               context: LegalQueryContext) -> List[LegalDocument]:
        """Apply metadata filtering to documents."""
        filtered_docs = documents
        
        # Filter by document types
        if context.document_types:
            filtered_docs = [doc for doc in filtered_docs 
                           if doc.document_type in context.document_types]
        
        # Filter by jurisdictions
        if context.jurisdictions:
            filtered_docs = [doc for doc in filtered_docs 
                           if doc.jurisdiction in context.jurisdictions]
        
        # Filter by quality score
        if context.min_quality_score > 0:
            filtered_docs = [doc for doc in filtered_docs 
                           if doc.quality_score >= context.min_quality_score]
        
        # Filter by date range
        if context.date_range:
            start_date, end_date = context.date_range
            filtered_docs = [doc for doc in filtered_docs 
                           if doc.publication_date and 
                           start_date <= doc.publication_date <= end_date]
        
        # Filter by case outcomes
        if context.case_outcomes:
            db = self.SessionLocal()
            try:
                outcome_types = [outcome.lower() for outcome in context.case_outcomes]
                doc_ids = set()
                
                for outcome_type in outcome_types:
                    outcomes = db.query(CaseOutcome).filter(
                        CaseOutcome.outcome_type.ilike(f"%{outcome_type}%")
                    ).all()
                    doc_ids.update(outcome.legal_documents for outcome in outcomes)
                
                filtered_docs = [doc for doc in filtered_docs if doc.id in doc_ids]
            finally:
                db.close()
        
        return filtered_docs

    def _calculate_final_relevance_score(self, semantic_score: float, keyword_score: float, 
                                       metadata_bonus: float, quality_score: float, 
                                       context_relevance: float) -> float:
        """Calculate final relevance score combining multiple factors."""
        # Weights for different score components
        weights = {
            'semantic': 0.4,    # Semantic similarity (40%)
            'keyword': 0.25,    # Keyword matching (25%)
            'quality': 0.2,     # Document quality (20%)
            'metadata': 0.1,    # Metadata relevance (10%)
            'context': 0.05     # Query context match (5%)
        }
        
        # Combine scores with weights
        final_score = (
            semantic_score * weights['semantic'] +
            keyword_score * weights['keyword'] +
            quality_score * weights['quality'] +
            metadata_bonus * weights['metadata'] +
            context_relevance * weights['context']
        )
        
        return min(1.0, final_score)

    def retrieve_with_context(self, context: LegalQueryContext) -> List[SearchResult]:
        """
        Retrieve documents using advanced RAG with metadata filtering and hybrid search.
        
        Args:
            context: LegalQueryContext containing query and filters
            
        Returns:
            List of SearchResult objects ranked by relevance
        """
        logger.info(f"Starting advanced retrieval for query: '{context.query}'")
        
        # Expand query with legal synonyms
        expanded_queries = self._expand_legal_query(context.query)
        
        all_results = []
        
        for expanded_query in expanded_queries:
            logger.info(f"Processing expanded query: '{expanded_query}'")
            
            # Semantic search
            logger.info("Performing semantic search...")
            semantic_docs_with_scores = self.vector_store.similarity_search_with_score(
                expanded_query, 
                k=context.max_results * 3  # Get more to filter later
            )
            
            # Keyword search
            logger.info("Performing keyword search...")
            keyword_results = self._keyword_search(expanded_query, context.max_results * 2)
            
            # Get database documents for metadata
            db = self.SessionLocal()
            try:
                documents = db.query(LegalDocument).all()
                
                # Create document lookup
                doc_lookup = {doc.id: doc for doc in documents}
                
                # Process semantic results
                for doc, semantic_score in semantic_docs_with_scores:
                    if "document_id" not in doc.metadata:
                        continue
                    
                    document_id = doc.metadata["document_id"]
                    db_doc = doc_lookup.get(document_id)
                    
                    if not db_doc:
                        continue
                    
                    # Calculate keyword score
                    keyword_score = self._calculate_keyword_score(doc.page_content, expanded_query)
                    
                    # Calculate metadata bonus
                    metadata_bonus = self._calculate_metadata_bonus(db_doc, context)
                    
                    # Calculate final relevance score
                    final_score = self._calculate_final_relevance_score(
                        semantic_score=semantic_score,
                        keyword_score=keyword_score,
                        metadata_bonus=metadata_bonus,
                        quality_score=db_doc.quality_score,
                        context_relevance=self._calculate_context_relevance(doc.page_content, context)
                    )
                    
                    search_result = SearchResult(
                        content=doc.page_content,
                        document_id=document_id,
                        title=db_doc.title,
                        source=db_doc.source,
                        document_type=db_doc.document_type,
                        jurisdiction=db_doc.jurisdiction,
                        publication_date=db_doc.publication_date,
                        relevance_score=final_score,
                        semantic_score=semantic_score,
                        keyword_score=keyword_score,
                        metadata_bonus=metadata_bonus,
                        quality_score=db_doc.quality_score
                    )
                    
                    all_results.append(search_result)
                
                # Add keyword-only results (semantic score = 0)
                for keyword_result in keyword_results:
                    if keyword_result["document_id"] not in [r.document_id for r in all_results]:
                        db_doc = doc_lookup.get(keyword_result["document_id"])
                        if db_doc:
                            search_result = SearchResult(
                                content=keyword_result["content"],
                                document_id=keyword_result["document_id"],
                                title=db_doc.title,
                                source=db_doc.source,
                                document_type=db_doc.document_type,
                                jurisdiction=db_doc.jurisdiction,
                                publication_date=db_doc.publication_date,
                                relevance_score=keyword_result["keyword_score"] * 0.8,  # Penalize semantic-only results
                                semantic_score=0.0,
                                keyword_score=keyword_result["keyword_score"],
                                metadata_bonus=self._calculate_metadata_bonus(db_doc, context),
                                quality_score=db_doc.quality_score
                            )
                            all_results.append(search_result)
            
            finally:
                db.close()
        
        # Remove duplicates and sort by relevance
        unique_results = {}
        for result in all_results:
            if result.document_id not in unique_results or result.relevance_score > unique_results[result.document_id].relevance_score:
                unique_results[result.document_id] = result
        
        # Apply metadata filters
        if context.document_types or context.jurisdictions or context.date_range or context.case_outcomes:
            filtered_results = []
            db = self.SessionLocal()
            try:
                documents = db.query(LegalDocument).all()
                doc_lookup = {doc.id: doc for doc in documents}
                
                for result in unique_results.values():
                    db_doc = doc_lookup.get(result.document_id)
                    if db_doc and self._document_matches_filters(db_doc, context):
                        filtered_results.append(result)
                
                unique_results = {r.document_id: r for r in filtered_results}
            finally:
                db.close()
        
        # Sort by relevance and return top results
        final_results = sorted(
            unique_results.values(), 
            key=lambda x: x.relevance_score, 
            reverse=True
        )[:context.max_results]
        
        logger.info(f"Retrieved {len(final_results)} results with average relevance: {np.mean([r.relevance_score for r in final_results]):.3f}")
        
        return final_results

    def _keyword_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform keyword-based search."""
        db = self.SessionLocal()
        try:
            # Get all documents and their content
            documents = db.query(LegalDocument).all()
            
            keyword_results = []
            for doc in documents:
                # Get chunked content (would need to be stored or retrieved from vector store)
                # For now, use extracted_text field
                content = doc.extracted_text or ""
                
                keyword_score = self._calculate_keyword_score(content, query)
                
                if keyword_score > 0.1:  # Minimum relevance threshold
                    keyword_results.append({
                        "document_id": doc.id,
                        "content": content[:1000],  # Truncate for performance
                        "keyword_score": keyword_score
                    })
            
            # Sort by keyword score and return top results
            keyword_results.sort(key=lambda x: x["keyword_score"], reverse=True)
            return keyword_results[:max_results]
            
        finally:
            db.close()

    def _calculate_metadata_bonus(self, doc: LegalDocument, context: LegalQueryContext) -> float:
        """Calculate bonus score based on metadata relevance."""
        bonus = 0.0
        
        # Bonus for exact type match
        if context.document_types and doc.document_type in context.document_types:
            bonus += 0.3
        
        # Bonus for jurisdiction match
        if context.jurisdictions and doc.jurisdiction in context.jurisdictions:
            bonus += 0.2
        
        # Bonus for recency
        if doc.publication_date:
            days_old = (datetime.now().date() - doc.publication_date).days
            if days_old <= 365:  # Less than 1 year
                bonus += 0.2
            elif days_old <= 730:  # Less than 2 years
                bonus += 0.1
        
        return min(0.5, bonus)

    def _calculate_context_relevance(self, content: str, context: LegalQueryContext) -> float:
        """Calculate relevance based on query context."""
        content_lower = content.lower()
        query_lower = context.query.lower()
        
        # Check for context-specific terms
        context_terms = []
        
        if context.case_outcomes:
            for outcome in context.case_outcomes:
                context_terms.extend(outcome.lower().split())
        
        if context.document_types:
            context_terms.extend([dt.lower() for dt in context.document_types])
        
        if context.jurisdictions:
            context_terms.extend([j.lower() for j in context.jurisdictions])
        
        matches = sum(1 for term in context_terms if term in content_lower)
        return min(0.5, matches * 0.1)

    def _document_matches_filters(self, doc: LegalDocument, context: LegalQueryContext) -> bool:
        """Check if document matches all specified filters."""
        # Document type filter
        if context.document_types and doc.document_type not in context.document_types:
            return False
        
        # Jurisdiction filter
        if context.jurisdictions and doc.jurisdiction not in context.jurisdictions:
            return False
        
        # Quality filter
        if context.min_quality_score > 0 and doc.quality_score < context.min_quality_score:
            return False
        
        # Date range filter
        if context.date_range:
            start_date, end_date = context.date_range
            if not doc.publication_date or not (start_date <= doc.publication_date <= end_date):
                return False
        
        # Case outcome filter
        if context.case_outcomes:
            db = self.SessionLocal()
            try:
                outcome_types = [outcome.lower() for outcome in context.case_outcomes]
                has_matching_outcome = False
                
                for outcome_type in outcome_types:
                    outcomes = db.query(CaseOutcome).filter(
                        and_(
                            CaseOutcome.legal_documents.any(LegalDocument.id == doc.id),
                            CaseOutcome.outcome_type.ilike(f"%{outcome_type}%")
                        )
                    ).all()
                    if outcomes:
                        has_matching_outcome = True
                        break
                
                if not has_matching_outcome:
                    return False
            finally:
                db.close()
        
        return True

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get comprehensive knowledge base statistics."""
        db = self.SessionLocal()
        try:
            total_docs = db.query(LegalDocument).count()
            
            # Document type distribution
            doc_types = db.query(LegalDocument.document_type).all()
            type_distribution = Counter(doc_type for doc_type, in doc_types)
            
            # Jurisdiction distribution
            jurisdictions = db.query(LegalDocument.jurisdiction).all()
            jurisdiction_distribution = Counter(jurisdiction for jurisdiction, in jurisdictions)
            
            # Quality score statistics
            quality_scores = db.query(LegalDocument.quality_score).all()
            avg_quality = np.mean([score for score, in quality_scores]) if quality_scores else 0
            
            # Publication date distribution
            recent_docs = db.query(LegalDocument).filter(
                LegalDocument.publication_date >= (datetime.now().date() - timedelta(days=365))
            ).count()
            
            return {
                "total_documents": total_docs,
                "document_types": dict(type_distribution),
                "jurisdictions": dict(jurisdiction_distribution),
                "average_quality_score": avg_quality,
                "recent_documents_365_days": recent_docs,
                "coverage_percentage": (recent_docs / total_docs * 100) if total_docs > 0 else 0
            }
        finally:
            db.close()

if __name__ == "__main__":
    # Example usage
    retriever = AdvancedRAGRetriever()
    
    # Create query context
    context = LegalQueryContext(
        query="multa de estacionamento artigo 135",
        document_types=["law", "regulation"],
        jurisdictions=["Portugal"],
        min_quality_score=0.6,
        max_results=5
    )
    
    # Retrieve documents
    results = retriever.retrieve_with_context(context)
    
    # Display results
    print(f"Retrieved {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title}")
        print(f"   Source: {result.source}")
        print(f"   Type: {result.document_type}")
        print(f"   Relevance: {result.relevance_score:.3f}")
        print(f"   Content preview: {result.content[:200]}...")
        print()
    
    # Get knowledge base stats
    stats = retriever.get_knowledge_base_stats()
    print("Knowledge Base Statistics:")
    print(json.dumps(stats, indent=2, default=str))