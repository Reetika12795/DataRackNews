import os
import json
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import List, Dict, Any
from serpapi import GoogleSearch  # For dynamic URL discovery
import pdfplumber  # For PDF scraping
from dotenv import load_dotenv

# Config
load_dotenv()

# Config
SERPAPI_TOKEN = os.getenv('SERPAPI_TOKEN')
OUTPUT_DIR = './output'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

if not SERPAPI_TOKEN:
    raise ValueError("SERPAPI_TOKEN environment variable is required.")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Search configs for dynamic URL building (focus on Europe, specs-rich pages)
SEARCH_CONFIGS = [
    # Aggregator directories for broad coverage
    {"q": "data centers Europe directory list site:datacentermap.com", "num": 10},
    {"q": "data centers Europe facilities site:baxtel.com", "num": 10},
    {"q": "data centers Europe specs site:cloudscene.com", "num": 10},
    # Provider-specific (Equinix, Digital Realty, Global Switch)
    {"q": "Equinix data centers Europe facility pages", "num": 15},
    {"q": "Digital Realty Europe data centers list specs", "num": 15},
    {"q": "Global Switch Europe data centers URLs", "num": 10},
    # Country/city-specific for depth (top hubs)
    {"q": "data centers Frankfurt specs size price energy carbon site:equinix.com OR site:digitalrealty.com", "num": 10},
    {"q": "data centers London colocation price sustainability site:globalswitch.com OR site:datacentermap.com", "num": 10},
    {"q": "data centers Amsterdam data centers MW PUE carbon footprint", "num": 10},
    {"q": "data centers Paris Equinix Digital Realty specs", "num": 10},
    {"q": "top data centers Europe size price energy carbon footprint", "num": 15},  # General top lists
]

def build_url_list(max_urls=50) -> List[str]:
    """Use SerpAPI to dynamically build a list of data center URLs."""
    all_urls = set()  # Dedupe
    params_base = {
        # "q": query,
        "api_key": SERPAPI_TOKEN,
        # "num": max_results,  # Limit per query to avoid quota drain
        # "location": "Europe",  # Bias to Europe
    }
    
    for config in SEARCH_CONFIGS:
        params = params_base.copy()
        params.update(config)  # Add query and num
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict().get('organic_results', [])
            
            for result in results:
                link = result.get('link')
                if link and re.search(r'(data[- ]center|datacenter|facility|colocation|specs|price|energy|carbon)', 
                                     (result.get('title', '') + ' ' + result.get('snippet', '')).lower()):
                    # Filter for relevant pages (e.g., individual facilities, not homepages)
                    if not any(skip in link.lower() for skip in ['home', 'about', 'contact', 'blog']):
                        all_urls.add(link)
                        if len(all_urls) >= max_urls:
                            break
            time.sleep(1)  # Rate limit
        except Exception as e:
            print(f"Search failed for {config['query']}: {e}")
    
    # Convert to list, shuffle for variety if needed
    url_list = list(all_urls)[:max_urls]
    print(f"Built URL list with {len(url_list)} links via SerpAPI.")
    return url_list

def scrape_datacenter_details(url):
    """Scrape detailed information from data center websites with enhanced algorithms"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements for cleaner text
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extract relevant information using multiple strategies
        details = {
            'url': url,
            'name': extract_name_enhanced(soup, url),
            'location': extract_location_enhanced(soup),
            'capacity': extract_capacity_enhanced(soup),
            'power_usage': extract_power_usage_enhanced(soup),
            'sustainability_info': extract_sustainability_enhanced(soup),
            'additional_specs': extract_additional_specs(soup)
        }
        
        # Try to get more data from structured data (JSON-LD, microdata)
        structured_data = extract_structured_data(soup)
        if structured_data:
            details['structured_data'] = structured_data
        
        return details
        
    except requests.exceptions.Timeout:
        print(f"Timeout scraping {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error scraping {url}: {e}")
        return None
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def extract_name_enhanced(soup, url):
    """Enhanced name extraction with multiple strategies"""
    # Strategy 1: Try specific selectors for common data center sites
    name_selectors = [
        'h1.facility-name', 'h1.datacenter-name', 'h1.site-title',
        '.facility-header h1', '.datacenter-header h1',
        'h1', '.page-title', '.hero-title', '.main-title'
    ]
    
    for selector in name_selectors:
        element = soup.select_one(selector)
        if element and element.get_text().strip():
            name = element.get_text().strip()
            # Clean up common prefixes/suffixes
            name = re.sub(r'^(Data Center|Datacenter|Facility|Location)\s*[-:|]?\s*', '', name, flags=re.IGNORECASE)
            if len(name) > 5:  # Avoid too short names
                return name
    
    # Strategy 2: Extract from title tag
    title = soup.find('title')
    if title:
        title_text = title.get_text().strip()
        # Remove common website suffixes
        title_text = re.sub(r'\s*[-|]\s*(Data Center|Datacenter|Location|Facility).*$', '', title_text, flags=re.IGNORECASE)
        if len(title_text) > 5:
            return title_text
    
    # Strategy 3: Extract from URL
    domain_match = re.search(r'://(?:www\.)?([^./]+)', url)
    if domain_match:
        domain = domain_match.group(1)
        return domain.replace('-', ' ').title()
    
    return "Unknown Facility"

def extract_location_enhanced(soup):
    """Enhanced location extraction with multiple strategies"""
    location_info = {}
    
    # Strategy 1: Look for structured address data
    address_selectors = [
        '.address', '.location', '.facility-address', '.datacenter-location',
        '[itemtype*="PostalAddress"]', '.contact-address', '.site-address'
    ]
    
    for selector in address_selectors:
        element = soup.select_one(selector)
        if element:
            address_text = element.get_text().strip()
            if len(address_text) > 10:
                location_info['full_address'] = address_text
                break
    
    # Strategy 2: Extract specific location components
    text = soup.get_text()
    
    # Look for city, state patterns
    city_state_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})\b'
    city_state_matches = re.findall(city_state_pattern, text)
    if city_state_matches:
        location_info['city_state'] = f"{city_state_matches[0][0]}, {city_state_matches[0][1]}"
    
    # Look for specific address patterns
    address_patterns = [
        r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Way|Lane|Ln)[^,]*,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}',
        r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Way|Lane|Ln)'
    ]
    
    for pattern in address_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            location_info['street_address'] = matches[0]
            break
    
    # Strategy 3: Look for coordinates
    coord_pattern = r'(\-?\d+\.\d+)\s*,\s*(\-?\d+\.\d+)'
    coord_matches = re.findall(coord_pattern, text)
    if coord_matches:
        location_info['coordinates'] = f"{coord_matches[0][0]}, {coord_matches[0][1]}"
    
    return location_info if location_info else "Location not found"

def extract_capacity_enhanced(soup):
    """Enhanced capacity extraction with multiple strategies"""
    capacity_info = {}
    text = soup.get_text()
    
    # Strategy 1: Power capacity patterns (more comprehensive)
    power_patterns = [
        r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:MW|megawatts?|MegaWatts?)',
        r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:kW|kilowatts?)',
        r'Power\s*:\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:MW|kW)',
        r'Capacity\s*:\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:MW|kW)',
        r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:MW|kW)\s*(?:capacity|power|electrical)',
    ]
    
    for pattern in power_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            power_value = matches[0].replace(',', '')
            if 'MW' in pattern.upper():
                capacity_info['power_mw'] = float(power_value)
            else:  # kW
                capacity_info['power_mw'] = float(power_value) / 1000
            break
    
    # Strategy 2: Space capacity patterns
    space_patterns = [
        r'(\d+(?:,\d+)*)\s*(?:sq\.?\s*ft\.?|square\s+feet|sqft)',
        r'(\d+(?:,\d+)*)\s*(?:sq\.?\s*m\.?|square\s+meters?|sqm)',
        r'(\d+(?:,\d+)*)\s*(?:acres?)',
        r'Space\s*:\s*(\d+(?:,\d+)*)\s*(?:sq\.?\s*ft\.?|square\s+feet)',
    ]
    
    for pattern in space_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            space_value = int(matches[0].replace(',', ''))
            if 'sq' in pattern.lower() and ('ft' in pattern.lower() or 'feet' in pattern.lower()):
                capacity_info['space_sqft'] = space_value
            elif 'acre' in pattern.lower():
                capacity_info['space_acres'] = space_value
                capacity_info['space_sqft'] = space_value * 43560  # Convert acres to sqft
            break
    
    # Strategy 3: Rack/Cabinet capacity
    rack_patterns = [
        r'(\d+(?:,\d+)*)\s*(?:racks?|cabinets?|servers?)',
        r'(\d+(?:,\d+)*)\s*(?:IT\s+)?(?:racks?|cabinets?)',
        r'Racks?\s*:\s*(\d+(?:,\d+)*)',
    ]
    
    for pattern in rack_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            capacity_info['racks'] = int(matches[0].replace(',', ''))
            break
    
    # Strategy 4: Look in meta tags and structured data
    meta_tags = soup.find_all('meta')
    for meta in meta_tags:
        content = meta.get('content', '').lower()
        if 'mw' in content or 'megawatt' in content:
            mw_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:mw|megawatt)', content)
            if mw_match:
                capacity_info['power_mw'] = float(mw_match.group(1))
    
    return capacity_info if capacity_info else "Capacity information not found"

def extract_power_usage_enhanced(soup):
    """Enhanced power usage extraction"""
    power_info = {}
    text = soup.get_text()
    
    # Strategy 1: PUE (Power Usage Effectiveness) patterns
    pue_patterns = [
        r'PUE\s*:?\s*(\d+\.\d+)',
        r'Power\s+Usage\s+Effectiveness\s*:?\s*(\d+\.\d+)',
        r'(\d+\.\d+)\s*PUE',
        r'PUE\s+of\s+(\d+\.\d+)',
        r'PUE\s+rating\s*:?\s*(\d+\.\d+)',
    ]
    
    for pattern in pue_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            pue_value = float(matches[0])
            if 1.0 <= pue_value <= 3.0:  # Valid PUE range
                power_info['pue'] = pue_value
            break
    
    # Strategy 2: Energy consumption patterns
    consumption_patterns = [
        r'(\d+(?:,\d+)*)\s*(?:kWh|kilowatt\s+hours?)\s*(?:per\s+year|annually)',
        r'(\d+(?:,\d+)*)\s*(?:MWh|megawatt\s+hours?)\s*(?:per\s+year|annually)',
        r'Annual\s+consumption\s*:?\s*(\d+(?:,\d+)*)\s*(?:kWh|MWh)',
    ]
    
    for pattern in consumption_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            consumption = int(matches[0].replace(',', ''))
            if 'MWh' in pattern:
                power_info['annual_consumption_mwh'] = consumption
            else:  # kWh
                power_info['annual_consumption_mwh'] = consumption / 1000
            break
    
    # Strategy 3: Renewable energy percentage
    renewable_patterns = [
        r'(\d+(?:\.\d+)?)\s*%\s*(?:renewable|clean|green)\s*(?:energy|power)',
        r'(?:renewable|clean|green)\s*(?:energy|power)\s*:?\s*(\d+(?:\.\d+)?)\s*%',
        r'(\d+(?:\.\d+)?)\s*percent\s*(?:renewable|clean|green)',
        r'(?:renewable|clean|green)\s*:?\s*(\d+(?:\.\d+)?)\s*%',
    ]
    
    for pattern in renewable_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            renewable_pct = float(matches[0])
            if 0 <= renewable_pct <= 100:
                power_info['renewable_percentage'] = renewable_pct
            break
    
    # Strategy 4: Cooling efficiency
    cooling_patterns = [
        r'CUE\s*:?\s*(\d+\.\d+)',
        r'Cooling\s+Usage\s+Effectiveness\s*:?\s*(\d+\.\d+)',
        r'(\d+\.\d+)\s*CUE',
    ]
    
    for pattern in cooling_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            power_info['cue'] = float(matches[0])
            break
    
    return power_info if power_info else "Power usage information not found"

def extract_sustainability_enhanced(soup):
    """Enhanced sustainability and carbon footprint extraction"""
    sustainability_info = {
        'certifications': [],
        'green_initiatives': [],
        'carbon_metrics': {},
        'sustainability_score': 0
    }
    
    text = soup.get_text().lower()
    
    # Strategy 1: Look for certifications
    certifications = [
        'leed', 'breeam', 'energy star', 'iso 14001', 'iso 50001',
        'green globes', 'uptime institute', 'tier iv', 'tier iii',
        'pci dss', 'soc 2', 'carbon neutral', 'net zero'
    ]
    
    for cert in certifications:
        if cert in text:
            sustainability_info['certifications'].append(cert.upper())
            sustainability_info['sustainability_score'] += 2
    
    # Strategy 2: Green energy initiatives
    green_keywords = [
        'solar power', 'wind power', 'renewable energy', 'clean energy',
        'carbon neutral', 'net zero', 'carbon negative', 'zero emissions',
        'green energy', 'sustainable power', 'hydroelectric', 'geothermal'
    ]
    
    for keyword in green_keywords:
        if keyword in text:
            sustainability_info['green_initiatives'].append(keyword)
            sustainability_info['sustainability_score'] += 1
    
    # Strategy 3: Carbon footprint metrics
    carbon_patterns = [
        r'(\d+(?:,\d+)*)\s*(?:tons?|tonnes?)\s*(?:co2|carbon dioxide)\s*(?:per year|annually)',
        r'carbon\s+footprint\s*:?\s*(\d+(?:,\d+)*)\s*(?:tons?|tonnes?)',
        r'(\d+(?:,\d+)*)\s*(?:kg|kilograms?)\s*co2\s*(?:per\s+kwh|\/kwh)',
        r'carbon\s+intensity\s*:?\s*(\d+(?:,\d+)*)',
    ]
    
    for pattern in carbon_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            if 'tons' in pattern or 'tonnes' in pattern:
                sustainability_info['carbon_metrics']['annual_co2_tons'] = int(matches[0].replace(',', ''))
            elif 'kg' in pattern:
                sustainability_info['carbon_metrics']['co2_kg_per_kwh'] = float(matches[0].replace(',', ''))
            break
    
    # Strategy 4: Water usage (important for data centers)
    water_patterns = [
        r'(\d+(?:,\d+)*)\s*(?:gallons?|liters?|litres?)\s*(?:per\s+year|annually)',
        r'water\s+usage\s*:?\s*(\d+(?:,\d+)*)',
        r'(\d+(?:,\d+)*)\s*(?:gallons?|liters?)\s*(?:per\s+mwh|\/mwh)',
    ]
    
    for pattern in water_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            sustainability_info['carbon_metrics']['water_usage'] = int(matches[0].replace(',', ''))
            break
    
    # Strategy 5: Look for specific sustainability sections
    sustainability_sections = soup.find_all(['div', 'section'], 
                                           class_=re.compile(r'sustain|green|environment|carbon', re.I))
    
    for section in sustainability_sections:
        section_text = section.get_text()
        if len(section_text) > 50:
            sustainability_info['sustainability_section'] = section_text[:300] + '...'
            sustainability_info['sustainability_score'] += 3
            break
    
    return sustainability_info

def extract_additional_specs(soup):
    """Extract additional technical specifications"""
    specs = {}
    text = soup.get_text()
    
    # Network connectivity
    network_patterns = [
        r'(\d+)\s*(?:gbps|gigabit)',
        r'(\d+)\s*(?:mbps|megabit)',
        r'(\d+)\s*(?:tbps|terabit)',
    ]
    
    for pattern in network_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            if 'gbps' in pattern.lower():
                specs['network_gbps'] = int(matches[0])
            elif 'tbps' in pattern.lower():
                specs['network_gbps'] = int(matches[0]) * 1000
            break
    
    # Redundancy levels
    redundancy_keywords = ['n+1', 'n+2', '2n', '2n+1', 'redundant', 'fault tolerant']
    for keyword in redundancy_keywords:
        if keyword in text.lower():
            specs['redundancy'] = keyword
            break
    
    # Cooling systems
    cooling_types = ['air cooled', 'liquid cooled', 'evaporative cooling', 'free cooling', 'chilled water']
    for cooling in cooling_types:
        if cooling in text.lower():
            specs['cooling_type'] = cooling
            break
    
    # Security features
    security_features = ['biometric', '24/7 security', 'keycard access', 'cctv', 'security cameras']
    specs['security_features'] = []
    for feature in security_features:
        if feature in text.lower():
            specs['security_features'].append(feature)
    
    return specs

def extract_structured_data(soup):
    """Extract structured data (JSON-LD, microdata) if available"""
    structured_data = {}
    
    # Look for JSON-LD data
    json_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if data.get('@type') in ['Place', 'Organization', 'LocalBusiness']:
                    structured_data['json_ld'] = data
                    break
        except:
            continue
    
    # Look for microdata
    microdata = soup.find_all(attrs={'itemtype': True})
    if microdata:
        structured_data['microdata_count'] = len(microdata)
    
    return structured_data

def fetch_and_extract(url: str, timeout=15) -> Dict[str, Any]:
    """Fetch page/PDF and extract data using enhanced scraper."""
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        if url.lower().endswith('.pdf'):
            # Handle PDF
            with pdfplumber.open(response.content) as pdf:
                text = ' '.join(page.extract_text() or '' for page in pdf.pages[:10])  # Limit to first 10 pages
            soup = None  # No soup for PDF; use text-based extraction if needed
            # For PDFs, fallback to simple regex (enhance if necessary)
            details = {
                'url': url,
                'name': re.search(r'([A-Z][a-zA-Z\s]+(?:Data\s+Center|Facility))', text) or 'Unknown',
                'name': details['name'].group(1) if details['name'] else 'Unknown',
                'location': extract_location_from_text(text),
                'capacity': extract_capacity_from_text(text),
                'power_usage': extract_power_from_text(text),
                'sustainability_info': extract_sustain_from_text(text),
                'additional_specs': {}
            }
            return details
        else:
            # Handle HTML with enhanced scraper
            return scrape_datacenter_details(url)
        
    except Exception as e:
        print(f"Fetch failed for {url}: {e}")
        return {'error': str(e), 'link': url}

def extract_location_from_text(text):
    """Simple location extract for PDFs."""
    match = re.search(r'([A-Z][a-z\s]+(?:,\s*[A-Z]{2}))', text)
    return match.group(1) if match else 'Europe'

def extract_capacity_from_text(text):
    """Simple capacity extract for PDFs."""
    match = re.search(r'(\d+(?:\.\d+)?)\s*(MW|sqft)', text, re.IGNORECASE)
    return {'power_mw': float(match.group(1)) if match and 'MW' in match.group(2).upper() else None} if match else {}

# Similar simple extracts for PDFs (power, sustain) - implement as needed
def extract_power_from_text(text):
    return {'pue': re.search(r'PUE\s*(\d+\.\d+)', text, re.IGNORECASE)}

def extract_sustain_from_text(text):
    return {'certifications': re.findall(r'(LEED|BREEAM)', text, re.IGNORECASE)}

# Main execution
print("Building URL list via SerpAPI...")
URL_LIST = build_url_list(max_urls=50)  # Adjust as needed

all_datacenters = []
for url in URL_LIST:
    print(f"Fetching: {url}")
    dc = fetch_and_extract(url)
    if dc and 'error' not in dc:
        all_datacenters.append(dc)
    time.sleep(1)  # Polite delay

# Dedupe by name + location
seen = set()
unique_datacenters = []
for dc in all_datacenters:
    key = (dc.get('name', ''), dc.get('location', ''))
    if key not in seen:
        seen.add(key)
        unique_datacenters.append(dc)

# Output JSONs
for idx, dc in enumerate(unique_datacenters):
    with open(f"{OUTPUT_DIR}/datacenter_{idx + 1}.json", 'w') as f:
        json.dump(dc, f, indent=2, ensure_ascii=False)

with open(f"{OUTPUT_DIR}/all_datacenters.json", 'w') as f:
    json.dump(unique_datacenters, f, indent=2, ensure_ascii=False)

# Save URL list for reference
with open(f"{OUTPUT_DIR}/scraped_urls.json", 'w') as f:
    json.dump(URL_LIST, f, indent=2)

print(f"Extracted {len(unique_datacenters)} unique data centers from {len(URL_LIST)} URLs. Check {OUTPUT_DIR}.")