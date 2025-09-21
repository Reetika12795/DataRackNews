"""
Equinix Data Center Scraper
Scrapes structured data center information from Equinix's official website
"""

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from urllib.parse import urljoin, urlparse
import time
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class EquinixDataCenterScraper:
    """Scraper for Equinix data center information"""
    
    def __init__(self):
        self.base_url = "https://www.equinix.com"
        self.data_centers_url = "https://www.equinix.com/data-centers"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Pre-defined structure based on the website
        self.data_centers = {
            'Americas': {
                'United States': [
                    'Atlanta', 'Boston', 'Chicago', 'Culpeper', 'Dallas', 'Denver', 
                    'Houston', 'Los Angeles', 'Miami', 'New York', 'Philadelphia', 
                    'Seattle', 'Silicon Valley', 'Washington'
                ],
                'Brazil': ['Rio de Janeiro', 'São Paulo'],
                'Chile': ['Santiago'],
                'Canada': [
                    'Calgary', 'Kamloops', 'Montreal', 'Ottawa', 'Saint John', 
                    'Toronto', 'Vancouver', 'Winnipeg'
                ],
                'Colombia': ['Bogotá'],
                'Mexico': ['Mexico City', 'Monterrey'],
                'Peru': ['Lima']
            },
            'Europe_Middle_East_Africa': {
                'United Kingdom': ['London', 'Manchester', 'Slough'],
                'Germany': ['Berlin', 'Düsseldorf', 'Frankfurt', 'Hamburg', 'Munich'],
                'France': ['Paris'],
                'Netherlands': ['Amsterdam'],
                'Spain': ['Barcelona', 'Madrid'],
                'Italy': ['Milan'],
                'Switzerland': ['Geneva', 'Zurich'],
                'Poland': ['Warsaw'],
                'Portugal': ['Lisbon'],
                'Ireland': ['Dublin'],
                'Finland': ['Helsinki'],
                'Sweden': ['Stockholm'],
                'Turkey': ['Istanbul'],
                'UAE': ['Dubai'],
                'South Africa': ['Cape Town', 'Johannesburg'],
                'Nigeria': ['Lagos']
            },
            'Asia_Pacific': {
                'Japan': ['Osaka', 'Tokyo'],
                'Australia': ['Melbourne', 'Perth', 'Sydney'],
                'Singapore': ['Singapore'],
                'Hong Kong': ['Hong Kong'],
                'South Korea': ['Seoul'],
                'India': ['Chennai', 'Mumbai'],
                'Indonesia': ['Jakarta'],
                'Philippines': ['Manila'],
                'Thailand': ['Bangkok']
            }
        }
    
    def get_city_url(self, country: str, city: str, region: str) -> str:
        """Generate the URL for a specific city's data centers"""
        # Create URL based on Equinix's URL pattern
        country_mapping = {
            'United States': 'united-states',
            'United Kingdom': 'united-kingdom',
            'South Africa': 'south-africa',
            'South Korea': 'south-korea',
            'Hong Kong': 'hong-kong',
            'New Zealand': 'new-zealand',
            'Saudi Arabia': 'saudi-arabia'
        }
        
        # Updated region mapping based on actual URL patterns
        region_mapping = {
            'Americas': 'americas-colocation',
            'Europe_Middle_East_Africa': 'emea-colocation', 
            'Asia_Pacific': 'asia-pacific-colocation'
        }
        
        country_slug = country_mapping.get(country, country.lower().replace(' ', '-'))
        region_slug = region_mapping.get(region, region.lower().replace('_', '-'))
        city_slug = city.lower().replace(' ', '-').replace('ã', 'a').replace('ç', 'c').replace('ü', 'u').replace('ö', 'o')
        
        # Try multiple URL patterns based on what we've observed
        possible_urls = []
        
        if region == 'Americas':
            url = f"{self.base_url}/data-centers/{region_slug}/{country_slug}-colocation/{city_slug}-data-centers"
            possible_urls.append(url)
        elif region == 'Europe_Middle_East_Africa':
            # Try different patterns for EMEA
            possible_urls.extend([
                f"{self.base_url}/data-centers/{region_slug}/{country_slug}-colocation/{city_slug}-data-centers",
                f"{self.base_url}/data-centers/europe-colocation/{country_slug}-colocation/{city_slug}-data-centers",
                f"{self.base_url}/data-centers/emea/{country_slug}/{city_slug}",
                f"{self.base_url}/data-centers/{city_slug}",
                f"{self.base_url}/locations/{city_slug}",
                f"{self.base_url}/data-centers/emea-colocation/{city_slug}-data-centers"
            ])
        elif region == 'Asia_Pacific':
            # Try different patterns for APAC
            possible_urls.extend([
                f"{self.base_url}/data-centers/{region_slug}/{country_slug}-colocation/{city_slug}-data-centers",
                f"{self.base_url}/data-centers/asia-pacific-colocation/{country_slug}-colocation/{city_slug}-data-centers",
                f"{self.base_url}/data-centers/apac/{country_slug}/{city_slug}",
                f"{self.base_url}/data-centers/{city_slug}",
                f"{self.base_url}/locations/{city_slug}"
            ])
        else:
            # Fallback patterns
            possible_urls.extend([
                f"{self.base_url}/data-centers/{city_slug}",
                f"{self.base_url}/locations/{city_slug}",
                f"{self.base_url}/data-centers/{country_slug}/{city_slug}"
            ])
        
        return possible_urls[0] if possible_urls else f"{self.base_url}/data-centers/{city_slug}"
    
    def scrape_individual_facility(self, facility_code: str, city: str, country: str) -> Dict[str, any]:
        """Scrape detailed information for an individual facility"""
        print(f"   🏢 Scraping individual facility: {facility_code}")
        
        # Build the correct URL based on the known pattern
        region = self.get_region_for_country(country)
        
        # Country mapping for URLs
        country_mapping = {
            'United States': 'united-states',
            'United Kingdom': 'united-kingdom',
            'South Africa': 'south-africa',
            'South Korea': 'south-korea',
            'Hong Kong': 'hong-kong',
            'New Zealand': 'new-zealand',
            'Saudi Arabia': 'saudi-arabia'
        }
        
        # Region mapping for URLs
        region_mapping = {
            'Americas': 'americas-colocation',
            'Europe_Middle_East_Africa': 'europe-colocation',
            'Asia_Pacific': 'asia-pacific-colocation'
        }
        
        country_slug = country_mapping.get(country, country.lower().replace(' ', '-'))
        region_slug = region_mapping.get(region, region.lower().replace('_', '-'))
        city_slug = city.lower().replace(' ', '-').replace('ã', 'a').replace('ç', 'c').replace('ü', 'u').replace('ö', 'o')
        facility_slug = facility_code.lower()
        
        # Build specific facility URL based on Equinix's pattern
        possible_urls = []
        
        if region == 'Europe_Middle_East_Africa':
            possible_urls = [
                f"{self.base_url}/data-centers/{region_slug}/{country_slug}-colocation/{city_slug}-data-centers/{facility_slug}",
                f"{self.base_url}/data-centers/emea-colocation/{country_slug}-colocation/{city_slug}-data-centers/{facility_slug}",
                f"{self.base_url}/data-centers/europe-colocation/{country_slug}-colocation/{city_slug}-data-centers/{facility_slug}"
            ]
        elif region == 'Americas':
            possible_urls = [
                f"{self.base_url}/data-centers/{region_slug}/{country_slug}-colocation/{city_slug}-data-centers/{facility_slug}",
                f"{self.base_url}/data-centers/americas-colocation/{country_slug}-colocation/{city_slug}-data-centers/{facility_slug}"
            ]
        elif region == 'Asia_Pacific':
            possible_urls = [
                f"{self.base_url}/data-centers/{region_slug}/{country_slug}-colocation/{city_slug}-data-centers/{facility_slug}",
                f"{self.base_url}/data-centers/asia-pacific-colocation/{country_slug}-colocation/{city_slug}-data-centers/{facility_slug}"
            ]
        
        # Fallback URLs
        possible_urls.extend([
            f"{self.base_url}/data-centers/{facility_slug}",
            f"{self.base_url}/locations/{facility_slug}",
            f"{self.base_url}/ibx/{facility_slug}"
        ])
        
        facility_details = {
            'code': facility_code,
            'name': f"Equinix {facility_code}",
            'city': city,
            'country': country,
            'address': 'Not available',
            'specifications': {},
            'technical_details': {},
            'connectivity_details': {},
            'certifications': [],
            'amenities': [],
            'electrical_redundancy': 'Not available',
            'cooling_redundancy': 'Not available',
            'sustainability_features': [],
            'availability_zones': [],
            'power_details': {},
            'cooling_details': {},
            'security_features': [],
            'carrier_access': [],
            'cloud_connectivity': [],
            'services_offered': [],
            'pricing_info': {},
            'contact_info': {},
            'scraped_at': datetime.now().isoformat()
        }
        
        # Try each URL pattern
        for url in possible_urls:
            try:
                print(f"     🌐 Trying URL: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    print(f"     ✅ Success! Extracting details from: {url}")
                    facility_details.update(self.extract_detailed_facility_info(response, facility_code))
                    facility_details['source_url'] = url
                    return facility_details
                else:
                    print(f"     ❌ Status {response.status_code} for: {url}")
                    
            except Exception as e:
                print(f"     ❌ Error accessing {url}: {str(e)}")
                continue
        
        print(f"     ⚠️  No direct URL found, extracting from city page...")
        # If individual facility URLs don't work, extract from the main city page
        return self.extract_facility_from_city_page(facility_code, city, country)
    
    def extract_detailed_facility_info(self, response, facility_code: str) -> Dict[str, any]:
        """Extract detailed information from a facility-specific page"""
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text()
        
        details = {
            'specifications': {},
            'certifications': [],
            'amenities': [],
            'electrical_redundancy': 'Not available',
            'cooling_redundancy': 'Not available',
            'address': 'Not available',
            'ibx_highlights': 'Not available'
        }
        
        # Extract address - improved patterns based on PA2 page structure
        address_patterns = [
            r'BUSINESS ADDRESS:\s*([^[]+?)(?=\[|$)',
            r'(\d+\s+[^,]+,\s*[^,]+,\s*France,?\s*\d+)',
            r'(\d+\s+Rue\s+[^,]+,?\s*[^,]+,?\s*France)',
            r'Address:\s*([^<>\n]+)',
            r'(?:located at|address):\s*([^<>\n]+)'
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE | re.DOTALL)
            if matches:
                address = matches[0].strip()
                if len(address) > 10:  # Meaningful address
                    details['address'] = address.replace('\n', ' ').strip()[:200]
                    break
        
        # Extract electrical system redundancy - exact pattern from PA2
        electrical_patterns = [
            r'Electrical\s+System\s+Redundancy\s*([^\n\r]*?)(?=\n|\r|$)',
            r'Electrical\s+System\s+Redundancy[:\s]*([^\n\r]+)',
            r'electrical[^:]*redundancy[:\s]*([^\n\r]+)',
        ]
        
        for pattern in electrical_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                redundancy = matches[0].strip()
                if redundancy and redundancy != '':
                    details['electrical_redundancy'] = redundancy
                    break
        
        # Extract cooling redundancy - exact pattern from PA2
        cooling_patterns = [
            r'Cooling\s+Redundancy\s*([^\n\r]*?)(?=\n|\r|$)',
            r'Cooling\s+Redundancy[:\s]*([^\n\r]+)',
            r'cooling[^:]*redundancy[:\s]*([^\n\r]+)',
        ]
        
        for pattern in cooling_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                redundancy = matches[0].strip()
                if redundancy and redundancy != '':
                    details['cooling_redundancy'] = redundancy
                    break
        
        # Extract certifications - comprehensive list from PA2
        cert_keywords = [
            'Climate Neutral Data Centre Pact', 'Cyber Essentials', 'EU Code of Conduct', 
            'HDS', 'ISO 14001', 'ISO 22301', 'ISO 27001', 'ISO 45001', 'ISO 50001', 
            'ISO 9001', 'PCI DSS', 'SOC 1 Type II', 'SOC 2 Type II'
        ]
        
        # Look for certifications section
        cert_section_pattern = r'Certifications\s*([^#]*?)(?=#{2,}|Amenities|$)'
        cert_matches = re.findall(cert_section_pattern, page_text, re.IGNORECASE | re.DOTALL)
        
        if cert_matches:
            cert_section = cert_matches[0]
            for cert in cert_keywords:
                if cert in cert_section:
                    details['certifications'].append(cert)
        else:
            # Fallback - check individual presence
            for cert in cert_keywords:
                if cert in page_text:
                    details['certifications'].append(cert)
        
        # Extract amenities - exact list from PA2
        amenity_keywords = [
            'Breakroom', 'Conference Room(s)', 'Crash Carts', 'Loaner tools', 'Wifi'
        ]
        
        # Look for amenities section
        amenity_section_pattern = r'Amenities\s*([^#]*?)(?=#{2,}|$)'
        amenity_matches = re.findall(amenity_section_pattern, page_text, re.IGNORECASE | re.DOTALL)
        
        if amenity_matches:
            amenity_section = amenity_matches[0]
            for amenity in amenity_keywords:
                if amenity in amenity_section:
                    details['amenities'].append(amenity)
        else:
            # Fallback - check individual presence
            for amenity in amenity_keywords:
                if amenity in page_text:
                    details['amenities'].append(amenity)
        
        # Extract IBX highlights - improved pattern for PA2 structure
        highlights_patterns = [
            r'IBX\s+Highlights\s*([^#]*?)(?=#{2,}|Electrical\s+System|$)',
            r'IBX\s+Highlights[:\s]*([^<>\n]*(?:\n[^<>\n]*)*?)(?=\n\n|\n#{2,}|\nElectrical|\n[A-Z][a-z]|\n$)',
            r'IBX®?\s+Highlights[:\s]*([^<>\n]*(?:\n[^<>\n]*)*?)(?=\n\n|\n#{2,}|\n$)'
        ]
        
        for pattern in highlights_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE | re.DOTALL)
            if matches:
                highlights_text = matches[0].strip()
                if len(highlights_text) > 20:
                    # Clean up the highlights text
                    highlights_text = re.sub(r'\s+', ' ', highlights_text)
                    details['ibx_highlights'] = highlights_text[:500]
                    break
        
        # Extract additional specifications if available
        spec_patterns = [
            (r'(\d+,?\d*)\s*(?:sq\.?\s*ft|square\s*feet)', 'square_feet'),
            (r'(\d+)\s*(?:mw|megawatt)', 'power_capacity_mw'),
            (r'(\d+)\s*floors?', 'floors'),
            (r'(\d+)\s*cabinets?', 'total_cabinets'),
            (r'(\d+)\s*racks?', 'total_racks'),
        ]
        
        for pattern, spec_name in spec_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                try:
                    value = matches[0].replace(',', '')
                    details['specifications'][spec_name] = int(value)
                except ValueError:
                    details['specifications'][spec_name] = matches[0]
        
        return details
    
    def extract_facility_from_city_page(self, facility_code: str, city: str, country: str) -> Dict[str, any]:
        """Extract facility details from the main city page using various patterns"""
        print(f"     🔍 Extracting {facility_code} details from city page...")
        
        city_url = self.get_city_url(country, city, self.get_region_for_country(country))
        
        try:
            response = self.session.get(city_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()
            
            facility_details = {
                'code': facility_code,
                'name': f"Equinix {facility_code}",
                'city': city,
                'country': country,
                'address': 'Extracted from city page',
                'specifications': {},
                'connectivity_details': {},
                'services_offered': [],
                'facility_features': [],
                'market_connectivity': {},
                'scraped_at': datetime.now().isoformat()
            }
            
            # Look for facility-specific information in structured data or JavaScript
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and facility_code.lower() in str(data).lower():
                        # Extract structured data about this facility
                        if 'address' in data:
                            facility_details['address'] = str(data['address'])[:200]
                except:
                    pass
            
            # Extract facility-specific information using more targeted patterns
            facility_section_patterns = [
                rf'{facility_code}[^a-zA-Z0-9]*([^<>\n]*(?:\n[^<>\n]*)*?)(?={facility_code[:-1]}|\n\n|\n[A-Z])',
                rf'(?:facility|datacenter|ibx)\s*{facility_code}[^a-zA-Z0-9]*([^<>\n]*(?:\n[^<>\n]*)*?)(?=facility|datacenter|\n\n)',
                rf'{facility_code}.*?(\d+[^a-zA-Z]*(?:sq\.?\s*ft|square\s*feet|m²))',
                rf'{facility_code}.*?(\d+[^a-zA-Z]*(?:mw|megawatt))',
            ]
            
            for pattern in facility_section_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE | re.DOTALL)
                if matches:
                    for match in matches[:3]:  # Limit to first 3 matches
                        match_text = match.strip()
                        if len(match_text) > 10:  # Only meaningful matches
                            facility_details['facility_features'].append(match_text[:200])
            
            # Extract specific technical specifications for this facility
            spec_patterns = [
                (rf'{facility_code}.*?(\d+,?\d*)\s*(?:sq\.?\s*ft|square\s*feet)', 'square_feet'),
                (rf'{facility_code}.*?(\d+)\s*(?:mw|megawatt)', 'power_capacity_mw'),
                (rf'{facility_code}.*?(\d+)\s*floors?', 'floors'),
                (rf'{facility_code}.*?(\d+)\s*cabinets?', 'total_cabinets'),
                (rf'{facility_code}.*?(\d+)\s*racks?', 'total_racks'),
            ]
            
            for pattern, spec_name in spec_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    try:
                        value = matches[0].replace(',', '')
                        facility_details['specifications'][spec_name] = int(value)
                    except ValueError:
                        facility_details['specifications'][spec_name] = matches[0]
            
            # Extract connectivity and market information specific to this facility
            connectivity_patterns = [
                (rf'{facility_code}.*?(\d+)\s*(?:carriers?|networks?)', 'network_count'),
                (rf'{facility_code}.*?(\d+)\s*cloud.*providers?', 'cloud_providers'),
                (rf'{facility_code}.*?(\d+)\s*enterprises?', 'enterprise_customers'),
            ]
            
            for pattern, conn_name in connectivity_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    try:
                        facility_details['connectivity_details'][conn_name] = int(matches[0])
                    except ValueError:
                        pass
            
            # Look for services offered at this specific facility
            services_keywords = [
                'colocation', 'interconnection', 'cloud connect', 'network edge',
                'equinix fabric', 'internet exchange', 'peering', 'disaster recovery',
                'managed services', 'remote hands', 'smart hands', 'cross connects'
            ]
            
            facility_text = page_text.lower()
            for service in services_keywords:
                if service in facility_text and facility_code.lower() in facility_text:
                    # Check if service is mentioned near the facility code
                    facility_mentions = [m.start() for m in re.finditer(facility_code.lower(), facility_text)]
                    service_mentions = [m.start() for m in re.finditer(service, facility_text)]
                    
                    # If service and facility are mentioned within 500 characters of each other
                    for f_pos in facility_mentions:
                        for s_pos in service_mentions:
                            if abs(f_pos - s_pos) < 500:
                                facility_details['services_offered'].append(service.title())
                                break
            
            # Remove duplicates
            facility_details['services_offered'] = list(set(facility_details['services_offered']))
            
            return facility_details
            
        except Exception as e:
            print(f"     ❌ Error extracting {facility_code} from city page: {e}")
            return {
                'code': facility_code,
                'name': f"Equinix {facility_code}",
                'city': city,
                'country': country,
                'error': str(e),
                'scraped_at': datetime.now().isoformat()
            }
    
    def get_region_for_country(self, country: str) -> str:
        """Get the region for a given country"""
        for region, region_data in self.data_centers.items():
            if country in region_data:
                return region
        return 'Americas'  # Default fallback
    
    def scrape_city_details(self, city: str, country: str, region: str) -> Dict[str, any]:
        """Scrape detailed information for a specific city's data centers"""
        print(f"🏢 Scraping details for {city}, {country}...")
        
        # Get possible URLs to try
        possible_urls = self.get_all_possible_urls(country, city, region)
        
        details = {
            'city': city,
            'country': country,
            'region': region,
            'url': 'Not found',
            'facilities': [],
            'total_facilities': 0,
            'services': [],
            'certifications': [],
            'sustainability': {},
            'connectivity': {},
            'key_stats': {},
            'detailed_facilities': [],  # New: detailed facility information
            'scraped_at': datetime.now().isoformat()
        }
        
        # Try each possible URL until we find one that works
        for url_attempt in possible_urls:
            try:
                print(f"   🔗 Trying URL: {url_attempt}")
                response = self.session.get(url_attempt, timeout=15)
                
                if response.status_code == 200:
                    print(f"   ✅ Successfully accessed: {url_attempt}")
                    details['url'] = url_attempt
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    text_content = soup.get_text().lower()
                    page_text = soup.get_text()
                    
                    # Extract facility information from page text
                    facility_patterns = [
                        r'([A-Z]{2}\d+)',  # NY1, SV1, etc.
                        r'equinix\s+([a-z]{2}\d+)',
                        r'ibx\s+([a-z]{2}\d+)'
                    ]
                    
                    facility_codes = set()
                    for pattern in facility_patterns:
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        facility_codes.update([code.upper() for code in matches])
                    
                    # Look for dropdown elements and facility-specific data
                    facility_sections = soup.find_all(['div', 'section', 'li'], class_=re.compile(r'facility|datacenter|location|dropdown'))
                    
                    # Try to find facility dropdown or list elements
                    dropdown_elements = soup.find_all(['select', 'ul', 'div'], class_=re.compile(r'dropdown|facility-list|datacenter-list'))
                    facility_links = soup.find_all('a', href=re.compile(r'data-center|facility'))
                    
                    # Extract detailed facility information
                    for code in facility_codes:
                        facility_info = {
                            'code': code,
                            'name': f"Equinix {code}",
                            'city': city,
                            'country': country,
                            'address': 'Not available',
                            'specifications': {},
                            'connectivity_details': {},
                            'certification_details': []
                        }
                        
                        # Try to find address information for this facility
                        address_patterns = [
                            rf'{code}.*?address.*?([^<>]+)',
                            rf'address.*?{code}.*?([^<>]+)',
                            rf'{code}.*?located.*?([^<>]+)'
                        ]
                        
                        for pattern in address_patterns:
                            address_matches = re.findall(pattern, page_text, re.IGNORECASE | re.DOTALL)
                            if address_matches:
                                facility_info['address'] = address_matches[0].strip()[:200]  # Limit length
                                break
                        
                        # Extract facility-specific specifications
                        spec_patterns = [
                            (rf'{code}.*?(\d+,?\d*)\s*sq\.?\s*ft', 'square_feet'),
                            (rf'{code}.*?(\d+)\s*mw', 'power_mw'),
                            (rf'{code}.*?(\d+)\s*floors?', 'floors'),
                            (rf'{code}.*?(\d+)\s*cabinets?', 'cabinets')
                        ]
                        
                        for pattern, spec_name in spec_patterns:
                            spec_matches = re.findall(pattern, page_text, re.IGNORECASE)
                            if spec_matches:
                                try:
                                    value = spec_matches[0].replace(',', '')
                                    facility_info['specifications'][spec_name] = int(value)
                                except ValueError:
                                    pass
                        
                        details['detailed_facilities'].append(facility_info)
                        
                        # Add to basic facilities list
                        details['facilities'].append({
                            'code': code,
                            'name': f"Equinix {code}",
                            'city': city,
                            'country': country
                        })
                    
                    details['total_facilities'] = len(details['facilities'])
                    
                    # Extract services information
                    services_keywords = [
                        ('colocation', 'Colocation'),
                        ('interconnection', 'Interconnection'),
                        ('cloud', 'Cloud Connect'),
                        ('network edge', 'Network Edge'),
                        ('fabric', 'Equinix Fabric'),
                        ('internet exchange', 'Internet Exchange'),
                        ('peering', 'Peering')
                    ]
                    
                    for keyword, service_name in services_keywords:
                        if keyword in text_content:
                            details['services'].append(service_name)
                    
                    # Extract certifications and compliance
                    cert_keywords = [
                        ('iso 27001', 'ISO 27001'),
                        ('soc 2', 'SOC 2'),
                        ('pci dss', 'PCI DSS'),
                        ('hipaa', 'HIPAA'),
                        ('ssae 16', 'SSAE 16'),
                        ('iso 14001', 'ISO 14001')
                    ]
                    
                    for keyword, cert_name in cert_keywords:
                        if keyword in text_content:
                            details['certifications'].append(cert_name)
                    
                    # Extract sustainability information
                    sustainability_keywords = [
                        'renewable energy',
                        'carbon neutral',
                        'green building',
                        'leed certified',
                        'energy efficient',
                        'sustainable'
                    ]
                    
                    sustainability_found = []
                    for keyword in sustainability_keywords:
                        if keyword in text_content:
                            sustainability_found.append(keyword)
                    
                    details['sustainability'] = {
                        'features': sustainability_found,
                        'has_green_initiatives': len(sustainability_found) > 0,
                        'green_score': len(sustainability_found)
                    }
                    
                    # Extract connectivity ecosystem information
                    connectivity_keywords = [
                        'cloud providers',
                        'network operators',
                        'enterprises',
                        'service providers',
                        'carriers',
                        'internet exchanges'
                    ]
                    
                    connectivity_found = []
                    for keyword in connectivity_keywords:
                        if keyword in text_content:
                            connectivity_found.append(keyword)
                    
                    details['connectivity'] = {
                        'ecosystem_types': connectivity_found,
                        'ecosystem_rich': len(connectivity_found) > 3,
                        'connectivity_score': len(connectivity_found)
                    }
                    
                    # Extract key statistics
                    stats_patterns = [
                        (r'(\d+)\s*(?:gbps|gb/s)', 'bandwidth_gbps'),
                        (r'(\d+)\s*carriers?', 'carriers_count'),
                        (r'(\d+)\s*networks?', 'networks_count'),
                        (r'(\d+)\s*cloud\s+providers?', 'cloud_providers_count'),
                        (r'(\d+)\s*enterprises?', 'enterprises_count')
                    ]
                    
                    for pattern, stat_name in stats_patterns:
                        matches = re.findall(pattern, text_content, re.IGNORECASE)
                        if matches:
                            try:
                                max_value = max([int(match) for match in matches])
                                details['key_stats'][stat_name] = max_value
                            except ValueError:
                                pass
                    
                    # Try to extract dropdown facility details if available
                    print(f"   📋 Found {len(details['facilities'])} facilities: {[f['code'] for f in details['facilities']]}")
                    
                    # Always scrape individual facility details for better accuracy
                    print(f"   🔍 Fetching detailed information for each facility...")
                    detailed_facilities = []
                    for facility in details['facilities']:
                        facility_detail = self.scrape_individual_facility(
                            facility['code'], city, country
                        )
                        detailed_facilities.append(facility_detail)
                        time.sleep(0.5)  # Rate limiting between facility requests
                    
                    details['detailed_facilities'] = detailed_facilities
                    
                    time.sleep(1)  # Rate limiting
                    return details
                    
                else:
                    print(f"   ❌ HTTP {response.status_code}: {url_attempt}")
                    
            except Exception as e:
                print(f"   ❌ Failed {url_attempt}: {str(e)[:50]}...")
                continue
        
        # If we get here, none of the URLs worked
        print(f"❌ Could not find working URL for {city}, {country}")
        details['error'] = f"No working URLs found for {city}, {country}"
        return details
    
    def get_all_possible_urls(self, country: str, city: str, region: str) -> List[str]:
        """Get all possible URL patterns to try for a city"""
        country_mapping = {
            'United States': 'united-states',
            'United Kingdom': 'united-kingdom',
            'South Africa': 'south-africa',
            'South Korea': 'south-korea',
            'Hong Kong': 'hong-kong',
            'New Zealand': 'new-zealand',
            'Saudi Arabia': 'saudi-arabia'
        }
        
        country_slug = country_mapping.get(country, country.lower().replace(' ', '-'))
        city_slug = city.lower().replace(' ', '-').replace('ã', 'a').replace('ç', 'c').replace('ü', 'u').replace('ö', 'o')
        
        possible_urls = []
        
        if region == 'Americas':
            possible_urls.extend([
                f"{self.base_url}/data-centers/americas-colocation/{country_slug}-colocation/{city_slug}-data-centers",
                f"{self.base_url}/data-centers/americas/{country_slug}/{city_slug}",
                f"{self.base_url}/data-centers/{city_slug}"
            ])
        elif region == 'Europe_Middle_East_Africa':
            possible_urls.extend([
                f"{self.base_url}/data-centers/emea-colocation/{country_slug}-colocation/{city_slug}-data-centers",
                f"{self.base_url}/data-centers/europe-colocation/{country_slug}-colocation/{city_slug}-data-centers",
                f"{self.base_url}/data-centers/emea/{country_slug}/{city_slug}",
                f"{self.base_url}/data-centers/europe/{country_slug}/{city_slug}",
                f"{self.base_url}/data-centers/{city_slug}",
                f"{self.base_url}/locations/{city_slug}",
                f"{self.base_url}/data-centers/emea-colocation/{city_slug}-data-centers"
            ])
        elif region == 'Asia_Pacific':
            possible_urls.extend([
                f"{self.base_url}/data-centers/asia-pacific-colocation/{country_slug}-colocation/{city_slug}-data-centers",
                f"{self.base_url}/data-centers/apac-colocation/{country_slug}-colocation/{city_slug}-data-centers",
                f"{self.base_url}/data-centers/apac/{country_slug}/{city_slug}",
                f"{self.base_url}/data-centers/asia/{country_slug}/{city_slug}",
                f"{self.base_url}/data-centers/{city_slug}",
                f"{self.base_url}/locations/{city_slug}"
            ])
        
        # Always add fallback patterns
        possible_urls.extend([
            f"{self.base_url}/data-centers/{city_slug}",
            f"{self.base_url}/locations/{city_slug}",
            f"{self.base_url}/data-centers/{country_slug}/{city_slug}",
            f"{self.base_url}/data-centers/{city_slug}-data-centers"
        ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in possible_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
                
        return unique_urls
    
    def scrape_region(self, region: str, max_cities: int = None) -> List[Dict[str, any]]:
        """Scrape all cities in a specific region"""
        if region not in self.data_centers:
            print(f"❌ Region '{region}' not found. Available: {list(self.data_centers.keys())}")
            return []
        
        all_cities_data = []
        total_processed = 0
        
        for country, cities in self.data_centers[region].items():
            print(f"\n🌍 Processing {country}...")
            
            for city in cities:
                if max_cities and total_processed >= max_cities:
                    break
                
                city_data = self.scrape_city_details(city, country, region)
                all_cities_data.append(city_data)
                total_processed += 1
            
            if max_cities and total_processed >= max_cities:
                break
        
        return all_cities_data
    
    def search_by_city(self, city_name: str) -> List[Dict[str, any]]:
        """Search for data centers in a specific city"""
        matches = []
        city_lower = city_name.lower()
        
        for region_name, region_data in self.data_centers.items():
            for country, cities in region_data.items():
                for city in cities:
                    if city_lower in city.lower() or city.lower() in city_lower:
                        city_data = self.scrape_city_details(city, country, region_name)
                        matches.append(city_data)
        
        return matches
    
    def search_by_country(self, country_name: str) -> List[Dict[str, any]]:
        """Search for data centers in a specific country"""
        matches = []
        country_lower = country_name.lower()
        
        for region_name, region_data in self.data_centers.items():
            for country, cities in region_data.items():
                if country_lower in country.lower() or country.lower() in country_lower:
                    print(f"🌍 Found {country} with {len(cities)} cities")
                    for city in cities:
                        city_data = self.scrape_city_details(city, country, region_name)
                        matches.append(city_data)
                    break
        
        return matches
    
    def get_regional_summary(self) -> Dict[str, Dict[str, int]]:
        """Get summary statistics for each region"""
        summary = {}
        
        for region_name, region_data in self.data_centers.items():
            total_countries = len(region_data)
            total_cities = sum(len(cities) for cities in region_data.values())
            
            summary[region_name] = {
                'countries': total_countries,
                'cities': total_cities,
                'countries_list': list(region_data.keys())
            }
        
        return summary
    
    def get_all_cities(self) -> List[Dict[str, str]]:
        """Get a list of all available cities"""
        all_cities = []
        
        for region_name, region_data in self.data_centers.items():
            for country, cities in region_data.items():
                for city in cities:
                    all_cities.append({
                        'city': city,
                        'country': country,
                        'region': region_name
                    })
        
        return all_cities
    
    def get_region_for_country(self, country: str) -> str:
        """Get the region for a given country"""
        for region_name, region_data in self.data_centers.items():
            if country in region_data:
                return region_name
        return 'Americas'  # Default fallback
    
    def export_to_csv(self, data: List[Dict[str, any]], filename: str = None):
        """Export scraped data to CSV"""
        if not filename:
            filename = f"equinix_datacenters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        all_records = []
        
        for city_data in data:
            if 'error' not in city_data:
                record = {
                    'region': city_data.get('region', ''),
                    'country': city_data.get('country', ''),
                    'city': city_data.get('city', ''),
                    'total_facilities': city_data.get('total_facilities', 0),
                    'facilities': ', '.join([f['code'] for f in city_data.get('facilities', [])]),
                    'services': ', '.join(city_data.get('services', [])),
                    'certifications': ', '.join(city_data.get('certifications', [])),
                    'sustainability_features': ', '.join(city_data.get('sustainability', {}).get('features', [])),
                    'connectivity_types': ', '.join(city_data.get('connectivity', {}).get('ecosystem_types', [])),
                    'green_score': city_data.get('sustainability', {}).get('green_score', 0),
                    'connectivity_score': city_data.get('connectivity', {}).get('connectivity_score', 0),
                    'url': city_data.get('url', ''),
                    'scraped_at': city_data.get('scraped_at', '')
                }
                all_records.append(record)
        
        df = pd.DataFrame(all_records)
        df.to_csv(filename, index=False)
        print(f"✅ Data exported to {filename}")
        return filename
    
    def export_to_json(self, data: List[Dict[str, any]], filename: str = None):
        """Export scraped data to JSON"""
        if not filename:
            filename = f"equinix_datacenters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Data exported to {filename}")
        return filename


def main():
    """Demo function showing how to use the Equinix scraper"""
    scraper = EquinixDataCenterScraper()
    
    print("🚀 Equinix Data Center Scraper Demo")
    print("=" * 50)
    
    # Get regional summary
    print("\n1. Getting Regional Summary...")
    summary = scraper.get_regional_summary()
    for region, stats in summary.items():
        print(f"{region}: {stats['countries']} countries, {stats['cities']} cities")
        print(f"  Countries: {', '.join(stats['countries_list'][:5])}{'...' if len(stats['countries_list']) > 5 else ''}")
    
    # Search for specific cities
    print("\n2. Searching for specific cities...")
    test_cities = ["New York", "London", "Tokyo"]
    
    for city in test_cities:
        print(f"\n🔍 Searching for {city}...")
        results = scraper.search_by_city(city)
        if results:
            for result in results:
                if 'error' not in result:
                    print(f"  ✅ Found: {result['city']}, {result['country']} - {result['total_facilities']} facilities")
                    print(f"     Services: {', '.join(result['services'][:3])}{'...' if len(result['services']) > 3 else ''}")
                else:
                    print(f"  ❌ Error: {result['error']}")
        else:
            print(f"  No results found for {city}")
    
    # Search by country
    print("\n3. Searching by country...")
    country_results = scraper.search_by_country("Brazil")
    if country_results:
        print(f"Found {len(country_results)} cities in Brazil:")
        for result in country_results:
            if 'error' not in result:
                print(f"  - {result['city']}: {result['total_facilities']} facilities")
    
    # Export sample data
    if country_results:
        print("\n4. Exporting sample data...")
        scraper.export_to_csv(country_results, "sample_equinix_brazil.csv")
        scraper.export_to_json(country_results, "sample_equinix_brazil.json")


if __name__ == "__main__":
    main()
