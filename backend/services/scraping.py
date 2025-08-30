import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def scrape_url(url: str) -> Optional[str]:
    """
    Scrape text content from a web URL using BeautifulSoup.
    
    Args:
        url: Web URL to scrape
        
    Returns:
        str: Extracted text content, or None if scraping fails
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            logger.error(f"Invalid URL: {url}")
            return None
        
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Extract text content
        text = soup.get_text()
        
        # Clean up the text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        if not text:
            logger.warning(f"No text content found for URL: {url}")
            return None
            
        return text
        
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP error while scraping {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None

def extract_links_from_page(url: str, domain_filter: Optional[str] = None) -> Optional[list]:
    """
    Extract all links from a web page, optionally filtered by domain.
    
    Args:
        url: Web URL to extract links from
        domain_filter: Optional domain to filter links by
        
    Returns:
        list: List of extracted URLs, or None if extraction fails
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Handle relative URLs
            if href.startswith('/'):
                parsed_url = urlparse(url)
                href = f"{parsed_url.scheme}://{parsed_url.netloc}{href}"
            elif href.startswith('#'):
                continue  # Skip anchor links
            elif not href.startswith('http'):
                continue  # Skip non-http links
                
            # Apply domain filter if specified
            if domain_filter:
                link_domain = urlparse(href).netloc
                if domain_filter not in link_domain:
                    continue
                    
            links.append(href)
        
        return list(set(links))  # Remove duplicates
        
    except Exception as e:
        logger.error(f"Error extracting links from {url}: {e}")
        return None

def get_page_title(url: str) -> Optional[str]:
    """
    Extract the title of a web page.
    
    Args:
        url: Web URL
        
    Returns:
        str: Page title, or None if extraction fails
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('title')
        
        return title.get_text().strip() if title else None
        
    except Exception as e:
        logger.error(f"Error getting title from {url}: {e}")
        return None
