"""
Entity Validation Service

Validates entity legitimacy through multiple signals:
- Digital presence (website, phone, social media)
- Address verification (geocoding, USPS)
- Business registration checks
- Domain/WHOIS lookups

All results stored as EvidenceItems with confidence scores.
Red flags contribute to anomaly scoring.
"""

from __future__ import annotations
import re
import requests
import socket
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, quote_plus
from datetime import datetime

# Free/low-cost validation strategies
# Most checks use free APIs or simple HTTP requests

def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web using DuckDuckGo (free, no API key needed)
    Returns list of {title, url, snippet}
    """
    try:
        # Use DuckDuckGo HTML search (no API key required)
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []
        
        # Simple HTML parsing (could use BeautifulSoup, but keeping dependencies minimal)
        html = response.text
        results = []
        
        # DuckDuckGo result pattern (simplified - may need adjustment)
        # Look for result links
        link_pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(link_pattern, html)
        
        for url, title in matches[:max_results]:
            results.append({
                "title": title.strip(),
                "url": url.strip(),
                "snippet": ""
            })
        
        return results
    except Exception as e:
        # Fallback: return empty results if search fails
        return []

def find_entity_website(entity_name: str, address: str = None, city: str = None, state: str = None) -> Optional[str]:
    """
    Search the web to find entity's website
    Returns website URL if found, None otherwise
    """
    # Build search query
    query_parts = [entity_name]
    if city and state:
        query_parts.append(f"{city} {state}")
    query = " ".join(query_parts) + " website"
    
    results = search_web(query, max_results=10)
    
    # Look for website URLs in results
    domain_pattern = re.compile(r'https?://([^/]+)', re.IGNORECASE)
    entity_words = set(re.findall(r'\w+', entity_name.lower()))
    
    for result in results:
        url = result.get("url", "")
        title = result.get("title", "").lower()
        
        # Check if URL looks like a website (not a directory page)
        if domain_pattern.match(url):
            domain = domain_pattern.match(url).group(1)
            # Skip obvious directory/social media sites
            skip_domains = ['facebook.com', 'linkedin.com', 'twitter.com', 'instagram.com', 
                          'yelp.com', 'bbb.org', 'yellowpages.com', 'whitepages.com',
                          'google.com', 'bing.com', 'duckduckgo.com']
            if any(skip in domain for skip in skip_domains):
                continue
            
            # Check if entity name words appear in title or domain
            title_words = set(re.findall(r'\w+', title))
            domain_words = set(re.findall(r'\w+', domain.replace('.', ' ')))
            
            # If significant word overlap, likely the right website
            if entity_words & title_words or entity_words & domain_words:
                return url
    
    return None

def find_entity_phone(entity_name: str, address: str = None, city: str = None, state: str = None) -> Optional[str]:
    """
    Search the web to find entity's phone number
    Returns phone number if found, None otherwise
    """
    # Build search query
    query_parts = [entity_name]
    if address:
        query_parts.append(address)
    if city and state:
        query_parts.append(f"{city} {state}")
    query = " ".join(query_parts) + " phone number"
    
    results = search_web(query, max_results=5)
    
    # Look for phone numbers in results
    phone_pattern = re.compile(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})')
    
    for result in results:
        # Search in title and URL
        text_to_search = result.get("title", "") + " " + result.get("url", "")
        match = phone_pattern.search(text_to_search)
        if match:
            phone = f"{match.group(2)}{match.group(3)}{match.group(4)}"
            if len(phone) == 10:
                return phone
    
    return None

def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from text"""
    if not text:
        return None
    # Match various phone formats
    phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    match = re.search(phone_pattern, text)
    if match:
        return f"{match.group(2)}{match.group(3)}{match.group(4)}"
    return None

def extract_website(text: str) -> Optional[str]:
    """Extract website URL from text"""
    if not text:
        return None
    # Match URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(url_pattern, text)
    if match:
        url = match.group(0).rstrip('.,;:')
        # Normalize
        if not url.startswith('http'):
            url = 'http://' + url
        return url
    return None

def check_website_exists(url: str, timeout: int = 5) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if website exists and is accessible
    Returns: (exists, status_code, error_message)
    """
    try:
        # Normalize URL
        if not url.startswith('http'):
            url = 'http://' + url
        
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        
        # First check DNS resolution
        try:
            socket.gethostbyname(domain)
        except socket.gaierror:
            return (False, None, "DNS lookup failed - domain doesn't resolve")
        
        # Then check HTTP
        response = requests.get(url, timeout=timeout, allow_redirects=True, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; CityFraudFinder/1.0)'
        })
        
        if response.status_code == 200:
            return (True, str(response.status_code), None)
        elif response.status_code < 500:
            return (True, str(response.status_code), f"Website exists but returned {response.status_code}")
        else:
            return (False, str(response.status_code), f"Server error {response.status_code}")
            
    except requests.exceptions.Timeout:
        return (False, None, "Request timeout")
    except requests.exceptions.ConnectionError:
        return (False, None, "Connection failed")
    except Exception as e:
        return (False, None, f"Error: {str(e)}")

def check_google_business(name: str, address: str) -> Tuple[bool, Optional[str]]:
    """
    Check if Google Business Profile exists
    Note: This is a simplified check - full implementation would use Google Places API
    
    Returns: (exists, profile_url)
    """
    # For now, return None - requires Google Places API key
    # Full implementation would search Google Places API
    return (None, None)

def validate_phone_format(phone: str) -> bool:
    """Basic phone format validation (US numbers)"""
    cleaned = re.sub(r'[^\d]', '', phone)
    return len(cleaned) == 10 and cleaned.isdigit()

def check_address_geocode(address: str, city: str = None, state: str = None) -> Tuple[bool, Optional[str]]:
    """
    Check if address can be geocoded (validates it's a real location)
    Uses free Nominatim API (OpenStreetMap)
    
    Returns: (valid, error_message)
    """
    try:
        full_address = address
        if city:
            full_address += f", {city}"
        if state:
            full_address += f", {state}"
        
        # Use free Nominatim API (rate limited, but free)
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": full_address,
                "format": "json",
                "limit": 1
            },
            headers={"User-Agent": "CityFraudFinder/1.0"},
            timeout=5
        )
        
        if response.status_code == 200:
            results = response.json()
            if results:
                return (True, None)
            else:
                return (False, "Address not found in geocoding database")
        else:
            return (False, f"Geocoding service error: {response.status_code}")
            
    except Exception as e:
        return (False, f"Geocoding error: {str(e)}")

def run_validation_checks(entity_name: str, address: str = None, city: str = None, 
                         state: str = None, phone: str = None, website: str = None,
                         license_id: str = None, search_web: bool = True) -> Dict[str, Dict]:
    """
    Run all available validation checks
    If search_web=True, will search the internet to find website/phone
    Otherwise, only uses provided phone/website parameters
    
    Returns dict of check_name -> {status: bool/None, confidence: float, details: str}
    """
    results = {}
    
    # WEB SEARCH: Try to find website and phone number online
    found_website = None
    found_phone = None
    
    if search_web:
        # Search for website
        found_website = find_entity_website(entity_name, address, city, state)
        if found_website:
            website = found_website  # Use found website for checks
        
        # Search for phone number
        found_phone = find_entity_phone(entity_name, address, city, state)
        if found_phone:
            phone = found_phone  # Use found phone for checks
    
    # 1. Address geocoding check
    if address:
        geocode_valid, geocode_error = check_address_geocode(address, city, state)
        results["address_geocode"] = {
            "status": geocode_valid,
            "confidence": 0.9 if geocode_valid else 0.3,
            "details": geocode_error or "Address geocoded successfully"
        }
    
    # 2. Website search and validation
    if website:
        site_exists, status_code, error = check_website_exists(website)
        source = "found via web search" if found_website else "provided"
        results["website_exists"] = {
            "status": site_exists,
            "confidence": 0.85 if site_exists else 0.2,
            "details": f"{error or f'Website accessible (HTTP {status_code})'} ({source})",
            "url": website if site_exists else None
        }
    elif search_web:
        # We searched but didn't find a website - this is a red flag
        results["website_search"] = {
            "status": False,
            "confidence": 0.7,
            "details": "No website found via web search"
        }
    
    # 3. Phone number search and validation
    if phone:
        phone_valid = validate_phone_format(phone)
        source = "found via web search" if found_phone else "provided"
        results["phone_format"] = {
            "status": phone_valid,
            "confidence": 0.8 if phone_valid else 0.2,
            "details": f"Valid US phone format ({source})" if phone_valid else f"Invalid phone format ({source})",
            "phone": phone if phone_valid else None
        }
    elif search_web:
        # We searched but didn't find a phone - this is a red flag
        results["phone_search"] = {
            "status": False,
            "confidence": 0.7,
            "details": "No phone number found via web search"
        }
    
    # 4. Missing digital presence flags
    missing_signals = []
    if not website:
        missing_signals.append("no website")
    if not phone:
        missing_signals.append("no phone")
    
    if missing_signals:
        results["missing_digital_presence"] = {
            "status": False,  # Red flag
            "confidence": 0.7,
            "details": f"Missing: {', '.join(missing_signals)}"
        }
    
    # 5. License ID present check (for regulated entities)
    if license_id:
        results["has_license_id"] = {
            "status": True,
            "confidence": 0.6,
            "details": f"License ID provided: {license_id}"
        }
    
    return results

def calculate_validation_score(results: Dict[str, Dict]) -> Tuple[float, List[str]]:
    """
    Calculate overall validation score and list red flags
    
    Returns: (score 0-100, list of red_flag_messages)
    """
    if not results:
        return (50.0, ["No validation data available"])
    
    total_weight = 0
    weighted_score = 0
    red_flags = []
    
    for check_name, result in results.items():
        status = result["status"]
        confidence = result.get("confidence", 0.5)
        
        if check_name == "missing_digital_presence":
            # This is a red flag - penalize score
            red_flags.append(result["details"])
            weighted_score += 20 * confidence  # Low score
            total_weight += 30
        elif status is True:
            weighted_score += 100 * confidence
            total_weight += 100
        elif status is False:
            # Failed check - red flag
            red_flags.append(f"{check_name}: {result['details']}")
            weighted_score += 30 * confidence  # Low score
            total_weight += 100
        # If status is None, skip (incomplete check)
    
    if total_weight == 0:
        return (50.0, ["No validation checks completed"])
    
    final_score = weighted_score / total_weight
    
    return (final_score, red_flags)

