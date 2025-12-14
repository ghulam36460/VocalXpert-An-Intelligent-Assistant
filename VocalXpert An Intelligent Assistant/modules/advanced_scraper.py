"""
Advanced Web Scraper with Search Engine Integration

Features:
    - Natural language command parsing ("web scrapper : command")
    - Three scraping modes: Normal, Deep/Force, and Realtime
    - Google, DuckDuckGo, Bing, Yahoo, and Brave search integration
    - Concurrent/parallel scraping with ThreadPoolExecutor
    - Smart retry mechanism with exponential backoff
    - Intelligent rate limiting per domain
    - Response caching to avoid duplicate requests
    - Background processing with real-time progress updates
    - Multiple scraping libraries (BeautifulSoup, Selenium, Requests)
    - Intelligent result management with JSON/CSV/Markdown export
    - Cross-source data aggregation and deduplication
    - Advanced content analysis with keyword extraction
    - Structured data extraction (tables, lists)
    - Image URL extraction
    - RSS/Atom feed parsing
    - Wikipedia API integration
    - Sentiment analysis (basic)
    - Entity extraction (people, places, organizations)

Usage:
    "web scrapper : give me list of fruits"
    "web scrapper -deep : find Python tutorials"
    "web scrapper -force : research quantum computing"
    "web scrapper -realtime : latest news about AI"
    "web scrapper --proxy : uncensored deep scraping using rotating proxies"

Dependencies:
    - requests: HTTP requests
    - beautifulsoup4: HTML parsing
    - selenium: Browser automation
    - lxml: Fast XML/HTML parsing
    - fake-useragent: User agent rotation
    - aiohttp: Asynchronous HTTP 
"""

import os
import json
import time
import threading
import uuid
import hashlib
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse, quote_plus, parse_qs
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from functools import lru_cache
import html

# Web scraping libraries
try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from fake_useragent import UserAgent
    FAKE_UA_AVAILABLE = True
except ImportError:
    FAKE_UA_AVAILABLE = False

try:
    import aiohttp
    import asyncio
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Try to import proxy manager for uncensored access
try:
    from . import proxy_manager
    PROXY_MANAGER_AVAILABLE = True
except ImportError:
    try:
        import proxy_manager
        PROXY_MANAGER_AVAILABLE = True
    except ImportError:
        PROXY_MANAGER_AVAILABLE = False
        print("Warning: proxy_manager not available. Install proxy dependencies for enhanced uncensored access.")

# Setup logging
import logging
logger = logging.getLogger('VocalXpert.AdvancedScraper')


# ============================================================================
# UTILITY CLASSES
# ============================================================================

class ResponseCache:
    """Simple in-memory cache for HTTP responses to avoid duplicate requests."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self._cache = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
    
    def _get_key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()
    
    def get(self, url: str) -> Optional[Dict]:
        key = self._get_key(url)
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if datetime.now() < entry['expires']:
                    return entry['data']
                else:
                    del self._cache[key]
        return None
    
    def set(self, url: str, data: Dict):
        key = self._get_key(url)
        with self._lock:
            # Evict oldest if full
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['expires'])
                del self._cache[oldest_key]
            
            self._cache[key] = {
                'data': data,
                'expires': datetime.now() + timedelta(seconds=self._ttl)
            }
    
    def clear(self):
        with self._lock:
            self._cache.clear()


class RateLimiter:
    """Rate limiter to avoid overwhelming servers."""
    
    def __init__(self, requests_per_second: float = 2.0):
        self._min_interval = 1.0 / requests_per_second
        self._domain_last_request = defaultdict(float)
        self._lock = threading.Lock()
    
    def wait(self, url: str):
        """Wait if necessary to respect rate limits."""
        domain = urlparse(url).netloc
        with self._lock:
            last_request = self._domain_last_request[domain]
            elapsed = time.time() - last_request
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._domain_last_request[domain] = time.time()


class RetryHandler:
    """Handles retries with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retries."""
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(delay)
                    logger.warning(f"Retry {attempt + 1}/{self.max_retries} after error: {e}")
        raise last_exception


class ScrapingResult:
    """Container for scraping results with metadata."""

    def __init__(self, query: str, mode: str, use_proxy: bool = False):
        self.id = str(uuid.uuid4())
        self.query = query
        self.mode = mode
        self.use_proxy = use_proxy
        self.timestamp = datetime.now()
        self.status = "running"
        self.progress = 0
        self.results = []
        self.sources = []
        self.errors = []
        self.metadata = {}
        self.entities = {'people': [], 'places': [], 'organizations': []}
        self.images = []
        self.tables = []
        self.keywords = []

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'query': self.query,
            'mode': self.mode,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'progress': self.progress,
            'results_count': len(self.results),
            'sources_count': len(self.sources),
            'errors_count': len(self.errors),
            'results': self.results[:100] if len(self.results) > 100 else self.results,
            'sources': self.sources,
            'errors': self.errors,
            'metadata': self.metadata,
            'entities': self.entities,
            'images': self.images[:20],
            'tables': self.tables[:10],
            'keywords': self.keywords[:30]
        }

class AdvancedWebScraper:
    """Advanced web scraping system with multiple modes and background processing."""

    def __init__(self):
        self.temp_dir = Path("temp_scraping_results")
        self.temp_dir.mkdir(exist_ok=True)

        # Active scraping tasks
        self.active_tasks: Dict[str, ScrapingResult] = {}

        # Initialize utility classes
        self.cache = ResponseCache(max_size=200, ttl_seconds=3600)
        self.rate_limiter = RateLimiter(requests_per_second=2.0)
        self.retry_handler = RetryHandler(max_retries=3)
        
        # Thread pool for concurrent scraping
        self.executor = ThreadPoolExecutor(max_workers=5)

        # Proxy manager for uncensored access (lazy initialization - only when --proxy flag is used)
        self.proxy_manager = None
        self.proxy_update_thread = None
        self.proxy_update_interval = 7200  # 2 hours in seconds
        self._proxy_initialized = False  # Track if proxy manager has been initialized

        # User agents for rotation (expanded list)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        ]

        if FAKE_UA_AVAILABLE:
            try:
                ua = UserAgent()
                self.user_agents.extend([ua.random for _ in range(5)])
            except:
                pass

        # Search engine configurations (expanded with uncensored options)
        self.search_engines = {
            'google': {
                'url': 'https://www.google.com/search?q={query}&num=15',
                'result_selector': 'div.g',
                'link_selector': 'a',
                'title_selector': 'h3',
                'snippet_selector': 'div.VwiC3b',
                'priority': 1
            },
            'duckduckgo': {
                'url': 'https://html.duckduckgo.com/html/?q={query}',
                'result_selector': 'div.result',
                'link_selector': 'a.result__a',
                'title_selector': 'a.result__a',
                'snippet_selector': 'a.result__snippet',
                'priority': 2
            },
            'bing': {
                'url': 'https://www.bing.com/search?q={query}&count=15',
                'result_selector': 'li.b_algo',
                'link_selector': 'a',
                'title_selector': 'h2',
                'snippet_selector': 'p',
                'priority': 3
            },
            'yahoo': {
                'url': 'https://search.yahoo.com/search?p={query}&n=10',
                'result_selector': 'div.algo',
                'link_selector': 'a',
                'title_selector': 'h3',
                'snippet_selector': 'p',
                'priority': 4
            },
            'brave': {
                'url': 'https://search.brave.com/search?q={query}',
                'result_selector': 'div.snippet',
                'link_selector': 'a',
                'title_selector': 'span.title',
                'snippet_selector': 'p.snippet-description',
                'priority': 5
            },
            'startpage': {
                'url': 'https://www.startpage.com/sp/search?q={query}&cat=web&pl=opensearch',
                'result_selector': 'div.result',
                'link_selector': 'a.result-link',
                'title_selector': 'a.result-link',
                'snippet_selector': 'p.result-snippet',
                'priority': 6
            },
            'qwant': {
                'url': 'https://www.qwant.com/?q={query}&t=web',
                'result_selector': 'div.result',
                'link_selector': 'a.external',
                'title_selector': 'span.result-title',
                'snippet_selector': 'span.result-desc',
                'priority': 7
            },
            'mojeek': {
                'url': 'https://www.mojeek.com/search?q={query}',
                'result_selector': 'div.result',
                'link_selector': 'a.title',
                'title_selector': 'a.title',
                'snippet_selector': 'p.s',
                'priority': 8
            }
        }
        
        # Wikipedia API endpoint
        self.wikipedia_api = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        self.wikipedia_search_api = "https://en.wikipedia.org/w/api.php"
        
        # Data directory for storing scraped content
        self.data_dir = Path("temp_scraping_results") / "scraped_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Export directory
        self.export_dir = Path("temp_scraping_results") / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # Common stop words for keyword extraction
        self.stop_words = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought',
            'used', 'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'when', 'where', 'why',
            'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'just', 'also', 'now', 'here', 'there', 'then', 'once'
        ])

    def _initialize_proxy_manager(self):
        """Initialize proxy manager for uncensored access (lazy initialization - only called when --proxy flag is used)"""
        if self._proxy_initialized:
            return  # Already initialized
            
        if not PROXY_MANAGER_AVAILABLE:
            logger.warning("Proxy manager not available. Install proxy dependencies for enhanced uncensored access.")
            return
            
        try:
            logger.info("Initializing proxy manager (--proxy flag detected)...")
            self.proxy_manager = proxy_manager.AdvancedProxyManager({
                'min_proxies': 20,
                'max_proxies': 200,
                'validation_interval': 300,  # 5 minutes
                'rotation_strategy': 'round_robin'
            })
            
            # Initialize proxy manager asynchronously
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.proxy_manager.initialize())
            loop.close()
            
            # Start automatic proxy updates every 2 hours
            self._start_proxy_auto_update()
            
            self._proxy_initialized = True
            logger.info(f"Proxy manager initialized with {len(self.proxy_manager.working_proxies)} working proxies")
            
        except Exception as e:
            logger.error(f"Failed to initialize proxy manager: {e}")
            self.proxy_manager = None

    def _start_proxy_auto_update(self):
        """Start automatic proxy updates every 2 hours"""
        if not self.proxy_manager:
            return
            
        def update_proxies():
            while True:
                try:
                    time.sleep(self.proxy_update_interval)
                    logger.info("Auto-updating proxy list...")
                    
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.proxy_manager.refresh_proxies())
                    loop.close()
                    
                    logger.info(f"Proxy list updated. Working proxies: {len(self.proxy_manager.working_proxies)}")
                    
                except Exception as e:
                    logger.error(f"Proxy auto-update failed: {e}")
                    time.sleep(300)  # Retry in 5 minutes on error
        
        self.proxy_update_thread = threading.Thread(target=update_proxies, daemon=True)
        self.proxy_update_thread.start()

    def _get_proxy_for_url(self, url: str, use_proxy: bool = False) -> Optional[Dict[str, str]]:
        """Get appropriate proxy for URL (lazy initialization - only when use_proxy=True)"""
        if not use_proxy:
            return None
        
        # Lazy initialize proxy manager only when --proxy flag is used
        if not self._proxy_initialized:
            self._initialize_proxy_manager()
            
        if not self.proxy_manager:
            logger.warning("Proxy manager not available, scraping without proxy")
            return None
            
        # Get a proxy from the manager
        proxy = self.proxy_manager.get_proxy()
        if proxy:
            return proxy.get_proxy_dict()
        
        return None

    def _create_browser_with_proxy(self, browser_type: str = 'chrome', proxy: Optional[Dict] = None) -> Optional[Any]:
        """Create a browser instance with proxy support"""
        if not SELENIUM_AVAILABLE:
            return None
            
        try:
            # For older selenium versions
            if browser_type.lower() == 'brave':
                # Try to find Brave browser
                brave_paths = [
                    'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
                    'C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
                    '/usr/bin/brave-browser',
                    '/usr/local/bin/brave-browser'
                ]
                brave_path = None
                for path in brave_paths:
                    if os.path.exists(path):
                        brave_path = path
                        break
                
                if brave_path:
                    from selenium.webdriver.chrome.options import Options
                    options = Options()
                    options.binary_location = brave_path
                    options.add_argument('--headless')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--disable-gpu')
                    options.add_argument('--window-size=1920,1080')
                    options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
                    
                    if proxy and proxy.get('http'):
                        proxy_url = proxy['http'].replace('http://', '')
                        options.add_argument(f'--proxy-server=http://{proxy_url}')
                    
                    return webdriver.Chrome(options=options)
                else:
                    logger.warning("Brave browser not found, falling back to Chrome")
            
            elif browser_type.lower() == 'firefox':
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                firefox_options = FirefoxOptions()
                firefox_options.add_argument('--headless')
                profile = webdriver.FirefoxProfile()
                if proxy and proxy.get('http'):
                    proxy_url = proxy['http'].replace('http://', '')
                    host, port = proxy_url.split(':')
                    profile.set_preference('network.proxy.type', 1)
                    profile.set_preference('network.proxy.http', host)
                    profile.set_preference('network.proxy.http_port', int(port))
                    profile.set_preference('network.proxy.ssl', host)
                    profile.set_preference('network.proxy.ssl_port', int(port))
                return webdriver.Firefox(options=firefox_options, firefox_profile=profile)
            
            # Default to Chrome
            from selenium.webdriver.chrome.options import Options
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
            
            if proxy and proxy.get('http'):
                proxy_url = proxy['http'].replace('http://', '')
                options.add_argument(f'--proxy-server=http://{proxy_url}')
            
            return webdriver.Chrome(options=options)
                
        except Exception as e:
            logger.error(f"Failed to create {browser_type} browser with proxy: {e}")
            return None

    def _scrape_with_browser(self, url: str, proxies: Optional[Dict] = None) -> Optional[Dict]:
        """Scrape content using browser automation for sites that block requests"""
        driver = None
        try:
            # Try Brave browser first for adult content
            driver = self._create_browser_with_proxy('brave', proxies)
            if not driver:
                # Fallback to Chrome
                driver = self._create_browser_with_proxy('chrome', proxies)
            
            if not driver:
                logger.error("No browser available for scraping")
                return None
            
            driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Get page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                script.decompose()
            
            # Extract title
            title = ''
            if soup.title:
                title = soup.title.string or ''
            if not title:
                h1 = soup.find('h1')
                title = h1.get_text().strip() if h1 else ''
            
            # Extract main content
            content = ''
            main_selectors = ['main', 'article', '[role="main"]', '.content', '#content', '.post', '.entry', '.article-body']
            
            for selector in main_selectors:
                main_elem = soup.select_one(selector)
                if main_elem:
                    content = main_elem.get_text(separator=' ', strip=True)
                    break
            
            # Fallback to body
            if not content or len(content) < 100:
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)
            
            # Extract links if needed
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('http') and len(href) > 10:
                    links.append({
                        'url': href,
                        'text': a.get_text().strip()[:100]
                    })
            
            return {
                'title': title[:200],
                'content': content[:5000],
                'url': url,
                'links': links[:20],
                'method': 'browser'
            }
            
        except Exception as e:
            logger.error(f"Browser scraping failed for {url}: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def parse_command(self, query: str) -> Tuple[str, str, bool]:
        """
        Parse web scraper command.

        Args:
            query: Full command string

        Returns:
            Tuple of (mode, actual_query, use_proxy)
            
        Note:
            When --proxy flag is used without specifying a mode, it automatically
            enables 'deep' mode for comprehensive scraping with uncensored access.
        """
        query = query.strip()

        # Check for proxy flag
        use_proxy = False
        if " --proxy " in query or query.endswith(" --proxy"):
            use_proxy = True
            query = query.replace(" --proxy", "").strip()

        # Check for mode flags
        mode = "normal"
        if " -deep " in query or query.endswith(" -deep"):
            mode = "deep"
            query = query.replace(" -deep", "").strip()
        elif " -force " in query or query.endswith(" -force"):
            mode = "deep"
            query = query.replace(" -force", "").strip()
        elif " -realtime " in query or query.endswith(" -realtime"):
            mode = "realtime"
            query = query.replace(" -realtime", "").strip()
        elif " -fast " in query or query.endswith(" -fast"):
            mode = "fast"
            query = query.replace(" -fast", "").strip()

        # If proxy is enabled and no specific mode was set, default to deep mode
        # This provides more thorough scraping when using proxies for uncensored access
        if use_proxy and mode == "normal":
            mode = "deep"
            logger.info("--proxy flag detected, automatically enabling deep scraping mode for comprehensive results")

        # Remove "web scrapper" or "web scraper" prefix (support both spellings)
        query = re.sub(r'^web\s+scrapp?er\s*[:,\s]*', '', query, flags=re.IGNORECASE).strip()
        
        # Also handle -mode at the start
        query = re.sub(r'^-?(deep|force|realtime|fast)\s*[:,\s]*', '', query, flags=re.IGNORECASE).strip()

        return mode, query, use_proxy

    def start_scraping(self, command: str) -> str:
        """
        Start a web scraping task.

        Args:
            command: Full command string

        Returns:
            Task ID for tracking
        """
        try:
            mode, query, use_proxy = self.parse_command(command)

            if not query:
                return "ERROR: Please provide a search query after 'web scrapper'"

            # Initialize proxy manager only if --proxy flag is used (lazy initialization)
            if use_proxy and not self._proxy_initialized:
                logger.info("--proxy flag detected, initializing proxy manager...")
                self._initialize_proxy_manager()

            # Create result container
            result = ScrapingResult(query, mode, use_proxy)
            self.active_tasks[result.id] = result

            # Start background scraping
            thread = threading.Thread(
                target=self._scrape_worker,
                args=(result,),
                daemon=True
            )
            thread.start()

            return f"Started {mode} web scraping for: '{query}'\nTask ID: {result.id}\nProcessing in background..."

        except Exception as e:
            logger.error(f"Failed to start scraping: {e}")
            return f"ERROR: Failed to start scraping: {str(e)}"

    def _scrape_worker(self, result: ScrapingResult):
        """Background worker for scraping tasks."""
        try:
            if result.mode == "normal":
                self._normal_scrape(result)
            elif result.mode == "fast":
                self._fast_scrape(result)
            elif result.mode == "realtime":
                self._realtime_scrape(result)
            else:  # deep mode
                self._deep_scrape(result)

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            result.errors.append(str(e))
            result.status = "error"

        finally:
            # Post-processing: Extract entities and keywords
            self._extract_entities(result)
            self._extract_keywords(result)
            
            # Save results
            self._save_results_if_large(result)

    def _fast_scrape(self, result: ScrapingResult):
        """Perform fast scraping using Wikipedia API and cached results."""
        result.status = "running"
        result.progress = 10
        
        query = result.query
        all_results = []
        
        # Try Wikipedia API first (fastest)
        wiki_result = self._query_wikipedia_api(query)
        if wiki_result:
            all_results.append(wiki_result)
            result.sources.append('Wikipedia API')
        
        result.progress = 50
        
        # Quick search with caching
        search_results = self._search_web(query, max_results=3, use_cache=True, use_proxy=result.use_proxy)
        
        # Parallel scraping for speed
        if search_results:
            urls = [s.get('url') for s in search_results if s.get('url') and self._is_valid_url(s.get('url'))]
            scraped = self._parallel_scrape(urls[:3], query)
            all_results.extend(scraped)
        
        result.progress = 80
        
        # Quick analysis
        result.results = self._analyze_results(all_results, query)
        
        result.metadata = {
            'total_sources': len(result.sources),
            'results_found': len(result.results),
            'mode': 'fast',
            'scraping_time': (datetime.now() - result.timestamp).total_seconds()
        }
        
        result.status = "completed"
        result.progress = 100

    def _realtime_scrape(self, result: ScrapingResult):
        """Perform realtime scraping focusing on recent/news content."""
        result.status = "running"
        result.progress = 5
        
        query = result.query
        all_results = []
        
        # Add time-related terms for freshness
        time_query = f"{query} latest news today 2024 2025"
        
        result.progress = 10
        
        # Search with focus on news
        search_results = self._search_web(time_query, max_results=10, use_all_engines=True, use_proxy=result.use_proxy)
        
        # Filter for news-like sources
        news_domains = ['news', 'bbc', 'cnn', 'reuters', 'guardian', 'times', 'post', 'daily']
        news_results = []
        other_results = []
        
        for item in search_results:
            url = item.get('url', '').lower()
            if any(domain in url for domain in news_domains):
                news_results.append(item)
            else:
                other_results.append(item)
        
        # Prioritize news sources
        prioritized = news_results + other_results
        
        result.progress = 30
        
        # Parallel scraping
        urls = [s.get('url') for s in prioritized if s.get('url') and self._is_valid_url(s.get('url'))]
        all_results = self._parallel_scrape(urls[:8], query)
        
        result.progress = 70
        
        # Check for RSS feeds
        rss_results = self._try_rss_feeds(query)
        all_results.extend(rss_results)
        
        result.progress = 85
        
        # Analyze with date weighting
        analyzed = self._analyze_results(all_results, query)
        result.results = analyzed
        
        result.metadata = {
            'total_sources': len(result.sources),
            'results_found': len(result.results),
            'mode': 'realtime',
            'scraping_time': (datetime.now() - result.timestamp).total_seconds(),
            'news_sources_found': len(news_results)
        }
        
        result.status = "completed"
        result.progress = 100

    def _normal_scrape(self, result: ScrapingResult):
        """Perform normal web scraping (quick, surface-level)."""
        result.status = "running"
        result.progress = 5

        query = result.query
        all_results = []
        
        # Check if this is an adult query
        adult_keywords = ['porn', 'sex', 'adult', 'xxx', 'nsfw', 'erotic', 'nude', 'naked', 'fuck', '18+', 'hentai', 'anime porn', 'korean porn', 'japanese porn', 'asian porn']
        is_adult_query = any(keyword in query.lower() for keyword in adult_keywords)
        
        logger.info(f"Normal scrape adult detection: query='{query}', is_adult={is_adult_query}")
        print(f"DEBUG: Normal adult detection - query='{query}', is_adult={is_adult_query}")
        
        if is_adult_query:
            # For adult queries, directly scrape adult sources only (no censorship - no fallback to search engines)
            result.progress = 10
            logger.info(f"Adult query detected - using direct adult source scraping only (uncensored mode): {query}")
            print(f"DEBUG: Adult query detected - uncensored mode: {query}")
            
            adult_sources = [
                {'url': 'https://www.pornhub.com', 'type': 'adult'},
                {'url': 'https://www.xvideos.com', 'type': 'adult'},
                {'url': 'https://www.xnxx.com', 'type': 'adult'},
                {'url': 'https://www.youporn.com', 'type': 'adult'},
                {'url': 'https://www.redtube.com', 'type': 'adult'},
                {'url': 'https://www.xhamster.com', 'type': 'adult'},
                {'url': 'https://www.tube8.com', 'type': 'adult'},
                {'url': 'https://www.spankbang.com', 'type': 'adult'},
            ]
            
            for i, source in enumerate(adult_sources):
                try:
                    result.progress = 10 + (i / len(adult_sources)) * 90
                    url = source['url']
                    logger.info(f"Scraping adult source (uncensored): {url}")
                    
                    # Use proxy and browser fallback for adult sites
                    page_data = self._scrape_url(url, query, use_proxy=result.use_proxy)
                    if page_data:
                        page_data['source_type'] = 'adult_direct_uncensored'
                        all_results.append(page_data)
                        result.sources.append(url)
                        
                except Exception as e:
                    logger.warning(f"Failed to scrape adult source {url}: {e}")
                    result.errors.append(f"Adult source {url}: {str(e)}")
        else:
            # Step 1: Search using search engines to find relevant URLs
            result.progress = 10
            logger.info(f"Searching for: {query}")
            search_results = self._search_web(query, max_results=5, use_proxy=result.use_proxy)
            
            if search_results:
                result.progress = 25
                logger.info(f"Found {len(search_results)} URLs from search engines")
                
                # Step 2: Scrape each discovered URL
                for i, search_item in enumerate(search_results):
                    try:
                        result.progress = 25 + (i / len(search_results)) * 40
                        url = search_item.get('url', '')
                        if url and self._is_valid_url(url):
                            page_data = self._scrape_url(url, query, use_proxy=result.use_proxy)
                            if page_data:
                                page_data['search_title'] = search_item.get('title', '')
                                page_data['search_snippet'] = search_item.get('snippet', '')
                                all_results.append(page_data)
                                result.sources.append(url)
                    except Exception as e:
                        result.errors.append(f"URL {search_item.get('url', 'unknown')}: {str(e)}")
        
        # Step 3: Also try predefined sources as backup
        result.progress = 65
        predefined_sources = self._get_search_sources(query, limit=2)
        for source in predefined_sources:
            try:
                data = self._scrape_source(source, query, depth="normal")
                if data:
                    all_results.extend(data)
                    if source['url'] not in result.sources:
                        result.sources.append(source['url'])
            except Exception as e:
                result.errors.append(f"Source {source['url']}: {str(e)}")

        result.progress = 75
        
        # Step 4: Save raw data to file
        raw_data_file = self._save_raw_data(result.id, query, all_results)
        
        # Step 5: Analyze and summarize results
        result.progress = 85
        analyzed_results = self._analyze_results(all_results, query)
        result.results = analyzed_results

        # Add metadata
        result.metadata = {
            'total_sources': len(result.sources),
            'results_found': len(result.results),
            'raw_data_file': str(raw_data_file) if raw_data_file else None,
            'scraping_time': (datetime.now() - result.timestamp).total_seconds(),
            'search_engines_used': list(self.search_engines.keys())
        }

        result.status = "completed"
        result.progress = 100

    def _deep_scrape(self, result: ScrapingResult):
        """Perform deep web scraping (thorough, multi-source)."""
        result.status = "running"
        result.progress = 5

        query = result.query
        all_results = []
        related_terms = []
        
        # Check if this is an adult query - prioritize direct adult source scraping
        adult_keywords = ['porn', 'sex', 'adult', 'xxx', 'nsfw', 'erotic', 'nude', 'naked', 'fuck', '18+', 'hentai', 'anime porn', 'korean porn', 'japanese porn', 'asian porn']
        is_adult_query = any(keyword in query.lower() for keyword in adult_keywords)
        
        logger.info(f"Adult query detection: query='{query}', is_adult={is_adult_query}")
        print(f"DEBUG: Adult detection - query='{query}', keywords={adult_keywords}, is_adult={is_adult_query}")
        
        if is_adult_query:
            # For adult queries in deep mode, directly scrape adult sources first (uncensored mode)
            result.progress = 10
            logger.info(f"Adult query detected in deep mode - using direct adult source scraping only (uncensored mode): {query}")
            print(f"DEBUG: Adult query detected in deep mode - uncensored mode: {query}")
            
            adult_sources = [
                {'url': 'https://www.pornhub.com', 'type': 'adult'},
                {'url': 'https://www.xvideos.com', 'type': 'adult'},
                {'url': 'https://www.xnxx.com', 'type': 'adult'},
                {'url': 'https://www.youporn.com', 'type': 'adult'},
                {'url': 'https://www.redtube.com', 'type': 'adult'},
                {'url': 'https://www.xhamster.com', 'type': 'adult'},
                {'url': 'https://www.tube8.com', 'type': 'adult'},
                {'url': 'https://www.spankbang.com', 'type': 'adult'},
            ]
            
            for i, source in enumerate(adult_sources):
                try:
                    result.progress = 10 + (i / len(adult_sources)) * 35  # Leave room for search engines
                    url = source['url']
                    logger.info(f"Priority scraping adult source (proxy uncensored): {url}")
                    
                    # Use proxy and browser fallback for adult sites
                    page_data = self._scrape_url(url, query, extract_links=True, use_proxy=result.use_proxy)
                    if page_data:
                        page_data['source_type'] = 'adult_direct_priority_proxy'
                        page_data['priority'] = 'high'
                        all_results.append(page_data)
                        result.sources.append(url)
                        
                        # For deep mode with proxy, scrape more linked pages from adult sites
                        linked_urls = page_data.get('linked_urls', [])[:5]  # More links for proxy mode
                        for linked_url in linked_urls:
                            try:
                                if self._is_valid_url(linked_url) and any(keyword in linked_url.lower() for keyword in ['porn', 'sex', 'adult', 'xxx', 'video', 'watch']):
                                    linked_data = self._scrape_url(linked_url, query, extract_links=False, use_proxy=result.use_proxy)
                                    if linked_data:
                                        linked_data['source_type'] = 'adult_linked_priority_proxy'
                                        linked_data['parent_url'] = url
                                        linked_data['priority'] = 'medium'
                                        all_results.append(linked_data)
                                        result.sources.append(linked_url)
                            except Exception as e:
                                logger.warning(f"Failed to scrape priority adult link {linked_url}: {e}")
                        
                except Exception as e:
                    logger.warning(f"Failed to priority scrape adult source {url}: {e}")
                    result.errors.append(f"Priority adult source {url}: {str(e)}")
            
            # Generate related terms for adult content and do search engines with lower priority
            related_terms = self._generate_related_terms(query)
            all_queries = [query] + related_terms[:2]  # Limit to 2 related terms for adult
            
            result.progress = 50
            logger.info(f"Adult deep scraping - now searching engines with queries: {all_queries}")
            
            # Search using multiple search engines (lower priority for adult content)
            all_search_results = []
            for search_query in all_queries:
                search_results = self._search_web(search_query, max_results=8, use_all_engines=True, use_proxy=result.use_proxy)  # Fewer results for adult
                all_search_results.extend(search_results)
            
            # Remove duplicate URLs and prioritize adult URLs
            seen_urls = set()
            unique_search_results = []
            for item in all_search_results:
                url = item.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    # Prioritize URLs that look like adult content
                    is_adult_url = any(keyword in url.lower() for keyword in ['porn', 'sex', 'adult', 'xxx', 'nsfw', 'erotic', 'xvideos', 'pornhub', 'xnxx', 'youporn'])
                    item['priority'] = 'high' if is_adult_url else 'normal'
                    unique_search_results.append(item)
            
            # Sort by priority (adult URLs first)
            unique_search_results.sort(key=lambda x: x.get('priority', 'normal'), reverse=True)
            
            result.progress = 60
            logger.info(f"Found {len(unique_search_results)} unique URLs from search engines (prioritized adult content)")
            
            # Scrape search results with priority for adult URLs
            for i, search_item in enumerate(unique_search_results[:12]):  # Limit for adult deep mode
                try:
                    result.progress = 60 + (i / min(len(unique_search_results), 12)) * 30
                    url = search_item.get('url', '')
                    if url and self._is_valid_url(url):
                        priority = search_item.get('priority', 'normal')
                        page_data = self._scrape_url(url, query, extract_links=True, use_proxy=result.use_proxy)
                        if page_data:
                            page_data['search_title'] = search_item.get('title', '')
                            page_data['search_snippet'] = search_item.get('snippet', '')
                            page_data['source_type'] = f'search_engine_adult_{priority}'
                            page_data['priority'] = priority
                            all_results.append(page_data)
                            result.sources.append(url)
                            
                            # For high priority adult URLs, scrape more linked pages
                            if priority == 'high':
                                linked_urls = page_data.get('linked_urls', [])[:5]
                            else:
                                linked_urls = page_data.get('linked_urls', [])[:2]
                            
                            for linked_url in linked_urls:
                                try:
                                    if self._is_valid_url(linked_url) and linked_url not in seen_urls:
                                        seen_urls.add(linked_url)
                                        linked_data = self._scrape_url(linked_url, query, extract_links=False, use_proxy=result.use_proxy)
                                        if linked_data:
                                            linked_data['source_type'] = f'linked_adult_{priority}'
                                            linked_data['parent_url'] = url
                                            linked_data['priority'] = 'low'
                                            all_results.append(linked_data)
                                            result.sources.append(linked_url)
                                except Exception as e:
                                    logger.warning(f"Failed to scrape adult linked page {linked_url}: {e}")
                except Exception as e:
                    result.errors.append(f"Adult search URL {search_item.get('url', 'unknown')}: {str(e)}")
            
        else:
            # Step 1: Generate related search terms for comprehensive coverage
            related_terms = self._generate_related_terms(query)
            all_queries = [query] + related_terms[:3]
            
            result.progress = 50
            logger.info(f"Deep scraping with queries: {all_queries}")
            
            # Step 2: Search using multiple search engines
            all_search_results = []
            for search_query in all_queries:
                search_results = self._search_web(search_query, max_results=10, use_all_engines=True, use_proxy=result.use_proxy)
                all_search_results.extend(search_results)
            
            # Remove duplicate URLs
            seen_urls = set()
            unique_search_results = []
            for item in all_search_results:
                url = item.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_search_results.append(item)
            
            result.progress = 60
            logger.info(f"Found {len(unique_search_results)} unique URLs from search engines")
            
            # Step 3: Scrape each discovered URL
            for i, search_item in enumerate(unique_search_results[:15]):  # Limit to 15 for deep
                try:
                    result.progress = 20 + (i / min(len(unique_search_results), 15)) * 45
                    url = search_item.get('url', '')
                    if url and self._is_valid_url(url):
                        page_data = self._scrape_url(url, query, extract_links=True, use_proxy=result.use_proxy)
                        if page_data:
                            page_data['search_title'] = search_item.get('title', '')
                            page_data['search_snippet'] = search_item.get('snippet', '')
                            page_data['search_engine'] = search_item.get('engine', 'unknown')
                            all_results.append(page_data)
                            result.sources.append(url)
                            
                            # For deep mode, also scrape linked pages (1 level deep)
                            linked_urls = page_data.get('linked_urls', [])[:3]
                            for linked_url in linked_urls:
                                try:
                                    if self._is_valid_url(linked_url) and linked_url not in seen_urls:
                                        seen_urls.add(linked_url)
                                        linked_data = self._scrape_url(linked_url, query, use_proxy=result.use_proxy)
                                        if linked_data:
                                            linked_data['parent_url'] = url
                                            all_results.append(linked_data)
                                except:
                                    pass
                except Exception as e:
                    result.errors.append(f"URL {search_item.get('url', 'unknown')}: {str(e)}")
            
            # Step 4: Also try predefined sources
            result.progress = 65
            predefined_sources = self._get_search_sources(query, limit=5)
            for source in predefined_sources:
                try:
                    data = self._scrape_source(source, query, depth="deep")
                    if data:
                        all_results.extend(data)
                        if source['url'] not in result.sources:
                            result.sources.append(source['url'])
                except Exception as e:
                    result.errors.append(f"Source {source['url']}: {str(e)}")
        
        result.progress = 75
        
        # Step 5: Save raw data to file
        raw_data_file = self._save_raw_data(result.id, query, all_results, is_deep=True)
        
        # Step 6: Comprehensive analysis and summarization
        result.progress = 85
        analyzed_results = self._analyze_results_deep(all_results, query)
        result.results = analyzed_results

        # Add comprehensive metadata
        result.metadata = {
            'total_sources': len(result.sources),
            'results_found': len(result.results),
            'related_searches': len(related_terms),
            'raw_data_file': str(raw_data_file) if raw_data_file else None,
            'scraping_time': (datetime.now() - result.timestamp).total_seconds(),
            'deep_analysis': True,
            'adult_content': is_adult_query,
            'proxy_used': use_proxy,
            'search_engines_used': list(self.search_engines.keys()),
            'queries_searched': all_queries,
            'adult_sources_prioritized': is_adult_query and use_proxy
        }

        result.status = "completed"
        result.progress = 100

    def _get_search_sources(self, query: str, limit: int = 5) -> List[Dict]:
        """Get relevant sources for scraping based on query."""
        # Categorized sources for different types of queries
        base_sources = [
            {'url': 'https://en.wikipedia.org', 'type': 'encyclopedia'},
            {'url': 'https://www.britannica.com', 'type': 'reference'},
            {'url': 'https://www.quora.com', 'type': 'community'},
        ]
        
        dictionary_sources = [
            {'url': 'https://www.dictionary.com', 'type': 'dictionary'},
            {'url': 'https://www.thesaurus.com', 'type': 'thesaurus'},
            {'url': 'https://www.merriam-webster.com', 'type': 'dictionary'},
        ]
        
        technical_sources = [
            {'url': 'https://stackoverflow.com', 'type': 'technical'},
            {'url': 'https://github.com', 'type': 'code'},
            {'url': 'https://www.geeksforgeeks.org', 'type': 'technical'},
        ]
        
        academic_sources = [
            {'url': 'https://www.sciencedirect.com', 'type': 'academic'},
            {'url': 'https://scholar.google.com', 'type': 'academic'},
        ]
        
        entertainment_sources = [
            {'url': 'https://en.wikipedia.org', 'type': 'encyclopedia'},
            {'url': 'https://www.imdb.com', 'type': 'entertainment'},
            {'url': 'https://www.rottentomatoes.com', 'type': 'entertainment'},
            {'url': 'https://www.themoviedb.org', 'type': 'entertainment'},
        ]
        
        news_sources = [
            {'url': 'https://en.wikipedia.org', 'type': 'encyclopedia'},
            {'url': 'https://www.britannica.com', 'type': 'reference'},
            {'url': 'https://www.bbc.com', 'type': 'news'},
        ]
        
        # New uncensored source categories
        social_media_sources = [
            {'url': 'https://www.reddit.com', 'type': 'social'},
            {'url': 'https://www.twitter.com', 'type': 'social'},
            {'url': 'https://www.facebook.com', 'type': 'social'},
            {'url': 'https://www.instagram.com', 'type': 'social'},
            {'url': 'https://www.tiktok.com', 'type': 'social'},
            {'url': 'https://www.youtube.com', 'type': 'social'},
        ]
        
        forum_sources = [
            {'url': 'https://forum.bodybuilding.com', 'type': 'forum'},
            {'url': 'https://www.bodybuilding.com', 'type': 'fitness'},
            {'url': 'https://www.resetera.com', 'type': 'gaming'},
            {'url': 'https://www.neogaf.com', 'type': 'gaming'},
        ]
        
        alternative_news_sources = [
            {'url': 'https://www.zerohedge.com', 'type': 'news'},
            {'url': 'https://www.thegatewaypundit.com', 'type': 'news'},
            {'url': 'https://www.infowars.com', 'type': 'news'},
            {'url': 'https://www.breitbart.com', 'type': 'news'},
        ]
        
        uncensored_search_sources = [
            {'url': 'https://www.duckduckgo.com', 'type': 'search'},
            {'url': 'https://www.startpage.com', 'type': 'search'},
            {'url': 'https://www.qwant.com', 'type': 'search'},
        ]
        
        # Adult content sources for uncensored scraping
        adult_sources = [
            {'url': 'https://www.pornhub.com', 'type': 'adult'},
            {'url': 'https://www.xvideos.com', 'type': 'adult'},
            {'url': 'https://www.xnxx.com', 'type': 'adult'},
            {'url': 'https://www.youporn.com', 'type': 'adult'},
            {'url': 'https://www.redtube.com', 'type': 'adult'},
            {'url': 'https://www.tube8.com', 'type': 'adult'},
        ]

        # Filter sources based on query type
        query_lower = query.lower()

        # Check for specific query patterns
        if any(word in query_lower for word in ['definition', 'meaning', 'what does', 'define']):
            # Definition queries - only use dictionary sources
            relevant = dictionary_sources + [base_sources[0]]  # Add Wikipedia
        elif any(word in query_lower for word in ['code', 'programming', 'python', 'javascript', 'api', 'software', 'developer', 'coding']):
            # Technical queries
            relevant = technical_sources + [base_sources[0]]
        elif any(word in query_lower for word in ['research', 'study', 'academic', 'paper', 'scientific']):
            # Academic queries
            relevant = academic_sources + [base_sources[0]]
        elif any(word in query_lower for word in ['porn', 'sex', 'adult', 'xxx', 'nsfw', 'erotic', 'nude', 'naked', 'fuck', 'sex']):
            # Adult/porn queries - use adult content sources (check before entertainment)
            relevant = adult_sources + social_media_sources[:2]  # Include some social media for discussions
        elif any(word in query_lower for word in ['movie', 'film', 'actor', 'actress', 'hollywood', 'bollywood', 
                                                    'celebrity', 'star', 'rating', 'rated', 'best', 'top',
                                                    'tv', 'show', 'series', 'entertainment', 'music', 'singer']):
            # Entertainment/celebrity queries
            relevant = entertainment_sources
        elif any(word in query_lower for word in ['news', 'current', 'today', 'latest', 'breaking']):
            # News/current events - include both mainstream and alternative
            relevant = news_sources + alternative_news_sources[:2]  # Add 2 alternative sources
        elif any(word in query_lower for word in ['social', 'twitter', 'facebook', 'instagram', 'tiktok', 'reddit', 'forum', 'discussion']):
            # Social media and forum queries
            relevant = social_media_sources + forum_sources[:2]
        elif any(word in query_lower for word in ['fitness', 'bodybuilding', 'workout', 'exercise', 'gym']):
            # Fitness queries
            relevant = [{'url': 'https://www.bodybuilding.com', 'type': 'fitness'}] + forum_sources[:1]
        elif any(word in query_lower for word in ['gaming', 'game', 'video game', 'console', 'pc gaming']):
            # Gaming queries
            relevant = [{'url': 'https://www.resetera.com', 'type': 'gaming'}, {'url': 'https://www.neogaf.com', 'type': 'gaming'}]
        elif any(word in query_lower for word in ['porn', 'sex', 'adult', 'xxx', 'nsfw', 'erotic', 'nude', 'naked', 'fuck', 'sex']):
            # Adult/porn queries - use adult content sources
            relevant = adult_sources + social_media_sources[:2]  # Include some social media for discussions
        elif any(word in query_lower for word in ['who is', 'what is', 'information about', 'tell me about', 'about the', 'list of', 'find']):
            # General informational queries - use encyclopedias and community sources
            relevant = base_sources + entertainment_sources[:1]
        elif any(word in query_lower for word in ['controversial', 'debate', 'opinion', 'political', 'conspiracy']):
            # Controversial/political queries - include alternative sources
            relevant = alternative_news_sources + social_media_sources[:2] + forum_sources[:1]
        else:
            # General queries - use general sources (not dictionaries)
            relevant = base_sources

        return relevant[:limit]

    def _search_web(self, query: str, max_results: int = 10, use_all_engines: bool = False, use_cache: bool = False, use_proxy: bool = False) -> List[Dict]:
        """Search the web using multiple search engines to find relevant URLs."""
        all_results = []
        # Use more privacy-focused engines by default for uncensored results
        engines_to_use = list(self.search_engines.keys()) if use_all_engines else ['duckduckgo', 'startpage', 'qwant', 'google']
        
        for engine_name in engines_to_use:
            try:
                results = self._search_single_engine(engine_name, query, max_results, use_cache, use_proxy)
                for r in results:
                    r['engine'] = engine_name
                all_results.extend(results)
                
                # If we got enough results, we can stop
                if len(all_results) >= max_results and not use_all_engines:
                    break
                    
                # Small delay between search engines to avoid rate limiting
                self.rate_limiter.wait(f"https://{engine_name}.com")
                
            except Exception as e:
                logger.warning(f"Search engine {engine_name} failed: {e}")
                continue
        
        return all_results[:max_results * 2] if use_all_engines else all_results[:max_results]

    def _search_single_engine(self, engine_name: str, query: str, max_results: int = 10, use_cache: bool = False, use_proxy: bool = False) -> List[Dict]:
        """Search using a single search engine."""
        if not REQUESTS_AVAILABLE:
            return []
        
        engine = self.search_engines.get(engine_name)
        if not engine:
            return []
        
        search_url = engine['url'].format(query=quote_plus(query))
        
        # Check cache first
        if use_cache:
            cached = self.cache.get(search_url)
            if cached:
                logger.info(f"Cache hit for {engine_name} search")
                return cached
        
        results = []
        
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            logger.info(f"Searching {engine_name}: {search_url}")
            
            # Get proxy for search engine (use proxies for uncensored results)
            proxies = self._get_proxy_for_url(search_url, use_proxy) if engine_name in ['duckduckgo', 'startpage', 'qwant'] else None
            
            # Use retry handler
            response = self.retry_handler.execute(
                requests.get, search_url, headers=headers, timeout=15, proxies=proxies
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find result containers
            result_containers = soup.select(engine['result_selector'])
            
            for container in result_containers[:max_results]:
                try:
                    # Extract link
                    link_elem = container.select_one(engine['link_selector'])
                    if not link_elem or not link_elem.get('href'):
                        continue
                    
                    url = link_elem.get('href', '')
                    
                    # Clean up URL (some engines wrap URLs)
                    if url.startswith('/url?'):
                        # Google redirect URL
                        parsed = parse_qs(urlparse(url).query)
                        url = parsed.get('q', [url])[0]
                    elif url.startswith('//duckduckgo.com/l/'):
                        # DuckDuckGo redirect
                        continue  # Skip DuckDuckGo tracking URLs
                    
                    if not url.startswith('http'):
                        continue
                    
                    # Extract title
                    title_elem = container.select_one(engine['title_selector'])
                    title = title_elem.get_text().strip() if title_elem else ''
                    
                    # Extract snippet
                    snippet_elem = container.select_one(engine['snippet_selector'])
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ''
                    
                    if url and title:
                        results.append({
                            'url': url,
                            'title': title,
                            'snippet': snippet
                        })
                        
                except Exception as e:
                    continue
            
            # Cache the results
            if results:
                self.cache.set(search_url, results)
            logger.info(f"{engine_name} returned {len(results)} results")
            
        except Exception as e:
            logger.warning(f"Failed to search {engine_name}: {e}")
        
        return results

    # ========================================================================
    # PARALLEL SCRAPING & ADVANCED METHODS
    # ========================================================================

    def _parallel_scrape(self, urls: List[str], query: str, max_workers: int = 5) -> List[Dict]:
        """Scrape multiple URLs in parallel using ThreadPoolExecutor."""
        results = []
        
        def scrape_single(url):
            try:
                return self._scrape_url(url, query, use_proxy=use_proxy)
            except Exception as e:
                logger.warning(f"Parallel scrape failed for {url}: {e}")
                return None
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(scrape_single, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Error scraping {url}: {e}")
        
        return results

    def _query_wikipedia_api(self, query: str) -> Optional[Dict]:
        """Query Wikipedia API for quick, accurate information."""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            # First, search for the best matching article
            search_params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'format': 'json',
                'srlimit': 1
            }
            
            response = requests.get(self.wikipedia_search_api, params=search_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            search_results = data.get('query', {}).get('search', [])
            if not search_results:
                return None
            
            # Get the summary of the top result
            title = search_results[0].get('title', '')
            if not title:
                return None
            
            summary_url = self.wikipedia_api.format(title=quote_plus(title))
            response = requests.get(summary_url, timeout=10)
            response.raise_for_status()
            summary_data = response.json()
            
            return {
                'title': summary_data.get('title', title),
                'content': summary_data.get('extract', ''),
                'url': summary_data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'source': 'Wikipedia API',
                'type': 'encyclopedia',
                'thumbnail': summary_data.get('thumbnail', {}).get('source', ''),
                'description': summary_data.get('description', ''),
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Wikipedia API query failed: {e}")
            return None

    def _try_rss_feeds(self, query: str) -> List[Dict]:
        """Try to get content from RSS/Atom news feeds."""
        if not REQUESTS_AVAILABLE:
            return []
        
        results = []
        
        # Common news RSS feeds
        rss_feeds = [
            f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en",
            f"https://www.reddit.com/search.rss?q={quote_plus(query)}&sort=relevance",
        ]
        
        for feed_url in rss_feeds:
            try:
                response = requests.get(feed_url, timeout=10, headers={
                    'User-Agent': random.choice(self.user_agents)
                })
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml-xml')
                
                # Parse RSS items
                items = soup.find_all('item')[:5]
                for item in items:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    pub_date = item.find('pubDate')
                    
                    if title and link:
                        results.append({
                            'title': title.get_text().strip(),
                            'url': link.get_text().strip() if link.string else str(link.next_sibling).strip(),
                            'content': html.unescape(description.get_text()[:500]) if description else '',
                            'source': 'RSS Feed',
                            'type': 'news',
                            'published': pub_date.get_text() if pub_date else '',
                            'scraped_at': datetime.now().isoformat()
                        })
                        
            except Exception as e:
                logger.warning(f"RSS feed failed {feed_url}: {e}")
                continue
        
        return results

    def _extract_entities(self, result: ScrapingResult):
        """Extract named entities (people, places, organizations) from results."""
        # Simple pattern-based entity extraction
        all_text = ' '.join([
            r.get('content', '') + ' ' + r.get('title', '')
            for r in result.results
        ])
        
        if not all_text:
            return
        
        # Common patterns for entity extraction
        # People names (capitalized words, especially with titles)
        people_patterns = [
            r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+\s+[A-Z][a-z]+',
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:\s+(?:Jr\.|Sr\.|III|IV))?'
        ]
        
        # Places (cities, countries with "in" prefix)
        place_patterns = [
            r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
            r'\b(?:New York|Los Angeles|London|Paris|Tokyo|Sydney|Berlin|Moscow|Beijing|Mumbai)\b'
        ]
        
        # Organizations
        org_patterns = [
            r'\b[A-Z][A-Z]+(?:\s+[A-Z][A-Z]+)*\b',  # Acronyms
            r'\b(?:University|Institute|Corporation|Company|Inc\.|Ltd\.|LLC)\b'
        ]
        
        people = set()
        places = set()
        organizations = set()
        
        for pattern in people_patterns:
            matches = re.findall(pattern, all_text)
            people.update(matches[:10])
        
        for pattern in place_patterns:
            matches = re.findall(pattern, all_text)
            places.update(matches[:10])
        
        for pattern in org_patterns:
            matches = re.findall(pattern, all_text)
            organizations.update(m for m in matches[:10] if len(m) > 2)
        
        result.entities = {
            'people': list(people)[:15],
            'places': list(places)[:15],
            'organizations': list(organizations)[:15]
        }

    def _extract_keywords(self, result: ScrapingResult):
        """Extract important keywords from results."""
        all_text = ' '.join([
            r.get('content', '') + ' ' + r.get('title', '')
            for r in result.results
        ])
        
        if not all_text:
            return
        
        # Tokenize and count words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', all_text.lower())
        word_freq = defaultdict(int)
        
        for word in words:
            if word not in self.stop_words:
                word_freq[word] += 1
        
        # Get top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        result.keywords = [word for word, freq in sorted_words[:30] if freq >= 2]

    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract tables from HTML as structured data."""
        tables = []
        
        for table in soup.find_all('table')[:5]:  # Limit tables
            try:
                headers = []
                rows = []
                
                # Get headers
                header_row = table.find('thead') or table.find('tr')
                if header_row:
                    for th in header_row.find_all(['th', 'td'])[:10]:
                        headers.append(th.get_text().strip()[:50])
                
                # Get rows
                for tr in table.find_all('tr')[1:10]:  # Limit rows
                    row = []
                    for td in tr.find_all(['td', 'th'])[:10]:
                        row.append(td.get_text().strip()[:100])
                    if row:
                        rows.append(row)
                
                if headers or rows:
                    tables.append({
                        'headers': headers,
                        'rows': rows,
                        'row_count': len(rows)
                    })
                    
            except Exception as e:
                continue
        
        return tables

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract image URLs from the page."""
        images = []
        
        for img in soup.find_all('img', src=True)[:20]:
            src = img.get('src', '')
            if src:
                # Make absolute URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)
                elif not src.startswith('http'):
                    src = urljoin(base_url, src)
                
                # Filter out small images (likely icons)
                width = img.get('width', '')
                height = img.get('height', '')
                if width and height:
                    try:
                        if int(width) < 50 or int(height) < 50:
                            continue
                    except:
                        pass
                
                # Skip common icon/logo patterns
                if any(skip in src.lower() for skip in ['icon', 'logo', 'avatar', 'button', 'sprite']):
                    continue
                
                images.append(src)
        
        return images[:15]

    def _calculate_sentiment(self, text: str) -> Dict:
        """Calculate basic sentiment of text."""
        positive_words = set([
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'best', 'love', 'happy', 'positive', 'success', 'beautiful', 'perfect',
            'awesome', 'brilliant', 'outstanding', 'superb', 'delightful'
        ])
        
        negative_words = set([
            'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'sad',
            'negative', 'failure', 'ugly', 'poor', 'disappointing', 'wrong',
            'disaster', 'catastrophe', 'painful', 'miserable', 'dreadful'
        ])
        
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        positive_count = sum(1 for w in words if w in positive_words)
        negative_count = sum(1 for w in words if w in negative_words)
        total = len(words)
        
        if total == 0:
            return {'sentiment': 'neutral', 'score': 0, 'positive': 0, 'negative': 0}
        
        score = (positive_count - negative_count) / max(positive_count + negative_count, 1)
        
        if score > 0.2:
            sentiment = 'positive'
        elif score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': round(score, 2),
            'positive': positive_count,
            'negative': negative_count
        }

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and safe to scrape."""
        if not url or not url.startswith('http'):
            return False
        
        # Only skip truly non-scrapable content (files, search results)
        skip_domains = [
            'google.com/search', 'bing.com/search', 'duckduckgo.com',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.exe', '.dmg', '.mp3', '.mp4', '.avi', '.mkv'
        ]
        
        url_lower = url.lower()
        for skip in skip_domains:
            if skip in url_lower:
                return False
        
        return True

    def _scrape_url(self, url: str, query: str, extract_links: bool = False, use_proxy: bool = False) -> Optional[Dict]:
        """Scrape content from a specific URL."""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # Get proxy for this URL if needed
            proxies = self._get_proxy_for_url(url, use_proxy)
            
            # Check if this is an adult site - always use browser for better success
            adult_domains = [
                'pornhub.com', 'xvideos.com', 'xnxx.com', 'youporn.com', 
                'redtube.com', 'tube8.com', 'spankbang.com', 'xhamster.com'
            ]
            domain = urlparse(url).netloc.lower()
            is_adult_site = any(adult_domain in domain for adult_domain in adult_domains)
            
            if is_adult_site:
                logger.info(f"Adult site detected ({domain}), using browser-based scraping")
                return self._scrape_with_browser(url, proxies)
            
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True, proxies=proxies)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                return None
            
            soup = BeautifulSoup(response.content, 'lxml')
            
        except Exception as e:
            # Fallback to browser-based scraping for adult sites
            adult_domains = [
                'pornhub.com', 'xvideos.com', 'xnxx.com', 'youporn.com', 
                'redtube.com', 'tube8.com', 'spankbang.com', 'xhamster.com'
            ]
            domain = urlparse(url).netloc.lower()
            if any(adult_domain in domain for adult_domain in adult_domains):
                logger.info(f"Requests failed for {domain}, trying browser-based scraping")
                return self._scrape_with_browser(url, proxies)
            else:
                logger.warning(f"Failed to scrape {url}: {e}")
                return None
        
        try:
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                script.decompose()
            
            # Extract title
            title = ''
            if soup.title:
                title = soup.title.string or ''
            if not title:
                h1 = soup.find('h1')
                title = h1.get_text().strip() if h1 else ''
            
            # Extract main content
            content = ''
            main_selectors = ['main', 'article', '[role="main"]', '.content', '#content', '.post', '.entry', '.article-body']
            
            for selector in main_selectors:
                main_elem = soup.select_one(selector)
                if main_elem:
                    content = main_elem.get_text(separator=' ', strip=True)
                    break
            
            # Fallback to body
            if not content or len(content) < 100:
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)
            
            # Clean content
            content = ' '.join(content.split())  # Normalize whitespace
            
            result = {
                'url': url,
                'title': title.strip(),
                'content': content[:5000] if len(content) > 5000 else content,
                'content_length': len(content),
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract links if requested (for deep scraping)
            if extract_links:
                links = []
                for a in soup.find_all('a', href=True)[:20]:
                    href = a.get('href', '')
                    if href.startswith('http'):
                        links.append(href)
                    elif href.startswith('/'):
                        links.append(urljoin(url, href))
                result['linked_urls'] = links
                
                # Also extract images and tables for deep mode
                result['images'] = self._extract_images(soup, url)
                result['tables'] = self._extract_tables(soup)
            
            # Calculate sentiment
            result['sentiment'] = self._calculate_sentiment(content)
            
            return result
            
        except Exception as e:
            logger.warning(f"Failed to scrape URL {url}: {e}")
            return None

    # ========================================================================
    # EXPORT FUNCTIONALITY
    # ========================================================================

    def export_results(self, task_id: str, format: str = 'json') -> Optional[str]:
        """Export scraping results to various formats."""
        task = self.get_task_status(task_id)
        if not task or task['status'] != 'completed':
            return None
        
        safe_query = re.sub(r'[^\w\s-]', '', task['query'])[:30].strip().replace(' ', '_')
        timestamp = int(time.time())
        
        if format == 'json':
            return self._export_json(task, safe_query, timestamp)
        elif format == 'csv':
            return self._export_csv(task, safe_query, timestamp)
        elif format == 'markdown' or format == 'md':
            return self._export_markdown(task, safe_query, timestamp)
        elif format == 'txt':
            return self._export_text(task, safe_query, timestamp)
        else:
            return self._export_json(task, safe_query, timestamp)

    def _export_json(self, task: Dict, safe_query: str, timestamp: int) -> str:
        """Export results as JSON."""
        filepath = self.export_dir / f"export_{safe_query}_{timestamp}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
        return str(filepath)

    def _export_csv(self, task: Dict, safe_query: str, timestamp: int) -> str:
        """Export results as CSV."""
        filepath = self.export_dir / f"export_{safe_query}_{timestamp}.csv"
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'URL', 'Summary', 'Source', 'Relevance Score'])
            
            for result in task.get('results', []):
                writer.writerow([
                    result.get('title', ''),
                    result.get('url', ''),
                    result.get('summary', result.get('content', ''))[:200],
                    result.get('source', ''),
                    result.get('relevance_score', 0)
                ])
        
        return str(filepath)

    def _export_markdown(self, task: Dict, safe_query: str, timestamp: int) -> str:
        """Export results as Markdown."""
        filepath = self.export_dir / f"export_{safe_query}_{timestamp}.md"
        
        lines = [
            f"# Web Scraping Results: {task['query']}",
            f"",
            f"**Mode:** {task['mode']}",
            f"**Date:** {task['timestamp']}",
            f"**Sources:** {task['sources_count']}",
            f"**Results:** {task['results_count']}",
            f"",
            "---",
            ""
        ]
        
        for i, result in enumerate(task.get('results', []), 1):
            lines.append(f"## {i}. {result.get('title', 'Untitled')}")
            lines.append(f"")
            lines.append(f"**Source:** [{result.get('source', 'Unknown')}]({result.get('url', '')})")
            lines.append(f"")
            summary = result.get('summary', result.get('content', ''))[:500]
            lines.append(f"{summary}")
            lines.append(f"")
            lines.append("---")
            lines.append("")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return str(filepath)

    def _export_text(self, task: Dict, safe_query: str, timestamp: int) -> str:
        """Export results as plain text."""
        filepath = self.export_dir / f"export_{safe_query}_{timestamp}.txt"
        
        lines = [
            f"WEB SCRAPING RESULTS",
            f"=" * 50,
            f"Query: {task['query']}",
            f"Mode: {task['mode']}",
            f"Date: {task['timestamp']}",
            f"Sources: {task['sources_count']}",
            f"Results: {task['results_count']}",
            f"=" * 50,
            ""
        ]
        
        for i, result in enumerate(task.get('results', []), 1):
            lines.append(f"{i}. {result.get('title', 'Untitled')}")
            lines.append(f"   URL: {result.get('url', '')}")
            lines.append(f"   Source: {result.get('source', 'Unknown')}")
            summary = result.get('summary', result.get('content', ''))[:300]
            lines.append(f"   {summary}")
            lines.append(f"")
            lines.append("-" * 50)
            lines.append("")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return str(filepath)

    def _save_raw_data(self, task_id: str, query: str, results: List[Dict], is_deep: bool = False) -> Optional[Path]:
        """Save raw scraped data to a JSON file for later analysis."""
        if not results:
            return None
        
        try:
            # Create filename with timestamp
            mode = "deep" if is_deep else "normal"
            safe_query = re.sub(r'[^\w\s-]', '', query)[:50].strip().replace(' ', '_')
            filename = f"{mode}_{safe_query}_{task_id[:8]}_{int(time.time())}.json"
            filepath = self.data_dir / filename
            
            data = {
                'task_id': task_id,
                'query': query,
                'mode': mode,
                'scraped_at': datetime.now().isoformat(),
                'total_results': len(results),
                'results': results
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved raw data to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save raw data: {e}")
            return None

    def _analyze_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Analyze and summarize scraped results for normal mode."""
        if not results:
            return []
        
        analyzed = []
        query_words = set(query.lower().split())
        
        for result in results:
            content = result.get('content', '')
            title = result.get('title', '')
            
            if not content or len(content) < 50:
                continue
            
            # Calculate relevance score
            content_lower = content.lower()
            relevance_score = sum(1 for word in query_words if word in content_lower)
            
            # Extract key sentences containing query terms
            sentences = re.split(r'[.!?]+', content)
            relevant_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 30 and any(word in sentence.lower() for word in query_words):
                    relevant_sentences.append(sentence)
            
            # Create summary
            summary = ' '.join(relevant_sentences[:3])[:500] if relevant_sentences else content[:500]
            
            analyzed.append({
                'title': title,
                'url': result.get('url', ''),
                'summary': summary + '...' if len(summary) == 500 else summary,
                'relevance_score': relevance_score,
                'source': result.get('source', urlparse(result.get('url', '')).netloc),
                'type': result.get('type', 'web')
            })
        
        # Sort by relevance and deduplicate
        analyzed.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Remove duplicates based on title similarity
        unique = []
        seen_titles = set()
        for item in analyzed:
            title_key = item['title'][:50].lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique.append(item)
        
        return unique[:20]

    def _analyze_results_deep(self, results: List[Dict], query: str) -> List[Dict]:
        """Comprehensive analysis for deep scraping mode."""
        if not results:
            return []
        
        # First do basic analysis
        analyzed = self._analyze_results(results, query)
        
        # Additional deep analysis
        query_words = set(query.lower().split())
        
        for item in analyzed:
            # Find the original result for more detailed analysis
            original = next((r for r in results if r.get('url') == item['url']), None)
            if original:
                content = original.get('content', '')
                
                # Extract key phrases (simple extraction)
                words = content.lower().split()
                word_freq = {}
                for word in words:
                    if len(word) > 4 and word.isalpha():
                        word_freq[word] = word_freq.get(word, 0) + 1
                
                top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
                item['key_terms'] = [w[0] for w in top_words]
                
                # Add content statistics
                item['content_length'] = original.get('content_length', len(content))
                item['has_images'] = 'img' in content.lower() or '<img' in content.lower()
        
        return analyzed[:50]

    def _scrape_source(self, source: Dict, query: str, depth: str = "normal") -> List[Dict]:
        """Scrape data from a specific source."""
        if not REQUESTS_AVAILABLE:
            return []

        try:
            headers = {
                'User-Agent': self.user_agents[hash(source['url']) % len(self.user_agents)],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }

            # Construct search URL
            search_url = self._construct_search_url(source['url'], query)

            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            if depth == "deep":
                return self._extract_deep_data(soup, query, source)
            else:
                return self._extract_normal_data(soup, query, source)

        except Exception as e:
            logger.warning(f"Failed to scrape {source['url']}: {e}")
            return []

    def _construct_search_url(self, base_url: str, query: str) -> str:
        """Construct search URL for different sources."""
        query_encoded = requests.utils.quote(query)
        
        # For dictionary sites, extract a single word if possible for definition lookups
        query_words = query.split()
        single_word = query_words[0] if query_words else query
        single_word_encoded = requests.utils.quote(single_word)

        if 'wikipedia.org' in base_url:
            return f"https://en.wikipedia.org/wiki/Special:Search?search={query_encoded}"
        elif 'britannica.com' in base_url:
            return f"https://www.britannica.com/search?query={query_encoded}"
        elif 'dictionary.com' in base_url:
            # Dictionary.com browse only works with single words
            return f"https://www.dictionary.com/browse/{single_word_encoded}"
        elif 'thesaurus.com' in base_url:
            return f"https://www.thesaurus.com/browse/{single_word_encoded}"
        elif 'merriam-webster.com' in base_url:
            return f"https://www.merriam-webster.com/dictionary/{single_word_encoded}"
        elif 'stackoverflow.com' in base_url:
            return f"https://stackoverflow.com/search?q={query_encoded}"
        elif 'github.com' in base_url:
            return f"https://github.com/search?q={query_encoded}&type=repositories"
        elif 'imdb.com' in base_url:
            return f"https://www.imdb.com/find/?q={query_encoded}"
        elif 'rottentomatoes.com' in base_url:
            return f"https://www.rottentomatoes.com/search?search={query_encoded}"
        elif 'themoviedb.org' in base_url:
            return f"https://www.themoviedb.org/search?query={query_encoded}"
        elif 'geeksforgeeks.org' in base_url:
            return f"https://www.geeksforgeeks.org/search/{query_encoded}/"
        elif 'quora.com' in base_url:
            return f"https://www.quora.com/search?q={query_encoded}"
        elif 'bbc.com' in base_url:
            return f"https://www.bbc.com/search?q={query_encoded}"
        elif 'sciencedirect.com' in base_url:
            return f"https://www.sciencedirect.com/search?qs={query_encoded}"
        elif 'scholar.google.com' in base_url:
            return f"https://scholar.google.com/scholar?q={query_encoded}"
        else:
            return f"{base_url}/search?q={query_encoded}"

    def _extract_normal_data(self, soup: BeautifulSoup, query: str, source: Dict) -> List[Dict]:
        """Extract data in normal mode (quick extraction)."""
        results = []

        # Try different extraction strategies based on source
        if 'wikipedia.org' in source['url']:
            results.extend(self._extract_wikipedia(soup, query))
        elif 'dictionary.com' in source['url'] or 'merriam-webster.com' in source['url']:
            results.extend(self._extract_dictionary(soup, query))
        elif 'imdb.com' in source['url']:
            results.extend(self._extract_imdb(soup, query))
        elif 'rottentomatoes.com' in source['url']:
            results.extend(self._extract_rottentomatoes(soup, query))
        elif 'themoviedb.org' in source['url']:
            results.extend(self._extract_tmdb(soup, query))
        else:
            results.extend(self._extract_general(soup, query))

        return results

    def _extract_deep_data(self, soup: BeautifulSoup, query: str, source: Dict) -> List[Dict]:
        """Extract data in deep mode (thorough extraction)."""
        results = self._extract_normal_data(soup, query, source)

        # Additional deep extraction
        try:
            # Extract from related links
            links = soup.find_all('a', href=True)
            related_urls = []

            for link in links[:5]:  # Limit to avoid overload
                href = link['href']
                if href.startswith('http') and source['url'] not in href:
                    related_urls.append(href)

            # Scrape related pages (limited for performance)
            for url in related_urls[:2]:
                try:
                    response = requests.get(url, headers={
                        'User-Agent': self.user_agents[0]
                    }, timeout=5)
                    related_soup = BeautifulSoup(response.content, 'lxml')
                    related_results = self._extract_general(related_soup, query)
                    results.extend(related_results)
                except:
                    pass

        except Exception as e:
            logger.warning(f"Deep extraction failed: {e}")

        return results

    def _extract_wikipedia(self, soup: BeautifulSoup, query: str) -> List[Dict]:
        """Extract data from Wikipedia."""
        results = []

        # Get main content
        content = soup.find('div', {'id': 'mw-content-text'})
        if content:
            paragraphs = content.find_all('p')[:3]  # First few paragraphs
            text = ' '.join([p.get_text() for p in paragraphs])
            if text.strip():
                results.append({
                    'title': soup.find('h1', {'id': 'firstHeading'}).get_text() if soup.find('h1', {'id': 'firstHeading'}) else query,
                    'content': text[:500] + '...' if len(text) > 500 else text,
                    'source': 'Wikipedia',
                    'url': soup.url if hasattr(soup, 'url') else 'https://en.wikipedia.org',
                    'type': 'encyclopedia'
                })

        return results

    def _extract_dictionary(self, soup: BeautifulSoup, query: str) -> List[Dict]:
        """Extract dictionary definitions."""
        results = []

        # Look for definition content
        definition_divs = soup.find_all(['div', 'section'], class_=re.compile(r'definition|meaning|entry'))
        for div in definition_divs[:2]:
            text = div.get_text().strip()
            if len(text) > 50:  # Meaningful content
                results.append({
                    'title': f"Definition of {query}",
                    'content': text[:300] + '...' if len(text) > 300 else text,
                    'source': soup.title.string if soup.title else 'Dictionary',
                    'type': 'definition'
                })

        return results

    def _extract_general(self, soup: BeautifulSoup, query: str) -> List[Dict]:
        """General content extraction."""
        results = []

        # Extract from main content areas
        content_selectors = ['main', 'article', '.content', '#content', '.post', '.entry']

        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                text = content.get_text().strip()
                if len(text) > 100:  # Substantial content
                    results.append({
                        'title': soup.title.string if soup.title else f"Results for {query}",
                        'content': text[:400] + '...' if len(text) > 400 else text,
                        'source': soup.title.string if soup.title else 'Web',
                        'type': 'general'
                    })
                    break

        return results

    def _extract_imdb(self, soup: BeautifulSoup, query: str) -> List[Dict]:
        """Extract data from IMDb search results."""
        results = []
        
        try:
            # Find search result items
            items = soup.find_all('li', class_=re.compile(r'find-result|ipc-metadata-list-summary-item'))
            if not items:
                items = soup.find_all('div', class_=re.compile(r'result|findResult'))
            
            for item in items[:10]:
                title_elem = item.find(['a', 'h3', 'span'], class_=re.compile(r'title|ipc-metadata')) or item.find('a')
                if title_elem:
                    title = title_elem.get_text().strip()
                    # Get additional info like year, rating
                    extra_info = item.get_text().strip()
                    if title and len(title) > 2:
                        results.append({
                            'title': title,
                            'content': extra_info[:300] if len(extra_info) > 300 else extra_info,
                            'source': 'IMDb',
                            'url': 'https://www.imdb.com',
                            'type': 'entertainment'
                        })
        except Exception as e:
            logger.warning(f"IMDb extraction error: {e}")
        
        # Fallback to general extraction if no specific results found
        if not results:
            results = self._extract_general(soup, query)
        
        return results

    def _extract_rottentomatoes(self, soup: BeautifulSoup, query: str) -> List[Dict]:
        """Extract data from Rotten Tomatoes search results."""
        results = []
        
        try:
            # Find search result items
            items = soup.find_all('search-page-media-row') or soup.find_all('li', class_=re.compile(r'search-result'))
            if not items:
                items = soup.find_all('a', class_=re.compile(r'articleLink|unset'))
            
            for item in items[:10]:
                title_elem = item.find(['h3', 'span', 'a']) or item
                if title_elem:
                    title = title_elem.get_text().strip()
                    if title and len(title) > 2:
                        results.append({
                            'title': title,
                            'content': item.get_text().strip()[:300],
                            'source': 'Rotten Tomatoes',
                            'url': 'https://www.rottentomatoes.com',
                            'type': 'entertainment'
                        })
        except Exception as e:
            logger.warning(f"Rotten Tomatoes extraction error: {e}")
        
        if not results:
            results = self._extract_general(soup, query)
        
        return results

    def _extract_tmdb(self, soup: BeautifulSoup, query: str) -> List[Dict]:
        """Extract data from TheMovieDB search results."""
        results = []
        
        try:
            # Find movie/person cards
            items = soup.find_all('div', class_=re.compile(r'card|result'))
            if not items:
                items = soup.find_all('a', class_=re.compile(r'result'))
            
            for item in items[:10]:
                title_elem = item.find(['h2', 'h3', 'a', 'p'])
                if title_elem:
                    title = title_elem.get_text().strip()
                    overview = item.find('p', class_=re.compile(r'overview'))
                    content = overview.get_text().strip() if overview else item.get_text().strip()
                    
                    if title and len(title) > 2:
                        results.append({
                            'title': title,
                            'content': content[:300] if len(content) > 300 else content,
                            'source': 'TheMovieDB',
                            'url': 'https://www.themoviedb.org',
                            'type': 'entertainment'
                        })
        except Exception as e:
            logger.warning(f"TMDB extraction error: {e}")
        
        if not results:
            results = self._extract_general(soup, query)
        
        return results

    def _process_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Process and deduplicate normal mode results."""
        if not results:
            return []

        # Remove duplicates based on content similarity
        unique_results = []
        seen_content = set()

        for result in results:
            content_hash = hash(result.get('content', '')[:100].lower())
            if content_hash not in seen_content:
                unique_results.append(result)
                seen_content.add(content_hash)

        return unique_results[:20]  # Limit results

    def _process_results_deep(self, results: List[Dict], query: str) -> List[Dict]:
        """Process results for deep mode with advanced analysis."""
        if not results:
            return []

        # Advanced deduplication and ranking
        processed = self._process_results(results, query)

        # Sort by relevance (simple keyword matching)
        query_words = set(query.lower().split())
        for result in processed:
            content_lower = result.get('content', '').lower()
            relevance_score = sum(1 for word in query_words if word in content_lower)
            result['relevance_score'] = relevance_score

        # Sort by relevance
        processed.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        return processed[:50]  # More results for deep mode

    def _generate_related_terms(self, query: str) -> List[str]:
        """Generate related search terms for deep scraping."""
        # Simple term expansion
        words = query.lower().split()
        related = []

        # Add common related terms
        expansions = {
            'programming': ['coding', 'development', 'software'],
            'python': ['programming', 'coding', 'scripting'],
            'web': ['internet', 'online', 'website'],
            'ai': ['artificial intelligence', 'machine learning', 'neural networks'],
            'data': ['information', 'database', 'analytics']
        }

        for word in words:
            if word in expansions:
                related.extend(expansions[word])

        return list(set(related))[:3]

    def _save_results_if_large(self, result: ScrapingResult):
        """Save results to file if they're large."""
        if len(result.results) > 10 or len(str(result.results)) > 2000:
            filename = f"scraping_{result.id}_{int(time.time())}.json"
            filepath = self.temp_dir / filename

            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

                result.metadata['saved_to_file'] = str(filepath)
                logger.info(f"Saved large scraping results to {filepath}")

            except Exception as e:
                logger.error(f"Failed to save results: {e}")

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a scraping task."""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].to_dict()
        return None

    def get_completed_results(self, task_id: str) -> Optional[Dict]:
        """Get completed results for a task."""
        task = self.get_task_status(task_id)
        if task and task['status'] == 'completed':
            # If results were saved to file, load them
            if 'saved_to_file' in task.get('metadata', {}):
                try:
                    with open(task['metadata']['saved_to_file'], 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
            return task
        return None

    def list_active_tasks(self) -> List[Dict]:
        """List all active scraping tasks."""
        return [task.to_dict() for task in self.active_tasks.values()]

    def cleanup_old_files(self, days: int = 7):
        """Clean up old temporary result files."""
        import glob
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        
        # Clean both directories
        for directory in [self.temp_dir, self.data_dir]:
            pattern = str(directory / "*.json")
            for filepath in glob.glob(pattern):
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_time < cutoff:
                        os.remove(filepath)
                        logger.info(f"Cleaned up old file: {filepath}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup {filepath}: {e}")

    def read_saved_data(self, query: str = None) -> List[Dict]:
        """Read and return saved scraping data files."""
        import glob
        
        results = []
        pattern = str(self.data_dir / "*.json")
        
        for filepath in glob.glob(pattern):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Filter by query if specified
                if query:
                    if query.lower() in data.get('query', '').lower():
                        results.append(data)
                else:
                    results.append(data)
            except Exception as e:
                logger.warning(f"Failed to read {filepath}: {e}")
        
        # Sort by date (newest first)
        results.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)
        return results

    def get_analysis_summary(self, task_id: str) -> str:
        """Get a human-readable summary of scraping results."""
        task = self.get_task_status(task_id)
        if not task:
            return "Task not found"
        
        if task['status'] != 'completed':
            return f"Task is still {task['status']} ({task['progress']}% complete)"
        
        results = task.get('results', [])
        if not results:
            return "No results found for this query"
        
        # Build summary
        summary_parts = [
            f"Found {len(results)} relevant results for: '{task['query']}'",
            f"Sources searched: {task['sources_count']}",
            f"Time taken: {task['metadata'].get('scraping_time', 0):.1f} seconds",
        ]
        
        # Add entities if available
        entities = task.get('entities', {})
        if entities.get('people'):
            summary_parts.append(f"People mentioned: {', '.join(entities['people'][:5])}")
        if entities.get('places'):
            summary_parts.append(f"Places mentioned: {', '.join(entities['places'][:5])}")
        
        # Add keywords
        keywords = task.get('keywords', [])
        if keywords:
            summary_parts.append(f"Key topics: {', '.join(keywords[:8])}")
        
        summary_parts.append("")
        summary_parts.append("Top Results:")
        
        for i, result in enumerate(results[:5], 1):
            title = result.get('title', 'Untitled')[:60]
            summary = result.get('summary', result.get('content', ''))[:150]
            source = result.get('source', result.get('url', 'Unknown'))
            sentiment = result.get('sentiment', {}).get('sentiment', '')
            
            summary_parts.append(f"\n{i}. {title}")
            summary_parts.append(f"   Source: {source}")
            if sentiment:
                summary_parts.append(f"   Sentiment: {sentiment}")
            summary_parts.append(f"   {summary}...")
        
        return "\n".join(summary_parts)

# Global scraper instance
advanced_scraper = AdvancedWebScraper()


# ============================================================================
# PUBLIC API FUNCTIONS
# ============================================================================

def start_web_scraping(command: str) -> str:
    """
    Start a web scraping task.
    
    Modes:
        - normal: Quick surface-level scraping (default)
        - deep/-force: Thorough multi-source scraping
        - fast: Quick Wikipedia API + cached results
        - realtime: Focus on recent news content
    
    Examples:
        start_web_scraping("web scrapper : list of fruits")
        start_web_scraping("web scrapper -deep : quantum computing")
        start_web_scraping("web scrapper -realtime : latest AI news")
    """
    return advanced_scraper.start_scraping(command)

def get_scraping_status(task_id: str) -> Optional[Dict]:
    """Get scraping task status including progress and metadata."""
    return advanced_scraper.get_task_status(task_id)

def get_scraping_results(task_id: str) -> Optional[Dict]:
    """Get completed scraping results with full data."""
    return advanced_scraper.get_completed_results(task_id)

def list_scraping_tasks() -> List[Dict]:
    """List all active and completed scraping tasks."""
    return advanced_scraper.list_active_tasks()

def get_scraping_summary(task_id: str) -> str:
    """Get human-readable summary of scraping results."""
    return advanced_scraper.get_analysis_summary(task_id)

def read_saved_scraping_data(query: str = None) -> List[Dict]:
    """Read saved scraping data files, optionally filtered by query."""
    return advanced_scraper.read_saved_data(query)

def export_scraping_results(task_id: str, format: str = 'json') -> Optional[str]:
    """
    Export scraping results to a file.
    
    Args:
        task_id: The ID of the completed task
        format: Export format - 'json', 'csv', 'markdown'/'md', or 'txt'
    
    Returns:
        Path to the exported file or None if failed
    """
    return advanced_scraper.export_results(task_id, format)

def clear_scraping_cache():
    """Clear the response cache."""
    advanced_scraper.cache.clear()
    return "Cache cleared"

def get_scraper_stats() -> Dict:
    """Get scraper statistics."""
    return {
        'active_tasks': len(advanced_scraper.active_tasks),
        'cache_size': len(advanced_scraper.cache._cache),
        'search_engines': list(advanced_scraper.search_engines.keys()),
        'supported_modes': ['normal', 'deep', 'force', 'fast', 'realtime'],
        'export_formats': ['json', 'csv', 'markdown', 'txt']
    }

if __name__ == "__main__":
    # Test the scraper
    print("Testing Advanced Web Scraper with Search Engine Integration...")
    print("=" * 60)

    # Test normal mode with a general query
    print("\n[TEST 1] Normal mode - General web search")
    result = start_web_scraping("web scrapper : best hollywood actresses")
    print(f"Started: {result}")

    # Wait for completion
    print("\nWaiting for results...")
    time.sleep(15)

    # Check status
    tasks = list_scraping_tasks()
    if tasks:
        print(f"\nActive tasks: {len(tasks)}")
        task = tasks[0]
        print(f"Task status: {task['status']}")
        print(f"Progress: {task['progress']}%")
        print(f"Sources: {task['sources_count']}")
        print(f"Results: {task['results_count']}")
        
        # Get summary
        if task['status'] == 'completed':
            summary = get_scraping_summary(task['id'])
            print(f"\n{summary}")
            
            # Check if raw data was saved
            if task.get('metadata', {}).get('raw_data_file'):
                print(f"\nRaw data saved to: {task['metadata']['raw_data_file']}")

    print("\n" + "=" * 60)
    print("Test completed.")