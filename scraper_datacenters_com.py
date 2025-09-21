import argparse
import json
import re
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


OPERATOR = "DataCenters.com"
BASE_URL = "https://www.datacenters.com"
LOCATIONS_BASE = f"{BASE_URL}/locations"


def fetch(url: str, timeout: int = 20) -> str:
    """Fetch HTML content from a URL"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    r = requests.get(url, timeout=timeout, headers=headers)
    r.raise_for_status()
    return r.text


def search_locations(country: str, city: Optional[str] = None) -> List[str]:
    """
    Search for data center locations in a country, optionally filtered by city.
    Returns a list of facility URLs.
    """
    # First, get the country page
    country_url = f"{LOCATIONS_BASE}/{country.lower()}"
    print(f"Fetching country page: {country_url}")
    
    try:
        html = fetch(country_url)
        soup = BeautifulSoup(html, "html.parser")
        
        # Look for search results or facility links
        facility_urls = []
        
        # Find all facility links - these typically have href attributes pointing to facility pages
        # Based on the HTML structure shown in the images, look for links with specific classes
        facility_links = soup.find_all("a", class_=re.compile(r"flex.*gap.*rounded.*border"))
        
        if not facility_links:
            # Fallback: look for any links that might be facility pages
            facility_links = soup.find_all("a", href=re.compile(r"/locations/"))
        
        for link in facility_links:
            href = link.get("href")
            if href:
                # Convert relative URLs to absolute
                full_url = urljoin(BASE_URL, href)
                
                # If city filter is specified, check if the link text contains the city
                if city:
                    link_text = link.get_text(strip=True).lower()
                    if city.lower() not in link_text:
                        continue
                
                facility_urls.append(full_url)
        
        print(f"Found {len(facility_urls)} facility URLs")
        return facility_urls
        
    except Exception as e:
        print(f"Error searching locations: {e}")
        return []


def parse_facility_details(html: str, url: str) -> Optional[Dict]:
    """
    Parse individual facility page to extract location, space, and power information.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    try:
        # Extract facility name/title
        title_element = soup.find("h1") or soup.find("title")
        title = title_element.get_text(strip=True) if title_element else "Unknown Facility"
        
        # Extract operator information from div with class 'text-xs text-gray-500'
        operator = OPERATOR  # Default fallback
        operator_element = soup.find("div", class_="text-xs text-gray-500")
        if operator_element:
            operator_text = operator_element.get_text(strip=True)
            if operator_text:
                operator = operator_text
        
        # Extract location information
        location_info = {}
        
        # Look for address information
        address_selectors = [
            ".LocationShowSidebar__sidebarAddress__AZdxu",  # Primary selector based on HTML structure
            ".location-address",
            ".address",
            "[class*='address']",
            ".contact-info"
        ]
        
        address = ""
        for selector in address_selectors:
            addr_element = soup.select_one(selector)
            if addr_element:
                address = addr_element.get_text(strip=True)
                break
        
        # Extract space and power from locationSidebarStats
        space_sqft = None
        power_mw = None
        
        # Look for the locationSidebarStats section
        sidebar_stats = soup.find("div", class_=re.compile(r"locationSidebarStats"))
        if sidebar_stats:
            # Find statInfo divs within the sidebar
            stat_infos = sidebar_stats.find_all("div", class_=re.compile(r"statInfo"))
            
            for stat in stat_infos:
                stat_text = stat.get_text(strip=True).lower()
                
                # Extract space (sqft)
                if "sqft" in stat_text or "square" in stat_text:
                    space_match = re.search(r"([\d,]+)\s*sqft", stat_text)
                    if space_match:
                        space_sqft = space_match.group(1).replace(",", "")
                
                # Extract power (MW)
                if "mw" in stat_text or "power" in stat_text:
                    power_match = re.search(r"([\d.]+)\s*mw", stat_text)
                    if power_match:
                        power_mw = power_match.group(1)
        
        # If not found in sidebar, look for alternative locations
        if not space_sqft or not power_mw:
            # Look for any text containing space/power information
            all_text = soup.get_text().lower()
            
            if not space_sqft:
                space_match = re.search(r"([\d,]+)\s*(?:sqft|square\s+feet)", all_text)
                if space_match:
                    space_sqft = space_match.group(1).replace(",", "")
            
            if not power_mw:
                power_match = re.search(r"([\d.]+)\s*mw", all_text)
                if power_match:
                    power_mw = power_match.group(1)
        
        # Generate facility ID
        facility_id = f"datacenters-com-{urlparse(url).path.strip('/').replace('/', '-')}"
        
        facility_data = {
            "facility_id": facility_id,
            "title": title,
            "operator": operator,
            "location": {
                "address": address,
            },
            "specifications": {
                "space_sqft": space_sqft,
                "power_mw": power_mw,
            },
            "source_url": url,
        }
        
        return facility_data
        
    except Exception as e:
        print(f"Error parsing facility details from {url}: {e}")
        return None


def scrape_facilities(country: str, city: Optional[str] = None) -> List[Dict]:
    """
    Main function to scrape data center facilities from datacenters.com
    """
    print(f"Scraping facilities for country: {country}" + (f", city: {city}" if city else ""))
    
    # Get facility URLs using the simple search method
    facility_urls = search_locations(country, city)
    
    if not facility_urls:
        print("No facility URLs found")
        return []
    
    facilities = []
    
    for i, url in enumerate(facility_urls, 1):
        print(f"Processing facility {i}/{len(facility_urls)}: {url}")
        
        try:
            html = fetch(url)
            facility_data = parse_facility_details(html, url)
            
            if facility_data:
                # Add country and city to location if provided
                if country:
                    facility_data["location"]["country"] = country
                if city:
                    facility_data["location"]["city"] = city
                    
                facilities.append(facility_data)
                print(f"  Extracted: {facility_data['title']}")
            else:
                print(f"  Failed to extract data")
                
        except Exception as e:
            print(f"  Error processing {url}: {e}")
        
        # Be respectful with requests
        time.sleep(1)
    
    print(f"Successfully scraped {len(facilities)} facilities")
    return facilities


def main():
    parser = argparse.ArgumentParser(description="Scrape data center facilities from datacenters.com")
    parser.add_argument("--country", required=True, help="Country to search (e.g., 'france', 'spain')")
    parser.add_argument("--city", help="Optional city filter (e.g., 'paris', 'barcelona')")
    parser.add_argument("--output", help="Output JSON file path")
    
    args = parser.parse_args()
    
    facilities = scrape_facilities(args.country, args.city)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(facilities, f, ensure_ascii=False, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(facilities, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
