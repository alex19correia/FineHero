import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin, urlparse
import os
from typing import List, Dict, Optional, Callable

class WebScraper:
    """
    A class for respectful web scraping of Portuguese legal documents.
    Handles rate limiting, user-agent rotation, and basic error handling.
    """

    def __init__(self, base_url: str, delay_min: float = 2, delay_max: float = 5):
        """
        Initializes the WebScraper with a base URL and delay parameters.

        Args:
            base_url (str): The base URL of the website to scrape.
            delay_min (float): Minimum delay in seconds between requests.
            delay_max (float): Maximum delay in seconds between requests.
        """
        self.base_url = base_url
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.headers = {
            "User-Agent": "FineHero-Bot/1.0 (+https://www.finehero.com/bot.html)", # Custom User-Agent
            "Accept-Language": "en-US,en;q=0.9,pt;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _make_request(self, url: str, method: str = "GET", data: Optional[Dict] = None, retries: int = 3) -> Optional[requests.Response]:
        """
        Makes an HTTP request with respectful delays and error handling.

        Args:
            url (str): The URL to request.
            method (str): HTTP method (GET or POST).
            data (Optional[Dict]): Data payload for POST requests.
            retries (int): Number of retries for failed requests.

        Returns:
            Optional[requests.Response]: The response object if successful, None otherwise.
        """
        for attempt in range(retries):
            time.sleep(random.uniform(self.delay_min, self.delay_max))
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, timeout=10)
                elif method.upper() == "POST":
                    response = self.session.post(url, data=data, timeout=10)
                else:
                    print(f"Unsupported HTTP method: {method}")
                    return None

                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response
            except requests.exceptions.RequestException as e:
                print(f"Request to {url} failed (Attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    return None
        return None

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetches a web page and returns its parsed BeautifulSoup object.

        Args:
            url (str): The URL of the page to fetch.

        Returns:
            Optional[BeautifulSoup]: A BeautifulSoup object if successful, None otherwise.
        """
        full_url = urljoin(self.base_url, url)
        print(f"Fetching: {full_url}")
        response = self._make_request(full_url)
        if response:
            return BeautifulSoup(response.text, "html.parser")
        return None

    def download_pdf(self, pdf_url: str, save_path: str) -> bool:
        """
        Downloads a PDF file from a given URL.

        Args:
            pdf_url (str): The URL of the PDF file.
            save_path (str): The local path to save the PDF.

        Returns:
            bool: True if download is successful, False otherwise.
        """
        full_pdf_url = urljoin(self.base_url, pdf_url)
        print(f"Downloading PDF from: {full_pdf_url}")
        response = self._make_request(full_pdf_url)
        if response and 'application/pdf' in response.headers.get('Content-Type', ''):
            try:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"PDF saved to: {save_path}")
                return True
            except IOError as e:
                print(f"Error saving PDF to {save_path}: {e}")
                return False
        print(f"Failed to download PDF from {full_pdf_url} or content type was not PDF.")
        return False

    def find_links(self, soup: BeautifulSoup, pattern: str = "a") -> List[str]:
        """
        Finds all links matching a given pattern within a BeautifulSoup object.

        Args:
            soup (BeautifulSoup): The parsed HTML content.
            pattern (str): CSS selector or tag name to find links.

        Returns:
            List[str]: A list of absolute URLs found.
        """
        links = []
        for a_tag in soup.select(pattern):
            href = a_tag.get("href")
            if href:
                absolute_url = urljoin(self.base_url, href)
                # Ensure the link is within the same domain or a sub-domain if desired
                if urlparse(absolute_url).netloc == urlparse(self.base_url).netloc:
                    links.append(absolute_url)
        return links

    def scrape_source(self, source_name: str, start_url: str, max_pages: int, parse_page_func: Callable[[BeautifulSoup, str], List[Dict]]) -> List[Dict]:
        """
        Generic method to scrape documents from a given source.

        Args:
            source_name (str): Name of the source (e.g., "ANSR", "Diario da Republica").
            start_url (str): The starting URL for scraping.
            max_pages (int): Maximum number of pages to scrape.
            parse_page_func (Callable): A function that takes a BeautifulSoup object and current URL,
                                        and returns a list of document dictionaries found on that page.

        Returns:
            List[Dict]: A list of dictionaries, each containing document info (e.g., title, URL, source).
        """
        print(f"Starting {source_name} scraping from {start_url}...")
        documents = []
        visited_urls = set()
        queue = [start_url]
        pages_scraped = 0

        while queue and pages_scraped < max_pages:
            current_url = queue.pop(0)
            if current_url in visited_urls:
                continue

            soup = self.fetch_page(current_url)
            if not soup:
                continue

            visited_urls.add(current_url)
            pages_scraped += 1

            print(f"Scraping page {pages_scraped}: {current_url}")

            # Parse documents and next page links using the provided function
            page_documents, next_page_links = parse_page_func(soup, current_url)
            documents.extend(page_documents)

            for next_link in next_page_links:
                if next_link not in visited_urls:
                    queue.append(next_link)

        print(f"Finished {source_name} scraping. Found {len(documents)} documents.")
        return documents

    def _parse_ansr_page(self, soup: BeautifulSoup, current_url: str) -> (List[Dict], List[str]):
        """
        Parses a single ANSR page for documents and pagination links.
        """
        page_documents = []
        next_page_links = []

        # Example: Find document titles and links
        for doc_link in soup.select("a[href$='.pdf']"): # Example: find links ending with .pdf
            doc_title = doc_link.text.strip()
            doc_url = urljoin(current_url, doc_link['href'])
            page_documents.append({"title": doc_title, "url": doc_url, "source": "ANSR", "document_type": "regulation"})
            print(f"Found ANSR document: {doc_title} at {doc_url}")

        # Example: Find pagination links to continue scraping
        for next_page_link in soup.select("a.pagination-next"): # Example: find a 'next page' link
            next_page_links.append(urljoin(current_url, next_page_link['href']))
        
        return page_documents, next_page_links

    def scrape_ansr_documents(self, start_url: str, max_pages: int = 5) -> List[Dict]:
        """
        Scrapes documents from the ANSR website.
        """
        return self.scrape_source("ANSR", start_url, max_pages, self._parse_ansr_page)

    def _parse_diario_da_republica_page(self, soup: BeautifulSoup, current_url: str) -> (List[Dict], List[str]):
        """
        Placeholder: Parses a single Diario da Republica page for documents and pagination links.
        Actual implementation would require detailed knowledge of DR.pt's HTML structure.
        """
        page_documents = []
        next_page_links = []
        print(f"Placeholder: Parsing Diario da Republica page: {current_url}")

        # Example: Look for links to legal acts or diplomas
        # This is highly speculative and needs to be adapted to the actual site.
        for article_link in soup.select("a.dr-article-link"): # Hypothetical CSS selector
            title = article_link.text.strip()
            url = urljoin(current_url, article_link['href'])
            page_documents.append({"title": title, "url": url, "source": "Diario da Republica", "document_type": "law"})
            print(f"Found DR document: {title} at {url}")

        # Example: Pagination
        for next_link in soup.select("a.next-page"): # Hypothetical CSS selector
            next_page_links.append(urljoin(current_url, next_link['href']))

        return page_documents, next_page_links

    def scrape_diario_da_republica_documents(self, start_url: str, max_pages: int = 5) -> List[Dict]:
        """
        Scrapes documents from the Diário da República website.
        """
        return self.scrape_source("Diario da Republica", start_url, max_pages, self._parse_diario_da_republica_page)

    def _parse_dgsi_page(self, soup: BeautifulSoup, current_url: str) -> (List[Dict], List[str]):
        """
        Placeholder: Parses a single DGSI.pt page for case law documents and pagination links.
        Actual implementation would require detailed knowledge of DGSI.pt's HTML structure and search forms.
        """
        page_documents = []
        next_page_links = []
        print(f"Placeholder: Parsing DGSI.pt page: {current_url}")

        # DGSI often involves complex search forms and POST requests.
        # This example assumes a direct listing of results, which is unlikely for DGSI.
        for case_link in soup.select("a.dgsi-case-link"): # Hypothetical CSS selector
            title = case_link.text.strip()
            url = urljoin(current_url, case_link['href'])
            page_documents.append({"title": title, "url": url, "source": "DGSI.pt", "document_type": "precedent", "jurisdiction": "Portugal"})
            print(f"Found DGSI document: {title} at {url}")

        # Example: Pagination
        for next_link in soup.select("a.next-results"): # Hypothetical CSS selector
            next_page_links.append(urljoin(current_url, next_link['href']))

        return page_documents, next_page_links

    def scrape_dgsi_documents(self, start_url: str, max_pages: int = 5) -> List[Dict]:
        """
        Scrapes documents (case law) from the DGSI.pt website.
        """
        return self.scrape_source("DGSI.pt", start_url, max_pages, self._parse_dgsi_page)

    # Placeholder for Selenium-based scraping for JavaScript-heavy sites
    # def scrape_with_selenium(self, url: str):
    #     from selenium import webdriver
    #     from selenium.webdriver.chrome.service import Service
    #     from selenium.webdriver.common.by import By
    #     from selenium.webdriver.chrome.options import Options

    #     chrome_options = Options()
    #     chrome_options.add_argument("--headless") # Run in headless mode
    #     service = Service(executable_path="/path/to/chromedriver") # Specify path to chromedriver
    #     driver = webdriver.Chrome(service=service, options=chrome_options)
    #     driver.get(url)
    #     time.sleep(random.uniform(self.delay_min, self.delay_max)) # Wait for page to load
    #     soup = BeautifulSoup(driver.page_source, "html.parser")
    #     driver.quit()
    #     return soup

if __name__ == "__main__":
    # Example Usage:
    # This is a hypothetical example and will likely need adjustments for real-world scraping.
    # Always check the website's robots.txt and terms of service before scraping.
    
    # ANSR_BASE_URL = "https://www.ansr.pt/"
    # scraper = WebScraper(base_url=ANSR_BASE_URL)
    # ansr_docs = scraper.scrape_ansr_documents(start_url="/documentos", max_pages=1)
    # if ansr_docs:
    #     print("\n--- Sample ANSR Documents Found ---")
    #     for doc in ansr_docs:
    #         print(f"Title: {doc['title']}, URL: {doc['url']}")
    # else:
    #     print("No ANSR documents found in this example run.")

    # DR_BASE_URL = "https://dre.pt/" # Hypothetical base URL
    # dr_scraper = WebScraper(base_url=DR_BASE_URL)
    # dr_docs = dr_scraper.scrape_diario_da_republica_documents(start_url="/search", max_pages=1)
    # if dr_docs:
    #     print("\n--- Sample Diario da Republica Documents Found ---")
    #     for doc in dr_docs:
    #         print(f"Title: {doc['title']}, URL: {doc['url']}")
    # else:
    #     print("No Diario da Republica documents found in this example run.")

    # DGSI_BASE_URL = "http://www.dgsi.pt/" # Hypothetical base URL
    # dgsi_scraper = WebScraper(base_url=DGSI_BASE_URL)
    # dgsi_docs = dgsi_scraper.scrape_dgsi_documents(start_url="/search", max_pages=1)
    # if dgsi_docs:
    #     print("\n--- Sample DGSI.pt Documents Found ---")
    #     for doc in dgsi_docs:
    #         print(f"Title: {doc['title']}, URL: {doc['url']}")
    # else:
    #     print("No DGSI.pt documents found in this example run.")
    pass