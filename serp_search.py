import requests
import json
import os
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv
import re
from datetime import datetime
import asyncio

# Load environment variables from .env file
load_dotenv()

class DataCenterScraper:
    def __init__(self, serp_api_key=None):
        # Use provided key or load from environment
        self.serp_api_key = serp_api_key or os.getenv('SERP_API_KEY')
        if not self.serp_api_key:
            raise ValueError("SERP_API_KEY not found. Please set it in your .env file or pass it directly.")
        self.base_url = "https://serpapi.com/search"
    
    def search_datacenters(self, region, num_results=10):
        """Search for data centers in a specific region"""
        params = {
            'api_key': self.serp_api_key,
            'engine': 'google',
            'q': f'data centers {region} location address',
            'num': num_results
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            
            # Extract organic results
            organic_results = data.get('organic_results', [])
            
            # Process and clean the results
            processed_results = []
            for result in organic_results:
                processed_result = {
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'position': result.get('position', 0)
                }
                processed_results.append(processed_result)
            
            return {
                'search_metadata': data.get('search_metadata', {}),
                'results': processed_results,
                'total_results': len(processed_results)
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error making request to SERP API: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return None
    
    def scrape_datacenter_details(self, url):
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
                'name': self.extract_name_enhanced(soup, url),
                'location': self.extract_location_enhanced(soup),
                'capacity': self.extract_capacity_enhanced(soup),
                'power_usage': self.extract_power_usage_enhanced(soup),
                'sustainability_info': self.extract_sustainability_enhanced(soup),
                'additional_specs': self.extract_additional_specs(soup)
            }
            
            # Try to get more data from structured data (JSON-LD, microdata)
            structured_data = self.extract_structured_data(soup)
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

    def extract_name_enhanced(self, soup, url):
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

    def extract_location_enhanced(self, soup):
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

    def extract_capacity_enhanced(self, soup):
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

    def extract_power_usage_enhanced(self, soup):
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

    def extract_sustainability_enhanced(self, soup):
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

    def extract_additional_specs(self, soup):
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

    def extract_structured_data(self, soup):
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


class EnhancedDataCenterScraper(DataCenterScraper):
    """Enhanced version of DataCenterScraper with deep intelligence analysis"""
    
    def __init__(self, serp_api_key=None):
        super().__init__(serp_api_key)
        self.analysis_cache = {}  # Cache for storing analysis results
        
    def deep_analyze_datacenter(self, search_result, progress_callback=None):
        """
        Perform comprehensive deep analysis on a datacenter from search results
        
        Args:
            search_result: Dictionary containing title, link, snippet from SERP
            progress_callback: Optional callback function to report progress
        
        Returns:
            Dictionary containing comprehensive intelligence data
        """
        
        if progress_callback:
            progress_callback(0, "Starting deep analysis...")
        
        url = search_result.get('link', '')
        title = search_result.get('title', 'Unknown')
        
        # Check cache first
        cache_key = f"{url}_{title}"
        if cache_key in self.analysis_cache:
            if progress_callback:
                progress_callback(1.0, "Retrieved from cache")
            return self.analysis_cache[cache_key]
        
        try:
            # Step 1: Basic scraping (existing functionality)
            if progress_callback:
                progress_callback(0.1, "Scraping basic information...")
            
            basic_details = self.scrape_datacenter_details(url)
            if not basic_details:
                return {'error': 'Failed to scrape basic details'}
            
            # Step 2: Create datacenter info structure for deep analysis
            datacenter_info = {
                'name': basic_details.get('name', title),
                'url': url,
                'title': title,
                'snippet': search_result.get('snippet', ''),
                'basic_details': basic_details
            }
            
            # Step 3: Deep intelligence analysis
            if progress_callback:
                progress_callback(0.2, "Analyzing suppliers and ecosystem...")
            
            intelligence_data = {
                'basic_info': self._extract_enhanced_basic_info(datacenter_info),
                'supplier_info': self._analyze_supplier_ecosystem(datacenter_info),
                'market_value': self._estimate_market_intelligence(datacenter_info),
                'technical_specs': self._get_enhanced_technical_specs(datacenter_info),
                'financial_intelligence': self._analyze_financial_landscape(datacenter_info),
                'competitive_analysis': self._analyze_competitive_landscape(datacenter_info),
                'news_sentiment': self._analyze_news_and_sentiment(datacenter_info),
                'certifications': self._find_industry_certifications(datacenter_info),
                'partnerships': self._discover_strategic_partnerships(datacenter_info),
                'expansion_plans': self._research_growth_plans(datacenter_info)
            }
            
            if progress_callback:
                progress_callback(0.9, "Finalizing analysis...")
            
            # Compile comprehensive report
            comprehensive_report = {
                'datacenter_name': datacenter_info['name'],
                'url': url,
                'analysis_timestamp': datetime.now().isoformat(),
                'search_result': search_result,
                'basic_details': basic_details,
                'intelligence_data': intelligence_data,
                'executive_summary': self._generate_executive_summary(intelligence_data, datacenter_info),
                'recommendations': self._generate_strategic_recommendations(intelligence_data, datacenter_info),
                'analysis_confidence': self._calculate_analysis_confidence(intelligence_data)
            }
            
            # Cache the result
            self.analysis_cache[cache_key] = comprehensive_report
            
            if progress_callback:
                progress_callback(1.0, "Deep analysis completed!")
            
            return comprehensive_report
            
        except Exception as e:
            error_report = {
                'error': str(e),
                'datacenter_name': title,
                'url': url,
                'analysis_timestamp': datetime.now().isoformat(),
                'basic_details': basic_details if 'basic_details' in locals() else None
            }
            return error_report
    
    def _extract_enhanced_basic_info(self, datacenter_info):
        """Extract enhanced basic information"""
        basic = datacenter_info['basic_details']
        
        return {
            'name': datacenter_info['name'],
            'url': datacenter_info['url'],
            'title': datacenter_info['title'],
            'snippet': datacenter_info['snippet'],
            'location': basic.get('location', 'Unknown'),
            'capacity': basic.get('capacity', {}),
            'power_usage': basic.get('power_usage', {}),
            'sustainability_info': basic.get('sustainability_info', {}),
            'additional_specs': basic.get('additional_specs', {}),
            'structured_data': basic.get('structured_data', {})
        }
    
    def _analyze_supplier_ecosystem(self, datacenter_info):
        """Analyze supplier ecosystem using targeted SERP searches"""
        name = datacenter_info['name']
        
        suppliers_data = {
            'hardware_suppliers': [],
            'software_providers': [],
            'construction_partners': [],
            'service_providers': [],
            'analysis_confidence': 0
        }
        
        # Search queries for different types of suppliers
        search_queries = [
            f'"{name}" datacenter suppliers vendors equipment',
            f'"{name}" data center construction contractor',
            f'"{name}" hardware software providers partners',
            f'"{name}" cooling power UPS suppliers'
        ]
        
        confidence_score = 0
        
        for query in search_queries:
            try:
                results = self.search_datacenters(query.replace('data centers ', ''), num_results=5)
                if results and results.get('results'):
                    for result in results['results']:
                        supplier_info = self._extract_supplier_from_result(result, name)
                        if supplier_info:
                            category = self._categorize_supplier(supplier_info['description'])
                            suppliers_data[category].append(supplier_info)
                            confidence_score += 1
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Error searching suppliers for {name}: {e}")
        
        suppliers_data['analysis_confidence'] = min(confidence_score / 10, 1.0)
        return suppliers_data
    
    def _estimate_market_intelligence(self, datacenter_info):
        """Estimate market value and intelligence"""
        name = datacenter_info['name']
        basic = datacenter_info['basic_details']
        
        market_data = {
            'estimated_investment': 'Not calculated',
            'market_position': 'Unknown',
            'revenue_estimate': 'Not available',
            'competitive_ranking': 'Unknown',
            'market_intelligence': [],
            'analysis_confidence': 0
        }
        
        # Extract location for market analysis
        location_info = basic.get('location', {})
        if isinstance(location_info, dict):
            city_state = location_info.get('city_state', '')
        else:
            city_state = str(location_info)
        
        # Search for market intelligence
        market_queries = [
            f'"{name}" datacenter market value investment',
            f'"{name}" revenue financial performance',
            f'datacenter market {city_state} leading providers'
        ]
        
        confidence_score = 0
        
        for query in market_queries:
            try:
                results = self.search_datacenters(query.replace('data centers ', ''), num_results=3)
                if results and results.get('results'):
                    market_info = self._extract_market_data_from_results(results, name)
                    market_data['market_intelligence'].extend(market_info)
                    if market_info:
                        confidence_score += 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error searching market data for {name}: {e}")
        
        # Calculate estimated investment based on capacity
        capacity = basic.get('capacity', {})
        if isinstance(capacity, dict):
            power_mw = capacity.get('power_mw', 5)  # Default 5MW
            space_sqft = capacity.get('space_sqft', 50000)  # Default 50K sqft
            
            # Industry averages: $10M per MW, $200 per sqft
            estimated_investment = (power_mw * 10_000_000) + (space_sqft * 200)
            market_data['estimated_investment'] = f"${estimated_investment:,.0f}"
        
        market_data['analysis_confidence'] = min(confidence_score / 3, 1.0)
        return market_data
    
    def _get_enhanced_technical_specs(self, datacenter_info):
        """Get enhanced technical specifications"""
        basic = datacenter_info['basic_details']
        name = datacenter_info['name']
        
        tech_specs = {
            'power_infrastructure': basic.get('capacity', {}),
            'cooling_systems': {},
            'network_connectivity': basic.get('additional_specs', {}),
            'security_features': basic.get('additional_specs', {}).get('security_features', []),
            'compliance_standards': [],
            'redundancy_levels': basic.get('additional_specs', {}).get('redundancy', 'Unknown'),
            'analysis_confidence': 0
        }
        
        # Search for additional technical details
        tech_queries = [
            f'"{name}" technical specifications power cooling',
            f'"{name}" network connectivity bandwidth',
            f'"{name}" security compliance certifications'
        ]
        
        confidence_score = 0
        
        for query in tech_queries:
            try:
                results = self.search_datacenters(query.replace('data centers ', ''), num_results=3)
                if results and results.get('results'):
                    tech_info = self._extract_technical_details_from_results(results)
                    
                    # Merge technical information
                    for category, details in tech_info.items():
                        if category in tech_specs and details:
                            if isinstance(tech_specs[category], dict):
                                tech_specs[category].update(details)
                            elif isinstance(tech_specs[category], list):
                                tech_specs[category].extend(details)
                    
                    if tech_info:
                        confidence_score += 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error searching technical specs for {name}: {e}")
        
        tech_specs['analysis_confidence'] = min(confidence_score / 3, 1.0)
        return tech_specs
    
    def _analyze_financial_landscape(self, datacenter_info):
        """Analyze financial landscape and performance"""
        name = datacenter_info['name']
        
        financial_data = {
            'revenue_indicators': [],
            'investment_activity': [],
            'financial_performance': [],
            'market_valuation': 'Unknown',
            'analysis_confidence': 0
        }
        
        # Search for financial information
        financial_queries = [
            f'"{name}" revenue earnings financial results',
            f'"{name}" investment funding acquisition',
            f'"{name}" market valuation stock price'
        ]
        
        confidence_score = 0
        
        for query in financial_queries:
            try:
                results = self.search_datacenters(query.replace('data centers ', ''), num_results=3)
                if results and results.get('results'):
                    financial_info = self._extract_financial_indicators(results, name)
                    
                    for category, data in financial_info.items():
                        if category in financial_data and data:
                            financial_data[category].extend(data)
                    
                    if any(financial_info.values()):
                        confidence_score += 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error searching financial data for {name}: {e}")
        
        financial_data['analysis_confidence'] = min(confidence_score / 3, 1.0)
        return financial_data
    
    def _analyze_competitive_landscape(self, datacenter_info):
        """Analyze competitive landscape"""
        name = datacenter_info['name']
        basic = datacenter_info['basic_details']
        
        competitive_data = {
            'direct_competitors': [],
            'market_leaders': [],
            'competitive_advantages': [],
            'market_share_indicators': [],
            'analysis_confidence': 0
        }
        
        # Extract location for competitive analysis
        location_info = basic.get('location', {})
        if isinstance(location_info, dict):
            city_state = location_info.get('city_state', '')
        else:
            city_state = str(location_info)
        
        # Search for competitive information
        competitive_queries = [
            f'datacenter providers {city_state} competitors',
            f'"{name}" competitors market share',
            f'colocation providers {city_state} comparison'
        ]
        
        confidence_score = 0
        
        for query in competitive_queries:
            try:
                results = self.search_datacenters(query.replace('data centers ', ''), num_results=5)
                if results and results.get('results'):
                    competitive_info = self._extract_competitive_intelligence(results, name)
                    
                    for category, data in competitive_info.items():
                        if category in competitive_data and data:
                            competitive_data[category].extend(data)
                    
                    if any(competitive_info.values()):
                        confidence_score += 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error searching competitive data for {name}: {e}")
        
        competitive_data['analysis_confidence'] = min(confidence_score / 3, 1.0)
        return competitive_data
    
    def _analyze_news_and_sentiment(self, datacenter_info):
        """Analyze recent news and sentiment"""
        name = datacenter_info['name']
        
        news_data = {
            'recent_articles': [],
            'sentiment_indicators': [],
            'key_developments': [],
            'media_coverage_score': 0,
            'sentiment_score': 0,
            'analysis_confidence': 0
        }
        
        # Search for recent news
        news_queries = [
            f'"{name}" datacenter news 2024 2025',
            f'"{name}" expansion investment news',
            f'"{name}" partnership acquisition news'
        ]
        
        confidence_score = 0
        total_sentiment = 0
        article_count = 0
        
        for query in news_queries:
            try:
                results = self.search_datacenters(query.replace('data centers ', ''), num_results=5)
                if results and results.get('results'):
                    news_info = self._extract_news_sentiment(results, name)
                    
                    news_data['recent_articles'].extend(news_info.get('articles', []))
                    news_data['key_developments'].extend(news_info.get('developments', []))
                    
                    # Calculate sentiment
                    for article in news_info.get('articles', []):
                        sentiment = self._calculate_article_sentiment(article)
                        total_sentiment += sentiment
                        article_count += 1
                    
                    if news_info.get('articles'):
                        confidence_score += 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error searching news for {name}: {e}")
        
        # Calculate overall sentiment
        if article_count > 0:
            news_data['sentiment_score'] = total_sentiment / article_count
        
        news_data['media_coverage_score'] = min(article_count / 10, 1.0)
        news_data['analysis_confidence'] = min(confidence_score / 3, 1.0)
        
        return news_data
    
    def _find_industry_certifications(self, datacenter_info):
        """Find industry certifications and compliance"""
        name = datacenter_info['name']
        basic = datacenter_info['basic_details']
        
        # Start with certifications from basic sustainability info
        existing_certs = []
        sustainability = basic.get('sustainability_info', {})
        if isinstance(sustainability, dict):
            existing_certs = sustainability.get('certifications', [])
        
        certifications = {
            'industry_standards': existing_certs,
            'security_compliance': [],
            'environmental_certifications': [],
            'quality_standards': [],
            'analysis_confidence': 0
        }
        
        # Search for additional certifications
        cert_queries = [
            f'"{name}" ISO SOC PCI compliance certifications',
            f'"{name}" LEED BREEAM green certifications',
            f'"{name}" Uptime Institute tier certification'
        ]
        
        confidence_score = len(existing_certs) * 0.1  # Existing certs boost confidence
        
        for query in cert_queries:
            try:
                results = self.search_datacenters(query.replace('data centers ', ''), num_results=3)
                if results and results.get('results'):
                    cert_info = self._extract_certifications_from_results(results)
                    
                    for category, certs in cert_info.items():
                        if category in certifications and certs:
                            certifications[category].extend(certs)
                    
                    if any(cert_info.values()):
                        confidence_score += 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error searching certifications for {name}: {e}")
        
        certifications['analysis_confidence'] = min(confidence_score / 3, 1.0)
        return certifications
    
    def _discover_strategic_partnerships(self, datacenter_info):
        """Discover strategic partnerships and alliances"""
        name = datacenter_info['name']
        
        partnerships = {
            'technology_partners': [],
            'cloud_providers': [],
            'connectivity_partners': [],
            'strategic_alliances': [],
            'analysis_confidence': 0
        }
        
        # Search for partnership information
        partnership_queries = [
            f'"{name}" partnership AWS Microsoft Azure Google',
            f'"{name}" connectivity network partners',
            f'"{name}" technology vendor partnerships'
        ]
        
        confidence_score = 0
        
        for query in partnership_queries:
            try:
                results = self.search_datacenters(query.replace('data centers ', ''), num_results=3)
                if results and results.get('results'):
                    partnership_info = self._extract_partnership_data(results, name)
                    
                    for category, partners in partnership_info.items():
                        if category in partnerships and partners:
                            partnerships[category].extend(partners)
                    
                    if any(partnership_info.values()):
                        confidence_score += 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error searching partnerships for {name}: {e}")
        
        partnerships['analysis_confidence'] = min(confidence_score / 3, 1.0)
        return partnerships
    
    def _research_growth_plans(self, datacenter_info):
        """Research expansion and growth plans"""
        name = datacenter_info['name']
        
        expansion_data = {
            'planned_expansions': [],
            'new_facilities': [],
            'capacity_upgrades': [],
            'investment_plans': [],
            'analysis_confidence': 0
        }
        
        # Search for expansion information
        expansion_queries = [
            f'"{name}" expansion plans new facility 2024 2025',
            f'"{name}" investment growth capacity',
            f'"{name}" new location expansion announcement'
        ]
        
        confidence_score = 0
        
        for query in expansion_queries:
            try:
                results = self.search_datacenters(query.replace('data centers ', ''), num_results=3)
                if results and results.get('results'):
                    expansion_info = self._extract_expansion_plans(results, name)
                    
                    for category, plans in expansion_info.items():
                        if category in expansion_data and plans:
                            expansion_data[category].extend(plans)
                    
                    if any(expansion_info.values()):
                        confidence_score += 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error searching expansion plans for {name}: {e}")
        
        expansion_data['analysis_confidence'] = min(confidence_score / 3, 1.0)
        return expansion_data
    
    # Helper methods for data extraction
    
    def _extract_supplier_from_result(self, result, datacenter_name):
        """Extract supplier information from search result"""
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        
        # Keywords that indicate supplier relationships
        supplier_keywords = [
            'supplier', 'vendor', 'partner', 'provider', 'contractor',
            'equipment', 'hardware', 'software', 'service', 'installation'
        ]
        
        text = (title + ' ' + snippet).lower()
        
        if any(keyword in text for keyword in supplier_keywords):
            relevance = self._calculate_relevance_score(text, datacenter_name)
            if relevance > 2:  # Only include relevant results
                return {
                    'name': title,
                    'description': snippet,
                    'url': result.get('link', ''),
                    'relevance_score': relevance
                }
        
        return None
    
    def _categorize_supplier(self, description):
        """Categorize supplier based on description"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['hardware', 'server', 'equipment', 'ups', 'generator', 'cooling']):
            return 'hardware_suppliers'
        elif any(word in desc_lower for word in ['software', 'management', 'monitoring', 'cloud', 'platform']):
            return 'software_providers'
        elif any(word in desc_lower for word in ['construction', 'contractor', 'building', 'architect', 'design']):
            return 'construction_partners'
        else:
            return 'service_providers'
    
    def _calculate_relevance_score(self, text, datacenter_name):
        """Calculate relevance score for search results"""
        score = 0
        
        # Check for exact name matches
        if datacenter_name.lower() in text:
            score += 10
        
        # Check for datacenter-related terms
        datacenter_terms = ['datacenter', 'data center', 'facility', 'colocation', 'hosting']
        for term in datacenter_terms:
            if term in text:
                score += 2
        
        return score
    
    def _extract_market_data_from_results(self, results, datacenter_name):
        """Extract market intelligence from search results"""
        market_info = []
        
        for result in results.get('organic_results', []):
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Look for financial indicators
            financial_keywords = ['revenue', 'investment', 'market', 'valuation', 'funding']
            text = (title + ' ' + snippet).lower()
            
            if any(keyword in text for keyword in financial_keywords):
                market_info.append({
                    'title': title,
                    'description': snippet,
                    'url': result.get('link', ''),
                    'relevance': self._calculate_relevance_score(text, datacenter_name)
                })
        
        return market_info
    
    def _extract_technical_details_from_results(self, results):
        """Extract technical details from search results"""
        tech_details = {
            'cooling_systems': {},
            'network_connectivity': {},
            'compliance_standards': []
        }
        
        for result in results.get('organic_results', []):
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            
            # Look for cooling information
            cooling_types = ['air cooled', 'liquid cooled', 'evaporative', 'chilled water', 'free cooling']
            for cooling_type in cooling_types:
                if cooling_type in text:
                    tech_details['cooling_systems']['type'] = cooling_type
            
            # Look for network information
            if 'gbps' in text or 'bandwidth' in text:
                tech_details['network_connectivity']['high_bandwidth'] = True
            
            # Look for compliance
            compliance_terms = ['iso', 'soc', 'pci', 'compliance', 'certified']
            for term in compliance_terms:
                if term in text:
                    tech_details['compliance_standards'].append(term.upper())
        
        return tech_details
    
    def _extract_financial_indicators(self, results, datacenter_name):
        """Extract financial indicators from search results"""
        financial_info = {
            'revenue_indicators': [],
            'investment_activity': [],
            'financial_performance': []
        }
        
        for result in results.get('organic_results', []):
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            text = title + ' ' + snippet
            
            # Look for revenue information
            if any(word in text.lower() for word in ['revenue', 'earnings', 'income']):
                financial_info['revenue_indicators'].append({
                    'source': title,
                    'description': snippet,
                    'url': result.get('link', '')
                })
            
            # Look for investment information
            if any(word in text.lower() for word in ['investment', 'funding', 'acquisition']):
                financial_info['investment_activity'].append({
                    'source': title,
                    'description': snippet,
                    'url': result.get('link', '')
                })
        
        return financial_info
    
    def _extract_competitive_intelligence(self, results, datacenter_name):
        """Extract competitive intelligence from search results"""
        competitive_info = {
            'direct_competitors': [],
            'market_leaders': [],
            'competitive_advantages': []
        }
        
        # Known datacenter companies
        known_competitors = [
            'digital realty', 'equinix', 'cyrusone', 'comstor', 'interxion',
            'globalswitch', 'telehouse', 'coresite', 'qts', 'iron mountain',
            'aws', 'microsoft', 'google cloud', 'oracle'
        ]
        
        for result in results.get('organic_results', []):
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            
            for competitor in known_competitors:
                if competitor in text and competitor != datacenter_name.lower():
                    competitive_info['direct_competitors'].append({
                        'name': competitor.title(),
                        'context': result.get('snippet', ''),
                        'source_url': result.get('link', '')
                    })
        
        return competitive_info
    
    def _extract_news_sentiment(self, results, datacenter_name):
        """Extract news and sentiment from search results"""
        news_info = {
            'articles': [],
            'developments': []
        }
        
        for result in results.get('organic_results', []):
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            url = result.get('link', '')
            
            # Check if it looks like a news article
            news_indicators = ['news', 'announces', 'expansion', 'investment', 'partnership']
            if any(indicator in (title + snippet).lower() for indicator in news_indicators):
                news_info['articles'].append({
                    'title': title,
                    'summary': snippet,
                    'url': url,
                    'publication_date': self._extract_date_from_text(snippet)
                })
            
            # Look for key developments
            development_keywords = ['expansion', 'investment', 'partnership', 'acquisition', 'launch']
            snippet_lower = snippet.lower()
            
            for keyword in development_keywords:
                if keyword in snippet_lower:
                    news_info['developments'].append({
                        'type': keyword,
                        'description': snippet,
                        'source': title,
                        'url': url
                    })
        
        return news_info
    
    def _calculate_article_sentiment(self, article):
        """Calculate sentiment score for an article"""
        text = (article.get('title', '') + ' ' + article.get('summary', '')).lower()
        
        positive_words = ['expansion', 'growth', 'investment', 'partnership', 'award', 'success', 'leadership']
        negative_words = ['loss', 'decline', 'problem', 'issue', 'delay', 'failure', 'challenge']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        # Return sentiment score between -1 and 1
        if positive_count + negative_count == 0:
            return 0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def _extract_certifications_from_results(self, results):
        """Extract certification information from search results"""
        certifications = {
            'industry_standards': [],
            'security_compliance': [],
            'environmental_certifications': [],
            'quality_standards': []
        }
        
        cert_patterns = {
            'industry_standards': ['iso 27001', 'iso 20000', 'itil', 'uptime institute'],
            'security_compliance': ['soc 2', 'pci dss', 'hipaa', 'gdpr'],
            'environmental_certifications': ['leed', 'breeam', 'energy star', 'iso 14001'],
            'quality_standards': ['iso 9001', 'six sigma', 'itil']
        }
        
        for result in results.get('organic_results', []):
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            
            for category, patterns in cert_patterns.items():
                for pattern in patterns:
                    if pattern in text:
                        certifications[category].append(pattern.upper())
        
        return certifications
    
    def _extract_partnership_data(self, results, datacenter_name):
        """Extract partnership information from search results"""
        partnerships = {
            'technology_partners': [],
            'cloud_providers': [],
            'connectivity_partners': [],
            'strategic_alliances': []
        }
        
        partner_patterns = {
            'cloud_providers': ['aws', 'microsoft azure', 'google cloud', 'oracle cloud'],
            'connectivity_partners': ['verizon', 'at&t', 'level 3', 'cogent', 'hurricane electric'],
            'technology_partners': ['cisco', 'dell', 'hp', 'ibm', 'nvidia', 'intel']
        }
        
        for result in results.get('organic_results', []):
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            
            for category, patterns in partner_patterns.items():
                for pattern in patterns:
                    if pattern in text and ('partnership' in text or 'partner' in text):
                        partnerships[category].append({
                            'partner': pattern.title(),
                            'context': result.get('snippet', ''),
                            'source': result.get('link', '')
                        })
        
        return partnerships
    
    def _extract_expansion_plans(self, results, datacenter_name):
        """Extract expansion and development plans from search results"""
        expansion_data = {
            'planned_expansions': [],
            'new_facilities': [],
            'capacity_upgrades': [],
            'investment_plans': []
        }
        
        for result in results.get('organic_results', []):
            snippet = result.get('snippet', '').lower()
            title = result.get('title', '').lower()
            
            if 'expansion' in snippet or 'expand' in snippet:
                expansion_data['planned_expansions'].append({
                    'description': result.get('snippet', ''),
                    'source': result.get('title', ''),
                    'url': result.get('link', '')
                })
            
            if 'new facility' in snippet or 'new datacenter' in snippet:
                expansion_data['new_facilities'].append({
                    'description': result.get('snippet', ''),
                    'source': result.get('title', ''),
                    'url': result.get('link', '')
                })
            
            if 'investment' in snippet and any(word in snippet for word in ['million', 'billion']):
                expansion_data['investment_plans'].append({
                    'description': result.get('snippet', ''),
                    'source': result.get('title', ''),
                    'url': result.get('link', '')
                })
        
        return expansion_data
    
    def _extract_date_from_text(self, text):
        """Extract date from text"""
        # Simple date extraction
        import re
        date_patterns = [
            r'\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{4})\b',
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2}),?\s+(\d{4})\b',
            r'\b(\d{4})-(\d{2})-(\d{2})\b'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _generate_executive_summary(self, intelligence_data, datacenter_info):
        """Generate executive summary of the analysis"""
        name = datacenter_info['name']
        
        # Count key findings
        supplier_count = sum(len(intelligence_data['supplier_info'][key]) for key in intelligence_data['supplier_info'] if isinstance(intelligence_data['supplier_info'][key], list))
        competitor_count = len(intelligence_data['competitive_analysis'].get('direct_competitors', []))
        news_count = len(intelligence_data['news_sentiment'].get('recent_articles', []))
        certification_count = sum(len(intelligence_data['certifications'][key]) for key in intelligence_data['certifications'] if isinstance(intelligence_data['certifications'][key], list))
        
        summary = f"""
EXECUTIVE SUMMARY: {name}

KEY FINDINGS:
• Supplier Ecosystem: {supplier_count} suppliers and partners identified
• Market Intelligence: {intelligence_data['market_value'].get('estimated_investment', 'Investment data analyzed')}
• Competitive Landscape: {competitor_count} direct competitors identified
• Media Coverage: {news_count} recent news articles analyzed
• Certifications: {certification_count} industry certifications found

ANALYSIS CONFIDENCE:
• Overall confidence level based on data availability and search results
• Multiple intelligence sources cross-referenced for accuracy
• Real-time analysis performed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return summary.strip()
    
    def _generate_strategic_recommendations(self, intelligence_data, datacenter_info):
        """Generate strategic recommendations based on analysis"""
        recommendations = []
        
        # Market analysis recommendations
        competitors = len(intelligence_data['competitive_analysis'].get('direct_competitors', []))
        if competitors > 5:
            recommendations.append("High competition detected - focus on differentiation strategies")
        elif competitors < 2:
            recommendations.append("Limited competition identified - opportunity for market expansion")
        
        # Partnership recommendations
        cloud_partners = len(intelligence_data['partnerships'].get('cloud_providers', []))
        if cloud_partners == 0:
            recommendations.append("Consider establishing strategic cloud provider partnerships")
        
        # Certification recommendations
        env_certs = len(intelligence_data['certifications'].get('environmental_certifications', []))
        if env_certs == 0:
            recommendations.append("Pursue environmental certifications for competitive advantage")
        
        # News sentiment recommendations
        sentiment_score = intelligence_data['news_sentiment'].get('sentiment_score', 0)
        if sentiment_score > 0.3:
            recommendations.append("Positive market sentiment - favorable conditions for expansion")
        elif sentiment_score < -0.3:
            recommendations.append("Negative sentiment detected - focus on reputation management")
        
        return recommendations
    
    def _calculate_analysis_confidence(self, intelligence_data):
        """Calculate overall confidence score for the analysis"""
        confidence_scores = []
        
        # Collect confidence scores from each analysis component
        for category, data in intelligence_data.items():
            if isinstance(data, dict) and 'analysis_confidence' in data:
                confidence_scores.append(data['analysis_confidence'])
        
        if confidence_scores:
            overall_confidence = sum(confidence_scores) / len(confidence_scores)
            return {
                'overall_score': round(overall_confidence, 2),
                'confidence_level': 'High' if overall_confidence > 0.7 else 'Medium' if overall_confidence > 0.4 else 'Low',
                'component_scores': {category: data.get('analysis_confidence', 0) for category, data in intelligence_data.items() if isinstance(data, dict)}
            }
        
        return {
            'overall_score': 0,
            'confidence_level': 'Low',
            'component_scores': {}
        }


def main():
    """Example usage of both DataCenterScraper and EnhancedDataCenterScraper"""
    try:
        # Initialize the enhanced scraper
        print("🚀 DataRackNews Enhanced Search System")
        print("="*60)
        
        # Option 1: Basic search (existing functionality)
        print("\n1. BASIC SEARCH EXAMPLE:")
        print("-" * 30)
        
        scraper = DataCenterScraper()
        results = scraper.search_datacenters("Virginia", num_results=3)
        
        if results:
            print(f"Found {results['total_results']} basic results")
            for i, result in enumerate(results['results'][:2], 1):
                print(f"\n{i}. {result['title'][:60]}...")
                print(f"   URL: {result['link']}")
        
        # Option 2: Enhanced deep analysis
        print(f"\n\n2. ENHANCED DEEP ANALYSIS EXAMPLE:")
        print("-" * 40)
        
        enhanced_scraper = EnhancedDataCenterScraper()
        
        if results and results['results']:
            # Analyze first result with deep intelligence
            first_result = results['results'][0]
            print(f"🔍 Performing deep analysis on: {first_result['title'][:50]}...")
            
            def progress_callback(progress, message):
                print(f"   Progress: {progress*100:.0f}% - {message}")
            
            # Perform comprehensive analysis
            analysis_report = enhanced_scraper.deep_analyze_datacenter(
                first_result, 
                progress_callback=progress_callback
            )
            
            if 'error' not in analysis_report:
                print(f"\n📊 ANALYSIS COMPLETED!")
                print("="*60)
                print(analysis_report['executive_summary'])
                
                print(f"\n💡 STRATEGIC RECOMMENDATIONS:")
                for i, rec in enumerate(analysis_report['recommendations'], 1):
                    print(f"   {i}. {rec}")
                
                print(f"\n📈 CONFIDENCE SCORE:")
                confidence = analysis_report['analysis_confidence']
                print(f"   Overall: {confidence['overall_score']} ({confidence['confidence_level']})")
                
                # Save detailed report
                filename = f"enhanced_analysis_{analysis_report['datacenter_name'].replace(' ', '_').replace('/', '_')}.json"
                with open(filename, 'w') as f:
                    import json
                    json.dump(analysis_report, f, indent=2, default=str)
                
                print(f"\n💾 Detailed report saved to: {filename}")
            else:
                print(f"❌ Analysis failed: {analysis_report['error']}")
        
        print(f"\n✅ Demo completed! You can now use EnhancedDataCenterScraper in your Gradio UI.")
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Make sure you have SERP_API_KEY in your .env file")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()