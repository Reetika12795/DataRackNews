"""
Data Center Carbon Footprint Tracker
Enhanced utilities for tracking data center environmental impact
"""

import json
import csv
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import requests
from serp_search import DataCenterScraper


@dataclass
class DataCenter:
    """Data structure for storing data center information"""
    name: str
    location: str
    operator: str
    capacity_mw: Optional[float] = None
    capacity_sqft: Optional[int] = None
    pue: Optional[float] = None
    renewable_percentage: Optional[float] = None
    carbon_footprint: Optional[float] = None
    last_updated: str = None
    source_url: str = ""
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()


class DataCenterTracker:
    """Main class for tracking data centers and their carbon footprints"""
    
    def __init__(self):
        self.scraper = DataCenterScraper()
        self.data_centers: List[DataCenter] = []
        self.regions = [
            "Virginia", "California", "Texas", "New York", "Washington",
            "Oregon", "North Carolina", "Georgia", "Illinois", "Ohio"
        ]
    
    def search_region(self, region: str, num_results: int = 10) -> List[Dict]:
        """Search for data centers in a specific region"""
        print(f"Searching for data centers in {region}...")
        
        # Different search queries for better coverage
        search_queries = [
            f"data centers {region} location",
            f"data center facilities {region}",
            f"cloud infrastructure {region}",
            f"colocation {region} data center"
        ]
        
        all_results = []
        for query in search_queries:
            results = self.scraper.search_datacenters(region, num_results//len(search_queries))
            if results and results.get('results'):
                all_results.extend(results['results'])
        
        return all_results
    
    def analyze_datacenter(self, url: str) -> Optional[DataCenter]:
        """Analyze a single data center and extract information"""
        details = self.scraper.scrape_datacenter_details(url)
        if not details:
            return None
        
        # Parse capacity information
        capacity = details.get('capacity', {})
        capacity_mw = None
        capacity_sqft = None
        
        if isinstance(capacity, dict):
            capacity_mw = float(capacity.get('power_mw', 0)) if capacity.get('power_mw') else None
            capacity_sqft = int(capacity.get('space_sqft', 0)) if capacity.get('space_sqft') else None
        
        # Parse power usage
        power_usage = details.get('power_usage', {})
        pue = None
        renewable_percentage = None
        
        if isinstance(power_usage, dict):
            pue = float(power_usage.get('pue', 0)) if power_usage.get('pue') else None
            renewable_percentage = float(power_usage.get('renewable_percentage', 0)) if power_usage.get('renewable_percentage') else None
        
        # Calculate carbon footprint estimate
        carbon_footprint = self.estimate_carbon_footprint(capacity_mw, pue, renewable_percentage)
        
        datacenter = DataCenter(
            name=details.get('name', 'Unknown'),
            location=details.get('location', 'Unknown'),
            operator=self.extract_operator(details.get('name', '')),
            capacity_mw=capacity_mw,
            capacity_sqft=capacity_sqft,
            pue=pue,
            renewable_percentage=renewable_percentage,
            carbon_footprint=carbon_footprint,
            source_url=url
        )
        
        return datacenter
    
    def estimate_carbon_footprint(self, capacity_mw: Optional[float], 
                                pue: Optional[float], 
                                renewable_percentage: Optional[float]) -> Optional[float]:
        """Estimate carbon footprint based on available data"""
        if not capacity_mw:
            return None
        
        # Default values for estimation
        pue = pue or 1.5  # Average PUE
        renewable_percentage = renewable_percentage or 20  # Conservative estimate
        
        # Average grid carbon intensity (kg CO2/MWh) - US average
        grid_carbon_intensity = 400
        
        # Calculate annual energy consumption
        annual_energy_mwh = capacity_mw * 8760 * (pue / 100)  # MWh/year
        
        # Calculate carbon footprint considering renewable energy
        non_renewable_percentage = (100 - renewable_percentage) / 100
        annual_carbon_footprint = annual_energy_mwh * grid_carbon_intensity * non_renewable_percentage
        
        return round(annual_carbon_footprint, 2)
    
    def extract_operator(self, name: str) -> str:
        """Extract operator name from facility name"""
        # Common data center operators
        operators = [
            'Amazon', 'Google', 'Microsoft', 'Meta', 'Facebook',
            'Digital Realty', 'Equinix', 'CyrusOne', 'CoreSite',
            'QTS', 'Iron Mountain', 'Switch', 'Vantage'
        ]
        
        name_lower = name.lower()
        for operator in operators:
            if operator.lower() in name_lower:
                return operator
        
        return "Unknown"
    
    def scan_all_regions(self, num_results_per_region: int = 5):
        """Scan all predefined regions for data centers"""
        for region in self.regions:
            try:
                results = self.search_region(region, num_results_per_region)
                
                for result in results:
                    datacenter = self.analyze_datacenter(result['link'])
                    if datacenter:
                        self.data_centers.append(datacenter)
                        print(f"Added: {datacenter.name} in {datacenter.location}")
                
                # Rate limiting
                import time
                time.sleep(5)
                
            except Exception as e:
                print(f"Error scanning {region}: {e}")
    
    def save_to_csv(self, filename: str = None):
        """Save data centers to CSV file"""
        if not filename:
            filename = f"datacenters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if not self.data_centers:
                print("No data centers to save")
                return
            
            fieldnames = list(asdict(self.data_centers[0]).keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for dc in self.data_centers:
                writer.writerow(asdict(dc))
        
        print(f"Saved {len(self.data_centers)} data centers to {filename}")
    
    def save_to_json(self, filename: str = None):
        """Save data centers to JSON file"""
        if not filename:
            filename = f"datacenters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = [asdict(dc) for dc in self.data_centers]
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(self.data_centers)} data centers to {filename}")
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics of tracked data centers"""
        if not self.data_centers:
            return {"message": "No data centers tracked"}
        
        total_capacity = sum(dc.capacity_mw for dc in self.data_centers if dc.capacity_mw)
        total_carbon = sum(dc.carbon_footprint for dc in self.data_centers if dc.carbon_footprint)
        avg_pue = sum(dc.pue for dc in self.data_centers if dc.pue) / len([dc for dc in self.data_centers if dc.pue])
        
        operators = {}
        for dc in self.data_centers:
            operators[dc.operator] = operators.get(dc.operator, 0) + 1
        
        return {
            "total_datacenters": len(self.data_centers),
            "total_capacity_mw": round(total_capacity, 2),
            "total_estimated_carbon_footprint": round(total_carbon, 2),
            "average_pue": round(avg_pue, 2) if avg_pue else None,
            "operators": operators
        }


def main():
    """Example usage of the DataCenterTracker"""
    tracker = DataCenterTracker()
    
    # Search specific region
    print("Searching Virginia data centers...")
    results = tracker.search_region("Virginia", 3)
    
    for result in results[:2]:  # Analyze first 2 results
        datacenter = tracker.analyze_datacenter(result['link'])
        if datacenter:
            tracker.data_centers.append(datacenter)
            print(f"Added: {datacenter.name}")
    
    # Show statistics
    stats = tracker.get_summary_stats()
    print("\nSummary Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Save results
    if tracker.data_centers:
        tracker.save_to_json("sample_datacenters.json")
        tracker.save_to_csv("sample_datacenters.csv")


if __name__ == "__main__":
    main()
