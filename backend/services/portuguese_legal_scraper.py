"""
Advanced Portuguese Legal Document Scraper for FineHero Knowledge Base
=====================================================================

This module provides comprehensive scraping capabilities for Portuguese legal databases:
- ANSR (Autoridade Nacional de Segurança Rodoviária) - Traffic regulations and fines
- Diário da República - Official government gazette
- DGSI (Diário da República Digital) - Court decisions and legal precedents

Features:
- Robust error handling and retry mechanisms
- Rate limiting with exponential backoff
- Multi-modal document extraction (PDF, HTML)
- Advanced legal document parsing
- Quality scoring and metadata enrichment
- Duplicate detection and filtering
- Automated text extraction and preprocessing

Target: 500+ legal documents collected weekly with 95% accuracy
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import hashlib
import re
import json
import os
from urllib.parse import urljoin, urlparse, quote
from typing import List, Dict, Optional, Callable, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import PyPDF2
from pdfplumber import PDF
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LegalDocument:
    """Data class for legal document metadata and content."""
    title: str
    content: str
    url: str
    source: str
    document_type: str
    jurisdiction: str
    publication_date: Optional[date]
    retrieval_date: datetime
    file_path: Optional[str] = None
    metadata: Dict = None
    quality_score: float = 0.0
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class PortugueseLegalScraper:
    """
    Advanced Portuguese Legal Document Scraper with comprehensive error handling,
    rate limiting, and document processing capabilities.
    """
    
    def __init__(self, rate_limit_delay: float = 2.0, max_retries: int = 3, 
                 concurrent_workers: int = 3, download_dir: str = "downloads/legal_docs"):
        """
        Initialize the Portuguese Legal Scraper.
        
        Args:
            rate_limit_delay: Minimum delay between requests in seconds
            max_retries: Maximum number of retry attempts for failed requests
            concurrent_workers: Number of concurrent workers for document processing
            download_dir: Directory for storing downloaded documents
        """
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.concurrent_workers = concurrent_workers
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup session with retry strategy
        self.session = self._setup_session()
        
        # Document tracking for deduplication
        self.seen_urls = set()
        self.processed_hashes = set()
        
        # Portuguese legal document patterns
        self.date_patterns = [
            r'(\d{1,2})\s+de\s+([a-zA-Z]+)\s+de\s+(\d{4})',  # "15 de janeiro de 2024"
            r'(\d{4})-(\d{2})-(\d{2})',  # ISO format
            r'(\d{2})\/(\d{2})\/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})\.(\d{2})\.(\d{4})'  # DD.MM.YYYY
        ]
        
        # Legal article patterns for traffic fines
        self.traffic_patterns = {
            'speed_limit': r'artigo\s+([\d]+)\s*-\s*([\d]+)',
            'parking': r'estacionamento',
            'red_light': r'luz\s+(vermelha|vermelha)',
            'mobile_phone': r'telefone.*mobil',
            'seatbelt': r'cinto.*seguranç'
        }

    def _setup_session(self) -> requests.Session:
        """Setup HTTP session with retry strategy and appropriate headers."""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Portuguese-focused headers
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        
        return session

    def _make_request(self, url: str, method: str = "GET", data: Optional[Dict] = None, 
                     use_selenium: bool = False) -> Optional[requests.Response]:
        """
        Make HTTP request with comprehensive error handling and rate limiting.
        This function handles retries, exponential backoff, and checks for already processed URLs.
        
        Args:
            url: Target URL for the HTTP request.
            method: HTTP method to use (GET or POST). Defaults to "GET".
            data: Request payload for POST requests.
            use_selenium: If True, uses Selenium for JavaScript-heavy pages.
            
        Returns:
            Response object if the request is successful and content type is HTML or PDF,
            otherwise None.
        """
        # Check if the URL has already been processed to avoid redundant requests
        if url in self.seen_urls:
            logger.info(f"Skipping already processed URL: {url}")
            return None
            
        # Apply rate limiting delay to avoid overwhelming the server
        time.sleep(random.uniform(self.rate_limit_delay * 0.5, self.rate_limit_delay * 1.5))
        
        # Attempt the request multiple times with retries
        for attempt in range(self.max_retries):
            try:
                # Use Selenium if specified for dynamic content
                if use_selenium:
                    # Selenium returns page source directly, not a requests.Response object
                    # This needs to be handled by the caller or converted if a uniform return is desired
                    return self._selenium_request(url)
                elif method.upper() == "GET":
                    response = self.session.get(url, timeout=15)
                elif method.upper() == "POST":
                    response = self.session.post(url, data=data, timeout=15)
                else:
                    logger.warning(f"Unsupported HTTP method: {method}")
                    return None
                
                # Raise an HTTPError for bad responses (4xx or 5xx)
                response.raise_for_status()
                
                # Check if response is HTML or PDF, as these are the expected document types
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type or 'application/xhtml+xml' in content_type:
                    self.seen_urls.add(url) # Mark URL as seen only on successful HTML/XHTML retrieval
                    return response
                elif 'application/pdf' in content_type:
                    self.seen_urls.add(url) # Mark URL as seen only on successful PDF retrieval
                    return response
                else:
                    logger.warning(f"Unexpected content type for {url}: {content_type}")
                    return None
                    
            except (requests.exceptions.RequestException, TimeoutException) as e:
                # Log warning for failed attempts and apply exponential backoff
                logger.warning(f"Request to {url} failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    return None # All retries exhausted
                time.sleep(2 ** attempt)  # Exponential backoff
                    
        return None

    def _selenium_request(self, url: str) -> Optional[str]:
        """
        Use Selenium for JavaScript-heavy pages that cannot be scraped with direct HTTP requests.
        Configures a headless Chrome browser to fetch the fully rendered page source.
        
        Args:
            url: The URL to fetch using Selenium.
            
        Returns:
            The page source (HTML) as a string if successful, otherwise None.
        """
        try:
            # Configure Chrome options for headless execution
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run Chrome in headless mode (without GUI)
            chrome_options.add_argument("--no-sandbox") # Required for running in some environments (e.g., Docker)
            chrome_options.add_argument("--disable-dev-shm-usage") # Overcomes limited resource problems in Docker
            chrome_options.add_argument("--disable-gpu") # Advised for headless mode
            
            # Initialize the Chrome WebDriver
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(15) # Set a timeout for the page to load
            driver.get(url) # Navigate to the specified URL
            
            # Wait for dynamic content to be present on the page.
            # This is crucial for JavaScript-rendered content to ensure the page is fully loaded.
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            page_source = driver.page_source # Get the fully rendered HTML content
            driver.quit() # Close the browser
            
            return page_source
            
        except Exception as e:
            logger.error(f"Selenium request failed for {url}: {e}")
            return None

    def _extract_publication_date(self, text: str) -> Optional[date]:
        """
        Extracts a publication date from a given text, supporting various Portuguese and ISO date formats.
        It iterates through predefined patterns and attempts to parse the date.
        
        Args:
            text: The text content from which to extract the date.
            
        Returns:
            A datetime.date object if a date is successfully extracted, otherwise None.
        """
        text_lower = text.lower()
        
        # Iterate through each defined date pattern
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    # Handle different date formats based on the pattern structure
                    if 'de' in text_lower:  # Portuguese format like "15 de janeiro de 2024"
                        match = matches[0] if isinstance(matches[0], tuple) else matches[0]
                        day, month_pt, year = match
                        
                        # Map Portuguese month names to their numerical representation
                        months_pt = {
                            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
                            'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
                            'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
                        }
                        
                        month = months_pt.get(month_pt, 1) # Default to 1 if month not found (shouldn't happen with good patterns)
                        return date(int(year), month, int(day))
                    else:  # ISO (YYYY-MM-DD) or DD/MM/YYYY, DD.MM.YYYY formats
                        match = matches[0] if isinstance(matches[0], tuple) else matches[0]
                        if len(match) == 3:
                            # Assuming order is YYYY, MM, DD or DD, MM, YYYY based on pattern
                            # For simplicity, assuming the pattern itself ensures correct order
                            year, month, day = match
                            return date(int(year), int(month), int(day))
                except (ValueError, KeyError):
                    # Continue to the next pattern if parsing fails for the current one
                    continue
                    
        return None # No date found after trying all patterns

    def _calculate_quality_score(self, doc: LegalDocument) -> float:
        """
        Calculates a comprehensive quality score for a legal document based on several weighted factors.
        The score ranges from 0.0 to 1.0, indicating the perceived utility and relevance of the document.
        
        Args:
            doc: The LegalDocument object to be scored.
            
        Returns:
            A float representing the calculated quality score.
        """
        score = 0.0
        
        # Factor 1: Content quality (40% weight)
        # Documents with substantial content are generally more valuable.
        if len(doc.content.strip()) > 500: # Arbitrary threshold for "good" length
            score += 0.4
        elif len(doc.content.strip()) > 200: # Arbitrary threshold for "moderate" length
            score += 0.2
        
        # Factor 2: Recency (30% weight)
        # More recent legal documents are often more relevant, especially for dynamic regulations.
        if doc.publication_date:
            days_old = (datetime.now().date() - doc.publication_date).days
            if days_old <= 365:  # Less than 1 year old
                score += 0.3
            elif days_old <= 1095:  # Less than 3 years old
                score += 0.15
        
        # Factor 3: Legal relevance (20% weight)
        # Presence of specific keywords indicates direct relevance to traffic fine legislation.
        content_lower = doc.content.lower()
        relevance_keywords = [
            'multa', 'contraordenação', 'trânsito', 'veículo', 'automóvel',
            'estacionamento', 'velocidade', 'sinalização', 'código da estrada',
            'artigo', 'lei', 'decreto', 'portaria'
        ]
        
        relevance_count = sum(1 for keyword in relevance_keywords if keyword in content_lower)
        # Cap the relevance score contribution to 0.2 (20% of total)
        score += min(0.2, relevance_count * 0.02) 
        
        # Factor 4: Source authority (10% weight)
        # Documents from highly authoritative sources are given a higher score.
        authority_sources = ['ansr', 'diário da república', 'dgsi', 'governo']
        if any(source in doc.source.lower() for source in authority_sources):
            score += 0.1
        
        # Ensure the final score does not exceed 1.0
        return min(1.0, score)

    def _calculate_content_hash(self, content: str) -> str:
        """Calculate hash for content deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def _process_pdf_content(self, pdf_path: str) -> str:
        """Extract text content from PDF using multiple methods."""
        try:
            # Try pdfplumber first (better for structured documents)
            with PDF(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                if text.strip():
                    return text
        except Exception as e:
            logger.warning(f"pdfplumber failed for {pdf_path}: {e}")
        
        try:
            # Fallback to PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"PyPDF2 failed for {pdf_path}: {e}")
            return ""
    
    def scrape_ansr_documents(self, max_documents: int = 100) -> List[LegalDocument]:
        """
        Scrapes documents from ANSR (Autoridade Nacional de Segurança Rodoviária) website.
        ANSR is a key source for traffic regulations and enforcement in Portugal.
        The function iterates through predefined ANSR URLs, extracts document links,
        downloads PDFs, extracts text content, and calculates a quality score for each document.
        
        Args:
            max_documents: The maximum number of documents to collect from ANSR sources.
            
        Returns:
            A list of LegalDocument objects collected from ANSR.
        """
        documents = []
        
        # Define ANSR official URLs for different document types related to traffic and fines.
        ansr_sources = [
            {
                'name': 'ANSR Regulations',
                'url': 'https://www.ansr.pt/pt/legislacao/Paginas/default.aspx',
                'type': 'regulation'
            },
            {
                'name': 'ANSR Fines Database', 
                'url': 'https://www.ansr.pt/pt/multas/Paginas/default.aspx',
                'type': 'fine_procedures'
            },
            {
                'name': 'ANSR Road Safety',
                'url': 'https://www.ansr.pt/pt/seguranca/Paginas/default.aspx',
                'type': 'safety_guidelines'
            }
        ]
        
        # Iterate through each defined ANSR source
        for source in ansr_sources:
            logger.info(f"Scraping ANSR source: {source['name']}")
            
            # Use _make_request with Selenium as ANSR pages might be JavaScript-heavy
            page_source = self._make_request(source['url'], use_selenium=True)
            if not page_source:
                logger.warning(f"Failed to retrieve page source for {source['name']}. Skipping.")
                continue
                
            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all anchor tags that link to PDF or DOC files (case-insensitive)
            doc_links = soup.find_all('a', href=re.compile(r'\.(pdf|doc|docx)$', re.I))
            
            # Process each document link found
            # Limit the number of documents per source to distribute max_documents evenly
            for link in doc_links[:max_documents // len(ansr_sources)]:
                try:
                    # Construct the absolute URL for the document
                    doc_url = urljoin(source['url'], link.get('href'))
                    doc_title = link.get_text(strip=True)
                    
                    # Skip if title is empty or too short, indicating a malformed link
                    if not doc_title or len(doc_title) < 10:
                        logger.debug(f"Skipping document with short/empty title: {doc_url}")
                        continue
                    
                    # Generate a unique filename for the downloaded document
                    file_name = f"ansr_{hashlib.md5(doc_url.encode()).hexdigest()[:8]}.pdf"
                    file_path = self.download_dir / file_name
                    
                    # Check if the document has already been downloaded
                    if file_path.exists():
                        logger.info(f"Document already exists locally: {doc_title} ({file_name}). Skipping download.")
                        continue
                    
                    # Download the PDF document
                    pdf_response = self._make_request(doc_url)
                    if pdf_response and 'application/pdf' in pdf_response.headers.get('Content-Type', ''):
                        with open(file_path, 'wb') as f:
                            f.write(pdf_response.content)
                        
                        # Extract text content from the downloaded PDF
                        content = self._process_pdf_content(str(file_path))
                        
                        # Create a LegalDocument object
                        doc = LegalDocument(
                            title=doc_title,
                            content=content,
                            url=doc_url,
                            source='ANSR',
                            document_type=source['type'],
                            jurisdiction='Portugal',
                            publication_date=self._extract_publication_date(content),
                            retrieval_date=datetime.now(),
                            file_path=str(file_path)
                        )
                        
                        # Calculate and assign a quality score to the document
                        doc.quality_score = self._calculate_quality_score(doc)
                        
                        # Check for content duplicates using a hash
                        content_hash = self._calculate_content_hash(content)
                        if content_hash not in self.processed_hashes:
                            documents.append(doc)
                            self.processed_hashes.add(content_hash)
                            logger.info(f"Collected ANSR document: {doc_title} (quality: {doc.quality_score:.2f})")
                        else:
                            logger.info(f"Skipping duplicate ANSR document: {doc_title}")
                    else:
                        logger.warning(f"Failed to download PDF or unexpected content type for {doc_url}")
                    
                except Exception as e:
                    logger.error(f"Error processing ANSR document {doc_title} from {doc_url}: {e}")
                    continue
        
        logger.info(f"ANSR scraping completed. Collected {len(documents)} documents.")
        # Return documents up to the max_documents limit
        return documents[:max_documents]

    def scrape_diario_da_republica_documents(self, max_documents: int = 100) -> List[LegalDocument]:
        """
        Scrape Diário da República (Official Government Gazette) documents.
        
        Args:
            max_documents: Maximum number of documents to collect
            
        Returns:
            List of LegalDocument objects
        """
        documents = []
        
        # Diário da República search URLs
        dr_searches = [
            {
                'name': 'Traffic Laws',
                'params': {'palavras': 'trânsito', 'tipo': 'DI'},
                'type': 'law'
            },
            {
                'name': 'Fines Regulations', 
                'params': {'palavras': 'multas contraordenação', 'tipo': 'DI'},
                'type': 'regulation'
            },
            {
                'name': 'Road Safety',
                'params': {'palavras': 'estradas segurança', 'tipo': 'DI'},
                'type': 'regulation'
            }
        ]
        
        base_url = "https://dre.pt/web/guest/home/-/dre/search"
        
        for search in dr_searches:
            logger.info(f"Scraping Diário da República: {search['name']}")
            
            try:
                # POST request to search
                response = self._make_request(base_url, method="POST", data=search['params'])
                if not response:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find document links
                doc_links = soup.find_all('a', href=re.compile(r'/detail/', re.I))
                
                for link in doc_links[:max_documents // len(dr_searches)]:
                    try:
                        doc_url = f"https://dre.pt{link.get('href')}"
                        doc_title = link.get_text(strip=True)
                        
                        if not doc_title or len(doc_title) < 10:
                            continue
                        
                        # Get document details page
                        detail_response = self._make_request(doc_url)
                        if not detail_response:
                            continue
                        
                        detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                        
                        # Extract content
                        content_element = detail_soup.find('div', class_='dre-content')
                        if not content_element:
                            continue
                        
                        content = content_element.get_text(separator='\n', strip=True)
                        
                        # Check for PDF download
                        pdf_link = detail_soup.find('a', href=re.compile(r'\.pdf$', re.I))
                        file_path = None
                        
                        if pdf_link:
                            pdf_url = f"https://dre.pt{pdf_link.get('href')}"
                            file_name = f"dre_{hashlib.md5(doc_url.encode()).hexdigest()[:8]}.pdf"
                            pdf_path = self.download_dir / file_name
                            
                            pdf_response = self._make_request(pdf_url)
                            if pdf_response:
                                with open(pdf_path, 'wb') as f:
                                    f.write(pdf_response.content)
                                file_path = str(pdf_path)
                        
                        # Create LegalDocument
                        doc = LegalDocument(
                            title=doc_title,
                            content=content,
                            url=doc_url,
                            source='Diário da República',
                            document_type=search['type'],
                            jurisdiction='Portugal',
                            publication_date=self._extract_publication_date(content),
                            retrieval_date=datetime.now(),
                            file_path=file_path
                        )
                        
                        doc.quality_score = self._calculate_quality_score(doc)
                        
                        # Check for duplicates
                        content_hash = self._calculate_content_hash(content)
                        if content_hash not in self.processed_hashes:
                            documents.append(doc)
                            self.processed_hashes.add(content_hash)
                            logger.info(f"Collected DR document: {doc_title} (quality: {doc.quality_score:.2f})")
                    
                    except Exception as e:
                        logger.error(f"Error processing DR document: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error searching Diário da República: {e}")
                continue
        
        logger.info(f"Diário da República scraping completed. Collected {len(documents)} documents.")
        return documents[:max_documents]

    def scrape_dgsi_documents(self, max_documents: int = 100) -> List[LegalDocument]:
        """
        Scrape DGSI (Diário da República Digital) court decisions.
        
        Args:
            max_documents: Maximum number of documents to collect
            
        Returns:
            List of LegalDocument objects
        """
        documents = []
        
        # DGSI court decision search
        dgsi_searches = [
            {
                'name': 'Traffic Court Decisions',
                'params': {'pesquisa': 'trânsito multa contraordenação'},
                'type': 'court_decision'
            },
            {
                'name': 'Road Safety Appeals',
                'params': {'pesquisa': 'estrada segurança recurso'},
                'type': 'court_decision'
            }
        ]
        
        base_url = "http://www.dgsi.pt/jstj.nsf/"
        
        for search in dgsi_searches:
            logger.info(f"Scraping DGSI: {search['name']}")
            
            try:
                # Use Selenium for DGSI complex search forms
                page_source = self._make_request(base_url, use_selenium=True)
                if not page_source:
                    continue
                
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Find court decision links (DGSI has specific structure)
                decision_links = soup.find_all('a', href=re.compile(r'.*decisao.*', re.I))
                
                for link in decision_links[:max_documents // len(dgsi_searches)]:
                    try:
                        decision_url = urljoin(base_url, link.get('href'))
                        decision_title = link.get_text(strip=True)
                        
                        if not decision_title or len(decision_title) < 10:
                            continue
                        
                        # Get decision details
                        decision_response = self._make_request(decision_url)
                        if not decision_response:
                            continue
                        
                        decision_soup = BeautifulSoup(decision_response.text, 'html.parser')
                        
                        # Extract decision content
                        content_element = decision_soup.find('div', {'class': re.compile(r'.*decision.*', re.I)})
                        if not content_element:
                            # Try alternative content extraction
                            content_element = decision_soup.find('body')
                        
                        if content_element:
                            content = content_element.get_text(separator='\n', strip=True)
                        else:
                            content = ""
                        
                        # Create LegalDocument
                        doc = LegalDocument(
                            title=decision_title,
                            content=content,
                            url=decision_url,
                            source='DGSI',
                            document_type=search['type'],
                            jurisdiction='Portugal',
                            publication_date=self._extract_publication_date(content),
                            retrieval_date=datetime.now(),
                            metadata={
                                'court_type': 'DGSI',
                                'case_type': 'traffic_violation'
                            }
                        )
                        
                        doc.quality_score = self._calculate_quality_score(doc)
                        
                        # Check for duplicates
                        content_hash = self._calculate_content_hash(content)
                        if content_hash not in self.processed_hashes and doc.quality_score > 0.3:
                            documents.append(doc)
                            self.processed_hashes.add(content_hash)
                            logger.info(f"Collected DGSI document: {decision_title} (quality: {doc.quality_score:.2f})")
                    
                    except Exception as e:
                        logger.error(f"Error processing DGSI document: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error searching DGSI: {e}")
                continue
        
        logger.info(f"DGSI scraping completed. Collected {len(documents)} documents.")
        return documents[:max_documents]

    def scrape_all_sources(self, max_documents: int = 300) -> Dict[str, List[LegalDocument]]:
        """
        Orchestrates the scraping of all defined Portuguese legal sources concurrently.
        It distributes the `max_documents` limit evenly among the sources and uses a
        ThreadPoolExecutor for parallel execution to improve efficiency.
        
        Args:
            max_documents: The total maximum number of documents to collect across all sources.
            
        Returns:
            A dictionary where keys are source names (e.g., 'ANSR', 'Diario_da_Republica', 'DGSI')
            and values are lists of LegalDocument objects collected from each source.
        """
        logger.info(f"Starting comprehensive Portuguese legal document scraping (target: {max_documents} documents)")
        
        results = {
            'ANSR': [],
            'Diario_da_Republica': [],
            'DGSI': []
        }
        
        # Distribute the total document limit evenly across the three main sources.
        per_source = max_documents // 3
        
        # Use ThreadPoolExecutor for concurrent scraping of different sources.
        # The number of workers is configurable via self.concurrent_workers.
        with ThreadPoolExecutor(max_workers=self.concurrent_workers) as executor:
            # Submit each scraping task to the executor and map the future to its source name.
            future_to_source = {
                executor.submit(self.scrape_ansr_documents, per_source): 'ANSR',
                executor.submit(self.scrape_diario_da_republica_documents, per_source): 'Diario_da_Republica',
                executor.submit(self.scrape_dgsi_documents, per_source): 'DGSI'
            }
            
            # Collect results as each future completes.
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    # Retrieve the results from the completed future.
                    # A timeout is applied to prevent any single source from hanging indefinitely.
                    documents = future.result(timeout=300)  # 5 minute timeout per source
                    results[source] = documents
                    logger.info(f"{source} completed: {len(documents)} documents collected")
                except Exception as e:
                    # Log any exceptions that occur during a source's scraping process.
                    logger.error(f"{source} scraping failed: {e}")
                    results[source] = [] # Ensure the source still has an empty list if it failed
        
        # Calculate and log summary statistics for the entire scraping operation.
        total_docs = sum(len(docs) for docs in results.values())
        high_quality_docs = sum(len([d for d in docs if d.quality_score > 0.7]) for docs in results.values())
        
        logger.info(f"Scraping completed. Total: {total_docs} documents, High quality: {high_quality_docs}")
        
        return results

    def save_scraping_results(self, results: Dict[str, List[LegalDocument]], 
                            output_dir: str = "knowledge_base/scraped") -> None:
        """
        Save scraping results to JSON files with metadata.
        
        Args:
            results: Dictionary of scraping results
            output_dir: Directory to save results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for source, documents in results.items():
            # Save to JSON
            json_file = output_path / f"{source.lower()}_documents_{timestamp}.json"
            
            doc_data = []
            for doc in documents:
                doc_dict = {
                    'title': doc.title,
                    'content': doc.content[:5000],  # Truncate for JSON
                    'url': doc.url,
                    'source': doc.source,
                    'document_type': doc.document_type,
                    'jurisdiction': doc.jurisdiction,
                    'publication_date': doc.publication_date.isoformat() if doc.publication_date else None,
                    'retrieval_date': doc.retrieval_date.isoformat(),
                    'file_path': doc.file_path,
                    'metadata': doc.metadata,
                    'quality_score': doc.quality_score
                }
                doc_data.append(doc_dict)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(documents)} {source} documents to {json_file}")
            
            # Save quality statistics
            stats_file = output_path / f"{source.lower()}_stats_{timestamp}.json"
            stats = {
                'total_documents': len(documents),
                'high_quality_documents': len([d for d in documents if d.quality_score > 0.7]),
                'average_quality_score': sum(d.quality_score for d in documents) / len(documents) if documents else 0,
                'document_types': list(set(d.document_type for d in documents)),
                'scraping_date': datetime.now().isoformat()
            }
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
        
        # Save combined summary
        summary_file = output_path / f"scraping_summary_{timestamp}.json"
        summary = {
            'total_documents': sum(len(docs) for docs in results.values()),
            'sources_scraped': list(results.keys()),
            'average_quality': sum(
                sum(d.quality_score for d in docs) / len(docs) if docs else 0 
                for docs in results.values()
            ) / len(results),
            'scraping_completed': datetime.now().isoformat()
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved scraping summary to {summary_file}")

if __name__ == "__main__":
    # Example usage
    scraper = PortugueseLegalScraper()
    
    # Scrape all sources
    results = scraper.scrape_all_sources(max_documents=50)  # Small test run
    
    # Save results
    scraper.save_scraping_results(results)
    
    print("Portuguese legal document scraping completed!")