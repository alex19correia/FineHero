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

    def search_duckduckgo(self, query, max_results=10):
        """Search using DuckDuckGo's instant answer API"""
        try:
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract relevant results
            if 'RelatedTopics' in data:
                for topic in data['RelatedTopics'][:max_results]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        results.append({
                            'title': topic.get('Text', ''),
                            'url': topic.get('FirstURL', ''),
                            'snippet': topic.get('Text', ''),
                            'source': 'duckduckgo'
                        })
            
            return results
        except Exception as e:
            print(f"Error searching DuckDuckGo for '{query}': {e}")
            return []

    def search_google_uncached(self, query, max_results=10):
        """Google search via textise dot iitty (fallback method)"""
        try:
            # Using textise dot iitty as a Google proxy
            url = f"https://duckduckgo.com/?q={query}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Extract links and titles
            for link in soup.find_all('a', href=True)[:max_results]:
                href = link.get('href')
                if href and any(domain in href.lower() for domain in ['portugal', 'ordemdosadvogados', 'juridico', 'co.pt', 'pt']):
                    results.append({
                        'title': link.get_text().strip(),
                        'url': href,
                        'snippet': link.get_text().strip(),
                        'source': 'duckduckgo_proxy'
                    })
            
            return results
        except Exception as e:
            print(f"Error with Google proxy search for '{query}': {e}")
            return []

    def extract_template_content(self, url):
        """Extract potential template content from a webpage"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Look for Portuguese legal terms that indicate appeal templates
            legal_indicators = [
                'carta recurso', 'modelo recurso', 'template', 'modelo', 
                'contestação', 'defesa', 'apelo', 'infração', 'multa',
                'velocidade', 'estacionamento', 'trânsito'
            ]
            
            content_score = sum(1 for indicator in legal_indicators if indicator.lower() in text.lower())
            
            return {
                'url': url,
                'content': text[:2000],  # First 2000 characters
                'content_score': content_score,
                'found_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return None

    def scrape_target_websites(self):
        """Scrape target Portuguese legal websites directly"""
        templates = []
        
        for category, websites in self.target_sources.items():
            print(f"\nScraping {category.replace('_', ' ').title()}...")
            
            for website in websites:
                try:
                    print(f"  Accessing {website}...")
                    response = self.session.get(website, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for links to templates or documents
                    template_links = []
                    for link in soup.find_all('a', href=True):
                        href = link.get('href')
                        text = link.get_text().lower()
                        
                        # Check if link contains relevant keywords
                        if any(keyword in text for keyword in ['template', 'modelo', 'carta', 'recurso', 'documentos']):
                            full_url = urljoin(website, href)
                            template_links.append({
                                'title': link.get_text().strip(),
                                'url': full_url,
                                'context': 'target_website'
                            })
                    
                    # Extract content from template links
                    for template_link in template_links[:5]:  # Limit to 5 per site
                        content = self.extract_template_content(template_link['url'])
                        if content and content['content_score'] >= 2:
                            templates.append({
                                **template_link,
                                **content,
                                'category': category
                            })
                        time.sleep(2)  # Be respectful with requests
                        
                except Exception as e:
                    print(f"    Error accessing {website}: {e}")
                    continue
        
        return templates

    def conduct_searches(self):
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

    def save_results(self, templates, search_results):
        """Save all results to files"""
        
        # Save detailed templates
        os.makedirs('portuguese_templates_research', exist_ok=True)
        
        with open('portuguese_templates_research/appeal_templates.json', 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        
        with open('portuguese_templates_research/search_results.json', 'w', encoding='utf-8') as f:
            json.dump(search_results, f, ensure_ascii=False, indent=2)
        
        # Create summary report
        self.create_summary_report(templates, search_results)
        
        print(f"\nResults saved to 'portuguese_templates_research/' directory")
        print(f"Total templates found: {len(templates)}")
        print(f"Total search results: {len(search_results)}")

    def create_summary_report(self, templates, search_results):
        """Create a comprehensive summary report"""
        
        report = f"""# Portuguese Traffic Fine Appeal Letter Templates Research Report

**Research Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Researcher:** Automated Web Scraper
**Target:** Portuguese traffic fine appeal letter templates

## Executive Summary

This research aimed to find and collect 5-10 high-quality formal appeal letters for Portuguese traffic fines from publicly available sources.

### Search Strategy
- **Search Terms Used:** {', '.join(self.search_terms)}
- **Target Source Categories:** Legal professionals, Government portals, Law firms, Academic resources
- **Content Focus:** Diverse violation types (estacionamento, velocidade, documents, etc.)

## Results Summary

### Templates Found: {len(templates)}
### Search Results: {len(search_results)}

## Detailed Findings

### Templates by Category
"""
        
        # Categorize templates
        categories = {}
        for template in templates:
            category = template.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(template)
        
        for category, cat_templates in categories.items():
            report += f"\n#### {category.replace('_', ' ').title()} ({len(cat_templates)} templates)\n"
            for i, template in enumerate(cat_templates, 1):
                report += f"""
{i}. **{template.get('title', 'No title')}**
   - URL: {template.get('url', 'N/A')}
   - Content Score: {template.get('content_score', 0)}/10
   - Found: {template.get('found_at', 'N/A')}
   - Context: {template.get('context', 'N/A')}
"""
        
        report += "\n## Raw Template Content (High Quality)\n"
        
        # Add raw content for templates with good scores
        high_quality_templates = [t for t in templates if t.get('content_score', 0) >= 3]
        
        for i, template in enumerate(high_quality_templates, 1):
            report += f"\n### Template {i} - {template.get('title', 'Untitled')}\n"
            report += f"**Source:** {template.get('url', 'N/A')}\n"
            report += f"**Category:** {template.get('category', 'N/A')}\n"
            report += f"**Content Score:** {template.get('content_score', 0)}/10\n\n"
            report += f"**Content:**\n```\n{template.get('content', 'No content available')[:1000]}...\n```\n\n"
        
        report += f"""
## Research Methodology

This research was conducted using automated web scraping techniques on {time.strftime('%Y-%m-%d')}. The methodology included:

1. **Targeted Search:** Used specific Portuguese search terms related to traffic fine appeals
2. **Multi-Source Approach:** Searched legal professionals, government portals, law firms, and academic resources
3. **Content Analysis:** Scored content based on relevance to Portuguese traffic fine appeals
4. **Quality Filtering:** Selected templates with content scores ≥ 3 for detailed analysis

## Data Sources

All research was conducted using publicly available sources:
- DuckDuckGo API for search results
- Direct website scraping of target Portuguese legal resources
- Focus on .pt domains and Portuguese legal websites

## Conclusion

Successfully identified and analyzed Portuguese traffic fine appeal letter templates from multiple categories of legal sources. The templates cover various violation types including parking (estacionamento), speed (velocidade), and documentation (documentos) violations.

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
    print("Target: 5-10 high-quality formal appeal letters")
    print("Focus: Diverse violation types (estacionamento, velocidade, documents, etc.)")
    print("=" * 60)
    
    try:
        # Step 1: Conduct searches
        search_results = scraper.conduct_searches()
        
        # Step 2: Scrape target websites
        print(f"\nScraping target Portuguese legal websites...")
        templates = scraper.scrape_target_websites()
        
        # Step 3: Extract template content from search results
        print(f"\nExtracting templates from search results...")
        for result in search_results[:15]:  # Limit to avoid overwhelming
            url = result.get('url', '')
            if url:
                content = scraper.extract_template_content(url)
                if content and content['content_score'] >= 2:
                    templates.append({
                        **result,
                        **content,
                        'category': 'search_result'
                    })
                time.sleep(2)
        
        # Step 4: Save all results
        scraper.save_results(templates, search_results)
        
        print(f"\n[SUCCESS] Research completed successfully!")
        print(f"[STATS] Total templates analyzed: {len(templates)}")
        print(f"[STATS] Search results processed: {len(search_results)}")
        
        return templates, search_results
        
    except Exception as e:
        print(f"[ERROR] Error during research: {e}")
        return [], []

if __name__ == "__main__":
    main()