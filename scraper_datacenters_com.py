import argparse
import json
import re
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import uuid
from datetime import datetime, timezone
import os


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


def _infer_operator_from_title(title: str) -> Optional[str]:
    if not title:
        return None
    # Many pages use pattern: "Equinix: PA10 Paris IBX Data Center"
    if ":" in title:
        left = title.split(":", 1)[0].strip()
        # Avoid generic site label
        if left.lower() != OPERATOR.lower():
            return left
    return None


def _infer_operator_from_url(url: str) -> Optional[str]:
    try:
        path = urlparse(url).path.strip("/")
        first_seg = (path.split("/", 1)[0] or "").lower()
        # Direct mappings for common vendors
        mappings = {
            "equinix": "Equinix",
            "digital-realty": "Digital Realty",
            "telehouse": "Telehouse",
            "global-switch": "Global Switch",
            "oracle": "Oracle",
            "ibm-cloud": "IBM Cloud",
            "microsoft-azure": "Microsoft Azure",
            "ntt": "NTT",
            "ntt-docomo": "NTT DOCOMO",
            "atlasedge": "AtlasEdge Data Centers",
            "exa-infrastructure": "EXA Infrastructure",
            "opcore": "Opcore",
        }
        # Exact first segment match
        if first_seg in mappings:
            return mappings[first_seg]
        # Keyword-based fallback on entire slug
        slug = first_seg
        for key, name in mappings.items():
            if key in slug:
                return name
    except Exception:
        pass
    return None


def parse_facility_details(html: str, url: str) -> Optional[Dict]:
    """
    Parse individual facility page to extract location, space, and power information.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    try:
        # Extract facility name/title
        title_element = soup.find("h1") or soup.find("title")
        title = title_element.get_text(strip=True) if title_element else "Unknown Facility"
        
        # Infer operator using multiple signals: Title prefix, URL slug, then fallback label
        operator = (
            _infer_operator_from_title(title)
            or _infer_operator_from_url(url)
            or None
        )
        if not operator:
            operator_element = soup.find("div", class_="text-xs text-gray-500")
            if operator_element:
                operator_text = operator_element.get_text(strip=True)
                # Use only if it's not the site label
                if operator_text and operator_text.lower() != OPERATOR.lower():
                    operator = operator_text
        # Final fallback
        operator = operator or OPERATOR
        
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


# =============================
# Normalization for PostgreSQL
# =============================

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def normalize_facility_to_data_center(facility: Dict) -> Dict:
    """
    Convert a facility dict from parse_facility_details() into a data_centers record shape.
    Fields mapped:
      - id (uuid)
      - name (title)
      - city, country (best-effort from location)
      - latitude, longitude (None - not available on this site)
      - power_capacity_mw (from specifications.power_mw)
      - server_count (None) — unknown
      - tier_level (None) — unknown
      - operator (operator)
      - status ("active")
      - created_at, updated_at (UTC timestamps)
    """
    loc = facility.get("location", {}) or {}
    specs = facility.get("specifications", {}) or {}

    # Parse numeric power if possible
    power_val = None
    try:
        if specs.get("power_mw") is not None:
            power_val = float(str(specs.get("power_mw")).strip())
    except Exception:
        power_val = None

    record = {
        "id": str(uuid.uuid4()),
        "name": facility.get("title") or "Unknown Facility",
        "city": (loc.get("city") or "") or None,
        "country": (loc.get("country") or "") or None,
        "latitude": None,
        "longitude": None,
        "power_capacity_mw": power_val,
        "server_count": None,
        "tier_level": None,
        "operator": facility.get("operator") or OPERATOR,
        "status": "active",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    return record

def build_search_cache_record(data_center_record: Dict, latest_cost_eur: Optional[float] = None) -> Dict:
    """
    Build a search_cache record using a data_centers record.
    - Tags include operator, country, city, status.
    - latest_power_mw mirrors data_center.power_capacity_mw.
    """
    name = data_center_record.get("name") or ""
    operator = data_center_record.get("operator") or ""
    country = data_center_record.get("country") or ""
    city = data_center_record.get("city") or ""
    status = data_center_record.get("status") or ""

    tags = [t for t in [operator, country, city, status] if t]
    search_text = " ".join([s for s in [name, operator, city, country] if s])

    rec = {
        "id": str(uuid.uuid4()),
        "data_center_id": data_center_record["id"],
        "search_text": search_text,
        "tags": tags,
        "latest_cost_eur": latest_cost_eur,
        "latest_power_mw": data_center_record.get("power_capacity_mw"),
        "updated_at": _now_iso(),
    }
    return rec

def _compose_address(loc: Dict) -> Optional[str]:
    if not isinstance(loc, dict):
        return None
    parts = []
    for key in ("address", "city", "country"):
        val = (loc.get(key) or "").strip()
        if val:
            parts.append(val)
    return ", ".join(parts) if parts else None


def geocode_address(query: str, email: Optional[str] = None, timeout: int = 15) -> Optional[Dict]:
    """
    Use OpenStreetMap Nominatim to geocode an address string. Returns {lat, lon} or None.
    Respect usage policy: include a descriptive User-Agent and contact email if provided.
    """
    try:
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 0,
        }
        ua = f"DataRackNews/1.0 (+https://example.com)"
        if email:
            ua = f"DataRackNews/1.0 ({email})"
        headers = {"User-Agent": ua}
        resp = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data:
            item = data[0]
            lat = float(item.get("lat")) if item.get("lat") else None
            lon = float(item.get("lon")) if item.get("lon") else None
            if lat is not None and lon is not None:
                return {"lat": lat, "lon": lon}
    except Exception as e:
        print(f"[geocode] Failed for '{query}': {e}")
    return None


def geocode_address_serpapi(query: str, api_key: Optional[str], timeout: int = 15) -> Optional[Dict]:
    """
    Use SerpAPI Google Maps to geocode an address string. Returns {lat, lon} or None.
    Requires a valid SerpAPI API key.
    """
    if not api_key:
        return None
    try:
        params = {
            "engine": "google_maps",
            "q": query,
            "api_key": api_key,
            "type": "search",
            "hl": "en",
        }
        resp = requests.get("https://serpapi.com/search", params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        # Try place_results (newer API shape)
        place_results = data.get("place_results")
        if isinstance(place_results, dict):
            gps = place_results.get("gps_coordinates") or {}
            lat = gps.get("latitude")
            lon = gps.get("longitude")
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                return {"lat": float(lat), "lon": float(lon)}
        # Fallback to local_results list
        local_results = data.get("local_results") or data.get("local_results_more_results")
        if isinstance(local_results, list) and local_results:
            first = local_results[0]
            gps = first.get("gps_coordinates") or {}
            lat = gps.get("latitude")
            lon = gps.get("longitude")
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                return {"lat": float(lat), "lon": float(lon)}
    except Exception as e:
        print(f"[geocode-serpapi] Failed for '{query}': {e}")
    return None


def facilities_to_db_payload(
    facilities: List[Dict],
    geocode: bool = False,
    email: Optional[str] = None,
    geocode_delay_s: float = 1.0,
    geocode_provider: str = "nominatim",
    serpapi_token: Optional[str] = None,
) -> Dict[str, List[Dict]]:
    """
    Convert a list of scraped facilities into DB-ready payloads.
    Returns a dict with keys: data_centers, search_cache.
    """
    data_centers: List[Dict] = []
    search_cache: List[Dict] = []

    for fac in facilities:
        dc = normalize_facility_to_data_center(fac)
        # Optional geocoding if latitude/longitude are missing but we have an address
        if geocode and (dc.get("latitude") is None or dc.get("longitude") is None):
            full_addr = _compose_address(fac.get("location", {}) or {})
            if full_addr:
                geo = None
                if geocode_provider == "serpapi":
                    # Resolve token from env if not provided
                    token = serpapi_token or os.getenv("SERPAPI_TOKEN")
                    geo = geocode_address_serpapi(full_addr, token)
                else:
                    geo = geocode_address(full_addr, email=email)
                if geo:
                    dc["latitude"] = geo["lat"]
                    dc["longitude"] = geo["lon"]
                # Respectful rate limiting
                time.sleep(geocode_delay_s)
        sc = build_search_cache_record(dc)
        data_centers.append(dc)
        search_cache.append(sc)

    return {
        "data_centers": data_centers,
        "search_cache": search_cache,
    }


def main():
    parser = argparse.ArgumentParser(description="Scrape data center facilities from datacenters.com")
    parser.add_argument("--country", required=True, help="Country to search (e.g., 'france', 'spain')")
    parser.add_argument("--city", help="Optional city filter (e.g., 'paris', 'barcelona')")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--db-ready", action="store_true", help="Output PostgreSQL-ready payload (data_centers + search_cache)")
    parser.add_argument("--geocode", action="store_true", help="If set with --db-ready, geocode addresses to fill latitude/longitude")
    parser.add_argument("--email", help="Contact email for geocoding User-Agent (recommended for Nominatim)")
    parser.add_argument("--geocode-provider", choices=["nominatim", "serpapi"], default="nominatim", help="Geocoder to use for lat/lon")
    parser.add_argument("--serpapi-token", help="SerpAPI token for google maps geocoding (falls back to env SERPAPI_TOKEN)")
    
    args = parser.parse_args()
    
    facilities = scrape_facilities(args.country, args.city)
    
    if args.output:
        payload = facilities_to_db_payload(
            facilities,
            geocode=args.geocode,
            email=args.email,
            geocode_provider=args.geocode_provider,
            serpapi_token=args.serpapi_token,
        ) if args.db_ready else facilities
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"Results saved to {args.output}")
    else:
        payload = facilities_to_db_payload(
            facilities,
            geocode=args.geocode,
            email=args.email,
            geocode_provider=args.geocode_provider,
            serpapi_token=args.serpapi_token,
        ) if args.db_ready else facilities
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
