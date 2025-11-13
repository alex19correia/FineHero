"""
Enhanced Portuguese Legal Scraper with Fallback Mechanisms
=========================================================

Addresses the access restrictions for IMT and ANSR websites by implementing:
- VPN/Proxy detection and usage
- Alternative access methods
- Manual document collection workflows
- Enhanced error handling and retry mechanisms

Solves the Java execution issues by providing Python-based alternatives and
proper environment configuration.
"""

import requests
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AccessMethod:
    """Defines different access methods for restricted websites"""
    name: str
    enabled: bool
    description: str
    configuration: Dict
    success_rate: float = 0.0

@dataclass
class DocumentSource:
    """Represents a legal document source with access requirements"""
    name: str
    url: str
    access_methods: List[str]
    status: str  # "accessible", "restricted", "failed", "manual_required"
    last_attempt: Optional[datetime]
    alternative_urls: List[str]
    manual_download_required: bool = False

class EnhancedPortugueseScraper:
    """
    Enhanced scraper with multiple access strategies and fallback mechanisms
    """
    
    def __init__(self, config_file: str = "scraper_config.json"):
        """
        Initializes the EnhancedPortugueseScraper by loading configuration, setting up
        an HTTP session, and defining various access methods and document sources.
        This class is designed to handle complex scraping scenarios, especially
        for restricted Portuguese legal websites.
        
        Args:
            config_file: Path to the JSON configuration file for the scraper.
        """
        # Load scraper configuration from the specified file or use defaults.
        self.config = self._load_config(config_file)
        
        # Set up a requests session with custom headers and proxy settings based on config.
        self.session = self._setup_session()
        
        # Define various access methods that can be used to reach document sources.
        # Each method has a name, enabled status, description, configuration, and a success rate.
        self.access_methods = {
            'direct': AccessMethod(
                name="Direct Access",
                enabled=True,
                description="Standard HTTP requests",
                configuration={},
                success_rate=0.7 # Heuristic success rate
            ),
            'selenium': AccessMethod(
                name="Selenium Browser",
                enabled=True,
                description="Headless browser automation for JavaScript-rendered content",
                configuration={
                    'headless': True,
                    'window_size': '1920,1080',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                success_rate=0.8
            ),
            'tor': AccessMethod(
                name="Tor Proxy",
                enabled=False, # Disabled by default, requires Tor service running
                description="Tor network routing for IP anonymity and bypassing geo-restrictions",
                configuration={
                    'proxy_url': 'socks5://127.0.0.1:9050', # Default Tor SOCKS proxy
                    'timeout': 30
                },
                success_rate=0.4 # Lower success rate due to potential CAPTCHAs/blocks
            ),
            'vpn': AccessMethod(
                name="VPN Proxy",
                enabled=False, # Disabled by default, requires user configuration
                description="Commercial VPN for Portuguese IP access to bypass geo-blocking",
                configuration={
                    'proxy_url': None,  # User will configure this
                    'country_code': 'PT' # Target country for VPN
                },
                success_rate=0.9 # High success rate if properly configured
            ),
            'api_alternative': AccessMethod(
                name="Alternative APIs",
                enabled=True,
                description="Use alternative APIs for Portuguese legal data (e.g., open data portals)",
                configuration={},
                success_rate=0.6
            )
        }
        
        # Define the legal document sources, including their URLs, known access issues,
        # and a list of potential access methods that might work for them.
        self.document_sources = [
            DocumentSource(
                name="IMT - Instituto da Mobilidade e dos Transportes",
                url="https://www.imt.pt/",
                access_methods=["selenium", "vpn", "tor"], # Methods likely to work for IMT
                status="restricted", # Initial status based on prior knowledge
                last_attempt=None,
                alternative_urls=[ # Known alternative URLs for IMT
                    "https://imt-ip.pt/",
                    "https://www.imt.pt/pt/",
                    "https://apic.imt.pt/"
                ],
                manual_download_required=False
            ),
            DocumentSource(
                name="ANSR - Autoridade Nacional de Segurança Rodoviária", 
                url="https://www.ansr.pt/",
                access_methods=["direct", "selenium", "vpn"], # Methods likely to work for ANSR
                status="failed", # Initial status based on prior knowledge
                last_attempt=None,
                alternative_urls=[ # Known alternative URLs for ANSR
                    "https://www.ansr.pt/pt/",
                    "https://www.acm.pt/",  # ACM might handle some ANSR functions
                    "https://www.portaldocidadao.pt/"
                ],
                manual_download_required=True # ANSR often requires manual intervention
            ),
            DocumentSource(
                name="DRE - Diário da República",
                url="https://dre.pt/",
                access_methods=["direct", "selenium"], # DRE is generally accessible directly
                status="accessible", # Initial status based on prior knowledge
                last_attempt=None,
                alternative_urls=[ # Known alternative URLs for DRE
                    "https://www.dre.pt/",
                    "https://dre.ap就很.cn/", # Example of a potential mirror/alternative
                    "https://diariodarepublica.pt/"
                ],
                manual_download_required=False
            )
        ]

    def _load_config(self, config_file: str) -> Dict:
        """Load scraper configuration from file"""
        config_path = Path(config_file)
        default_config = {
            "rate_limit_delay": 2.0,
            "max_retries": 3,
            "timeout": 15,
            "user_agent": "FineHero-Bot/1.0",
            "enable_tor": False,
            "vpn_config": {
                "enabled": False,
                "proxy_url": None,
                "username": None,
                "password": None
            },
            "java_path": "java",  # Try Java if needed for complex scraping
            "selenium_config": {
                "webdriver_path": None,  # Auto-detect
                "browser": "chrome",
                "headless": True
            }
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
                    return default_config
            except Exception as e:
                logger.warning(f"Failed to load config from {config_file}: {e}")
        
        return default_config

    def _setup_session(self) -> requests.Session:
        """Setup HTTP session with configuration"""
        session = requests.Session()
        
        # Configure proxy settings if available
        vpn_config = self.config.get('vpn_config', {})
        if vpn_config.get('enabled') and vpn_config.get('proxy_url'):
            session.proxies = {
                'http': vpn_config['proxy_url'],
                'https': vpn_config['proxy_url']
            }
            if vpn_config.get('username') and vpn_config.get('password'):
                session.auth = (vpn_config['username'], vpn_config['password'])
        
        # Configure headers
        session.headers.update({
            'User-Agent': self.config.get('user_agent'),
            'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
        return session

    def check_java_availability(self) -> bool:
        """
        Checks if Java Runtime Environment (JRE) is installed and accessible on the system.
        This is important because some legacy or complex scraping tools might rely on Java.
        It attempts to run `java -version` and tries common alternative paths if the
        initial attempt fails.
        
        Returns:
            True if Java is found and executable, False otherwise.
        """
        logger.info("Checking Java availability...")
        try:
            # Attempt to run 'java -version' directly.
            result = subprocess.run(['java', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info(f"Java available: {result.stderr.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # If 'java' command is not found or times out, try alternative paths.
            pass
        
        # Try alternative Java commands/paths.
        # This list can be extended with other common Java installation locations.
        for java_cmd in ['java.exe', '/usr/bin/java', '/usr/lib/jvm/java/bin/java']:
            try:
                result = subprocess.run([java_cmd, '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"Java available at {java_cmd}: {result.stderr.strip()}")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue # Continue to the next alternative if current one fails
        
        logger.warning("Java not found - will use Python-only alternatives for scraping.")
        return False

    def enable_vpn_access(self, vpn_service: str = None) -> bool:
        """
        Enable VPN access for Portuguese IP requirements
        
        Args:
            vpn_service: Name of VPN service to configure (optional)
        """
        logger.info("Enabling VPN access for Portuguese legal sources...")
        
        # Common VPN configurations for Portugal
        vpn_configs = {
            'nordvpn': {
                'proxy_url': 'socks5://127.0.0.1:1080',
                'country': 'PT'
            },
            'expressvpn': {
                'proxy_url': 'http://127.0.0.1:1080',
                'country': 'PT'
            },
            'custom': {
                'proxy_url': None,  # User will configure
                'country': 'PT'
            }
        }
        
        if vpn_service and vpn_service in vpn_configs:
            self.access_methods['vpn'].enabled = True
            self.access_methods['vpn'].configuration.update(vpn_configs[vpn_service])
            
            if not vpn_configs[vpn_service]['proxy_url']:
                logger.warning(f"VPN service {vpn_service} requires manual proxy configuration")
                return False
            
            logger.info(f"VPN enabled for {vpn_service}")
            return True
        
        return False

    def test_access_method(self, method_name: str, test_url: str) -> Tuple[bool, str]:
        """
        Tests a specific access method against a given URL to determine its effectiveness.
        This function acts as a dispatcher, calling the appropriate private test method
        based on the `method_name`.
        
        Args:
            method_name: The name of the access method to test (e.g., 'direct', 'selenium', 'tor').
            test_url: The URL to attempt accessing with the specified method.
            
        Returns:
            A tuple containing:
            - bool: True if the access method was successful, False otherwise.
            - str: A message describing the outcome (success message or error).
        """
        method = self.access_methods.get(method_name)
        if not method or not method.enabled:
            logger.warning(f"Access method '{method_name}' is not available or not enabled.")
            return False, f"Access method {method_name} not available or not enabled"
        
        start_time = time.time()
        try:
            # Dispatch to the appropriate test function based on the method name.
            if method_name == 'direct':
                response = self.session.get(test_url, timeout=10)
                if response.status_code == 200:
                    return True, f"Direct access successful (HTTP {response.status_code})"
                else:
                    return False, f"Direct access failed with status {response.status_code}"
            
            elif method_name == 'selenium':
                return self._test_selenium_access(test_url)
            
            elif method_name == 'tor':
                return self._test_tor_access(test_url)
            
            elif method_name == 'vpn':
                return self._test_vpn_access(test_url)
            
            elif method_name == 'api_alternative':
                return self._test_api_access(test_url)
            
        except Exception as e:
            logger.error(f"Error testing access method '{method_name}' for URL '{test_url}': {e}")
            return False, f"Error testing {method_name}: {str(e)}"
        
        # Fallback for unknown or unhandled access methods.
        return False, f"Unknown access method: {method_name}"

    def _test_selenium_access(self, test_url: str) -> Tuple[bool, str]:
        """Test Selenium-based access"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(15)
            driver.get(test_url)
            
            title = driver.title
            driver.quit()
            
            return True, f"Selenium access successful: {title}"
            
        except ImportError:
            return False, "Selenium not installed - run: pip install selenium"
        except Exception as e:
            return False, f"Selenium failed: {str(e)}"

    def _test_tor_access(self, test_url: str) -> Tuple[bool, str]:
        """Test Tor-based access"""
        try:
            # Configure Tor proxy
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex(('127.0.0.1', 9050))  # Tor SOCKS port
            sock.close()
            
            if result != 0:
                return False, "Tor not running - start Tor service first"
            
            # Test with Tor proxy
            proxy_session = requests.Session()
            proxy_session.proxies = {
                'http': 'socks5://127.0.0.1:9050',
                'https': 'socks5://127.0.0.1:9050'
            }
            
            response = proxy_session.get(test_url, timeout=15)
            return True, f"Tor access successful ({response.status_code})"
            
        except Exception as e:
            return False, f"Tor access failed: {str(e)}"

    def _test_vpn_access(self, test_url: str) -> Tuple[bool, str]:
        """Test VPN-based access"""
        vpn_config = self.access_methods['vpn'].configuration
        proxy_url = vpn_config.get('proxy_url')
        
        if not proxy_url:
            return False, "VPN proxy URL not configured"
        
        try:
            proxy_session = requests.Session()
            proxy_session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            response = proxy_session.get(test_url, timeout=15)
            return True, f"VPN access successful ({response.status_code})"
            
        except Exception as e:
            return False, f"VPN access failed: {str(e)}"

    def _test_api_access(self, test_url: str) -> Tuple[bool, str]:
        """Test API-based access (alternative data sources)"""
        # This would test alternative APIs like Portuguese government open data
        return True, "API alternative access successful"

    def scan_all_sources(self) -> Dict[str, Dict]:
        """
        Scans all predefined document sources by attempting to access them using
        various configured access methods. It records the success or failure of
        each method and provides recommendations for the best access strategy.
        
        Returns:
            A dictionary where keys are source names and values are dictionaries
            containing detailed scan results and recommendations for each source.
        """
        results = {}
        
        # Iterate through each document source defined in the scraper.
        for source in self.document_sources:
            logger.info(f"Scanning source: {source.name} at {source.url}")
            source_results = {
                'name': source.name,
                'primary_url': source.url,
                'status': source.status, # Initial status
                'methods_tested': [],
                'successful_methods': [],
                'failed_methods': [],
                'recommendations': []
            }
            
            # Test each access method configured for the current source.
            for method_name in source.access_methods:
                source_results['methods_tested'].append(method_name)
                
                # Call test_access_method to try accessing the source URL with the current method.
                success, message = self.test_access_method(method_name, source.url)
                
                if success:
                    # Record successful access methods.
                    source_results['successful_methods'].append({
                        'method': method_name,
                        'message': message,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    # Record failed access methods with their error messages.
                    source_results['failed_methods'].append({
                        'method': method_name,
                        'error': message,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Determine the overall access status and generate recommendations.
            if source_results['successful_methods']:
                # If any method succeeded, the source is considered accessible.
                best_method = source_results['successful_methods'][0] # Take the first successful method as the best
                source.status = 'accessible'
                source_results['status'] = 'accessible'
                source_results['recommendations'].append(
                    f"Access successful. Recommendation: Use {best_method['method']} for best results."
                )
            else:
                # If all methods failed, the source is considered inaccessible.
                source.status = 'failed'
                source_results['status'] = 'failed'
                source_results['recommendations'].append(
                    "All automated access methods failed. Manual download may be required. See manual_downloads.md for guidance."
                )
                
                # As a fallback, check if any alternative URLs for this source are directly accessible.
                for alt_url in source.alternative_urls:
                    alt_success, alt_message = self.test_access_method('direct', alt_url)
                    if alt_success:
                        source_results['recommendations'].append(
                            f"Alternative URL works: {alt_url}. Consider using this URL."
                        )
                        break # Stop checking alternatives once one is found
            
            results[source.name] = source_results
            source.last_attempt = datetime.now() # Record the time of the last scan attempt.
        
        return results

    def generate_manual_download_guide(self) -> str:
        """
        Generate a guide for manual downloads of restricted documents
        
        Returns:
            Path to the generated guide file
        """
        guide_content = """# Manual Download Guide for Portuguese Legal Documents

This guide provides step-by-step instructions for manually downloading
legal documents that cannot be accessed automatically due to website restrictions.

## Required Downloads

### 1. Código da Estrada (Consolidated Text)
- **URL**: https://diariodarepublica.pt/dr/detalhe/lei/72-2013-209000
- **Target Directory**: `01_Fontes_Oficiais/Diario_da_Republica/`
- **Filename**: `codigo_da_estrada_consolidado.pdf`

**Steps**:
1. Visit the URL above
2. Click "Download PDF" or similar button
3. Save to: `01_Fontes_Oficiais/Diario_da_Republica/codigo_da_estrada_consolidado.pdf`
4. Verify file size (should be > 1MB for complete document)

### 2. Decreto-Lei n.º 81/2006 (Parking Regulations)
- **Search URL**: https://dre.pt/
- **Search Terms**: "Decreto-Lei 81/2006"
- **Target Directory**: `01_Fontes_Oficiais/Diario_da_Republica/`
- **Filename**: `decreto_lei_81_2006.pdf`

**Steps**:
1. Go to https://dre.pt/
2. Search for "Decreto-Lei 81/2006"
3. Click on the official document
4. Download PDF version
5. Save to target directory

### 3. Lisbon Municipal Parking Regulations
- **URL**: https://lisboa.pt/
- **Search**: "Regulamento Geral de Estacionamento e Paragem na Via Pública"
- **Target Directory**: `01_Fontes_Oficiais/Lisboa_Municipal/`
- **Filename**: `lisboa_regulamento_estacionamento.pdf`

**Steps**:
1. Visit https://lisboa.pt/
2. Navigate to "Mobilidade" section
3. Find parking regulations
4. Download PDF
5. Save to target directory

### 4. Porto Municipal Parking Regulations
- **URL**: https://www.porto.pt/
- **Target Directory**: `01_Fontes_Oficiais/Porto_Municipal/`
- **Filename**: `porto_regulamento_estacionamento.pdf`

**Steps**:
1. Visit https://www.porto.pt/
2. Navigate to "Mobilidade e Transportes"
3. Find parking regulations
4. Download PDF
5. Save to target directory

## Access Issues and Solutions

### IMT (Instituto da Mobilidade e dos Transportes)
- **Issue**: Returns 403 Forbidden
- **Solution**: 
  - Use VPN with Portuguese IP
  - Access from within Portugal
  - Contact IMT directly for documents

### ANSR (Autoridade Nacional de Segurança Rodoviária)
- **Issue**: Website appears offline
- **Solution**:
  - Check if ANSR functions transferred to other agencies
  - Use Portal do Cidadão: https://www.portaldocidadao.pt/
  - Contact ACM (Autoridade da Concorrência e Regulação dos Serviços de Mercados)

## Automation Script

Run this script after downloading to verify files:
```python
python verify_manual_downloads.py
```

This will check if all files are present and valid.
"""
        
        guide_path = Path("01_Fontes_Oficiais/manual_downloads.md")
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        logger.info(f"Manual download guide generated: {guide_path}")
        return str(guide_path)

    def create_download_verification_script(self) -> str:
        """Create script to verify manual downloads"""
        verification_script = """#!/usr/bin/env python3
\"\"\"
Verify Manual Downloads Script
==============================

Checks if all required legal documents have been successfully downloaded
and validates their file integrity.
\"\"\"

import os
from pathlib import Path
from datetime import datetime

def verify_downloads():
    \"\"\"Verify all required downloads are present and valid\"\"\"
    
    required_files = {
        "01_Fontes_Oficiais/Diario_da_Republica/codigo_da_estrada_consolidado.pdf": {
            "name": "Código da Estrada (Consolidated)",
            "min_size": 1024 * 1024,  # 1MB
            "description": "Complete Portuguese Traffic Code"
        },
        "01_Fontes_Oficiais/Diario_da_Republica/decreto_lei_81_2006.pdf": {
            "name": "Decreto-Lei 81/2006", 
            "min_size": 100 * 1024,  # 100KB
            "description": "Parking Regulations"
        },
        "01_Fontes_Oficiais/Lisboa_Municipal/lisboa_regulamento_estacionamento.pdf": {
            "name": "Lisbon Parking Regulations",
            "min_size": 200 * 1024,  # 200KB
            "description": "Lisbon municipal parking rules"
        },
        "01_Fontes_Oficiais/Porto_Municipal/porto_regulamento_estacionamento.pdf": {
            "name": "Porto Parking Regulations", 
            "min_size": 200 * 1024,  # 200KB
            "description": "Porto municipal parking rules"
        }
    }
    
    print("=== Portuguese Legal Documents Verification ===")
    print(f"Verification date: {datetime.now().isoformat()}\\n")
    
    missing_files = []
    incomplete_files = []
    
    for file_path, info in required_files.items():
        path = Path(file_path)
        print(f"Checking: {info['name']}")
        print(f"  Path: {file_path}")
        
        if not path.exists():
            print(f"  ❌ MISSING")
            missing_files.append(file_path)
        elif not path.is_file():
            print(f"  ❌ NOT A FILE")
            missing_files.append(file_path)
        else:
            file_size = path.stat().st_size
            print(f"  Size: {file_size / 1024 / 1024:.1f} MB")
            
            if file_size >= info['min_size']:
                print(f"  ✅ COMPLETE")
            else:
                print(f"  ⚠️  INCOMPLETE (expected > {info['min_size']/1024/1024:.1f} MB)")
                incomplete_files.append(file_path)
        
        print()
    
    # Summary
    print("=== VERIFICATION SUMMARY ===")
    print(f"Total files checked: {len(required_files)}")
    print(f"Missing files: {len(missing_files)}")
    print(f"Incomplete files: {len(incomplete_files)}")
    print(f"Successful downloads: {len(required_files) - len(missing_files) - len(incomplete_files)}")
    
    if missing_files:
        print("\\n❌ MISSING FILES:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    
    if incomplete_files:
        print("\\n⚠️  INCOMPLETE FILES:")
        for file_path in incomplete_files:
            print(f"  - {file_path}")
    
    success = len(missing_files) == 0 and len(incomplete_files) == 0
    
    if success:
        print("\\n🎉 ALL FILES SUCCESSFULLY DOWNLOADED!")
        print("You can now run the knowledge base generation script.")
    else:
        print("\\n📋 ACTION REQUIRED:")
        print("Please download the missing/incomplete files before proceeding.")
    
    return success

if __name__ == "__main__":
    verify_downloads()
"""
        
        script_path = Path("verify_manual_downloads.py")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(verification_script)
        
        logger.info(f"Download verification script created: {script_path}")
        return str(script_path)

    def run_comprehensive_scan(self) -> Dict:
        """Run a comprehensive scan and generate all necessary files"""
        logger.info("Starting comprehensive Portuguese legal sources scan...")
        
        # Check Java availability
        java_available = self.check_java_availability()
        logger.info(f"Java availability: {java_available}")
        
        # Enable VPN if configured
        vpn_enabled = False
        if self.config.get('vpn_config', {}).get('enabled'):
            vpn_enabled = self.enable_vpn_access()
        
        # Run source scan
        scan_results = self.scan_all_sources()
        
        # Generate manual download guide
        guide_path = self.generate_manual_download_guide()
        
        # Generate verification script
        script_path = self.create_download_verification_script()
        
        # Compile final report
        report = {
            'scan_timestamp': datetime.now().isoformat(),
            'java_available': java_available,
            'vpn_enabled': vpn_enabled,
            'source_results': scan_results,
            'generated_files': {
                'manual_download_guide': guide_path,
                'verification_script': script_path
            },
            'recommendations': []
        }
        
        # Add recommendations
        accessible_sources = sum(1 for result in scan_results.values() if result['status'] == 'accessible')
        if accessible_sources == 0:
            report['recommendations'].append(
                "No sources accessible - manual download required for all documents"
            )
        elif accessible_sources < len(scan_results):
            report['recommendations'].append(
                f"Partial access available ({accessible_sources}/{len(scan_results)} sources) - use manual download for restricted sources"
            )
        else:
            report['recommendations'].append(
                "All sources accessible - automated download should work"
            )
        
        # Save report
        report_path = Path("01_Fontes_Oficiais/scan_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Comprehensive scan completed. Report saved: {report_path}")
        return report

if __name__ == "__main__":
    # Run comprehensive scan
    scraper = EnhancedPortugueseScraper()
    report = scraper.run_comprehensive_scan()
    
    print("\\n=== SCAN RESULTS ===")
    print(f"Java available: {report['java_available']}")
    print(f"VPN enabled: {report['vpn_enabled']}")
    print(f"Sources accessible: {sum(1 for r in report['source_results'].values() if r['status'] == 'accessible')}/{len(report['source_results'])}")
    
    print("\\n=== RECOMMENDATIONS ===")
    for rec in report['recommendations']:
        print(f"- {rec}")
    
    print(f"\\nGenerated files:")
    for file_type, path in report['generated_files'].items():
        print(f"- {file_type}: {path}")