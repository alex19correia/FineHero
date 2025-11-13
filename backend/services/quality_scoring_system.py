"""
Automated Quality Scoring & Filtering System for Legal Documents
================================================================

This module provides comprehensive document quality assessment and filtering capabilities:
- Multi-factor quality scoring algorithm (content, recency, authority, relevance)
- Automated filtering of low-quality content (80%+ reduction target)
- Continuous learning loop for quality improvement
- Legal authority and recency scoring
- Performance tracking and analytics
- A/B testing framework for quality thresholds

Target: 95% document quality classification accuracy
"""

import numpy as np
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from collections import defaultdict, Counter
from pathlib import Path
import hashlib
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine, and_, or_, desc, func
from sqlalchemy.orm import sessionmaker

# Import models
from backend.app.models import LegalDocument, CaseOutcome

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Quality metrics breakdown for a document."""
    overall_score: float
    content_quality: float
    relevance_score: float
    authority_score: float
    freshness_score: float
    completeness_score: float
    legal_accuracy_score: float
    source_reliability: float

@dataclass
class FilteringResult:
    """Result of quality filtering process."""
    total_documents: int
    high_quality_documents: int
    medium_quality_documents: int
    low_quality_documents: int
    filtered_out_documents: List[int]
    quality_distribution: Dict[str, int]
    average_quality_scores: Dict[str, float]

class QualityScoringEngine:
    """
    Advanced quality scoring engine for Portuguese legal documents.
    
    Implements multi-factor scoring based on:
    - Content quality (structure, completeness, language)
    - Legal relevance (traffic fine focus, citations)
    - Authority scoring (source reliability, legal standing)
    - Recency scoring (publication date, legal validity)
    - Completeness scoring (metadata, references)
    - Legal accuracy (citations, references validation)
    """
    
    def __init__(self, database_url: str = "sqlite:///./sql_app.db"):
        """
        Initialize the Quality Scoring Engine.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Quality thresholds
        self.quality_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        
        # Portuguese legal authority sources (weighted by reliability)
        self.authority_sources = {
            'ANSR': 0.95,  # Highest authority for traffic regulations
            'Diário da República': 0.90,  # Official government publication
            'DGSI': 0.85,  # Court decisions (high but not always current law)
            'Governo': 0.80,
            'Ministério': 0.75,
            'CM Lisboa': 0.70,  # Municipal sources
            'Other': 0.50
        }
        
        # Legal relevance keywords (traffic fine specific)
        self.legal_keywords = {
            'primary': [
                'multa', 'contraordenação', 'trânsito', 'código da estrada',
                'estacionamento', 'velocidade', 'limite', 'sinalização',
                'veículo', 'automóvel', 'infraçção', 'penalidade'
            ],
            'secondary': [
                'autoridade', 'segurança', 'rodoviária', 'ANS', 'fiscalização',
                'notificação', 'auto', 'decisão', 'recurso', 'defesa'
            ],
            'procedural': [
                'procedimento', 'tramitação', 'prazo', 'competência',
                'notificação', 'citação', 'coima', 'pagamento'
            ]
        }
        
        # Citation patterns for legal accuracy
        self.citation_patterns = {
            'article': r'artigo\s+(\d+(?:-\d+)?)\s*[º°]?',
            'law': r'(?:lei|decreto-lei)\s+n\.?\s*(\d+(?:\.\d+)*)',
            'regulation': r'portaria\s+n\.?\s*(\d+(?:\.\d+)*)',
            'court_case': r'(?:acórdão|decisão)\s+(?:do\s+)?([^\s,;]+)'
        }
        
        # Initialize TF-IDF vectorizer for content similarity
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=self._get_portuguese_stopwords(),
            ngram_range=(1, 2)
        )
        
        # Quality model features (for machine learning enhancement)
        self.feature_weights = {
            'content_length': 0.15,
            'keyword_density': 0.25,
            'citation_count': 0.20,
            'structural_elements': 0.15,
            'source_authority': 0.25
        }

    def _get_portuguese_stopwords(self) -> List[str]:
        """Get Portuguese stopwords for text processing."""
        return [
            'a', 'o', 'as', 'os', 'um', 'uma', 'uns', 'umas', 'de', 'da', 'do', 'das', 'dos',
            'em', 'na', 'no', 'nas', 'nos', 'por', 'para', 'com', 'sem', 'sobre',
            'que', 'qual', 'quais', 'cujo', 'cuja', 'cujos', 'cujas', 'quem', 'onde',
            'quando', 'como', 'porque', 'embora', 'se', 'caso', 'embora', 'pelo', 'pela',
            'este', 'esta', 'estes', 'estas', 'esse', 'essa', 'esses', 'essas',
            'aquele', 'aquela', 'aqueles', 'aquelas', 'todo', 'toda', 'todos', 'todas'
        ]

    def calculate_comprehensive_quality_score(self, document: LegalDocument) -> QualityMetrics:
        """
        Calculates a comprehensive quality score for a given legal document by aggregating
        scores from various sub-assessments. Each sub-assessment evaluates a specific aspect
        of the document's quality, relevance, and reliability.
        
        Args:
            document: The LegalDocument object for which to calculate the quality score.
            
        Returns:
            A QualityMetrics object containing the overall score and a breakdown of
            individual quality components.
        """
        logger.info(f"Calculating quality score for document: {document.title}")
        
        # 1. Content quality assessment: Evaluates the structural integrity, length,
        #    and linguistic quality of the document's text.
        content_quality = self._assess_content_quality(document.extracted_text)
        
        # 2. Legal relevance scoring: Determines how pertinent the document's content is
        #    to the domain of traffic fine defense, based on keyword analysis.
        relevance_score = self._assess_legal_relevance(document.extracted_text)
        
        # 3. Authority scoring: Assesses the trustworthiness and official standing of the
        #    document's source (e.g., ANSR, Diário da República).
        authority_score = self._assess_authority_score(document.source)
        
        # 4. Freshness scoring: Evaluates the recency of the document, as legal validity
        #    can be time-sensitive.
        freshness_score = self._assess_freshness_score(document.publication_date)
        
        # 5. Completeness scoring: Checks if essential metadata (title, URL, date, etc.)
        #    is present, indicating a well-formed and usable document.
        completeness_score = self._assess_completeness(document)
        
        # 6. Legal accuracy scoring: Analyzes the presence and proper formatting of
        #    legal citations and references within the text.
        legal_accuracy_score = self._assess_legal_accuracy(document.extracted_text)
        
        # 7. Source reliability: A more granular assessment of the source's overall
        #    dependability, potentially incorporating external factors.
        source_reliability = self._assess_source_reliability(document)
        
        # Define weights for each quality component. These weights are heuristics
        # and can be tuned based on domain expertise or machine learning.
        weights = {
            'content': 0.25,
            'relevance': 0.30,
            'authority': 0.20,
            'freshness': 0.10,
            'completeness': 0.10,
            'accuracy': 0.05
        }
        
        # Calculate the overall weighted score.
        overall_score = (
            content_quality * weights['content'] +
            relevance_score * weights['relevance'] +
            authority_score * weights['authority'] +
            freshness_score * weights['freshness'] +
            completeness_score * weights['completeness'] +
            legal_accuracy_score * weights['accuracy']
        )
        
        # Assemble all calculated metrics into a QualityMetrics object.
        metrics = QualityMetrics(
            overall_score=overall_score,
            content_quality=content_quality,
            relevance_score=relevance_score,
            authority_score=authority_score,
            freshness_score=freshness_score,
            completeness_score=completeness_score,
            legal_accuracy_score=legal_accuracy_score,
            source_reliability=source_reliability
        )
        
        logger.info(f"Quality scores for {document.title}: Overall={overall_score:.3f}, "
                   f"Relevance={relevance_score:.3f}, Authority={authority_score:.3f}")
        
        return metrics

    def _assess_content_quality(self, content: str) -> float:
        """
        Assesses the quality of the document's content based on its length,
        the presence of structural legal elements, and typical Portuguese legal phrasing.
        
        Args:
            content: The extracted text content of the legal document.
            
        Returns:
            A float score between 0.0 and 1.0 representing content quality.
        """
        if not content:
            return 0.0
        
        content_lower = content.lower()
        
        # 1. Length quality (40% contribution to content quality)
        # Documents within a certain length range are considered more complete and informative.
        length_score = 0.0
        content_length = len(content.strip())
        
        if 500 <= content_length <= 5000: # Optimal length range
            length_score = 1.0
        elif content_length >= 200:       # Sufficient length
            length_score = 0.7
        elif content_length >= 100:       # Minimal length
            length_score = 0.4
        else:                             # Very short content
            length_score = 0.1
        
        # 2. Structural elements score (30% contribution to content quality)
        # Presence of legal structural markers (articles, chapters, etc.) indicates
        # a well-formatted and official legal document.
        structural_score = 0.0
        structural_elements = [
            r'artigo\s+\d+',  # Articles (e.g., "Artigo 123")
            r'capítulo',      # Chapters
            r'secção',        # Sections
            r'§\s*\d+',       # Paragraphs (e.g., "§ 1")
            r'\[.*?\]'        # Common pattern for references or annotations
        ]
        
        # Count matches for each structural pattern
        structure_matches = sum(len(re.findall(pattern, content_lower)) for pattern in structural_elements)
        # Score is capped at 1.0, with each match contributing 0.1 (heuristic)
        structural_score = min(1.0, structure_matches * 0.1)
        
        # 3. Language quality (30% contribution to content quality)
        # Presence of typical legal phrases in Portuguese indicates formal legal language.
        language_score = 0.0
        legal_phrases = [
            'nos termos', 'de acordo com', 'em conformidade', 'face ao',
            'considerando que', 'determina-se', 'estabelece-se'
        ]
        
        phrase_matches = sum(1 for phrase in legal_phrases if phrase in content_lower)
        # Score is capped at 1.0, with each phrase match contributing 0.15 (heuristic)
        language_score = min(1.0, phrase_matches * 0.15)
        
        # Combine the three sub-scores with their respective weights for content quality.
        return (length_score * 0.4 + structural_score * 0.3 + language_score * 0.3)

    def _assess_legal_relevance(self, content: str) -> float:
        """
        Assesses the legal relevance of the document's content to traffic fine defense
        by analyzing the presence and density of specific keywords. Keywords are categorized
        into primary, secondary, and procedural, each contributing differently to the score.
        
        Args:
            content: The extracted text content of the legal document.
            
        Returns:
            A float score between 0.0 and 1.0 representing legal relevance.
        """
        if not content:
            return 0.0
        
        content_lower = content.lower()
        words = content_lower.split()
        total_words = len(words)
        
        if total_words == 0:
            return 0.0
        
        # 1. Primary keywords (highest weight): Directly related to traffic fines and violations.
        primary_matches = sum(1 for keyword in self.legal_keywords['primary'] 
                            if keyword in content_lower)
        primary_score = min(1.0, primary_matches * 0.2) # Each match contributes, capped at 1.0
        
        # 2. Secondary keywords: Related to legal authority, enforcement, and safety.
        secondary_matches = sum(1 for keyword in self.legal_keywords['secondary'] 
                              if keyword in content_lower)
        secondary_score = min(0.8, secondary_matches * 0.15) # Capped at 0.8
        
        # 3. Procedural keywords: Related to legal processes, notifications, and appeals.
        procedural_matches = sum(1 for keyword in self.legal_keywords['procedural'] 
                               if keyword in content_lower)
        procedural_score = min(0.6, procedural_matches * 0.1) # Capped at 0.6
        
        # Calculate keyword density: The proportion of relevant keywords in the document.
        keyword_density = (primary_matches + secondary_matches + procedural_matches) / total_words * 100
        
        # Density score: A higher density indicates more focused content.
        density_score = min(1.0, keyword_density / 2.0)  # Heuristic: 2% density = full score
        
        # Combine the scores from different keyword categories and density.
        return (primary_score * 0.5 + secondary_score * 0.3 + 
                procedural_score * 0.1 + density_score * 0.1)

    def _assess_authority_score(self, source: str) -> float:
        """Assess document authority based on source reliability."""
        source_lower = source.lower()
        
        for source_name, score in self.authority_sources.items():
            if source_name.lower() in source_lower:
                return score
        
        # Default authority for unknown sources
        return 0.3

    def _assess_freshness_score(self, publication_date: Optional[date]) -> float:
        """Assess document freshness based on publication date."""
        if not publication_date:
            return 0.3  # Default for documents without dates
        
        days_old = (datetime.now().date() - publication_date).days
        
        # Freshness scoring based on legal document lifecycle
        if days_old <= 365:    # Within 1 year = highest freshness
            return 1.0
        elif days_old <= 730:  # 1-2 years = high freshness
            return 0.8
        elif days_old <= 1825:  # 2-5 years = medium freshness
            return 0.6
        elif days_old <= 3650:  # 5-10 years = low freshness
            return 0.4
        else:                   # Over 10 years = very low freshness
            return 0.2

    def _assess_completeness(self, document: LegalDocument) -> float:
        """Assess document completeness based on metadata and content."""
        score = 0.0
        
        # Title completeness
        if document.title and len(document.title.strip()) > 10:
            score += 0.2
        
        # Source URL completeness
        if document.source_url:
            score += 0.15
        
        # Publication date completeness
        if document.publication_date:
            score += 0.15
        
        # Jurisdiction completeness
        if document.jurisdiction:
            score += 0.1
        
        # Document type completeness
        if document.document_type:
            score += 0.1
        
        # Content completeness (already assessed in content quality)
        if document.extracted_text and len(document.extracted_text.strip()) > 200:
            score += 0.3
        
        return min(1.0, score)

    def _assess_legal_accuracy(self, content: str) -> float:
        """
        Assesses the legal accuracy of the document by analyzing the presence and
        correct formatting of legal citations and references.
        
        Args:
            content: The extracted text content of the legal document.
            
        Returns:
            A float score between 0.0 and 1.0 representing legal accuracy.
        """
        if not content:
            return 0.0
        
        content_lower = content.lower()
        accuracy_score = 0.0
        
        # 1. Citation analysis: Count how many legal citations are present.
        citation_count = 0
        for pattern_type, pattern in self.citation_patterns.items():
            citations = re.findall(pattern, content_lower)
            citation_count += len(citations)
        
        # Score based on citation density: An optimal number of citations suggests good accuracy.
        # Too few might mean lack of legal grounding, too many might mean verbosity without substance.
        if 1 <= citation_count <= 10: # Optimal range for citations
            accuracy_score = 0.8
        elif citation_count == 0:     # No citations, low accuracy
            accuracy_score = 0.3  
        elif citation_count <= 20:    # Moderate number of citations
            accuracy_score = 0.6
        else:                         # Potentially excessive citations
            accuracy_score = 0.4  
        
        # 2. Legal reference accuracy: Verify if numerical references are associated with legal terms.
        legal_numbers = re.findall(r'\b\d+(?:-\d+)?\b', content) # Find all numbers that could be legal references
        proper_legal_refs = sum(1 for num in legal_numbers if 
                              re.search(rf'\b{num}\b.*(?:artigo|lei|decreto)', content_lower))
        
        # Adjust accuracy score based on the proportion of proper legal references.
        if legal_numbers:
            reference_accuracy = proper_legal_refs / len(legal_numbers)
            accuracy_score = (accuracy_score + reference_accuracy) / 2 # Average with citation score
        
        return accuracy_score

    def _assess_source_reliability(self, document: LegalDocument) -> float:
        """Assess overall source reliability."""
        # Base reliability from authority scoring
        base_reliability = self._assess_authority_score(document.source)
        
        # Bonus for official sources
        if any(official in document.source.lower() for official in 
               ['ansr', 'diário da república', 'governo', 'minister']):
            base_reliability += 0.1
        
        # Penalty for documents without proper metadata
        if not document.publication_date or not document.source_url:
            base_reliability -= 0.2
        
        return max(0.0, min(1.0, base_reliability))

    def filter_documents_by_quality(self, documents: List[LegalDocument], 
                                  threshold: float = 0.6) -> FilteringResult:
        """
        Filter documents based on quality scores.
        
        Args:
            documents: List of LegalDocument objects
            threshold: Quality threshold (documents below this score are filtered out)
            
        Returns:
            FilteringResult with detailed filtering statistics
        """
        logger.info(f"Filtering {len(documents)} documents with threshold {threshold}")
        
        high_quality = []
        medium_quality = []
        low_quality = []
        filtered_out = []
        
        quality_scores = []
        
        for doc in documents:
            metrics = self.calculate_comprehensive_quality_score(doc)
            
            # Update document with new quality score
            doc.quality_score = metrics.overall_score
            
            quality_scores.append(metrics.overall_score)
            
            if metrics.overall_score >= self.quality_thresholds['high']:
                high_quality.append(doc)
            elif metrics.overall_score >= self.quality_thresholds['medium']:
                medium_quality.append(doc)
            elif metrics.overall_score >= threshold:
                low_quality.append(doc)
            else:
                filtered_out.append(doc.id)
        
        # Calculate distribution statistics
        distribution = {
            'high': len(high_quality),
            'medium': len(medium_quality),
            'low': len(low_quality),
            'filtered': len(filtered_out)
        }
        
        # Calculate average scores by category
        avg_scores = {}
        for category, docs in [('high', high_quality), ('medium', medium_quality), ('low', low_quality)]:
            if docs:
                avg_scores[f'{category}_avg'] = np.mean([doc.quality_score for doc in docs])
        
        result = FilteringResult(
            total_documents=len(documents),
            high_quality_documents=len(high_quality),
            medium_quality_documents=len(medium_quality),
            low_quality_documents=len(low_quality),
            filtered_out_documents=filtered_out,
            quality_distribution=distribution,
            average_quality_scores=avg_scores
        )
        
        # Calculate filtering effectiveness
        total_filtered = len(filtered_out)
        filter_percentage = (total_filtered / len(documents)) * 100 if documents else 0
        
        logger.info(f"Quality filtering completed: {total_filtered}/{len(documents)} "
                   f"documents filtered out ({filter_percentage:.1f}%)")
        
        return result

    def save_quality_scores_to_database(self, documents: List[LegalDocument]) -> None:
        """Save calculated quality scores to database."""
        db = self.SessionLocal()
        try:
            for doc in documents:
                metrics = self.calculate_comprehensive_quality_score(doc)
                
                # Update document in database
                db_doc = db.query(LegalDocument).filter(LegalDocument.id == doc.id).first()
                if db_doc:
                    db_doc.quality_score = metrics.overall_score
                    db_doc.relevance_score = metrics.relevance_score
                    db_doc.freshness_score = metrics.freshness_score
                    db_doc.authority_score = metrics.authority_score
            
            db.commit()
            logger.info(f"Quality scores saved to database for {len(documents)} documents")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving quality scores to database: {e}")
        finally:
            db.close()

    def batch_quality_assessment(self, batch_size: int = 100) -> Dict[str, Any]:
        """Perform batch quality assessment on all documents in database."""
        logger.info("Starting batch quality assessment")
        
        db = self.SessionLocal()
        try:
            # Get all documents
            total_docs = db.query(LegalDocument).count()
            logger.info(f"Found {total_docs} documents for quality assessment")
            
            processed_docs = []
            batch_count = 0
            
            # Process in batches
            for offset in range(0, total_docs, batch_size):
                batch_count += 1
                logger.info(f"Processing batch {batch_count} (offset {offset})")
                
                documents = db.query(LegalDocument).offset(offset).limit(batch_size).all()
                
                for doc in documents:
                    metrics = self.calculate_comprehensive_quality_score(doc)
                    
                    # Update document
                    doc.quality_score = metrics.overall_score
                    doc.relevance_score = metrics.relevance_score
                    doc.freshness_score = metrics.freshness_score
                    doc.authority_score = metrics.authority_score
                    
                    processed_docs.append(doc)
                
                # Commit batch
                db.commit()
            
            # Generate quality report
            quality_distribution = self._analyze_quality_distribution(processed_docs)
            
            report = {
                'total_documents_processed': len(processed_docs),
                'quality_distribution': quality_distribution,
                'average_quality_score': np.mean([doc.quality_score for doc in processed_docs]),
                'processing_date': datetime.now().isoformat()
            }
            
            logger.info(f"Batch quality assessment completed: {len(processed_docs)} documents processed")
            
            return report
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in batch quality assessment: {e}")
            raise
        finally:
            db.close()

    def _analyze_quality_distribution(self, documents: List[LegalDocument]) -> Dict[str, Any]:
        """Analyze quality score distribution across documents."""
        if not documents:
            return {}
        
        scores = [doc.quality_score for doc in documents]
        
        distribution = {
            'total': len(scores),
            'high_quality': len([s for s in scores if s >= self.quality_thresholds['high']]),
            'medium_quality': len([s for s in scores if self.quality_thresholds['medium'] <= s < self.quality_thresholds['high']]),
            'low_quality': len([s for s in scores if s < self.quality_thresholds['medium']]),
            'statistics': {
                'mean': np.mean(scores),
                'median': np.median(scores),
                'std': np.std(scores),
                'min': np.min(scores),
                'max': np.max(scores),
                'percentile_25': np.percentile(scores, 25),
                'percentile_75': np.percentile(scores, 75)
            }
        }
        
        return distribution

    def continuous_learning_update(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Updates the quality scoring model based on user feedback, enabling a continuous
        learning loop. This function analyzes feedback patterns to dynamically adjust
        quality thresholds and potentially feature weights, making the scoring system
        more adaptive and accurate over time.
        
        Args:
            feedback_data: A list of dictionaries, where each dictionary contains user
                           feedback for a document, including 'document_id', 'rating', and 'reason'.
            
        Returns:
            A dictionary containing statistics about the learning update, including
            processed feedback entries, updated thresholds, and feature weights.
        """
        logger.info(f"Processing {len(feedback_data)} feedback entries for continuous learning")
        
        # 1. Analyze feedback patterns: Categorize feedback into positive/negative
        #    and calculate average quality scores for each category.
        feedback_analysis = self._analyze_feedback_patterns(feedback_data)
        
        # 2. Update quality thresholds: Adjust the 'high', 'medium', and 'low' quality
        #    thresholds based on the insights from user feedback. This makes the system
        #    more aligned with user perception of quality.
        updated_thresholds = self._update_quality_thresholds(feedback_analysis)
        
        # 3. Update feature weights: (Placeholder for a more advanced ML-driven approach)
        #    In a production system, this step would involve training a machine learning
        #    model to adjust the weights of different quality features based on how
        #    they correlate with positive or negative user feedback.
        updated_weights = self._update_feature_weights(feedback_data)
        
        # Compile statistics about the learning update.
        learning_stats = {
            'feedback_entries_processed': len(feedback_data),
            'quality_distribution_feedback': feedback_analysis,
            'updated_thresholds': updated_thresholds,
            'updated_feature_weights': updated_weights,
            'learning_date': datetime.now().isoformat()
        }
        
        logger.info("Continuous learning update completed")
        
        return learning_stats

    def _analyze_feedback_patterns(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in user feedback."""
        positive_ratings = [f for f in feedback_data if f.get('rating', 0) >= 4]
        negative_ratings = [f for f in feedback_data if f.get('rating', 0) <= 2]
        
        # Analyze quality scores of positively/negatively rated documents
        positive_scores = []
        negative_scores = []
        
        db = self.SessionLocal()
        try:
            for feedback in feedback_data:
                doc_id = feedback.get('document_id')
                if doc_id:
                    doc = db.query(LegalDocument).filter(LegalDocument.id == doc_id).first()
                    if doc:
                        if feedback.get('rating', 0) >= 4:
                            positive_scores.append(doc.quality_score)
                        else:
                            negative_scores.append(doc.quality_score)
        finally:
            db.close()
        
        analysis = {
            'positive_feedback_count': len(positive_ratings),
            'negative_feedback_count': len(negative_ratings),
            'positive_documents_avg_quality': np.mean(positive_scores) if positive_scores else 0,
            'negative_documents_avg_quality': np.mean(negative_scores) if negative_scores else 0,
            'quality_threshold_feedback_ratio': len(positive_scores) / len(negative_scores) if negative_scores else float('inf')
        }
        
        return analysis

    def _update_quality_thresholds(self, feedback_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Update quality thresholds based on feedback analysis."""
        # Get feedback-based quality scores
        positive_avg = feedback_analysis.get('positive_documents_avg_quality', 0.7)
        negative_avg = feedback_analysis.get('negative_documents_avg_quality', 0.4)
        
        # Adjust thresholds based on feedback
        # High threshold should be slightly below average of positively rated documents
        new_high_threshold = max(0.7, min(0.9, positive_avg * 0.9))
        
        # Medium threshold should be between high and low
        new_medium_threshold = max(0.5, min(0.7, (positive_avg + negative_avg) / 2))
        
        updated_thresholds = {
            'high': new_high_threshold,
            'medium': new_medium_threshold,
            'low': max(0.3, new_medium_threshold * 0.7)
        }
        
        # Update instance thresholds
        self.quality_thresholds.update(updated_thresholds)
        
        return updated_thresholds

    def _update_feature_weights(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Update feature weights based on feedback."""
        # This is a simplified approach - in production, use machine learning
        # For now, adjust weights slightly based on document success patterns
        
        db = self.SessionLocal()
        try:
            successful_docs = []
            unsuccessful_docs = []
            
            for feedback in feedback_data:
                doc_id = feedback.get('document_id')
                if doc_id and feedback.get('rating', 0) >= 4:
                    doc = db.query(LegalDocument).filter(LegalDocument.id == doc_id).first()
                    if doc:
                        successful_docs.append(doc)
                elif doc_id and feedback.get('rating', 0) <= 2:
                    doc = db.query(LegalDocument).filter(LegalDocument.id == doc_id).first()
                    if doc:
                        unsuccessful_docs.append(doc)
            
            # Analyze differences between successful and unsuccessful documents
            if successful_docs and unsuccessful_docs:
                # Adjust weights based on patterns
                # This is a simplified heuristic approach
                pass  # In a full implementation, use ML models here
            
            return self.feature_weights.copy()
            
        finally:
            db.close()

if __name__ == "__main__":
    # Example usage
    quality_engine = QualityScoringEngine()
    
    # Get documents from database
    db = quality_engine.SessionLocal()
    try:
        documents = db.query(LegalDocument).limit(10).all()
        
        # Perform quality assessment
        filtering_result = quality_engine.filter_documents_by_quality(documents, threshold=0.6)
        
        print("Quality Filtering Results:")
        print(f"Total documents: {filtering_result.total_documents}")
        print(f"High quality: {filtering_result.high_quality_documents}")
        print(f"Medium quality: {filtering_result.medium_quality_documents}")
        print(f"Low quality: {filtering_result.low_quality_documents}")
        print(f"Filtered out: {len(filtering_result.filtered_out_documents)}")
        
        # Save quality scores
        quality_engine.save_quality_scores_to_database(documents)
        
        print("Quality scoring completed!")
        
    finally:
        db.close()