from typing import Dict, Optional
import requests
import json
import re
import uuid
from datetime import datetime, timezone

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

    def search_electricity_price_ai(self, country: str, year: Optional[int] = 2025) -> Optional[Dict]:
        """Use SerpAPI Google AI Mode to find industrial electricity price in EUR/MWh for a target year.
        Accepts country code (e.g., 'DE') or country name (e.g., 'Germany'). Default year is 2025."""
        if not self.serpapi_key:
            print("Warning: No SerpAPI key provided. Cannot fetch electricity price.")
            return None
        year_str = str(year) if year else "2025"
        query = (
            f"What is the average industrial electricity price in {country} in EUR/MWh for {year_str}? "
            f"If price is given in €/kWh or c/kWh, provide it too. Prefer official 2025 sources."
        )
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.serpapi_key,
            "google_domain": "google.com",
            "hl": "en",
            "gl": "us",
            "ai_overview": "true"
        }
        try:
            print(f"🤖 Searching electricity price for {country} using Google AI Mode...")
            response = requests.get(self.serpapi_base, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            price_data = self._extract_price_from_ai(data, country)
            if not price_data:
                price_data = self._extract_price_from_results(data, country, prefer_year=year)
            if price_data:
                price_data["source"] = "SerpAPI Google AI Mode"
                price_data["search_method"] = "ai"
                print(f"✅ Found price via AI Mode: {price_data.get('price_eur_per_mwh', 'N/A')} EUR/MWh")
                return price_data
            else:
                print(f"❌ No price data found in AI Mode results for {country}")
                return None
        except Exception as e:
            print(f"❌ Error with SerpAPI AI search (price): {e}")
            return None

    def _extract_price_from_ai(self, data: Dict, country: str) -> Optional[Dict]:
        ai_overview = data.get("ai_overview", {})
        if not ai_overview:
            return None
        text = ai_overview.get("overview") or ai_overview.get("text") or ""
        if text:
            print(f"🤖 AI Overview (price) found: {text[:200]}...")
            return self._parse_price_from_text(text, country)
        return None

    def _extract_price_from_results(self, data: Dict, country: str, prefer_year: Optional[int] = None) -> Optional[Dict]:
        organic_results = data.get("organic_results", [])
        # Prefer results that mention the target year in title/snippet
        preferred: List[Dict] = []
        others: List[Dict] = []
        year_token = str(prefer_year) if prefer_year else None
        for result in organic_results[:10]:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            text = f"{title} {snippet}"
            if year_token and year_token in text:
                preferred.append(result)
            else:
                others.append(result)
        for bucket in (preferred, others):
            for result in bucket:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                text = f"{title} {snippet}"
                price_data = self._parse_price_from_text(text, country)
                if price_data:
                    price_data["result_title"] = title
                    price_data["result_url"] = result.get("link", "")
                    return price_data
        return None

    def _parse_price_from_text(self, text: str, country: str) -> Optional[Dict]:
        """Parse electricity price and normalize to EUR/MWh.
        Supports patterns: EUR/MWh, €/MWh, €/kWh, c/kWh."""
        try:
            # Try to detect an explicit year present in the snippet
            detected_year = None
            ym = re.search(r"(20\d{2})", text)
            if ym:
                try:
                    detected_year = int(ym.group(1))
                except Exception:
                    detected_year = None
            # EUR/MWh or €/MWh
            m = re.search(r"(\d+(?:[\.,]\d+)?)\s*(?:EUR|€)\s*/\s*MWh", text, re.IGNORECASE)
            if m:
                val = float(m.group(1).replace(",", "."))
                return {
                    "country": country,
                    "price_eur_per_mwh": round(val, 2),
                    "unit_detected": "EUR/MWh",
                    "extracted_text": text[:200] + ("..." if len(text) > 200 else ""),
                    "datetime": datetime.now(timezone.utc).isoformat(),
                    "detected_year": detected_year,
                }
            # EUR/kWh or €/kWh
            m = re.search(r"(\d+(?:[\.,]\d+)?)\s*(?:EUR|€)\s*/\s*kWh", text, re.IGNORECASE)
            if m:
                eur_per_kwh = float(m.group(1).replace(",", "."))
                eur_per_mwh = eur_per_kwh * 1000.0
                return {
                    "country": country,
                    "price_eur_per_mwh": round(eur_per_mwh, 2),
                    "unit_detected": "EUR/kWh",
                    "extracted_text": text[:200] + ("..." if len(text) > 200 else ""),
                    "datetime": datetime.now(timezone.utc).isoformat(),
                    "detected_year": detected_year,
                }
            # c/kWh (cents per kWh)
            m = re.search(r"(\d+(?:[\.,]\d+)?)\s*c\s*/\s*kWh", text, re.IGNORECASE)
            if m:
                cents_per_kwh = float(m.group(1).replace(",", "."))
                eur_per_mwh = cents_per_kwh * 10.0  # 1 c/kWh = €0.01/kWh => €10/MWh
                return {
                    "country": country,
                    "price_eur_per_mwh": round(eur_per_mwh, 2),
                    "unit_detected": "c/kWh",
                    "extracted_text": text[:200] + ("..." if len(text) > 200 else ""),
                    "datetime": datetime.now(timezone.utc).isoformat(),
                    "detected_year": detected_year,
                }
        except Exception:
            pass
        return None

    def get_electricity_price(self, country: str, year: Optional[int] = 2025) -> Optional[Dict]:
        """Convenience wrapper to fetch electricity price (EUR/MWh) for a target year (default 2025)."""
        return self.search_electricity_price_ai(country, year)
    
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

    def export_metrics_record(
        self,
        energy_metrics: Dict,
        data_center_id: str,
        price_eur_per_mwh: Optional[float] = None,
        temperature_celsius: Optional[float] = None,
        uptime_percent: Optional[float] = None,
        recorded_at: Optional[str] = None,
        auto_price: bool = True,
    ) -> Dict:
        """
        Map EnergyAnalyzer.calculate_energy_metrics() output to the requested metrics JSON shape.
        - power_usage_mw is derived as average load = annual_energy_consumption_mwh / 8760
        - energy_cost_eur is computed if price_eur_per_mwh is provided or auto-fetched via Google AI search
        - carbon_emissions_kg is derived from annual_co2_emissions_tons
        - temperature_celsius and uptime_percent are pass-through optional inputs
        - recorded_at defaults to current UTC time if not provided
        """
        if not energy_metrics or "error" in energy_metrics:
            return {
                "error": energy_metrics.get("error", "Invalid energy metrics input") if isinstance(energy_metrics, dict) else "Invalid energy metrics input"
            }
        
        annual_energy_mwh = energy_metrics.get("annual_energy_consumption_mwh")
        annual_co2_tons = energy_metrics.get("annual_co2_emissions_tons")
        installed_capacity_mw = energy_metrics.get("installed_capacity_mw")
        
        avg_power_mw = None
        if isinstance(annual_energy_mwh, (int, float)):
            avg_power_mw = round(annual_energy_mwh / 8760.0, 6)
        elif isinstance(installed_capacity_mw, (int, float)) and "sustainability_metrics" in energy_metrics:
            # Fallback to capacity * utilization if available in sustainability metrics
            util = energy_metrics["sustainability_metrics"].get("utilization_factor")
            if isinstance(util, (int, float)):
                avg_power_mw = round(installed_capacity_mw * util, 6)
        
        # Optionally fetch price if not provided
        if price_eur_per_mwh is None and auto_price:
            # Try to infer country from sustainability metrics zone (ISO code)
            zone = None
            if isinstance(energy_metrics.get("sustainability_metrics"), dict):
                zone = energy_metrics["sustainability_metrics"].get("zone")
            country_for_price = zone or energy_metrics.get("location", {}).get("country")
            if country_for_price:
                price_info = self.get_electricity_price(country_for_price)
                if price_info and isinstance(annual_energy_mwh, (int, float)):
                    price_eur_per_mwh = price_info.get("price_eur_per_mwh")
        
        energy_cost_eur = None
        if price_eur_per_mwh is not None and isinstance(annual_energy_mwh, (int, float)):
            energy_cost_eur = round(annual_energy_mwh * float(price_eur_per_mwh), 2)
        
        carbon_emissions_kg = None
        if isinstance(annual_co2_tons, (int, float)):
            carbon_emissions_kg = round(annual_co2_tons * 1000.0, 2)
        
        timestamp = recorded_at or datetime.now(timezone.utc).isoformat()
        
        return {
            "id": str(uuid.uuid4()),
            "data_center_id": str(data_center_id),
            "power_usage_mw": avg_power_mw,
            "energy_cost_eur": energy_cost_eur,
            "carbon_emissions_kg": carbon_emissions_kg,
            "temperature_celsius": temperature_celsius,
            "uptime_percent": uptime_percent,
            "recorded_at": timestamp,
        }

    def metrics_from_data_center_record(
        self,
        data_center_record: Dict,
        country_code: Optional[str] = None,
        temperature_celsius: Optional[float] = None,
        uptime_percent: Optional[float] = None,
        recorded_at: Optional[str] = None,
        auto_price: bool = True,
    ) -> Dict:
        """
        Produce a `metrics` table record from a `data_centers`-shaped record.
        Expects keys: id, power_capacity_mw, country (or provide country_code explicitly).
        - Computes energy and emissions using calculate_location_emissions()
        - Uses export_metrics_record() to emit schema-compliant dict
        """
        if not data_center_record or "id" not in data_center_record:
            return {"error": "data_center_record missing id"}

        capacity_mw = data_center_record.get("power_capacity_mw")
        if not isinstance(capacity_mw, (int, float)):
            try:
                capacity_mw = float(capacity_mw) if capacity_mw is not None else None
            except Exception:
                capacity_mw = None

        if not capacity_mw or capacity_mw <= 0:
            return {"error": "Invalid or missing power_capacity_mw"}

        zone = (country_code or data_center_record.get("country") or "").strip()
        if not zone:
            return {"error": "Missing country_code/country for carbon intensity lookup"}

        # Build a minimal data_center input shape for calculate_energy_metrics()
        dc_input = {
            "title": data_center_record.get("name"),
            "operator": data_center_record.get("operator"),
            "location": {
                "city": data_center_record.get("city"),
                "country": data_center_record.get("country"),
            },
            "estimated_capacity": f"{capacity_mw}MW",
        }

        energy_metrics = self.calculate_energy_metrics(dc_input, zone)
        if "error" in energy_metrics:
            return {"error": energy_metrics.get("error", "Failed energy metrics calc")}

        return self.export_metrics_record(
            energy_metrics=energy_metrics,
            data_center_id=data_center_record["id"],
            price_eur_per_mwh=None,
            temperature_celsius=temperature_celsius,
            uptime_percent=uptime_percent,
            recorded_at=recorded_at,
            auto_price=auto_price,
        )

    def export_records_to_file(self, records: list, out_path: str) -> bool:
        """Write a list of metrics records to a JSON file."""
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            print(f"💾 Exported {len(records)} record(s) to {out_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to write export file: {e}")
            return False

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
    
    analysis_records = []
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
        
        # Price lookup (AI)
        price_info = analyzer.get_electricity_price(country)
        if not price_info:
            print(f"  ⚠️  No price data found in AI Mode results for {country}")
        
        # Compute average power
        avg_power_mw = round(energy_metrics['annual_energy_consumption_mwh'] / 8760.0, 6)
        price_eur_per_mwh = price_info.get('price_eur_per_mwh') if price_info else None
        energy_cost_eur = round(energy_metrics['annual_energy_consumption_mwh'] * price_eur_per_mwh, 2) if isinstance(price_eur_per_mwh, (int, float)) else None
        
        # Rich analysis record
        analysis_record = {
            "id": str(uuid.uuid4()),
            "data_center_id": str(i + 1),
            "facility_name": energy_metrics['facility_name'],
            "operator": energy_metrics['operator'],
            "location": energy_metrics['location'],
            "installed_capacity_mw": energy_metrics['installed_capacity_mw'],
            "power_usage_mw": avg_power_mw,
            "annual_energy_mwh": energy_metrics['annual_energy_consumption_mwh'],
            "grid": {
                "zone": energy_metrics['sustainability_metrics'].get('zone') if isinstance(energy_metrics.get('sustainability_metrics'), dict) else None,
                "carbon_intensity_gco2_kwh": energy_metrics.get('grid_carbon_intensity_gco2_kwh'),
                "renewable_percentage": energy_metrics.get('grid_renewable_percentage'),
            },
            "emissions": {
                "annual_co2_tons": energy_metrics['annual_co2_emissions_tons'],
                "annual_co2_kg": round(energy_metrics['annual_co2_emissions_tons'] * 1000.0, 2),
            },
            "cost": {
                "price_eur_per_mwh": price_eur_per_mwh,
                "energy_cost_eur": energy_cost_eur,
            },
            "water": water_metrics if 'error' not in water_metrics else None,
            "ops": {
                "temperature_celsius": None,
                "uptime_percent": None,
            },
            "provenance": {
                "co2_source": energy_metrics['sustainability_metrics'].get('data_source') if isinstance(energy_metrics.get('sustainability_metrics'), dict) else None,
                "co2_timestamp": energy_metrics['sustainability_metrics'].get('data_timestamp') if isinstance(energy_metrics.get('sustainability_metrics'), dict) else None,
                "price_source": price_info.get('source') if price_info else None,
                "price_unit_detected": price_info.get('unit_detected') if price_info else None,
                "price_text_excerpt": price_info.get('extracted_text') if price_info else None,
            },
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        analysis_records.append(analysis_record)
        
        # Demonstrate metrics export mapping (pricing optional; pass None to trigger auto-price lookup)
        record = analyzer.export_metrics_record(
            energy_metrics=energy_metrics,
            data_center_id=str(i + 1),
            price_eur_per_mwh=None,
            temperature_celsius=None,
            uptime_percent=None,
            recorded_at=None,
            auto_price=True,
        )
        print(f"  📦 Metrics JSON (partial): {json.dumps(record)[:200]}...")
    
    # Write rich analysis export (testing only)
    try:
        out_path = "analysis_export.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(analysis_records, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Wrote analysis export with {len(analysis_records)} record(s) to {out_path}")
    except Exception as e:
        print(f"\n❌ Failed to write analysis export: {e}")
    
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
