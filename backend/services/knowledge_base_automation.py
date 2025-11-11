"""
Knowledge Base Maintenance Automation System
==========================================

This module provides comprehensive automation for knowledge base maintenance:
- Scheduled monitoring for new legal developments
- Automated document updates and version control
- Duplicate detection and removal system
- Knowledge base statistics and growth tracking
- Self-updating knowledge base with minimal manual intervention
- Performance monitoring and alerting

Target: Zero manual intervention for standard document processing
"""

import schedule
import time
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict, Counter
from sqlalchemy import create_engine, and_, or_, desc, func, text
from sqlalchemy.orm import sessionmaker
import threading
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import our systems
from .portuguese_legal_scraper import PortugueseLegalScraper
from .quality_scoring_system import QualityScoringEngine
from backend.app.models import LegalDocument, CaseOutcome

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MaintenanceSchedule:
    """Maintenance schedule configuration."""
    scraping_frequency: str = "daily"  # daily, weekly, monthly
    quality_assessment_frequency: str = "weekly"
    duplicate_check_frequency: str = "weekly"
    stats_update_frequency: str = "daily"
    backup_frequency: str = "weekly"
    cleanup_frequency: str = "monthly"

@dataclass
class KnowledgeBaseStats:
    """Comprehensive knowledge base statistics."""
    total_documents: int
    documents_by_source: Dict[str, int]
    documents_by_type: Dict[str, int]
    documents_by_jurisdiction: Dict[str, int]
    quality_distribution: Dict[str, int]
    growth_rate: float  # documents per day
    average_quality_score: float
    recent_additions: List[Dict[str, Any]]
    maintenance_metrics: Dict[str, Any]

class DuplicateDetector:
    """
    Advanced duplicate detection system for legal documents.
    
    Uses multiple approaches:
    1. Content similarity (TF-IDF + cosine similarity)
    2. Hash-based deduplication
    3. Metadata matching
    4. URL deduplication
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize duplicate detector.
        
        Args:
            similarity_threshold: Similarity threshold for considering documents duplicates
        """
        self.similarity_threshold = similarity_threshold
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=self._get_portuguese_stopwords(),
            ngram_range=(1, 2)
        )
        
    def _get_portuguese_stopwords(self) -> List[str]:
        """Get Portuguese stopwords for text processing."""
        return [
            'a', 'o', 'as', 'os', 'um', 'uma', 'uns', 'umas', 'de', 'da', 'do', 'das', 'dos',
            'em', 'na', 'no', 'nas', 'nos', 'por', 'para', 'com', 'sem', 'sobre',
            'que', 'qual', 'quais', 'cujo', 'cuja', 'cujos', 'cujas', 'quem', 'onde',
            'quando', 'como', 'porque', 'embora', 'se', 'caso', 'embora', 'pelo', 'pela'
        ]
    
    def find_duplicates(self, documents: List[LegalDocument]) -> Dict[int, List[int]]:
        """
        Find duplicate documents using multiple detection methods.
        
        Args:
            documents: List of LegalDocument objects
            
        Returns:
            Dictionary mapping primary document IDs to lists of duplicate IDs
        """
        logger.info(f"Starting duplicate detection for {len(documents)} documents")
        
        duplicates = {}
        processed_content_hashes = set()
        processed_urls = set()
        
        # Method 1: URL deduplication
        url_duplicates = self._find_url_duplicates(documents)
        
        # Method 2: Content hash deduplication
        hash_duplicates = self._find_hash_duplicates(documents)
        
        # Method 3: Content similarity deduplication
        similarity_duplicates = self._find_similarity_duplicates(documents)
        
        # Method 4: Metadata deduplication
        metadata_duplicates = self._find_metadata_duplicates(documents)
        
        # Combine all duplicate detection methods
        all_duplicates = {}
        
        # Add URL duplicates
        for primary_id, duplicate_list in url_duplicates.items():
            all_duplicates[primary_id] = duplicate_list
        
        # Add hash duplicates
        for primary_id, duplicate_list in hash_duplicates.items():
            if primary_id not in all_duplicates:
                all_duplicates[primary_id] = []
            all_duplicates[primary_id].extend(duplicate_list)
        
        # Add similarity duplicates
        for primary_id, duplicate_list in similarity_duplicates.items():
            if primary_id not in all_duplicates:
                all_duplicates[primary_id] = []
            all_duplicates[primary_id].extend(duplicate_list)
        
        # Remove duplicates from the duplicate lists
        for primary_id in all_duplicates:
            all_duplicates[primary_id] = list(set(all_duplicates[primary_id]))
        
        logger.info(f"Found duplicate groups: {len(all_duplicates)}")
        
        return all_duplicates
    
    def _find_url_duplicates(self, documents: List[LegalDocument]) -> Dict[int, List[int]]:
        """Find duplicates based on source URLs."""
        url_groups = defaultdict(list)
        
        for doc in documents:
            if doc.source_url:
                url_groups[doc.source_url].append(doc.id)
        
        duplicates = {}
        for url, doc_ids in url_groups.items():
            if len(doc_ids) > 1:
                primary_id = doc_ids[0]  # Keep first document
                duplicates[primary_id] = doc_ids[1:]  # Mark others as duplicates
        
        return duplicates
    
    def _find_hash_duplicates(self, documents: List[LegalDocument]) -> Dict[int, List[int]]:
        """Find duplicates based on content hashes."""
        content_hashes = defaultdict(list)
        
        for doc in documents:
            if doc.extracted_text:
                content_hash = hashlib.sha256(doc.extracted_text.encode()).hexdigest()
                content_hashes[content_hash].append(doc.id)
        
        duplicates = {}
        for content_hash, doc_ids in content_hashes.items():
            if len(doc_ids) > 1:
                primary_id = doc_ids[0]
                duplicates[primary_id] = doc_ids[1:]
        
        return duplicates
    
    def _find_similarity_duplicates(self, documents: List[LegalDocument]) -> Dict[int, List[int]]:
        """Find duplicates based on content similarity."""
        if len(documents) < 2:
            return {}
        
        # Prepare documents for similarity analysis
        valid_docs = [doc for doc in documents if doc.extracted_text and len(doc.extracted_text.strip()) > 50]
        
        if len(valid_docs) < 2:
            return {}
        
        # Extract content
        contents = [doc.extracted_text for doc in valid_docs]
        doc_ids = [doc.id for doc in valid_docs]
        
        # Calculate TF-IDF similarity matrix
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(contents)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            duplicates = {}
            
            # Find similar document pairs
            for i in range(len(valid_docs)):
                for j in range(i + 1, len(valid_docs)):
                    similarity = similarity_matrix[i][j]
                    
                    if similarity >= self.similarity_threshold:
                        primary_id = doc_ids[i]
                        duplicate_id = doc_ids[j]
                        
                        if primary_id not in duplicates:
                            duplicates[primary_id] = []
                        duplicates[primary_id].append(duplicate_id)
            
            return duplicates
            
        except Exception as e:
            logger.warning(f"Error in similarity duplicate detection: {e}")
            return {}
    
    def _find_metadata_duplicates(self, documents: List[LegalDocument]) -> Dict[int, List[int]]:
        """Find duplicates based on metadata similarity."""
        # Group by similar titles and publication dates
        title_date_groups = defaultdict(list)
        
        for doc in documents:
            if doc.title and doc.publication_date:
                # Create normalized title (remove extra spaces, convert to lowercase)
                normalized_title = ' '.join(doc.title.lower().split())
                key = f"{normalized_title}_{doc.publication_date.isoformat()}"
                title_date_groups[key].append(doc.id)
        
        duplicates = {}
        for key, doc_ids in title_date_groups.items():
            if len(doc_ids) > 1:
                primary_id = doc_ids[0]
                duplicates[primary_id] = doc_ids[1:]
        
        return duplicates

class KnowledgeBaseAutomation:
    """
    Main automation system for knowledge base maintenance.
    
    Coordinates:
    - Scheduled scraping
    - Quality assessment
    - Duplicate detection and removal
    - Statistics tracking
    - Performance monitoring
    - Alert systems
    """
    
    def __init__(self, database_url: str = "sqlite:///./sql_app.db",
                 config_path: str = "knowledge_base_config.json"):
        """
        Initialize Knowledge Base Automation system.
        
        Args:
            database_url: Database connection URL
            config_path: Path to configuration file
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.scraper = PortugueseLegalScraper(
            rate_limit_delay=self.config.get('rate_limit_delay', 2.0),
            max_retries=self.config.get('max_retries', 3),
            concurrent_workers=self.config.get('concurrent_workers', 3)
        )
        
        self.quality_engine = QualityScoringEngine(database_url)
        self.duplicate_detector = DuplicateDetector()
        
        # Setup logging
        self.setup_logging()
        
        # Initialize maintenance statistics
        self.maintenance_stats = {
            'last_scrape': None,
            'last_quality_assessment': None,
            'last_duplicate_cleanup': None,
            'documents_scraped': 0,
            'documents_quality_checked': 0,
            'duplicates_removed': 0,
            'errors_encountered': 0
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        default_config = {
            "rate_limit_delay": 2.0,
            "max_retries": 3,
            "concurrent_workers": 3,
            "daily_targets": {
                "documents_to_scrape": 50,
                "min_quality_threshold": 0.6,
                "similarity_threshold": 0.85
            },
            "email_alerts": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipient_email": ""
            },
            "backup": {
                "enabled": True,
                "backup_directory": "backups/",
                "max_backups": 10
            }
        }
        
        try:
            if Path(config_path).exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Merge with default config
                default_config.update(config)
                logger.info(f"Loaded configuration from {config_path}")
            else:
                logger.info(f"Using default configuration (config file not found at {config_path})")
        except Exception as e:
            logger.warning(f"Error loading configuration: {e}. Using defaults.")
        
        return default_config

    def setup_logging(self):
        """Setup detailed logging for maintenance operations."""
        log_dir = Path("logs/maintenance")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create file handler for maintenance logs
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"maintenance_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add to logger
        logger.addHandler(file_handler)

    def start_scheduled_maintenance(self):
        """Start scheduled maintenance tasks."""
        logger.info("Starting Knowledge Base Automation System")
        
        # Schedule tasks based on configuration
        daily_targets = self.config.get('daily_targets', {})
        
        # Daily tasks
        schedule.every().day.at("06:00").do(self._scheduled_scrape)
        schedule.every().day.at("12:00").do(self._scheduled_stats_update)
        schedule.every().day.at("18:00").do(self._scheduled_quality_check)
        
        # Weekly tasks
        schedule.every().monday.at("09:00").do(self._scheduled_duplicate_cleanup)
        schedule.every().sunday.at("20:00").do(self._scheduled_backup)
        
        # Monthly tasks
        schedule.every().month.do(self._scheduled_comprehensive_cleanup)
        
        logger.info("Scheduled maintenance tasks configured")
        
        # Start scheduler in a separate thread
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("Maintenance automation system started")

    def _run_scheduler(self):
        """Run the scheduler in a background thread."""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def _scheduled_scrape(self):
        """Scheduled daily scraping task."""
        logger.info("Starting scheduled daily scraping")
        
        try:
            # Scrape from all sources
            results = self.scraper.scrape_all_sources(
                max_documents=self.config['daily_targets']['documents_to_scrape']
            )
            
            # Process and save results
            self._process_scraped_documents(results)
            
            self.maintenance_stats['last_scrape'] = datetime.now()
            self.maintenance_stats['documents_scraped'] += sum(len(docs) for docs in results.values())
            
            logger.info("Scheduled scraping completed successfully")
            
        except Exception as e:
            logger.error(f"Scheduled scraping failed: {e}")
            self.maintenance_stats['errors_encountered'] += 1
            self._send_alert(f"Scheduled scraping failed: {e}")

    def _scheduled_quality_check(self):
        """Scheduled daily quality assessment."""
        logger.info("Starting scheduled quality assessment")
        
        try:
            # Get recent documents (last 7 days)
            cutoff_date = datetime.now() - timedelta(days=7)
            
            db = self.SessionLocal()
            try:
                recent_docs = db.query(LegalDocument).filter(
                    LegalDocument.retrieval_date >= cutoff_date
                ).all()
                
                if recent_docs:
                    # Run quality assessment
                    filtering_result = self.quality_engine.filter_documents_by_quality(
                        recent_docs,
                        threshold=self.config['daily_targets']['min_quality_threshold']
                    )
                    
                    # Save quality scores
                    self.quality_engine.save_quality_scores_to_database(recent_docs)
                    
                    self.maintenance_stats['last_quality_assessment'] = datetime.now()
                    self.maintenance_stats['documents_quality_checked'] += len(recent_docs)
                    
                    logger.info(f"Quality assessment completed: {len(recent_docs)} documents processed")
            
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Scheduled quality check failed: {e}")
            self.maintenance_stats['errors_encountered'] += 1
            self._send_alert(f"Scheduled quality check failed: {e}")

    def _scheduled_duplicate_cleanup(self):
        """Scheduled weekly duplicate cleanup."""
        logger.info("Starting scheduled duplicate cleanup")
        
        try:
            db = self.SessionLocal()
            try:
                # Get all documents for duplicate detection
                all_docs = db.query(LegalDocument).all()
                
                if len(all_docs) > 1:
                    # Find duplicates
                    duplicates = self.duplicate_detector.find_duplicates(all_docs)
                    
                    # Remove duplicates (keep highest quality document)
                    removed_count = 0
                    for primary_id, duplicate_ids in duplicates.items():
                        for duplicate_id in duplicate_ids:
                            # Check quality scores to decide which to keep
                            primary_doc = next((d for d in all_docs if d.id == primary_id), None)
                            duplicate_doc = next((d for d in all_docs if d.id == duplicate_id), None)
                            
                            if primary_doc and duplicate_doc:
                                # Remove lower quality document
                                if duplicate_doc.quality_score <= primary_doc.quality_score:
                                    db.delete(duplicate_doc)
                                    removed_count += 1
                    
                    db.commit()
                    self.maintenance_stats['duplicates_removed'] += removed_count
                    self.maintenance_stats['last_duplicate_cleanup'] = datetime.now()
                    
                    logger.info(f"Duplicate cleanup completed: {removed_count} duplicates removed")
            
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Scheduled duplicate cleanup failed: {e}")
            self.maintenance_stats['errors_encountered'] += 1
            self._send_alert(f"Scheduled duplicate cleanup failed: {e}")

    def _scheduled_stats_update(self):
        """Scheduled daily statistics update."""
        logger.info("Updating knowledge base statistics")
        
        try:
            stats = self.generate_comprehensive_stats()
            
            # Save stats to file
            stats_file = Path("knowledge_base/maintenance/stats.json")
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats.__dict__, f, indent=2, default=str)
            
            logger.info("Statistics updated successfully")
            
        except Exception as e:
            logger.error(f"Statistics update failed: {e}")
            self.maintenance_stats['errors_encountered'] += 1

    def _scheduled_backup(self):
        """Scheduled weekly backup."""
        logger.info("Starting scheduled backup")
        
        if not self.config.get('backup', {}).get('enabled', True):
            logger.info("Backup is disabled in configuration")
            return
        
        try:
            backup_dir = Path(self.config['backup']['backup_directory'])
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"knowledge_base_backup_{timestamp}"
            backup_path = backup_dir / backup_name
            
            # Create database backup
            db_backup_path = backup_path / "database.db"
            db_backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy database file
            import shutil
            shutil.copy2("sql_app.db", db_backup_path)
            
            # Copy knowledge base files
            kb_backup_path = backup_path / "knowledge_base"
            if Path("knowledge_base").exists():
                shutil.copytree("knowledge_base", kb_backup_path, dirs_exist_ok=True)
            
            # Copy vector store
            vector_backup_path = backup_path / "vector_store"
            if Path("vector_store").exists():
                shutil.copytree("vector_store", vector_backup_path, dirs_exist_ok=True)
            
            # Clean up old backups
            self._cleanup_old_backups(backup_dir)
            
            logger.info(f"Backup completed: {backup_path}")
            
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
            self.maintenance_stats['errors_encountered'] += 1
            self._send_alert(f"Scheduled backup failed: {e}")

    def _scheduled_comprehensive_cleanup(self):
        """Scheduled monthly comprehensive cleanup."""
        logger.info("Starting comprehensive monthly cleanup")
        
        try:
            db = self.SessionLocal()
            try:
                # Remove very old documents (> 5 years) that have low quality
                cutoff_date = datetime.now().date() - timedelta(days=1825)  # 5 years
                
                old_low_quality_docs = db.query(LegalDocument).filter(
                    and_(
                        LegalDocument.publication_date < cutoff_date,
                        LegalDocument.quality_score < 0.3
                    )
                ).all()
                
                removed_count = 0
                for doc in old_low_quality_docs:
                    db.delete(doc)
                    removed_count += 1
                
                db.commit()
                
                logger.info(f"Comprehensive cleanup completed: {removed_count} old documents removed")
            
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Comprehensive cleanup failed: {e}")
            self.maintenance_stats['errors_encountered'] += 1
            self._send_alert(f"Comprehensive cleanup failed: {e}")

    def _process_scraped_documents(self, results: Dict[str, List]):
        """Process and save scraped documents."""
        db = self.SessionLocal()
        try:
            for source, documents in results.items():
                for doc in documents:
                    # Check for duplicates before adding
                    existing_doc = db.query(LegalDocument).filter(
                        LegalDocument.source_url == doc.url
                    ).first()
                    
                    if not existing_doc:
                        # Add new document
                        db_doc = LegalDocument(
                            title=doc.title,
                            extracted_text=doc.content,
                            source_url=doc.url,
                            source=doc.source,
                            document_type=doc.document_type,
                            jurisdiction=doc.jurisdiction,
                            publication_date=doc.publication_date,
                            retrieval_date=doc.retrieval_date,
                            quality_score=doc.quality_score
                        )
                        
                        db.add(db_doc)
            
            db.commit()
            logger.info(f"Processed and saved {sum(len(docs) for docs in results.values())} new documents")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing scraped documents: {e}")
            raise
        finally:
            db.close()

    def _cleanup_old_backups(self, backup_dir: Path):
        """Clean up old backup files."""
        if not self.config.get('backup', {}).get('enabled', True):
            return
        
        max_backups = self.config['backup'].get('max_backups', 10)
        
        try:
            backup_files = list(backup_dir.glob("knowledge_base_backup_*"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove excess backups
            for backup_path in backup_files[max_backups:]:
                import shutil
                shutil.rmtree(backup_path)
                logger.info(f"Removed old backup: {backup_path}")
                
        except Exception as e:
            logger.warning(f"Error cleaning up old backups: {e}")

    def _send_alert(self, message: str):
        """Send email alert if configured."""
        email_config = self.config.get('email_alerts', {})
        
        if not email_config.get('enabled', False):
            return
        
        try:
            smtp_server = email_config.get('smtp_server')
            smtp_port = email_config.get('smtp_port', 587)
            sender_email = email_config.get('sender_email')
            sender_password = email_config.get('sender_password')
            recipient_email = email_config.get('recipient_email')
            
            if not all([smtp_server, sender_email, sender_password, recipient_email]):
                logger.warning("Email configuration incomplete, cannot send alert")
                return
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Knowledge Base Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            body = f"""
Knowledge Base Automation Alert

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Message: {message}

Maintenance Statistics:
- Last scrape: {self.maintenance_stats.get('last_scrape')}
- Documents scraped: {self.maintenance_stats['documents_scraped']}
- Documents quality checked: {self.maintenance_stats['documents_quality_checked']}
- Duplicates removed: {self.maintenance_stats['duplicates_removed']}
- Errors encountered: {self.maintenance_stats['errors_encountered']}

Best regards,
FineHero Knowledge Base Automation System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            
            logger.info("Alert email sent successfully")
            
        except Exception as e:
            logger.warning(f"Failed to send alert email: {e}")

    def generate_comprehensive_stats(self) -> KnowledgeBaseStats:
        """Generate comprehensive knowledge base statistics."""
        db = self.SessionLocal()
        try:
            # Basic counts
            total_documents = db.query(LegalDocument).count()
            
            # Distribution by source
            source_results = db.query(LegalDocument.source).all()
            documents_by_source = Counter(source for source, in source_results)
            
            # Distribution by type
            type_results = db.query(LegalDocument.document_type).all()
            documents_by_type = Counter(doc_type for doc_type, in type_results)
            
            # Distribution by jurisdiction
            jurisdiction_results = db.query(LegalDocument.jurisdiction).all()
            documents_by_jurisdiction = Counter(jurisdiction for jurisdiction, in jurisdiction_results)
            
            # Quality distribution
            quality_results = db.query(LegalDocument.quality_score).all()
            quality_scores = [score for score, in quality_results]
            
            quality_distribution = {
                'high': len([s for s in quality_scores if s >= 0.8]),
                'medium': len([s for s in quality_scores if 0.6 <= s < 0.8]),
                'low': len([s for s in quality_scores if 0.4 <= s < 0.6]),
                'very_low': len([s for s in quality_scores if s < 0.4])
            }
            
            # Calculate growth rate (documents per day over last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_docs = db.query(LegalDocument).filter(
                LegalDocument.retrieval_date >= thirty_days_ago
            ).count()
            growth_rate = recent_docs / 30.0
            
            # Recent additions (last 7 days)
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_additions = db.query(LegalDocument).filter(
                LegalDocument.retrieval_date >= seven_days_ago
            ).all()
            
            recent_additions_data = [
                {
                    'title': doc.title,
                    'source': doc.source,
                    'retrieval_date': doc.retrieval_date.isoformat(),
                    'quality_score': doc.quality_score
                }
                for doc in recent_additions
            ]
            
            # Average quality score
            average_quality_score = np.mean(quality_scores) if quality_scores else 0.0
            
            # Maintenance metrics
            maintenance_metrics = {
                'last_scrape': self.maintenance_stats.get('last_scrape'),
                'last_quality_assessment': self.maintenance_stats.get('last_quality_assessment'),
                'last_duplicate_cleanup': self.maintenance_stats.get('last_duplicate_cleanup'),
                'total_documents_scraped': self.maintenance_stats['documents_scraped'],
                'total_quality_checked': self.maintenance_stats['documents_quality_checked'],
                'total_duplicates_removed': self.maintenance_stats['duplicates_removed'],
                'total_errors_encountered': self.maintenance_stats['errors_encountered']
            }
            
            return KnowledgeBaseStats(
                total_documents=total_documents,
                documents_by_source=dict(documents_by_source),
                documents_by_type=dict(documents_by_type),
                documents_by_jurisdiction=dict(documents_by_jurisdiction),
                quality_distribution=quality_distribution,
                growth_rate=growth_rate,
                average_quality_score=average_quality_score,
                recent_additions=recent_additions_data,
                maintenance_metrics=maintenance_metrics
            )
            
        finally:
            db.close()

    def run_manual_maintenance_cycle(self):
        """Run a complete maintenance cycle manually."""
        logger.info("Starting manual maintenance cycle")
        
        try:
            # 1. Scrape new documents
            logger.info("Step 1: Scraping new documents")
            results = self.scraper.scrape_all_sources(
                max_documents=self.config['daily_targets']['documents_to_scrape']
            )
            self._process_scraped_documents(results)
            
            # 2. Quality assessment
            logger.info("Step 2: Quality assessment")
            db = self.SessionLocal()
            try:
                all_docs = db.query(LegalDocument).all()
                filtering_result = self.quality_engine.filter_documents_by_quality(
                    all_docs,
                    threshold=self.config['daily_targets']['min_quality_threshold']
                )
                self.quality_engine.save_quality_scores_to_database(all_docs)
            finally:
                db.close()
            
            # 3. Duplicate cleanup
            logger.info("Step 3: Duplicate cleanup")
            db = self.SessionLocal()
            try:
                all_docs = db.query(LegalDocument).all()
                duplicates = self.duplicate_detector.find_duplicates(all_docs)
                
                removed_count = 0
                for primary_id, duplicate_ids in duplicates.items():
                    primary_doc = next((d for d in all_docs if d.id == primary_id), None)
                    for duplicate_id in duplicate_ids:
                        duplicate_doc = next((d for d in all_docs if d.id == duplicate_id), None)
                        if primary_doc and duplicate_doc and duplicate_doc.quality_score <= primary_doc.quality_score:
                            db.delete(duplicate_doc)
                            removed_count += 1
                
                db.commit()
            finally:
                db.close()
            
            # 4. Update statistics
            logger.info("Step 4: Updating statistics")
            stats = self.generate_comprehensive_stats()
            
            logger.info(f"Manual maintenance cycle completed successfully")
            logger.info(f"Documents scraped: {sum(len(docs) for docs in results.values())}")
            logger.info(f"Duplicates removed: {removed_count}")
            logger.info(f"Total documents: {stats.total_documents}")
            logger.info(f"Average quality score: {stats.average_quality_score:.3f}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Manual maintenance cycle failed: {e}")
            self.maintenance_stats['errors_encountered'] += 1
            raise

if __name__ == "__main__":
    # Example usage
    automation = KnowledgeBaseAutomation()
    
    # Run manual maintenance cycle
    stats = automation.run_manual_maintenance_cycle()
    
    # Print comprehensive statistics
    print("Knowledge Base Statistics:")
    print(f"Total documents: {stats.total_documents}")
    print(f"Growth rate: {stats.growth_rate:.2f} documents/day")
    print(f"Average quality score: {stats.average_quality_score:.3f}")
    print(f"Documents by source: {stats.documents_by_source}")
    print(f"Quality distribution: {stats.quality_distribution}")
    
    # To start automated maintenance:
    # automation.start_scheduled_maintenance()
    # while True:
    #     time.sleep(1)