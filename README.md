# DataRackNews
Real-time monitoring of data center infrastructure costs, environmental impact, and market intelligence with comprehensive analysis across European facilities.

<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/ab4003d6-e229-4aa1-812c-5c5bfc578c0a" />

---

## Overview
DataRackNews is a comprehensive data center intelligence platform that provides:

- **Real Data Center Discovery**: Multi-vendor scraping from DataCenters.com, Digital Realty, and Equinix
- **Energy & Carbon Analysis**: Real-time carbon intensity data using SerpAPI Google AI Mode
- **EU Compliance Intelligence**: Automated assessment for EU Regulation 2024/1364 (≥500kW threshold)
- **Financial Market Analysis**: Real-time operator stock data and news sentiment analysis
- **Economic Impact Modeling**: 10-year cost projections with country-specific electricity pricing
- **Database-Ready Output**: Structured JSON payloads for data centers, metrics, and news articles

The platform combines web scraping, AI-powered search, and financial APIs to deliver actionable intelligence for data center operators, investors, and sustainability professionals.

## Quick Start

### Prerequisites
1. **Python 3.10+**
2. **Required Dependencies**:
   ```bash
   pip install requests beautifulsoup4 python-dotenv
   ```

### Basic Usage
1. **Create Environment File**: Copy the `.env` template below and add your API keys
2. **Run Analysis**: Execute the orchestrator with your target location

```bash
# Basic analysis for a country
python orchestrator.py --country spain

# City-specific analysis with news enrichment
python orchestrator.py --country france --city paris --include-news --output payload.paris.json

# Full analysis with geocoding
python orchestrator.py --country germany --city berlin --include-news --geocode --email your@email.com
```

### Output
The system generates structured JSON payloads containing:
- **data_centers**: Facility details with location, capacity, and operator info
- **metrics**: Energy consumption, carbon footprint, and EU compliance data
- **articles**: Operator news and market intelligence (when `--include-news` is used)
- **search_cache**: Geocoding and search metadata

## Environment Configuration

Create a `.env` file in the project root:

```bash
# SerpAPI Token (Required for real data)
# Get your key at: https://serpapi.com/
SERPAPI_TOKEN=your_serpapi_key_here

# Optional: Default analysis region
CITY=Berlin
COUNTRY=Germany

# Optional: Contact email for geocoding services
EMAIL=your@email.com
```

### API Keys Required
- **SerpAPI**: Powers carbon intensity search, news analysis, and financial data
  - Sign up at [serpapi.com](https://serpapi.com/)
  - Provides Google Search, Google News, and Google Finance APIs
  - Free tier: 100 searches/month

## Architecture & Components

### Core Pipeline
1. **Data Center Discovery** (`scraper_datacenters_com.py`, `scraper_digital_realty.py`)
   - Scrapes facilities from multiple vendor websites
   - Extracts location, capacity, and operator information
   - Normalizes data into standardized format

2. **Energy Analysis** (`energy_analyzer.py`)
   - **Carbon Intensity**: Real-time grid data via SerpAPI Google AI Mode
   - **EU Compliance**: Automated assessment for Regulation 2024/1364
   - **Economic Impact**: 10-year cost projections with country-specific pricing
   - **Water Usage**: Industry-standard WUE calculations (0.8 L/kWh)

3. **Market Intelligence** (`operator_analyzer.py`)
   - **Financial Analysis**: Real-time stock data via SerpAPI Google Finance
   - **News Sentiment**: Automated analysis of operator news coverage
   - **Risk Assessment**: Combined financial health and market sentiment scoring

4. **Orchestration** (`orchestrator.py`)
   - End-to-end pipeline coordination
   - Database-ready JSON payload generation
   - Configurable enrichment options (news, geocoding)

### Data Flow
```
Country/City Input → Facility Scraping → Energy Analysis → Market Intelligence → JSON Output
                                     ↓
                              EU Compliance Assessment
                                     ↓
                              Economic Impact Modeling
```

## Project Structure

### Core Files
- **`orchestrator.py`** – Main entry point with CLI interface and pipeline coordination
- **`energy_analyzer.py`** – Energy consumption, carbon footprint, and EU compliance analysis
- **`operator_analyzer.py`** – Financial analysis and news sentiment for data center operators
- **`scraper_datacenters_com.py`** – Primary scraper for DataCenters.com facility data
- **`scraper_digital_realty.py`** – Specialized scraper for Digital Realty facilities
- **`db_connection.py`** – Database utilities and connection management
- **`ingest_output.py`** – Data ingestion and output formatting utilities

### Data Files
- **`payload.*.json`** – Example output payloads for different cities (Paris, Barcelona, etc.)
- **`analysis_export.json`** – Exported analysis results
- **`output/`** – Directory for generated reports and analysis files

### Configuration
- **`.env`** – Environment variables and API keys
- **`.gitignore`** – Git ignore patterns
- **`README.md`** – This documentation

## Key Features

### 🏢 Multi-Vendor Data Center Discovery
- **DataCenters.com Integration**: Comprehensive facility database scraping
- **Digital Realty**: Direct vendor data extraction
- **Equinix Support**: Planned integration for major colocation provider

### ⚡ Real-Time Energy Intelligence
- **Carbon Intensity**: Live grid data using SerpAPI Google AI Mode (e.g., 30 gCO2/kWh for France)
- **EU Compliance**: Automated assessment for facilities ≥500kW (EU Regulation 2024/1364)
- **Economic Modeling**: 10-year cost projections with 3% annual price increases
- **Water Usage**: Industry-standard calculations (0.8 L/kWh based on USGBC/ASHRAE)

### 📈 Financial Market Analysis
- **Stock Data**: Real-time metrics for 20+ major data center operators
- **News Sentiment**: Automated analysis of operator coverage with relevance scoring
- **Risk Assessment**: Combined financial health and market sentiment (0-10 scale)

### 🌍 Geographic Intelligence
- **Multi-Country Support**: 15+ European countries with localized electricity pricing
- **Geocoding**: Optional latitude/longitude enrichment via SerpAPI or Nominatim
- **Location Filtering**: Country, city, and region-based facility discovery

## Example Usage

### Basic Country Analysis
```bash
python orchestrator.py --country spain --output spain_analysis.json
```

### Comprehensive City Analysis with Market Intelligence
```bash
python orchestrator.py \
  --country france \
  --city paris \
  --include-news \
  --news-days 30 \
  --geocode \
  --email contact@yourcompany.com \
  --output paris_comprehensive.json
```

### Command Line Options
- `--country`: Target country (required)
- `--city`: Optional city filter
- `--include-news`: Enable operator news analysis
- `--news-days`: Days back for news search (default: 14)
- `--max-news-per-dc`: Max news items per facility (default: 5)
- `--geocode`: Enable lat/lon geocoding
- `--geocode-provider`: Choose `serpapi` or `nominatim` (default: serpapi)
- `--output`: JSON output file path

## Data Output Schema

### data_centers
```json
{
  "id": "uuid",
  "name": "Facility Name",
  "operator": "Operator Name",
  "city": "Paris",
  "country": "France",
  "address": "Full Address",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "power_capacity_mw": 25.0,
  "space_sqft": 50000
}
```

### metrics
```json
{
  "data_center_id": "uuid",
  "carbon_intensity_gco2_kwh": 30,
  "renewable_percentage": 75.0,
  "annual_energy_cost_eur": 2500000,
  "eu_compliance_required": true,
  "sustainability_rating": "Excellent",
  "recorded_at": "2024-01-15T10:30:00Z"
}
```

### articles (when --include-news is used)
```json
{
  "data_center_id": "uuid",
  "title": "News Title",
  "source": "TechCrunch",
  "published_date": "2024-01-15",
  "sentiment_score": 0.8,
  "relevance_score": 0.9,
  "url": "https://..."
}
```

## Development & Testing

### Running Tests
```bash
python testing.py
```

### Database Integration
The system generates database-ready JSON payloads that can be ingested into PostgreSQL, MongoDB, or other databases using the provided `db_connection.py` utilities.

## Roadmap

### Immediate (Q1 2024)
- ✅ SerpAPI integration for real carbon intensity data
- ✅ Multi-vendor facility scraping (DataCenters.com, Digital Realty)
- ✅ Financial analysis with Google Finance API
- ✅ News sentiment analysis

### Short-term (Q2 2024)
- 🔄 Equinix vendor integration
- 🔄 Enhanced geocoding with address validation
- 🔄 Real-time monitoring dashboard
- 🔄 API rate limiting and caching

### Long-term (Q3-Q4 2024)
- 📋 Machine learning models for capacity prediction
- 📋 Integration with building management systems
- 📋 Carbon offset marketplace integration
- 📋 Mobile application for field operations
