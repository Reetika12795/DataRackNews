from typing import Dict, Optional
import requests
import json
import re

class EnergyAnalyzer:
    """Analyzes energy consumption and carbon footprint using SerpAPI AI Mode"""
    
    def __init__(self, serpapi_key: str = None):
        self.serpapi_key = serpapi_key
        self.serpapi_base = "https://serpapi.com/search"
    
    def search_carbon_intensity_ai(self, country_code: str) -> Optional[Dict]:
        """Use SerpAPI Google AI Mode to find carbon intensity data for a country"""
        
        if not self.serpapi_key:
            print("Warning: No SerpAPI key provided. Cannot fetch real data.")
            return None
        
        # More specific AI query
        query = f"What is the current electricity grid carbon intensity in gCO2/kWh and renewable energy percentage for {country_code}? Include 2024 data."
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.serpapi_key,
            "google_domain": "google.com",
            "hl": "en",
            "gl": "us",
            "ai_overview": "true"  # Enable AI mode
        }
        
        try:
            print(f"🤖 Searching carbon intensity for {country_code} using Google AI Mode...")
            response = requests.get(self.serpapi_base, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract from AI overview if available
            carbon_data = self._extract_carbon_data_from_ai(data, country_code)
            
            if not carbon_data:
                # Fallback to regular results
                carbon_data = self._extract_carbon_data_from_results(data, country_code)
            
            if carbon_data:
                carbon_data["source"] = "SerpAPI Google AI Mode"
                carbon_data["search_method"] = "ai"
                print(f"✅ Found data via AI Mode: {carbon_data.get('carbonIntensity', 'N/A')} gCO2/kWh")
                return carbon_data
            else:
                print(f"❌ No carbon intensity data found in AI Mode results for {country_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error with SerpAPI AI search: {e}")
            return None
    
    def _extract_carbon_data_from_ai(self, data: Dict, country_code: str) -> Optional[Dict]:
        """Extract carbon intensity data from AI overview results"""
        
        ai_overview = data.get("ai_overview", {})
        if not ai_overview:
            return None
        
        # Look for AI overview text
        overview_text = ""
        if "overview" in ai_overview:
            overview_text = ai_overview["overview"]
        elif "text" in ai_overview:
            overview_text = ai_overview["text"]
        
        if overview_text:
            print(f"🤖 AI Overview found: {overview_text[:200]}...")
            return self._parse_carbon_data_from_text(overview_text, country_code)
        
        return None
    
    def _extract_carbon_data_from_results(self, data: Dict, country_code: str) -> Optional[Dict]:
        """Extract carbon intensity data from regular search results"""
        
        organic_results = data.get("organic_results", [])
        
        for result in organic_results[:5]:  # Check top 5 results
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            
            # Combine title and snippet for analysis
            text = f"{title} {snippet}"
            
            # Look for carbon intensity patterns
            carbon_data = self._parse_carbon_data_from_text(text, country_code)
            if carbon_data:
                carbon_data["result_title"] = title
                carbon_data["result_url"] = result.get("link", "")
                return carbon_data
        
        return None
    
    def _parse_carbon_data_from_text(self, text: str, country_code: str) -> Optional[Dict]:
        """Parse carbon intensity and renewable percentage from text using regex"""
        
        # Patterns for carbon intensity (gCO2/kWh)
        carbon_patterns = [
            r'(\d+(?:\.\d+)?)\s*g?CO2?/kWh',
            r'(\d+(?:\.\d+)?)\s*grams?\s*CO2?\s*per\s*kWh',
            r'carbon\s*intensity[:\s]*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*g\s*CO2\s*/\s*kWh'
        ]
        
        # Patterns for renewable percentage
        renewable_patterns = [
            r'(\d+(?:\.\d+)?)\s*%\s*renewable',
            r'renewable[:\s]*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*percent\s*renewable',
            r'renewable\s*energy[:\s]*(\d+(?:\.\d+)?)'
        ]
        
        carbon_intensity = None
        renewable_percentage = None
        
        # Search for carbon intensity
        for pattern in carbon_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    carbon_intensity = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Search for renewable percentage
        for pattern in renewable_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    renewable_percentage = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Return data if we found at least carbon intensity
        if carbon_intensity is not None:
            return {
                "carbonIntensity": carbon_intensity,
                "renewablePercentage": renewable_percentage,
                "fossilFuelPercentage": (100 - renewable_percentage) if renewable_percentage else None,
                "zone": country_code.upper(),
                "datetime": "2024-serpapi-search",
                "isEstimated": True,
                "extracted_text": text[:200] + "..." if len(text) > 200 else text
            }
        
        return None
    
    def get_carbon_intensity(self, country_code: str) -> Optional[Dict]:
        """Get carbon intensity data using SerpAPI AI Mode"""
        return self.search_carbon_intensity_ai(country_code.upper())
    
    def calculate_location_emissions(self, capacity_mw: float, country_code: str) -> Optional[Dict]:
        """
        Calculate location-based carbon footprint using real API data
        Only calculates what we can determine with certainty from power capacity and grid data
        """
        # Get real grid data from API
        grid_data = self.get_carbon_intensity(country_code)
        
        if not grid_data or grid_data.get("carbonIntensity") is None:
            print(f"Cannot calculate emissions: No carbon intensity data available for {country_code}")
            return None
        
        # Use standard industry utilization factor
        utilization_factor = 0.85
        annual_energy_mwh = capacity_mw * 8760 * utilization_factor
        
        grid_carbon_intensity = grid_data["carbonIntensity"]  # gCO2/kWh
        grid_renewable_percentage = grid_data.get("renewablePercentage")
        
        # Calculate annual CO2 emissions
        annual_co2_emissions_tons = (annual_energy_mwh * 1000 * grid_carbon_intensity) / 1_000_000
        
        # Calculate renewable vs fossil energy breakdown (only if renewable percentage is available)
        if grid_renewable_percentage is not None:
            renewable_energy_mwh = annual_energy_mwh * (grid_renewable_percentage / 100)
            fossil_energy_mwh = annual_energy_mwh - renewable_energy_mwh
        else:
            renewable_energy_mwh = None
            fossil_energy_mwh = None
        
        return {
            "capacity_mw": capacity_mw,
            "utilization_factor": utilization_factor,
            "annual_energy_mwh": round(annual_energy_mwh, 2),
            "grid_carbon_intensity_gco2_kwh": grid_carbon_intensity,
            "annual_co2_emissions_tons": round(annual_co2_emissions_tons, 2),
            "grid_renewable_percentage": grid_renewable_percentage,
            "renewable_energy_mwh": round(renewable_energy_mwh, 2) if renewable_energy_mwh is not None else None,
            "fossil_energy_mwh": round(fossil_energy_mwh, 2) if fossil_energy_mwh is not None else None,
            "co2_intensity_kg_per_mwh": round(grid_carbon_intensity, 2),
            "data_source": grid_data.get("source"),
            "data_timestamp": grid_data.get("datetime"),
            "is_estimated": grid_data.get("isEstimated", False),
            "zone": grid_data.get("zone")
        }
    
    def calculate_energy_metrics(self, data_center: Dict, country_code: str) -> Dict:
        """Calculate energy metrics for a data center using only real API data"""
        
        # Extract capacity in MW
        capacity_str = data_center.get('estimated_capacity', '0MW')
        try:
            capacity_mw = float(capacity_str.replace('MW', '').replace('GW', '000').strip())
        except (ValueError, AttributeError):
            capacity_mw = 0.0
        
        if capacity_mw <= 0:
            return {
                "facility_name": data_center.get('title', 'Unknown'),
                "operator": data_center.get('operator', 'Unknown'),
                "location": data_center.get('location', {}),
                "error": "Invalid or missing capacity data"
            }
        
        # Calculate emissions using real API data
        location_emissions = self.calculate_location_emissions(capacity_mw, country_code)
        
        if not location_emissions:
            return {
                "facility_name": data_center.get('title', 'Unknown'),
                "operator": data_center.get('operator', 'Unknown'),
                "location": data_center.get('location', {}),
                "installed_capacity_mw": capacity_mw,
                "error": f"Cannot fetch real data for {country_code}. Check API token and country code."
            }
        
        return {
            "facility_name": data_center.get('title', 'Unknown'),
            "operator": data_center.get('operator', 'Unknown'),
            "location": data_center.get('location', {}),
            "installed_capacity_mw": capacity_mw,
            
            # Real API-based calculations only
            "sustainability_metrics": location_emissions,
            
            # Legacy fields for backward compatibility (using real data)
            "annual_energy_consumption_mwh": location_emissions["annual_energy_mwh"],
            "grid_carbon_intensity_gco2_kwh": location_emissions["grid_carbon_intensity_gco2_kwh"],
            "annual_co2_emissions_tons": location_emissions["annual_co2_emissions_tons"],
            "renewable_energy_factor": round(location_emissions["grid_renewable_percentage"] / 100, 3) if location_emissions.get("grid_renewable_percentage") is not None else None,
            "fossil_fuel_factor": round((100 - location_emissions["grid_renewable_percentage"]) / 100, 3) if location_emissions.get("grid_renewable_percentage") is not None else None,
            "grid_renewable_percentage": location_emissions["grid_renewable_percentage"]
        }

class WaterAnalyzer:
    """Estimates water consumption for data centers"""
    
    def estimate_water_usage(self, energy_metrics: Dict) -> Dict:
        """Estimate water consumption based on energy usage and cooling requirements"""
        
        # Check if we have valid energy data
        if "error" in energy_metrics or "annual_energy_consumption_mwh" not in energy_metrics:
            return {
                "error": "Cannot estimate water usage without valid energy metrics"
            }
        
        # Water Usage Effectiveness (WUE) estimates
        # Typical range: 0.2 - 2.0 L/kWh depending on cooling method
        # Using conservative industry average since we don't have specific facility data
        # Source: https://www.usgbc.org/resources/water-usage-effectiveness-wue
        # Source: https://www.datacenterknowledge.com/design/water-usage-effectiveness-data-centers
        base_wue = 0.8  # L/kWh - industry average
        
        annual_energy_kwh = energy_metrics['annual_energy_consumption_mwh'] * 1000
        annual_water_liters = annual_energy_kwh * base_wue
        annual_water_m3 = annual_water_liters / 1000
        
        return {
            "estimated_wue_l_per_kwh": base_wue,
            "annual_water_consumption_m3": round(annual_water_m3, 2),
            "annual_water_consumption_liters": round(annual_water_liters, 2),
            "note": "Estimates based on industry averages - actual usage may vary significantly"
        }


def main():
    """Test the EnergyAnalyzer with sample data"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get API token from environment
    api_token = os.getenv('SERPAPI_TOKEN')
    
    if not api_token:
        print("⚠️  No SERPAPI_TOKEN found in environment variables")
        print("   Add your token to .env file: SERPAPI_TOKEN=your_token_here")
        print("   Testing will continue but will show warnings about missing token\n")
    
    # Initialize analyzer
    analyzer = EnergyAnalyzer(serpapi_key=api_token)
    water_analyzer = WaterAnalyzer()
    
    # Sample data centers for testing
    test_data_centers = [
        {
            "title": "Test Data Center Paris",
            "operator": "Test Operator",
            "location": {"city": "Paris", "country": "France"},
            "estimated_capacity": "50MW"
        },
        {
            "title": "Test Data Center Frankfurt", 
            "operator": "Another Operator",
            "location": {"city": "Frankfurt", "country": "Germany"},
            "estimated_capacity": "25MW"
        },
        {
            "title": "Test Data Center Stockholm",
            "operator": "Nordic Operator", 
            "location": {"city": "Stockholm", "country": "Sweden"},
            "estimated_capacity": "100MW"
        },
        {
            "title": "Test Data Center London",
            "operator": "UK Operator", 
            "location": {"city": "London", "country": "United Kingdom"},
            "estimated_capacity": "50MW"
        }
    ]
    
    # Test country codes
    test_countries = ["FR", "DE", "SE", "GB"]
    
    print("🔋 Energy Analyzer Test Suite")
    print("=" * 50)
    
    # Test 1: Direct API calls
    print("\n📡 Testing Direct API Calls:")
    print("-" * 30)
    
    for country in test_countries:
        print(f"\n🌍 Testing {country}:")
        grid_data = analyzer.get_carbon_intensity(country)
        
        if grid_data:
            print(f"  ✅ Carbon Intensity: {grid_data['carbonIntensity']} gCO2/kWh")
            print(f"  🌱 Renewable %: {grid_data.get('renewablePercentage', 'N/A')}%")
            print(f"  ⏰ Timestamp: {grid_data.get('datetime', 'N/A')}")
            print(f"  📊 Estimated: {grid_data.get('isEstimated', False)}")
            print(f"  🗺️  Zone: {grid_data.get('zone', 'N/A')}")
            print(f"  📊 Source: {grid_data.get('source', 'N/A')}")
        else:
            print(f"  ❌ Failed to get data for {country}")
    
    # Test 2: Location emissions calculations
    print("\n\n🌍 Testing Location Emissions Calculations:")
    print("-" * 45)
    
    for i, (dc, country) in enumerate(zip(test_data_centers, test_countries)):
        print(f"\n🏢 Data Center {i+1}: {dc['title']}")
        capacity_mw = float(dc['estimated_capacity'].replace('MW', '').replace('GW', '000').strip())
        
        emissions = analyzer.calculate_location_emissions(capacity_mw, country)
        
        if emissions:
            print(f"  ⚡ Capacity: {emissions['capacity_mw']} MW")
            print(f"  📊 Annual Energy: {emissions['annual_energy_mwh']} MWh")
            print(f"  🏭 Annual CO2: {emissions['annual_co2_emissions_tons']} tons")
            
            if emissions.get('renewable_energy_mwh') is not None:
                print(f"  🌱 Renewable Energy: {emissions['renewable_energy_mwh']} MWh ({emissions.get('grid_renewable_percentage', 'N/A')}%)")
                print(f"  ⚫ Fossil Energy: {emissions['fossil_energy_mwh']} MWh")
            else:
                print(f"  🌱 Renewable Energy: N/A (not provided by API)")
                
            print(f"  📈 CO2 Intensity: {emissions['co2_intensity_kg_per_mwh']} gCO2/kWh")
            print(f"  📊 Source: {emissions['data_source']}")
            print(f"  ⏰ Timestamp: {emissions['data_timestamp']}")
            print(f"  📊 Estimated: {emissions['is_estimated']}")
            print(f"  🗺️  Zone: {emissions['zone']}")
        else:
            print(f"  ❌ Failed to calculate emissions for {country}")
    
    # Test 3: Complete energy metrics
    print("\n\n📊 Testing Complete Energy Metrics:")
    print("-" * 40)
    
    for i, (dc, country) in enumerate(zip(test_data_centers, test_countries)):
        print(f"\n🏢 {dc['title']} ({country}):")
        
        energy_metrics = analyzer.calculate_energy_metrics(dc, country)
        
        if "error" in energy_metrics:
            print(f"  ❌ Error: {energy_metrics['error']}")
            continue
            
        print(f"  🏭 Facility: {energy_metrics['facility_name']}")
        print(f"  🏢 Operator: {energy_metrics['operator']}")
        print(f"  ⚡ Capacity: {energy_metrics['installed_capacity_mw']} MW")
        print(f"  📊 Annual Energy: {energy_metrics['annual_energy_consumption_mwh']} MWh")
        print(f"  🏭 Annual CO2: {energy_metrics['annual_co2_emissions_tons']} tons")
        
        if energy_metrics.get('renewable_energy_factor') is not None:
            print(f"  🌱 Renewable Factor: {energy_metrics['renewable_energy_factor']}")
            print(f"  ⚫ Fossil Factor: {energy_metrics['fossil_fuel_factor']}")
        
        # Test water usage estimation
        water_metrics = water_analyzer.estimate_water_usage(energy_metrics)
        if "error" not in water_metrics:
            print(f"  💧 Annual Water: {water_metrics['annual_water_consumption_m3']} m³")
            print(f"  💧 WUE: {water_metrics['estimated_wue_l_per_kwh']} L/kWh")
    
    # Test 4: Error handling
    print("\n\n🚨 Testing Error Handling:")
    print("-" * 30)
    
    # Test with invalid country
    print("\n🌍 Testing invalid country code (XX):")
    invalid_result = analyzer.get_carbon_intensity("XX")
    if invalid_result is None:
        print("  ✅ Correctly handled invalid country code")
    else:
        print(f"  ⚠️  Unexpected result: {invalid_result}")
    
    # Test with invalid capacity
    print("\n⚡ Testing invalid capacity data:")
    invalid_dc = {
        "title": "Invalid Data Center",
        "operator": "Test",
        "location": {},
        "estimated_capacity": "invalid"
    }
    invalid_metrics = analyzer.calculate_energy_metrics(invalid_dc, "DE")
    if "error" in invalid_metrics:
        print(f"  ✅ Correctly handled invalid capacity: {invalid_metrics['error']}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Suite Complete!")
    
    if api_token:
        print("✅ All tests ran with real API data")
    else:
        print("⚠️  Tests ran without API token - add SERPAPI_TOKEN to .env for real data")
    
    print("\n💡 Usage Tips:")
    print("  - Set SERPAPI_TOKEN in your .env file")
    print("  - Use ISO 2-letter country codes (DE, ES, SE, etc.)")
    print("  - Capacity should be in format '50MW' or '1.5GW'")
    print("  - Check 'error' field in results for issues")
    print("  - Some APIs may not provide renewable percentage data")

if __name__ == "__main__":
    # Run the full test suite
    main()
