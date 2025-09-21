"""
Gradio UI for DataRackNews - Data Center Search and Visualization
"""

import gradio as gr
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from serp_search import DataCenterScraper, EnhancedDataCenterScraper
from equinix_scraper import EquinixDataCenterScraper
from datacenter_tracker import DataCenterTracker, DataCenter
import threading


class DataCenterUI:
    def __init__(self):
        self.scraper = DataCenterScraper()
        self.enhanced_scraper = EnhancedDataCenterScraper()  # Add enhanced scraper
        self.equinix_scraper = EquinixDataCenterScraper()  # Add Equinix scraper
        self.tracker = DataCenterTracker()
        self.search_results = []
        self.analyzed_centers = []
        self.deep_analysis_cache = {}  # Cache for deep analysis results
        self.current_city_facilities = []  # Store facilities for current city
    
    def search_datacenters(self, region, num_results, progress=gr.Progress()):
        """Search for data centers and return formatted results"""
        try:
            progress(0, desc="Starting search...")
            
            # Perform search
            results = self.scraper.search_datacenters(region, num_results)
            
            if not results or not results.get('results'):
                return ("No results found", None, "No data available", 
                        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                        gr.update(visible=False), gr.update(visible=False))
            
            progress(0.5, desc="Processing results...")
            
            # Store results for later analysis
            self.search_results = results['results']
            
            # Format results for display
            formatted_results = []
            
            for i, result in enumerate(results['results'], 1):
                title = result.get('title', 'N/A')
                formatted_results.append({
                    'Position': i,
                    'Title': title,
                    'URL': result.get('link', 'N/A'),
                    'Snippet': result.get('snippet', 'N/A')[:200] + '...' if len(result.get('snippet', '')) > 200 else result.get('snippet', 'N/A')
                })
            
            # Create DataFrame for table display
            df = pd.DataFrame(formatted_results)
            
            progress(1.0, desc="Search completed!")
            
            # Create summary
            summary = f"""
            ## Search Results Summary
            
            **Region:** {region}  
            **Total Results:** {len(results['results'])}  
            **Search Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Click any "Analyze Result #X" button below to get detailed analysis of that specific data center.
            """
            
            # Create button updates based on number of results
            button_updates = []
            deep_button_updates = []
            for i in range(5):  # We have 5 buttons
                if i < len(self.search_results):
                    result = self.search_results[i]
                    title = result.get('title', 'Unknown')[:40] + '...' if len(result.get('title', '')) > 40 else result.get('title', 'Unknown')
                    button_updates.append(gr.update(visible=True, value=f"📊 Quick: {title}"))
                    deep_button_updates.append(gr.update(visible=True, value=f"🔍 Deep: {title}"))
                else:
                    button_updates.append(gr.update(visible=False))
                    deep_button_updates.append(gr.update(visible=False))
            
            return (summary, df, "Search completed successfully!") + tuple(button_updates) + tuple(deep_button_updates)
            
        except Exception as e:
            return (f"Error: {str(e)}", None, f"Search failed: {str(e)}",
                    gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                    gr.update(visible=False), gr.update(visible=False),
                    gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                    gr.update(visible=False), gr.update(visible=False))
    
    def analyze_datacenter_by_index(self, index, progress=gr.Progress()):
        """Analyze data center by its index in search results"""
        if not self.search_results or index >= len(self.search_results):
            return "No data center found at this position.", "❌ Analysis failed"
        
        try:
            progress(0, desc=f"Analyzing data center #{index + 1}...")
            
            selected_result = self.search_results[index]
            url = selected_result['link']
            title = selected_result.get('title', 'Unknown')
            
            progress(0.3, desc=f"Scraping {title[:30]}...")
            
            # Scrape detailed information
            details = self.scraper.scrape_datacenter_details(url)
            
            if not details:
                return "Failed to scrape data center details. The website might be blocking automated access.", "❌ Scraping failed"
            
            progress(0.7, desc="Processing extracted data...")
            
            # Create detailed analysis
            analysis = self.format_analysis(details, url)
            
            progress(1.0, desc="Analysis completed!")
            
            return analysis, "✅ Analysis completed successfully!"
            
        except Exception as e:
            return f"Error analyzing data center: {str(e)}", f"❌ Analysis failed: {str(e)}"
    
    def deep_analyze_datacenter_by_index(self, index, progress=gr.Progress()):
        """Perform comprehensive deep intelligence analysis on a data center"""
        if not self.search_results or index >= len(self.search_results):
            return "No data center found at this position.", "❌ Deep analysis failed"
        
        try:
            selected_result = self.search_results[index]
            url = selected_result['link']
            title = selected_result.get('title', 'Unknown')
            
            # Check cache first
            cache_key = f"{url}_{title}"
            if cache_key in self.deep_analysis_cache:
                return self.format_deep_analysis(self.deep_analysis_cache[cache_key]), "✅ Deep analysis completed (cached)!"
            
            progress(0, desc=f"🔍 Starting deep intelligence analysis...")
            
            # Define progress callback for the enhanced scraper
            def analysis_progress(prog, message):
                progress(prog, desc=f"🔍 {message}")
            
            # Perform deep analysis
            analysis_report = self.enhanced_scraper.deep_analyze_datacenter(
                selected_result, 
                progress_callback=analysis_progress
            )
            
            if 'error' in analysis_report:
                return f"Deep analysis failed: {analysis_report['error']}", "❌ Deep analysis failed"
            
            # Cache the result
            self.deep_analysis_cache[cache_key] = analysis_report
            
            progress(1.0, desc="🎉 Deep intelligence analysis completed!")
            
            # Format for display
            formatted_analysis = self.format_deep_analysis(analysis_report)
            
            return formatted_analysis, "✅ Deep intelligence analysis completed successfully!"
            
        except Exception as e:
            return f"Error performing deep analysis: {str(e)}", f"❌ Deep analysis failed: {str(e)}"
    
    def format_analysis(self, details, url):
        """Format the enhanced analysis results for display"""
        
        # Extract key information
        name = details.get('name', 'Unknown')
        location = details.get('location', 'Not found')
        capacity = details.get('capacity', 'Not found')
        power_usage = details.get('power_usage', 'Not found')
        sustainability = details.get('sustainability_info', 'Not found')
        additional_specs = details.get('additional_specs', {})
        
        # Format capacity information
        capacity_info = "Not available"
        if isinstance(capacity, dict) and capacity:
            capacity_parts = []
            if 'power_mw' in capacity:
                capacity_parts.append(f"**Power Capacity:** {capacity['power_mw']} MW")
            if 'space_sqft' in capacity:
                sqft = capacity['space_sqft']
                capacity_parts.append(f"**Floor Space:** {sqft:,} sq ft ({sqft/1000:.1f}K sq ft)")
            if 'space_acres' in capacity:
                capacity_parts.append(f"**Site Area:** {capacity['space_acres']} acres")
            if 'racks' in capacity:
                capacity_parts.append(f"**IT Racks:** {capacity['racks']:,} racks")
            capacity_info = "\n".join(capacity_parts) if capacity_parts else "Not available"
        
        # Format power usage information
        power_info = "Not available"
        if isinstance(power_usage, dict) and power_usage:
            power_parts = []
            if 'pue' in power_usage:
                pue = power_usage['pue']
                efficiency = "Excellent" if pue < 1.2 else "Good" if pue < 1.5 else "Average" if pue < 2.0 else "Poor"
                power_parts.append(f"**PUE (Power Usage Effectiveness):** {pue} ({efficiency})")
            if 'annual_consumption_mwh' in power_usage:
                consumption = power_usage['annual_consumption_mwh']
                power_parts.append(f"**Annual Energy Consumption:** {consumption:,} MWh")
            if 'renewable_percentage' in power_usage:
                renewable = power_usage['renewable_percentage']
                power_parts.append(f"**Renewable Energy:** {renewable}%")
            if 'cue' in power_usage:
                power_parts.append(f"**CUE (Cooling Usage Effectiveness):** {power_usage['cue']}")
            power_info = "\n".join(power_parts) if power_parts else "Not available"
        
        # Format location information
        location_info = "Not available"
        if isinstance(location, dict) and location:
            location_parts = []
            if 'full_address' in location:
                location_parts.append(f"**Full Address:** {location['full_address']}")
            if 'city_state' in location:
                location_parts.append(f"**City, State:** {location['city_state']}")
            if 'street_address' in location:
                location_parts.append(f"**Street Address:** {location['street_address']}")
            if 'coordinates' in location:
                location_parts.append(f"**Coordinates:** {location['coordinates']}")
            location_info = "\n".join(location_parts) if location_parts else str(location)
        elif isinstance(location, str) and location != "Location not found":
            location_info = location
        
        # Format sustainability information
        sustainability_info = "Not available"
        if isinstance(sustainability, dict) and sustainability:
            sustainability_parts = []
            
            if 'certifications' in sustainability and sustainability['certifications']:
                certs = ', '.join(sustainability['certifications'])
                sustainability_parts.append(f"**Certifications:** {certs}")
            
            if 'green_initiatives' in sustainability and sustainability['green_initiatives']:
                initiatives = ', '.join(set(sustainability['green_initiatives']))  # Remove duplicates
                sustainability_parts.append(f"**Green Initiatives:** {initiatives}")
            
            if 'carbon_metrics' in sustainability and sustainability['carbon_metrics']:
                metrics = sustainability['carbon_metrics']
                if 'annual_co2_tons' in metrics:
                    sustainability_parts.append(f"**Annual CO2 Emissions:** {metrics['annual_co2_tons']:,} tons")
                if 'co2_kg_per_kwh' in metrics:
                    sustainability_parts.append(f"**Carbon Intensity:** {metrics['co2_kg_per_kwh']} kg CO2/kWh")
                if 'water_usage' in metrics:
                    sustainability_parts.append(f"**Water Usage:** {metrics['water_usage']:,} gallons/year")
            
            score = sustainability.get('sustainability_score', 0)
            if score > 0:
                sustainability_level = "High" if score > 8 else "Medium" if score > 4 else "Low"
                sustainability_parts.append(f"**Sustainability Score:** {score}/15 ({sustainability_level})")
            
            sustainability_info = "\n".join(sustainability_parts) if sustainability_parts else "Not available"
        
        # Format additional specifications
        additional_info = "Not available"
        if additional_specs:
            additional_parts = []
            if 'network_gbps' in additional_specs:
                additional_parts.append(f"**Network Capacity:** {additional_specs['network_gbps']:,} Gbps")
            if 'redundancy' in additional_specs:
                additional_parts.append(f"**Redundancy:** {additional_specs['redundancy']}")
            if 'cooling_type' in additional_specs:
                additional_parts.append(f"**Cooling Type:** {additional_specs['cooling_type'].title()}")
            if 'security_features' in additional_specs and additional_specs['security_features']:
                security = ', '.join(additional_specs['security_features'])
                additional_parts.append(f"**Security Features:** {security}")
            additional_info = "\n".join(additional_parts) if additional_parts else "Not available"
        
        # Calculate estimated carbon footprint
        carbon_estimate = self.calculate_carbon_footprint_estimate(capacity, power_usage)
        
        analysis = f"""
# 🏢 Data Center Analysis Report

## 📍 Basic Information
**Name:** {name}  
**Location:** {location_info}  
**Source URL:** {url}  
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## ⚡ Capacity & Infrastructure
{capacity_info}

## 🔌 Power & Energy Usage
{power_info}

## 🌱 Sustainability & Environmental Impact
{sustainability_info}

## 🔧 Technical Specifications
{additional_info}

## 📊 Carbon Footprint Estimate
{carbon_estimate}

---
*Analysis performed using enhanced SERP API and web scraping algorithms*
        """
        
        return analysis
    
    def calculate_carbon_footprint_estimate(self, capacity, power_usage):
        """Calculate estimated carbon footprint based on available data"""
        if not isinstance(capacity, dict) or not capacity.get('power_mw'):
            return "**Insufficient data for carbon footprint calculation**"
        
        power_mw = capacity['power_mw']
        pue = power_usage.get('pue', 1.5) if isinstance(power_usage, dict) else 1.5
        renewable_pct = power_usage.get('renewable_percentage', 20) if isinstance(power_usage, dict) else 20
        
        # US average grid carbon intensity (kg CO2/MWh)
        grid_carbon_intensity = 400
        
        # Calculate annual energy consumption
        annual_energy_mwh = power_mw * 8760 * pue
        
        # Calculate carbon footprint considering renewable energy
        non_renewable_pct = (100 - renewable_pct) / 100
        annual_carbon_tons = (annual_energy_mwh * grid_carbon_intensity * non_renewable_pct) / 1000
        
        return f"""**Estimated Annual Carbon Footprint:** {annual_carbon_tons:,.1f} tons CO2  
**Based on:** {power_mw} MW capacity, {pue} PUE, {renewable_pct}% renewable energy  
**Methodology:** US grid average carbon intensity with renewable energy offset
        
*Note: This is an estimate based on available data and industry averages.*"""
    
    def format_deep_analysis(self, analysis_report):
        """Format the comprehensive deep analysis results for display"""
        
        if 'error' in analysis_report:
            return f"❌ **Deep Analysis Error:** {analysis_report['error']}"
        
        # Extract main components
        intelligence = analysis_report.get('intelligence_data', {})
        basic_info = intelligence.get('basic_info', {})
        supplier_info = intelligence.get('supplier_info', {})
        market_value = intelligence.get('market_value', {})
        tech_specs = intelligence.get('technical_specs', {})
        financial_data = intelligence.get('financial_intelligence', {})
        competitive_analysis = intelligence.get('competitive_analysis', {})
        news_sentiment = intelligence.get('news_sentiment', {})
        certifications = intelligence.get('certifications', {})
        partnerships = intelligence.get('partnerships', {})
        expansion_plans = intelligence.get('expansion_plans', {})
        
        # Create comprehensive report
        analysis = f"""
# 🧠 DEEP INTELLIGENCE ANALYSIS REPORT

## 📋 Executive Summary
{analysis_report.get('executive_summary', 'Executive summary not available')}

---

## 🏢 Facility Intelligence
**Name:** {basic_info.get('name', 'Unknown')}  
**Location:** {basic_info.get('location', 'Unknown')}  
**Analysis Date:** {analysis_report.get('analysis_timestamp', 'Unknown')}  
**Source URL:** {basic_info.get('url', 'Unknown')}

---

## 💰 Market Intelligence & Valuation
**Estimated Investment:** {market_value.get('estimated_investment', 'Not calculated')}  
**Market Position:** {market_value.get('market_position', 'Unknown')}  
**Revenue Estimate:** {market_value.get('revenue_estimate', 'Not available')}  
**Competitive Ranking:** {market_value.get('competitive_ranking', 'Unknown')}

### Market Intelligence Insights
"""
        
        # Add market intelligence items
        market_intel = market_value.get('market_intelligence', [])
        if market_intel:
            for i, intel in enumerate(market_intel[:3], 1):
                analysis += f"**{i}.** {intel.get('title', 'Market insight')}\n   *{intel.get('description', 'No description')[:150]}...*\n\n"
        else:
            analysis += "*No specific market intelligence found*\n\n"
        
        analysis += """---

## 🏭 Supplier Ecosystem Analysis
"""
        
        # Add supplier information
        total_suppliers = sum(len(supplier_info.get(key, [])) for key in supplier_info if isinstance(supplier_info.get(key), list))
        analysis += f"**Total Suppliers Identified:** {total_suppliers}\n\n"
        
        for category, suppliers in supplier_info.items():
            if isinstance(suppliers, list) and suppliers:
                category_name = category.replace('_', ' ').title()
                analysis += f"**{category_name}:** {len(suppliers)} identified\n"
                for supplier in suppliers[:2]:  # Show top 2
                    if isinstance(supplier, dict):
                        analysis += f"  • {supplier.get('name', 'Unknown')}\n"
        
        analysis += f"\n**Analysis Confidence:** {supplier_info.get('analysis_confidence', 0)*100:.0f}%\n\n"
        
        analysis += """---

## ⚡ Enhanced Technical Specifications
"""
        
        # Add technical specifications
        for category, specs in tech_specs.items():
            if category != 'analysis_confidence' and specs:
                category_name = category.replace('_', ' ').title()
                analysis += f"**{category_name}:** "
                if isinstance(specs, dict):
                    analysis += f"{len(specs)} specifications found\n"
                elif isinstance(specs, list):
                    analysis += f"{len(specs)} items\n"
                else:
                    analysis += f"{specs}\n"
        
        analysis += f"\n**Technical Analysis Confidence:** {tech_specs.get('analysis_confidence', 0)*100:.0f}%\n\n"
        
        analysis += """---

## 🏆 Competitive Landscape Analysis
"""
        
        # Add competitive analysis
        competitors = competitive_analysis.get('direct_competitors', [])
        analysis += f"**Direct Competitors Identified:** {len(competitors)}\n\n"
        
        if competitors:
            analysis += "**Key Competitors:**\n"
            for comp in competitors[:5]:  # Show top 5
                if isinstance(comp, dict):
                    analysis += f"  • {comp.get('name', 'Unknown')}\n"
        
        market_leaders = competitive_analysis.get('market_leaders', [])
        if market_leaders:
            analysis += f"\n**Market Leaders:** {len(market_leaders)} identified\n"
        
        analysis += f"\n**Competitive Analysis Confidence:** {competitive_analysis.get('analysis_confidence', 0)*100:.0f}%\n\n"
        
        analysis += """---

## 📰 News Sentiment & Media Analysis
"""
        
        # Add news and sentiment analysis
        articles = news_sentiment.get('recent_articles', [])
        sentiment_score = news_sentiment.get('sentiment_score', 0)
        
        analysis += f"**Recent Articles Found:** {len(articles)}\n"
        analysis += f"**Sentiment Score:** {sentiment_score:.2f} "
        
        if sentiment_score > 0.3:
            analysis += "(Positive 😊)\n"
        elif sentiment_score < -0.3:
            analysis += "(Negative 😟)\n"
        else:
            analysis += "(Neutral 😐)\n"
        
        analysis += f"**Media Coverage Score:** {news_sentiment.get('media_coverage_score', 0)*100:.0f}%\n"
        
        # Show recent developments
        developments = news_sentiment.get('key_developments', [])
        if developments:
            analysis += f"\n**Key Developments:**\n"
            for dev in developments[:3]:
                if isinstance(dev, dict):
                    analysis += f"  • **{dev.get('type', 'Update').title()}:** {dev.get('description', 'No description')[:100]}...\n"
        
        analysis += f"\n**News Analysis Confidence:** {news_sentiment.get('analysis_confidence', 0)*100:.0f}%\n\n"
        
        analysis += """---

## 🎖️ Certifications & Compliance
"""
        
        # Add certifications
        total_certs = sum(len(certifications.get(key, [])) for key in certifications if isinstance(certifications.get(key), list))
        analysis += f"**Total Certifications Found:** {total_certs}\n\n"
        
        for category, certs in certifications.items():
            if isinstance(certs, list) and certs:
                category_name = category.replace('_', ' ').title()
                analysis += f"**{category_name}:** {', '.join(set(certs))}\n"
        
        analysis += f"\n**Certification Analysis Confidence:** {certifications.get('analysis_confidence', 0)*100:.0f}%\n\n"
        
        analysis += """---

## 🤝 Strategic Partnerships
"""
        
        # Add partnerships
        total_partnerships = sum(len(partnerships.get(key, [])) for key in partnerships if isinstance(partnerships.get(key), list))
        analysis += f"**Total Partnerships Identified:** {total_partnerships}\n\n"
        
        for category, partners in partnerships.items():
            if isinstance(partners, list) and partners:
                category_name = category.replace('_', ' ').title()
                analysis += f"**{category_name}:** {len(partners)} partnerships\n"
        
        analysis += f"\n**Partnership Analysis Confidence:** {partnerships.get('analysis_confidence', 0)*100:.0f}%\n\n"
        
        analysis += """---

## 🚀 Growth & Expansion Intelligence
"""
        
        # Add expansion plans
        total_plans = sum(len(expansion_plans.get(key, [])) for key in expansion_plans if isinstance(expansion_plans.get(key), list))
        analysis += f"**Growth Initiatives Identified:** {total_plans}\n\n"
        
        for category, plans in expansion_plans.items():
            if isinstance(plans, list) and plans:
                category_name = category.replace('_', ' ').title()
                analysis += f"**{category_name}:** {len(plans)} initiatives\n"
                for plan in plans[:2]:  # Show top 2
                    if isinstance(plan, dict):
                        analysis += f"  • {plan.get('description', 'No description')[:100]}...\n"
        
        analysis += f"\n**Expansion Analysis Confidence:** {expansion_plans.get('analysis_confidence', 0)*100:.0f}%\n\n"
        
        analysis += """---

## 💡 Strategic Recommendations
"""
        
        # Add recommendations
        recommendations = analysis_report.get('recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                analysis += f"**{i}.** {rec}\n"
        else:
            analysis += "*No specific recommendations generated*\n"
        
        analysis += """

---

## 📊 Analysis Confidence Score
"""
        
        # Add confidence information
        confidence = analysis_report.get('analysis_confidence', {})
        overall_score = confidence.get('overall_score', 0)
        confidence_level = confidence.get('confidence_level', 'Unknown')
        
        analysis += f"**Overall Confidence:** {overall_score*100:.0f}% ({confidence_level})\n\n"
        
        # Add component scores
        component_scores = confidence.get('component_scores', {})
        if component_scores:
            analysis += "**Component Confidence Scores:**\n"
            for component, score in component_scores.items():
                if isinstance(score, (int, float)):
                    component_name = component.replace('_', ' ').title()
                    analysis += f"  • {component_name}: {score*100:.0f}%\n"
        
        analysis += """

---

**🎯 Analysis Method:** SERP-powered intelligence gathering with multi-source cross-validation  
**📅 Generated:** Real-time analysis  
**🔄 Cache Status:** Results cached for performance optimization
        
*This comprehensive analysis combines public data sources, industry intelligence, and market research to provide strategic insights into datacenter operations and market positioning.*
"""
        
        return analysis
    
    def create_visualization_data(self, details):
        """Create visualization data for the analyzed data center"""
        
        # Extract numeric values for visualization
        viz_data = {
            'sustainability_score': 0,
            'capacity_mw': 0,
            'pue': 0,
            'renewable_percentage': 0
        }
        
        # Extract sustainability score
        sustainability = details.get('sustainability_info', {})
        if isinstance(sustainability, dict):
            viz_data['sustainability_score'] = sustainability.get('sustainability_score', 0)
        
        # Extract capacity and power data
        capacity = details.get('capacity', {})
        power_usage = details.get('power_usage', {})
        
        if isinstance(capacity, dict):
            power_mw = capacity.get('power_mw', '0')
            try:
                viz_data['capacity_mw'] = float(str(power_mw).replace(',', '')) if power_mw else 0
            except:
                viz_data['capacity_mw'] = 0
        
        if isinstance(power_usage, dict):
            pue = power_usage.get('pue', '0')
            renewable = power_usage.get('renewable_percentage', '0')
            
            try:
                viz_data['pue'] = float(str(pue)) if pue else 0
            except:
                viz_data['pue'] = 0
            
            try:
                viz_data['renewable_percentage'] = float(str(renewable)) if renewable else 0
            except:
                viz_data['renewable_percentage'] = 0
        
        return viz_data
    
    def create_dashboard_plot(self, viz_data):
        """Create a dashboard visualization"""
        if not viz_data:
            return None
        
        # Create subplots
        fig = go.Figure()
        
        # Sustainability Score Gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=viz_data['sustainability_score'],
            domain={'x': [0, 0.5], 'y': [0.5, 1]},
            title={'text': "Sustainability Score"},
            gauge={
                'axis': {'range': [None, 12]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 4], 'color': "lightgray"},
                    {'range': [4, 8], 'color': "yellow"},
                    {'range': [8, 12], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 10
                }
            }
        ))
        
        # Capacity Bar
        if viz_data['capacity_mw'] > 0:
            fig.add_trace(go.Bar(
                x=['Capacity (MW)'],
                y=[viz_data['capacity_mw']],
                name='Capacity',
                marker_color='blue'
            ))
        
        fig.update_layout(
            title="Data Center Metrics Dashboard",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def batch_analyze_regions(self, regions_text, num_results_per_region, progress=gr.Progress()):
        """Analyze multiple regions and create summary"""
        if not regions_text.strip():
            return "Please enter at least one region", None, "No input"
        
        regions = [r.strip() for r in regions_text.split(',') if r.strip()]
        
        if not regions:
            return "Please enter valid region names separated by commas", None, "Invalid input"
        
        try:
            all_results = []
            total_steps = len(regions) * 2  # Search + analyze
            current_step = 0
            
            for region in regions:
                progress(current_step / total_steps, desc=f"Searching {region}...")
                
                # Search for data centers in region
                results = self.scraper.search_datacenters(region, num_results_per_region)
                current_step += 1
                
                if results and results.get('results'):
                    progress(current_step / total_steps, desc=f"Analyzing {region} data centers...")
                    
                    for result in results['results'][:2]:  # Analyze top 2 results per region
                        details = self.scraper.scrape_datacenter_details(result['link'])
                        if details:
                            result_data = {
                                'Region': region,
                                'Name': details.get('name', 'Unknown'),
                                'Location': details.get('location', 'Unknown'),
                                'URL': result['link'],
                                'Sustainability Score': self.extract_sustainability_score(details),
                                'Search Snippet': result.get('snippet', '')[:100] + '...'
                            }
                            all_results.append(result_data)
                        
                        # Small delay to avoid overwhelming servers
                        time.sleep(1)
                
                current_step += 1
                # Delay between regions
                time.sleep(2)
            
            if not all_results:
                return "No data centers found in the specified regions", None, "No results"
            
            # Create summary DataFrame
            df = pd.DataFrame(all_results)
            
            # Create summary report
            summary = f"""
# Multi-Region Data Center Analysis

**Regions Analyzed:** {', '.join(regions)}  
**Total Data Centers Found:** {len(all_results)}  
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics
- **Average Sustainability Score:** {df['Sustainability Score'].mean():.1f}
- **Regions with Most Data Centers:** {df['Region'].value_counts().head(3).to_dict()}

The table below shows all discovered data centers with their basic information.
            """
            
            progress(1.0, desc="Analysis completed!")
            
            return summary, df, "Multi-region analysis completed!"
            
        except Exception as e:
            return f"Error in batch analysis: {str(e)}", None, f"Batch analysis failed: {str(e)}"
    
    def extract_sustainability_score(self, details):
        """Extract sustainability score from details"""
        sustainability = details.get('sustainability_info', {})
        if isinstance(sustainability, dict):
            return sustainability.get('sustainability_score', 0)
        return 0
    
    def search_equinix_datacenters(self, query, progress=gr.Progress()):
        """Search Equinix data centers by city, country, or region"""
        try:
            progress(0, desc="Starting Equinix search...")
            
            # Try searching by city first
            results = self.equinix_scraper.search_by_city(query)
            
            # If no city results, try country
            if not results:
                progress(0.3, desc="Searching by country...")
                results = self.equinix_scraper.search_by_country(query)
            
            # If still no results, search in all regions
            if not results:
                progress(0.6, desc="Searching all regions...")
                all_cities = self.equinix_scraper.get_all_cities()
                query_lower = query.lower()
                
                # Search in region names too
                region_matches = []
                if 'america' in query_lower:
                    region_matches.extend(self.equinix_scraper.scrape_region('Americas', max_cities=5))
                elif 'europe' in query_lower or 'emea' in query_lower:
                    region_matches.extend(self.equinix_scraper.scrape_region('Europe_Middle_East_Africa', max_cities=5))
                elif 'asia' in query_lower or 'pacific' in query_lower:
                    region_matches.extend(self.equinix_scraper.scrape_region('Asia_Pacific', max_cities=5))
                
                results.extend(region_matches)
            
            progress(0.8, desc="Processing results...")
            
            if not results:
                return (
                    f"No Equinix data centers found for '{query}'",
                    None,
                    "No results found",
                    gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                    gr.update(visible=False), gr.update(visible=False)
                )
            
            # Filter out error results
            valid_results = [r for r in results if 'error' not in r]
            
            if not valid_results:
                return (
                    f"Error retrieving data for '{query}'",
                    None,
                    "Data retrieval failed",
                    gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                    gr.update(visible=False), gr.update(visible=False)
                )
            
            # Store results for analysis
            self.search_results = valid_results
            
            # Create DataFrame
            df_data = []
            for result in valid_results:
                df_data.append({
                    'City': result.get('city', 'Unknown'),
                    'Country': result.get('country', 'Unknown'),
                    'Region': result.get('region', 'Unknown'),
                    'Facilities': result.get('total_facilities', 0),
                    'Services': ', '.join(result.get('services', [])[:3]),
                    'Certifications': ', '.join(result.get('certifications', [])[:3]),
                    'Green Score': result.get('sustainability', {}).get('green_score', 0),
                    'Connectivity Score': result.get('connectivity', {}).get('connectivity_score', 0)
                })
            
            df = pd.DataFrame(df_data)
            
            # Create summary
            total_facilities = sum(r.get('total_facilities', 0) for r in valid_results)
            unique_countries = len(set(r.get('country', '') for r in valid_results))
            
            summary = f"""
            ## Equinix Search Results for "{query}"
            
            **Total Cities Found:** {len(valid_results)}  
            **Total Facilities:** {total_facilities}  
            **Countries Covered:** {unique_countries}  
            **Search Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            ### Equinix Data Centers
            Use the buttons below to analyze specific facilities or get detailed information.
            """
            
            # Create button updates based on number of results
            button_updates = []
            for i in range(5):  # We have 5 buttons
                if i < len(valid_results):
                    result = valid_results[i]
                    city_name = result.get('city', 'Unknown')[:30] + '...' if len(result.get('city', '')) > 30 else result.get('city', 'Unknown')
                    button_updates.append(gr.update(visible=True, value=f"📊 Analyze: {city_name}"))
                else:
                    button_updates.append(gr.update(visible=False))
            
            progress(1.0, desc="Search completed!")
            
            return (summary, df, "Equinix search completed successfully!") + tuple(button_updates)
            
        except Exception as e:
            return (f"Error: {str(e)}", None, f"Equinix search failed: {str(e)}",
                    gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                    gr.update(visible=False), gr.update(visible=False))
    
    def analyze_equinix_datacenter_by_index(self, index, progress=gr.Progress()):
        """Analyze Equinix data center by its index in search results"""
        try:
            progress(0, desc="Starting Equinix analysis...")
            
            if not self.search_results or index >= len(self.search_results):
                return "No data center found at this index.", "Analysis failed"
            
            datacenter = self.search_results[index]
            
            if 'error' in datacenter:
                return f"Error in data: {datacenter['error']}", "Data error"
            
            progress(0.5, desc="Formatting comprehensive analysis...")
            
            # Format detailed analysis with enhanced information
            analysis = f"""
            # 🏢 Equinix Data Center Comprehensive Analysis
            
            ## � **{datacenter.get('city', 'Unknown')}, {datacenter.get('country', 'Unknown')}**
            
            ### 📍 Location & Regional Details
            - **Region:** {datacenter.get('region', 'Unknown')}
            - **Total Facilities in City:** {datacenter.get('total_facilities', 0)}
            - **Data Center Codes:** {', '.join([f['code'] for f in datacenter.get('facilities', [])])}
            - **Official URL:** [{datacenter.get('url', 'Not available')}]({datacenter.get('url', '')})
            
            ### 🏭 Individual Facility Details
            """
            
            # Add detailed facility information if available
            detailed_facilities = datacenter.get('detailed_facilities', [])
            if detailed_facilities:
                for facility in detailed_facilities:
                    if 'error' not in facility:
                        analysis += f"""
            #### 🏢 **{facility.get('code', 'Unknown')} - {facility.get('name', 'Unknown')}**
            
            **Address:** {facility.get('address', 'Not available')}
            
            **Electrical System Redundancy:** {facility.get('electrical_redundancy', 'Not available')}
            
            **Cooling Redundancy:** {facility.get('cooling_redundancy', 'Not available')}
            
            **Specifications:**
            """
                        specs = facility.get('specifications', {})
                        if specs:
                            for spec_name, value in specs.items():
                                readable_name = spec_name.replace('_', ' ').title()
                                analysis += f"- **{readable_name}:** {value}\n"
                        else:
                            analysis += "- No detailed specifications available\n"
                        
                        # Add certifications
                        certifications = facility.get('certifications', [])
                        if certifications:
                            analysis += "\n**Certifications:**\n"
                            for cert in certifications:
                                analysis += f"- {cert}\n"
                        
                        # Add amenities  
                        amenities = facility.get('amenities', [])
                        if amenities:
                            analysis += "\n**Amenities:**\n"
                            for amenity in amenities:
                                analysis += f"- {amenity}\n"
                        
                        # Add IBX highlights if available
                        highlights = facility.get('ibx_highlights', '')
                        if highlights:
                            analysis += f"\n**IBX Highlights:**\n{highlights}\n"
                        
                        # Add facility features
                        features = facility.get('facility_features', [])
                        if features:
                            analysis += "\n**Facility Features:**\n"
                            for feature in features[:5]:  # Limit to first 5
                                analysis += f"- {feature}\n"
                        
                        # Add services offered
                        services = facility.get('services_offered', [])
                        if services:
                            analysis += f"\n**Services:** {', '.join(services)}\n"
                        
                        # Add connectivity details
                        connectivity = facility.get('connectivity_details', {})
                        if connectivity:
                            analysis += "\n**Connectivity:**\n"
                            for conn_name, value in connectivity.items():
                                readable_name = conn_name.replace('_', ' ').title()
                                analysis += f"- **{readable_name}:** {value}\n"
                        
                        # Add source URL if available
                        source_url = facility.get('source_url', '')
                        if source_url:
                            analysis += f"\n**Source:** [Official Equinix Page]({source_url})\n"
                        
                        analysis += "\n---\n"
            else:
                analysis += "- Individual facility details not available (enable detailed scraping for more information)\n\n"
            
            analysis += f"""
            ### 🛠️ Services & Capabilities Overview
            {chr(10).join([f"- **{service}**" for service in datacenter.get('services', ['No services data available'])])}
            
            ### 🏅 Certifications & Compliance
            {chr(10).join([f"- **{cert}**" for cert in datacenter.get('certifications', ['No certifications data available'])])}
            
            ### 🌱 Sustainability & Green Initiatives
            - **Green Score:** {datacenter.get('sustainability', {}).get('green_score', 0)}/10
            - **Has Green Initiatives:** {datacenter.get('sustainability', {}).get('has_green_initiatives', False)}
            
            **Green Features:**
            {chr(10).join([f"- {feature}" for feature in datacenter.get('sustainability', {}).get('features', ['No green features identified'])])}
            
            ### 🌐 Connectivity Ecosystem
            - **Connectivity Score:** {datacenter.get('connectivity', {}).get('connectivity_score', 0)}/10
            - **Rich Ecosystem:** {datacenter.get('connectivity', {}).get('ecosystem_rich', False)}
            
            **Ecosystem Types:**
            {chr(10).join([f"- {eco_type.title()}" for eco_type in datacenter.get('connectivity', {}).get('ecosystem_types', ['No ecosystem data available'])])}
            
            ### 📊 Key Market Statistics
            """
            
            # Add key stats if available
            key_stats = datacenter.get('key_stats', {})
            if key_stats:
                for stat_name, value in key_stats.items():
                    readable_name = stat_name.replace('_', ' ').title()
                    analysis += f"- **{readable_name}:** {value:,}\n"
            else:
                analysis += "- No detailed market statistics available\n"
            
            # Add summary metrics
            total_services = len(datacenter.get('services', []))
            total_certs = len(datacenter.get('certifications', []))
            green_score = datacenter.get('sustainability', {}).get('green_score', 0)
            conn_score = datacenter.get('connectivity', {}).get('connectivity_score', 0)
            
            analysis += f"""
            
            ### � Analysis Summary
            - **Service Portfolio Strength:** {total_services}/7 core services
            - **Compliance Level:** {total_certs}/6 major certifications
            - **Sustainability Rating:** {green_score}/10
            - **Connectivity Rating:** {conn_score}/10
            - **Overall Facility Score:** {(total_services + total_certs + green_score + conn_score)/3.4:.1f}/10
            
            ### 🔗 Source Information
            - **Data Source:** Official Equinix Website
            - **Last Updated:** {datacenter.get('scraped_at', 'Unknown')}
            - **Analysis Method:** Multi-pattern extraction with facility-specific parsing
            
            ---
            *Comprehensive Analysis by DataRackNews Equinix Intelligence Engine*
            
            **Recommendation:** {'🟢 Excellent connectivity and service portfolio' if (total_services + conn_score) > 8 else '🟡 Good facility with growth potential' if (total_services + conn_score) > 5 else '🔴 Limited service information available'}
            """
            
            progress(1.0, desc="Analysis completed!")
            return analysis, "✅ Comprehensive Equinix analysis completed successfully!"
            
        except Exception as e:
            return f"Analysis error: {str(e)}", "❌ Analysis failed"


def create_gradio_interface():
    """Create the main Gradio interface"""
    
    ui = DataCenterUI()
    
    with gr.Blocks(title="DataRackNews - Data Center Tracker", theme=gr.themes.Soft()) as interface:
        
        gr.Markdown("""
        # 🏢 DataRackNews - Data Center Search & Analysis
        
        Track data centers and their carbon footprints with real-time search capabilities.
        
        **Features:**
        - Search data centers by region using SERP API
        - Analyze sustainability metrics and carbon footprints
        - Batch analysis across multiple regions
        - Export results for further analysis
        """)
        
        with gr.Tabs():
            
            # Tab 1: Single Region Search
            with gr.TabItem("🔍 Search Data Centers"):
                
                with gr.Row():
                    with gr.Column(scale=1):
                        region_input = gr.Textbox(
                            label="Region/Location", 
                            placeholder="e.g., Virginia, California, Texas",
                            value="Virginia"
                        )
                        num_results = gr.Slider(
                            minimum=1, 
                            maximum=20, 
                            value=5, 
                            step=1,
                            label="Number of Results"
                        )
                        search_btn = gr.Button("🔍 Search Data Centers", variant="primary")
                    
                    with gr.Column(scale=2):
                        search_status = gr.Textbox(label="Status", interactive=False)
                
                search_summary = gr.Markdown()
                search_results_table = gr.Dataframe(
                    label="Search Results",
                    interactive=False,
                    wrap=True
                )
                
                # Quick Analysis Section - Show buttons for each result
                gr.Markdown("## � Quick Analysis")
                gr.Markdown("Click any button below to analyze that specific data center:")
                
                with gr.Row():
                    analyze_btn_1 = gr.Button("📊 Analyze Result #1", visible=False, variant="secondary", size="sm")
                    analyze_btn_2 = gr.Button("📊 Analyze Result #2", visible=False, variant="secondary", size="sm")
                    analyze_btn_3 = gr.Button("📊 Analyze Result #3", visible=False, variant="secondary", size="sm")
                
                with gr.Row():
                    analyze_btn_4 = gr.Button("📊 Analyze Result #4", visible=False, variant="secondary", size="sm")
                    analyze_btn_5 = gr.Button("📊 Analyze Result #5", visible=False, variant="secondary", size="sm")
                
                # Deep Analysis Buttons
                gr.Markdown("### 🔍 Deep Intelligence Analysis")
                gr.Markdown("Comprehensive analysis including market intelligence, supplier ecosystem, competitive landscape, and more:")
                
                with gr.Row():
                    deep_analyze_btn_1 = gr.Button("🔍 Deep Analysis #1", visible=False, variant="primary", size="sm")
                    deep_analyze_btn_2 = gr.Button("🔍 Deep Analysis #2", visible=False, variant="primary", size="sm")
                    deep_analyze_btn_3 = gr.Button("🔍 Deep Analysis #3", visible=False, variant="primary", size="sm")
                
                with gr.Row():
                    deep_analyze_btn_4 = gr.Button("🔍 Deep Analysis #4", visible=False, variant="primary", size="sm")
                    deep_analyze_btn_5 = gr.Button("🔍 Deep Analysis #5", visible=False, variant="primary", size="sm")
                
                analysis_status = gr.Textbox(label="Analysis Status", interactive=False)
                analysis_results = gr.Markdown()
            
            # Tab 2: Multi-Region Analysis
            with gr.TabItem("🌍 Multi-Region Analysis"):
                
                with gr.Row():
                    with gr.Column():
                        regions_input = gr.Textbox(
                            label="Regions (comma-separated)",
                            placeholder="Virginia, California, Texas, New York",
                            lines=3,
                            value="Virginia, California"
                        )
                        batch_num_results = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=3,
                            step=1,
                            label="Results per Region"
                        )
                        batch_analyze_btn = gr.Button("🚀 Start Batch Analysis", variant="primary")
                    
                    with gr.Column():
                        batch_status = gr.Textbox(label="Batch Status", interactive=False)
                
                batch_summary = gr.Markdown()
                batch_results_table = gr.Dataframe(label="Multi-Region Results")
            
            # Tab 3: Equinix Data Centers
            with gr.TabItem("🏢 Equinix Data Centers"):
                gr.Markdown("""
                ## 🏢 Official Equinix Data Center Search
                
                Search through Equinix's official data center network across Americas, EMEA, and Asia-Pacific regions.
                Get detailed information about facilities, services, certifications, and connectivity.
                """)
                
                with gr.Row():
                    with gr.Column(scale=1):
                        equinix_query = gr.Textbox(
                            label="Search Query", 
                            placeholder="e.g., New York, Brazil, London, Asia",
                            value="New York"
                        )
                        equinix_search_btn = gr.Button("🔍 Search Equinix", variant="primary")
                    
                    with gr.Column(scale=2):
                        equinix_status = gr.Textbox(label="Status", interactive=False)
                
                equinix_summary = gr.Markdown()
                equinix_results_table = gr.Dataframe(
                    label="Equinix Data Centers",
                    interactive=False,
                    wrap=True
                )
                
                # Equinix Analysis Buttons
                gr.Markdown("### 🔍 Detailed Analysis")
                gr.Markdown("Click any button below to get detailed information about specific Equinix data centers:")
                
                with gr.Row():
                    equinix_analyze_btn_1 = gr.Button("📊 Analyze #1", visible=False, variant="secondary", size="sm")
                    equinix_analyze_btn_2 = gr.Button("📊 Analyze #2", visible=False, variant="secondary", size="sm")
                    equinix_analyze_btn_3 = gr.Button("📊 Analyze #3", visible=False, variant="secondary", size="sm")
                    equinix_analyze_btn_4 = gr.Button("📊 Analyze #4", visible=False, variant="secondary", size="sm")
                    equinix_analyze_btn_5 = gr.Button("📊 Analyze #5", visible=False, variant="secondary", size="sm")
                
                equinix_analysis_status = gr.Textbox(label="Analysis Status", interactive=False)
                equinix_analysis_results = gr.Markdown()
            
            # Tab 4: Data Export
            with gr.TabItem("💾 Export Data"):
                gr.Markdown("""
                ## Export Your Data
                
                After running searches and analyses, you can export your data in various formats.
                """)
                
                with gr.Row():
                    export_csv_btn = gr.Button("📁 Export to CSV")
                    export_json_btn = gr.Button("📄 Export to JSON")
                
                export_status = gr.Textbox(label="Export Status", interactive=False)
        
        # Event handlers
        search_btn.click(
            fn=ui.search_datacenters,
            inputs=[region_input, num_results],
            outputs=[search_summary, search_results_table, search_status, 
                    analyze_btn_1, analyze_btn_2, analyze_btn_3, analyze_btn_4, analyze_btn_5,
                    deep_analyze_btn_1, deep_analyze_btn_2, deep_analyze_btn_3, deep_analyze_btn_4, deep_analyze_btn_5]
        )
        
        # Analysis button event handlers
        analyze_btn_1.click(
            fn=lambda: ui.analyze_datacenter_by_index(0),
            inputs=[],
            outputs=[analysis_results, analysis_status]
        )
        
        analyze_btn_2.click(
            fn=lambda: ui.analyze_datacenter_by_index(1),
            inputs=[],
            outputs=[analysis_results, analysis_status]
        )
        
        analyze_btn_3.click(
            fn=lambda: ui.analyze_datacenter_by_index(2),
            inputs=[],
            outputs=[analysis_results, analysis_status]
        )
        
        analyze_btn_4.click(
            fn=lambda: ui.analyze_datacenter_by_index(3),
            inputs=[],
            outputs=[analysis_results, analysis_status]
        )
        
        analyze_btn_5.click(
            fn=lambda: ui.analyze_datacenter_by_index(4),
            inputs=[],
            outputs=[analysis_results, analysis_status]
        )
        
        # Deep Analysis button event handlers
        deep_analyze_btn_1.click(
            fn=lambda: ui.deep_analyze_datacenter_by_index(0),
            inputs=[],
            outputs=[analysis_results, analysis_status]
        )
        
        deep_analyze_btn_2.click(
            fn=lambda: ui.deep_analyze_datacenter_by_index(1),
            inputs=[],
            outputs=[analysis_results, analysis_status]
        )
        
        deep_analyze_btn_3.click(
            fn=lambda: ui.deep_analyze_datacenter_by_index(2),
            inputs=[],
            outputs=[analysis_results, analysis_status]
        )
        
        deep_analyze_btn_4.click(
            fn=lambda: ui.deep_analyze_datacenter_by_index(3),
            inputs=[],
            outputs=[analysis_results, analysis_status]
        )
        
        deep_analyze_btn_5.click(
            fn=lambda: ui.deep_analyze_datacenter_by_index(4),
            inputs=[],
            outputs=[analysis_results, analysis_status]
        )
        
        batch_analyze_btn.click(
            fn=ui.batch_analyze_regions,
            inputs=[regions_input, batch_num_results],
            outputs=[batch_summary, batch_results_table, batch_status]
        )
        
        # Equinix search functionality
        equinix_search_btn.click(
            fn=ui.search_equinix_datacenters,
            inputs=[equinix_query],
            outputs=[equinix_summary, equinix_results_table, equinix_status,
                    equinix_analyze_btn_1, equinix_analyze_btn_2, equinix_analyze_btn_3, 
                    equinix_analyze_btn_4, equinix_analyze_btn_5]
        )
        
        # Equinix analysis button handlers
        equinix_analyze_btn_1.click(
            fn=lambda: ui.analyze_equinix_datacenter_by_index(0),
            inputs=[],
            outputs=[equinix_analysis_results, equinix_analysis_status]
        )
        
        equinix_analyze_btn_2.click(
            fn=lambda: ui.analyze_equinix_datacenter_by_index(1),
            inputs=[],
            outputs=[equinix_analysis_results, equinix_analysis_status]
        )
        
        equinix_analyze_btn_3.click(
            fn=lambda: ui.analyze_equinix_datacenter_by_index(2),
            inputs=[],
            outputs=[equinix_analysis_results, equinix_analysis_status]
        )
        
        equinix_analyze_btn_4.click(
            fn=lambda: ui.analyze_equinix_datacenter_by_index(3),
            inputs=[],
            outputs=[equinix_analysis_results, equinix_analysis_status]
        )
        
        equinix_analyze_btn_5.click(
            fn=lambda: ui.analyze_equinix_datacenter_by_index(4),
            inputs=[],
            outputs=[equinix_analysis_results, equinix_analysis_status]
        )
        
        # Footer
        gr.Markdown("""
        ---
        **DataRackNews** - Powered by SERP API | Built with Gradio
        """)
    
    return interface


if __name__ == "__main__":
    # Create and launch the interface
    interface = create_gradio_interface()
    
    # Docker-friendly configuration
    import os
    server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")  # Bind to all interfaces for Docker
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    
    interface.launch(
        server_name=server_name,
        server_port=server_port,
        share=False,  # Set to True if you want to create a public link
        debug=True
    )
