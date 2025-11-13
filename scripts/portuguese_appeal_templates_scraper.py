#!/usr/bin/env python3
"""
Portuguese Traffic Fine Appeal Letter Templates Scraper
Research conducted on: 2025-11-11

This script searches for Portuguese traffic fine appeal letter templates
using specific search terms and target sources.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
import os
from typing import List, Dict, Any, Optional

class PortugueseAppealTemplatesScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.templates_found = []
        self.search_results = []
        
        # Search terms for Portuguese traffic fine appeals
        self.search_terms = [
            "carta recurso multa Portugal",
            "modelo recurso contrafine trânsito", 
            "carta contestação multa estacionamento",
            "recurso velocidade excesso",
            "template apelo infração"
        ]
        
        # Target source categories
        self.target_sources = {
            'legal_professionals': [
                'https://www.ordemdosadvogados.pt',
                'https://www.caixalaw.com',
                'https://www.martinsfreitas.com'
            ],
            'government_portals': [
                'https://www.portaldocidadao.pt',
                'https://www.dgvi.mj.pt',
                'https://www.impic.pt'
            ],
            'law_firms': [
                'https://www.galvaosilva.com',
                'https://www.fga.pt',
                'https://www.lccs.pt'
            ],
            'legal_resources': [
                'https://juridico.co.pt',
                'https://www.conjur.pt',
                'https://www.rotadefuga.pt'
            ]
        }









    def extract_template_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract potential template content from a webpage"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Initialize content and score
            extracted_content = ""
            content_score = 0
            
            # Look for specific keywords in proximity or within structured tags
            
            # Prioritize content within <pre>, <code>, or <textarea> tags
            for tag in soup.find_all(['pre', 'code', 'textarea']):
                tag_text = tag.get_text(strip=True)
                if any(keyword in tag_text.lower() for keyword in ['modelo de recurso', 'carta de contestação', 'requerimento']):
                    extracted_content = tag_text
                    content_score += 5 # High score for structured template-like content
                    break # Found a strong candidate, no need to check other tags
            
            # If no strong candidate found in structured tags, search in general text
            if not extracted_content:
                text = soup.get_text()
                
                # Look for Portuguese legal terms that indicate appeal templates
                legal_indicators = [
                    'carta recurso', 'modelo recurso', 'template', 'modelo', 
                    'contestação', 'defesa', 'apelo', 'infração', 'multa',
                    'velocidade', 'estacionamento', 'trânsito', 'código da estrada',
                    'artigo', 'decreto-lei', 'portaria', 'formulário', 'requerimento',
                    'impugnação', 'coima', 'contraordenação', 'lei', 'regulamento'
                ]
                
                # Look for combinations of keywords
                if re.search(r'modelo\s+de\s+recurso', text.lower()) or \
                   re.search(r'carta\s+de\s+contestação', text.lower()) or \
                   re.search(r'requerimento\s+de\s+impugnação', text.lower()):
                    content_score += 3
                
                content_score += sum(1 for indicator in legal_indicators if indicator.lower() in text.lower())
                extracted_content = text
            
            return {
                'url': url,
                'content': extracted_content[:4000],  # First 4000 characters for more context
                'content_score': content_score,
                'found_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return None



    def search_duckduckgo(self, query: str, max_results: int) -> List[Dict]:
        """
        Perform a DuckDuckGo search and return results.
        
        Args:
            query: The search query string
            max_results: Maximum number of results to return
            
        Returns:
            A list of result dictionaries with 'title', 'url', and 'snippet' keys
        """
        try:
            from duckduckgo_search import DDGS
            
            results = []
            ddgs = DDGS()
            
            # Perform the search
            search_results = ddgs.text(query, max_results=max_results)
            
            # Convert results to the expected format
            for result in search_results:
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('href', ''),
                    'snippet': result.get('body', '')
                })
            
            return results
            
        except ImportError:
            # Fallback to HTTP-based search if duckduckgo_search is not installed
            print(f"Note: duckduckgo_search package not found, attempting HTTP fallback for '{query}'")
            return self._search_duckduckgo_http(query, max_results)
        except Exception as e:
            print(f"Error searching DuckDuckGo for '{query}': {e}")
            return []

    def _search_duckduckgo_http(self, query: str, max_results: int) -> List[Dict]:
        """
        Fallback HTTP-based DuckDuckGo search when the package is unavailable.
        
        Args:
            query: The search query string
            max_results: Maximum number of results to return
            
        Returns:
            A list of result dictionaries with 'title', 'url', and 'snippet' keys
        """
        try:
            # DuckDuckGo HTML search endpoint
            url = "https://duckduckgo.com/html/"
            params = {'q': query}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Parse DuckDuckGo HTML results
            for result in soup.find_all('div', class_='result'):
                if len(results) >= max_results:
                    break
                
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem and snippet_elem:
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'url': title_elem.get('href', ''),
                        'snippet': snippet_elem.get_text(strip=True)
                    })
            
            return results
            
        except Exception as e:
            print(f"Error in HTTP fallback search for '{query}': {e}")
            return []

    def conduct_searches(self) -> List[Dict]:

        """Conduct searches for all specified terms"""
        print("Starting web research for Portuguese traffic fine appeal templates...")
        print(f"Research Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Search Terms: {', '.join(self.search_terms)}")
        
        all_results = []
        
        for term in self.search_terms:
            print(f"\nSearching for: '{term}'")
            
            # Try DuckDuckGo search
            results = self.search_duckduckgo(term, 10)
            if results:
                all_results.extend(results)
                print(f"  Found {len(results)} results via DuckDuckGo")
            
            time.sleep(3)  # Rate limiting
        
        return all_results

    def process_search_results_for_templates(self, search_results: List[Dict]) -> List[Dict]:
        """
        Iterate through search results, filter for relevant URLs, and extract template content.
        """
        templates = []
        processed_urls = set()
        
        print("\nProcessing search results for potential templates...")
        
        for result in search_results:
            url = result.get('url')
            if not url or url in processed_urls:
                continue
            
            # Filter for relevant domains (e.g., .pt, legal-sounding domains)
            parsed_url = urlparse(url)
            if not parsed_url.netloc.endswith('.pt') and \
               not any(keyword in parsed_url.netloc for keyword in ['advogados', 'juridico', 'lei', 'governo', 'multas', 'contrafine']):
                continue # Skip irrelevant domains
            
            print(f"  Attempting to extract content from: {url}")
            content_data = self.extract_template_content(url)
            
            if content_data and content_data['content_score'] >= 2: # Threshold for quality
                templates.append({
                    **result,
                    **content_data,
                    'category': 'search_result_template'
                })
                processed_urls.add(url)
            time.sleep(1) # Be respectful
            
        return templates

    def save_results(self, templates: List[Dict], search_results: List[Dict]):
        """Save all results to files"""
        
        os.makedirs('portuguese_templates_research', exist_ok=True)
        
        with open('portuguese_templates_research/appeal_templates.json', 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        
        with open('portuguese_templates_research/search_results.json', 'w', encoding='utf-8') as f:
            json.dump(search_results, f, ensure_ascii=False, indent=2)
        
        self.create_summary_report(templates, search_results)
        
        print(f"\nResults saved to 'portuguese_templates_research/' directory")
        print(f"Total templates found: {len(templates)}")
        print(f"Total search results: {len(search_results)}")

    def create_summary_report(self, templates: List[Dict], search_results: List[Dict]):
        """Create a comprehensive summary report"""
        
        report = f"""# Portuguese Traffic Fine Appeal Letter Templates Research Report

**Research Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Researcher:** Automated Web Scraper
**Target:** Portuguese traffic fine appeal letter templates

## Executive Summary

This research aimed to find and collect high-quality formal appeal letters for Portuguese traffic fines from publicly available sources, primarily through web search.

### Search Strategy
- **Search Terms Used:** {', '.join(self.search_terms)}
- **Content Focus:** Diverse violation types (estacionamento, velocidade, documents, etc.)

## Results Summary

### Templates Found: {len(templates)}
### Search Results Processed: {len(search_results)}

## Detailed Findings

### Templates Collected
"""
        
        for i, template in enumerate(templates, 1):
            report += f"""
{i}. **{template.get('title', 'No title')}**
   - URL: {template.get('url', 'N/A')}
   - Content Score: {template.get('content_score', 0)}/10
   - Found: {template.get('found_at', 'N/A')}
   - Category: {template.get('category', 'N/A')}
"""
        
        report += "\n## Raw Template Content (High Quality)\n"
        
        high_quality_templates = [t for t in templates if t.get('content_score', 0) >= 3]
        
        for i, template in enumerate(high_quality_templates, 1):
            report += f"\n### Template {i} - {template.get('title', 'Untitled')}\n"
            report += f"**Source:** {template.get('url', 'N/A')}\n"
            report += f"**Category:** {template.get('category', 'N/A')}\n"
            report += f"**Content Score:** {template.get('content_score', 0)}/10\n\n"
            report += f"**Content:**\n```\n{template.get('content', 'No content available')[:1000]}...\n```\n\n"
        
        report += f"""
## Research Methodology

This research was conducted using automated web search and content extraction techniques on {time.strftime('%Y-%m-%d')}. The methodology included:

1. **Targeted Search:** Used specific Portuguese search terms related to traffic fine appeals via DuckDuckGo.
2. **Search Result Processing:** Iterated through search results, filtering for relevant domains (.pt, legal-themed) and extracting potential template content.
3. **Content Analysis:** Scored extracted content based on relevance to Portuguese traffic fine appeals.
4. **Quality Filtering:** Selected templates with content scores ≥ 2 for detailed analysis.

## Data Sources

All research was conducted using publicly available sources:
- DuckDuckGo API for search results
- Publicly accessible websites found via search results

## Conclusion

This revised approach focuses on leveraging web search to discover publicly available appeal letter templates, adapting to the challenges of direct scraping of specific, often dynamic or inaccessible, target websites.

**Research completed on:** {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open('portuguese_templates_research/research_report.md', 'w', encoding='utf-8') as f:
            f.write(report)

def main():
    """Main execution function"""
    scraper = PortugueseAppealTemplatesScraper()
    
    print("Portuguese Traffic Fine Appeal Templates Research")
    print("=" * 60)
    print(f"Research Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Target: High-quality formal appeal letters from web search")
    print("Focus: Diverse violation types (estacionamento, velocidade, documents, etc.)")
    print("=" * 60)
    
    try:
        # Step 1: Conduct searches
        raw_search_results = scraper.conduct_searches()
        
        # Step 2: Process search results to extract templates
        templates = scraper.process_search_results_for_templates(raw_search_results)
        
        # Step 3: Save all results
        scraper.save_results(templates, raw_search_results)
        
        print(f"\n[SUCCESS] Research completed successfully!")
        print(f"[STATS] Total templates analyzed: {len(templates)}")
        print(f"[STATS] Raw search results processed: {len(raw_search_results)}")
        
        return templates, raw_search_results
        
    except Exception as e:
        print(f"[ERROR] Error during research: {e}")
        return [], []

if __name__ == "__main__":
    main()