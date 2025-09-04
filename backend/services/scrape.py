import logging
import requests
import io
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import re
import time
from fake_useragent import UserAgent

# PDF processing
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

# Arxiv processing
try:
    import arxiv
    HAS_ARXIV = True
except ImportError:
    HAS_ARXIV = False

# HTML scraping
try:
    from requests_html import HTMLSession
    HAS_REQUESTS_HTML = True
except ImportError:
    HAS_REQUESTS_HTML = False

logger = logging.getLogger(__name__)

class ScrapingService:
    """Service for scraping different types of content sources"""

    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random
        })

        if HAS_REQUESTS_HTML:
            self.html_session = HTMLSession()
            self.html_session.headers.update({
                'User-Agent': self.ua.random
            })

    def scrape_content(self, source_url: str, source_type: str, content: str = "") -> Optional[str]:
        """
        Main scraping method that routes to appropriate scraper based on source_type

        Args:
            source_url: URL of the content to scrape
            source_type: Type of source (pdf, video, arxiv-no-link, tool, etc.)
            content: Additional content/title for arxiv-no-link type

        Returns:
            str: Scraped content or None if failed
        """
        try:
            if source_type == 'pdf':
                return self._scrape_pdf(source_url)
            elif source_type == 'video':
                # Video processing is handled separately in video processing task
                logger.info(f"Video source type detected, skipping scraping: {source_url}")
                return None
            elif source_type == 'arxiv-no-link':
                return self._scrape_arxiv_by_title(content)
            elif source_type == 'tool':
                # Tool sources don't need scraping
                logger.info(f"Tool source type detected, skipping scraping: {source_url}")
                return None
            else:
                # Check if URL is PDF or arxiv domain
                if self._is_pdf_url(source_url):
                    return self._scrape_pdf(source_url)
                elif self._is_arxiv_url(source_url):
                    return self._scrape_arxiv_by_url(source_url)
                else:
                    return self._scrape_html(source_url)

        except Exception as e:
            logger.error(f"Error scraping {source_type} from {source_url}: {e}")
            return None

    def _is_pdf_url(self, url: str) -> bool:
        """Check if URL points to a PDF file"""
        if not url:
            return False

        url_lower = url.lower()
        # Check file extension
        if url_lower.endswith('.pdf'):
            return True

        # Check URL patterns that typically serve PDFs
        pdf_patterns = [
            '/pdf/', '/download/', '/paper/', '/document/',
            'arxiv.org/pdf/', 'papers.nips.cc/paper/',
            'openreview.net/pdf?', 'proceedings.mlr.press/'
        ]

        for pattern in pdf_patterns:
            if pattern in url_lower:
                return True

        return False

    def _is_arxiv_url(self, url: str) -> bool:
        """Check if URL is from arxiv domain"""
        if not url:
            return False

        try:
            domain = urlparse(url).netloc.lower()
            return 'arxiv.org' in domain
        except:
            return False

    def _extract_arxiv_id(self, url: str) -> Optional[str]:
        """Extract arxiv ID from URL"""
        if not url:
            return None

        # Pattern for arxiv URLs: arxiv.org/abs/{id} or arxiv.org/pdf/{id}
        patterns = [
            r'arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+(?:v[0-9]+)?)',
            r'arxiv\.org/(?:abs|pdf)/([a-z\-]+/[0-9]+(?:v[0-9]+)?)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _scrape_pdf(self, url: str) -> Optional[str]:
        """Scrape text content from PDF file"""
        if not url:
            return None

        logger.info(f"Scraping PDF from: {url}")

        try:
            # Try PyMuPDF (fitz) first
            if HAS_FITZ:
                return self._scrape_pdf_fitz(url)
            elif HAS_PDFPLUMBER:
                return self._scrape_pdf_pdfplumber(url)
            else:
                logger.error("No PDF processing library available")
                return None

        except Exception as e:
            logger.error(f"Error scraping PDF {url}: {e}")
            return None

    def _scrape_pdf_fitz(self, url: str) -> Optional[str]:
        """Scrape PDF using PyMuPDF (fitz)"""
        try:
            # Download PDF
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Open PDF from bytes
            doc = fitz.open(stream=response.content, filetype="pdf")
            text = ""

            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()

                # Skip pages with very little text (likely images/figures)
                if len(page_text.strip()) > 50:  # Minimum 50 characters
                    text += page_text + "\n\n"

            doc.close()

            if text.strip():
                logger.info(f"Successfully extracted {len(text)} characters from PDF")
                return text.strip()
            else:
                logger.warning("No text content found in PDF")
                return None

        except Exception as e:
            logger.error(f"Error with PyMuPDF: {e}")
            return None

    def _scrape_pdf_pdfplumber(self, url: str) -> Optional[str]:
        """Scrape PDF using pdfplumber (fallback)"""
        try:
            # Download PDF
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            text = ""
            with pdfplumber.open(io.BytesIO(response.content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text and len(page_text.strip()) > 50:
                        text += page_text + "\n\n"

            if text.strip():
                logger.info(f"Successfully extracted {len(text)} characters from PDF using pdfplumber")
                return text.strip()
            else:
                logger.warning("No text content found in PDF")
                return None

        except Exception as e:
            logger.error(f"Error with pdfplumber: {e}")
            return None

    def _scrape_arxiv_by_title(self, title: str) -> Optional[str]:
        """Search arxiv by title and scrape the PDF"""
        if not HAS_ARXIV:
            logger.warning("Arxiv library not available")
            return None

        logger.info(f"Arxiv search input - title: '{title}', type: {type(title)}, length: {len(title) if title else 0}")

        if not title or not title.strip():
            logger.warning(f"Empty or None title provided for arxiv search. Title: '{title}', type: {type(title)}")
            return None

        title = title.strip()
        logger.info(f"Searching arxiv for cleaned title: '{title}' (length: {len(title)})")

        try:
            client = arxiv.Client()

            # Strategy 1: Try exact title match first
            logger.info("Strategy 1: Exact title search")
            search_exact = arxiv.Search(
                query=f'ti:"{title}"',
                max_results=1,
                sort_by=arxiv.SortCriterion.Relevance
            )
            results_exact = list(client.results(search_exact))

            if results_exact:
                paper = results_exact[0]
                logger.info(f"Found exact match: {paper.title}")
                if self._is_title_match(title, paper.title):
                    pdf_url = paper.pdf_url
                    return self._scrape_pdf(pdf_url)

            # Strategy 2: Try simplified query with key terms
            logger.info("Strategy 2: Simplified query with key terms")
            # Extract key terms from title (remove colons, split by spaces)
            key_terms = title.replace(':', '').split()[:3]  # Take first 3 words
            simplified_query = ' '.join(key_terms)
            logger.info(f"Using simplified query: '{simplified_query}'")

            search_simplified = arxiv.Search(
                query=simplified_query,
                max_results=5,  # Get more results to find the right one
                sort_by=arxiv.SortCriterion.Relevance
            )
            results_simplified = list(client.results(search_simplified))

            # Look for the best title match
            best_match = None
            best_score = 0

            for paper in results_simplified:
                score = self._calculate_title_similarity(title, paper.title)
                logger.info(f"Paper: {paper.title[:60]}... (score: {score})")
                if score > best_score:
                    best_score = score
                    best_match = paper

            if best_match and best_score > 0.5:  # Threshold for good match
                logger.info(f"Best match found: {best_match.title} (score: {best_score})")
                pdf_url = best_match.pdf_url
                return self._scrape_pdf(pdf_url)

            # Strategy 3: Try the original query as fallback
            logger.info("Strategy 3: Original query as fallback")
            search_original = arxiv.Search(
                query=title,
                max_results=5,
                sort_by=arxiv.SortCriterion.Relevance
            )
            results_original = list(client.results(search_original))

            # Look for any paper that contains key terms
            key_terms_lower = [term.lower() for term in key_terms]
            for paper in results_original:
                paper_title_lower = paper.title.lower()
                if any(term in paper_title_lower for term in key_terms_lower):
                    logger.info(f"Fallback match found: {paper.title}")
                    pdf_url = paper.pdf_url
                    return self._scrape_pdf(pdf_url)

            logger.warning(f"No suitable arxiv results found for title: {title}")
            return None

        except Exception as e:
            logger.error(f"Error searching arxiv for title '{title}': {e}")
            return None

    def _is_title_match(self, search_title: str, result_title: str) -> bool:
        """Check if result title matches search title closely"""
        search_lower = search_title.lower()
        result_lower = result_title.lower()

        # Exact match
        if search_lower == result_lower:
            return True

        # Contains all key words
        search_words = set(search_lower.split())
        result_words = set(result_lower.split())

        # Check if most important words are present
        common_words = search_words.intersection(result_words)
        return len(common_words) >= len(search_words) * 0.8

    def _calculate_title_similarity(self, search_title: str, result_title: str) -> float:
        """Calculate similarity score between search title and result title"""
        search_lower = search_title.lower()
        result_lower = result_title.lower()

        # Exact match gets highest score
        if search_lower == result_lower:
            return 1.0

        # Count common words
        search_words = set(search_lower.split())
        result_words = set(result_lower.split())
        common_words = search_words.intersection(result_words)

        if not common_words:
            return 0.0

        # Calculate Jaccard similarity
        union_words = search_words.union(result_words)
        similarity = len(common_words) / len(union_words)

        # Boost score if key terms are present
        key_terms = ['ahelm', 'audio', 'language', 'models', 'evaluation', 'holistic']
        key_matches = sum(1 for term in key_terms if term in result_lower)
        key_boost = key_matches * 0.1

        return min(1.0, similarity + key_boost)

    def _scrape_arxiv_by_url(self, url: str) -> Optional[str]:
        """Scrape arxiv paper by URL"""
        if not url or not HAS_ARXIV:
            return None

        logger.info(f"Scraping arxiv paper from: {url}")

        try:
            # Extract arxiv ID from URL
            arxiv_id = self._extract_arxiv_id(url)
            if not arxiv_id:
                logger.error(f"Could not extract arxiv ID from URL: {url}")
                return None

            # Use modern arxiv Client API
            client = arxiv.Client()
            search = arxiv.Search(id_list=[arxiv_id])
            results = list(client.results(search))

            if not results:
                logger.warning(f"No arxiv paper found for ID: {arxiv_id}")
                return None

            paper = results[0]
            logger.info(f"Found arxiv paper: {paper.title}")

            # Get PDF URL and scrape it
            pdf_url = paper.pdf_url
            return self._scrape_pdf(pdf_url)

        except Exception as e:
            logger.error(f"Error scraping arxiv URL {url}: {e}")
            return None

    def _scrape_html(self, url: str) -> Optional[str]:
        """Scrape text content from HTML page"""
        if not url:
            return None

        logger.info(f"Scraping HTML from: {url}")

        try:
            # Try requests-html first for JavaScript rendering
            if HAS_REQUESTS_HTML:
                return self._scrape_html_requests_html(url)
            else:
                return self._scrape_html_requests(url)

        except Exception as e:
            logger.error(f"Error scraping HTML {url}: {e}")
            return None

    def _scrape_html_requests_html(self, url: str) -> Optional[str]:
        """Scrape HTML using requests-html (handles JavaScript)"""
        try:
            response = self.html_session.get(url, timeout=30)
            response.raise_for_status()

            # Render JavaScript if needed
            response.html.render(timeout=20)

            # Extract text content
            text = response.html.text

            # Clean up the text
            if text:
                # Remove excessive whitespace
                text = re.sub(r'\n\s*\n', '\n\n', text)
                text = re.sub(r'\s+', ' ', text)

                # Remove very short content (likely navigation/scripts)
                if len(text.strip()) > 200:  # Minimum 200 characters
                    logger.info(f"Successfully extracted {len(text)} characters from HTML")
                    return text.strip()

            logger.warning("HTML content too short or empty")
            return None

        except Exception as e:
            logger.error(f"Error with requests-html: {e}")
            return None

    def _scrape_html_requests(self, url: str) -> Optional[str]:
        """Scrape HTML using requests + BeautifulSoup (fallback)"""
        try:
            from bs4 import BeautifulSoup

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract text
            text = soup.get_text()

            # Clean up the text
            if text:
                # Remove excessive whitespace
                text = re.sub(r'\n\s*\n', '\n\n', text)
                text = re.sub(r'\s+', ' ', text)

                # Remove very short content
                if len(text.strip()) > 200:
                    logger.info(f"Successfully extracted {len(text)} characters from HTML using BeautifulSoup")
                    return text.strip()

            logger.warning("HTML content too short or empty")
            return None

        except Exception as e:
            logger.error(f"Error with BeautifulSoup: {e}")
            return None

def clean_text_content(text: str) -> str:
    """
    Clean text content by removing null characters and other problematic characters.

    Args:
        text: Raw text content that may contain null characters

    Returns:
        str: Cleaned text content safe for database storage
    """
    if not text:
        return ""

    # Remove null characters (0x00)
    cleaned = text.replace('\x00', '')

    # Remove other problematic control characters except common whitespace
    # Keep: \n, \r, \t, space
    # Remove: other control characters (0x01-0x1F except \n\r\t)
    cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\r\t')

    return cleaned.strip()

# Global scraping service instance
scraping_service = ScrapingService()

# Convenience functions
def scrape_content(source_url: str, source_type: str, content: str = "") -> Optional[str]:
    """Scrape content based on source type"""
    return scraping_service.scrape_content(source_url, source_type, content)

def scrape_pdf(url: str) -> Optional[str]:
    """Scrape PDF content"""
    return scraping_service._scrape_pdf(url)

def scrape_arxiv_by_title(title: str) -> Optional[str]:
    """Search and scrape arxiv paper by title"""
    return scraping_service._scrape_arxiv_by_title(title)

def scrape_html(url: str) -> Optional[str]:
    """Scrape HTML content"""
    return scraping_service._scrape_html(url)
