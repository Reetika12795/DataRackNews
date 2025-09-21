# DataRackNews 🏢

**Real-time Data Center Intelligence & Monitoring Platform**
https://datarack.info/

A comprehensive web application for searching, analyzing, and monitoring data centers worldwide with detailed facility information, sustainability metrics, and market intelligence.

<img width="1024" height="1024" alt="DataRackNews Dashboard" src="https://github.com/user-attachments/assets/ab4003d6-e229-4aa1-812c-5c5bfc578c0a" />

## 🚀 Features

### 🌍 Global Data Center Search
- **Multi-Provider Support**: Search across multiple data center providers
- **Equinix Specialized Search**: Detailed Equinix facility information extraction
- **Location-Based Search**: Find data centers by city, country, or region
- **Real-time Scraping**: Fresh data extraction from official sources

### 🏢 Detailed Facility Information
- **Complete Specifications**: Address, electrical/cooling redundancy, floor space
- **Certification Tracking**: ISO standards, SOC compliance, PCI DSS, and more
- **Amenities & Services**: Breakrooms, conference facilities, technical services
- **Connectivity Ecosystem**: Network providers, cloud connectivity, peering options

### 📊 Advanced Analytics
- **Sustainability Scoring**: Environmental impact assessment
- **Market Intelligence**: Carrier counts, enterprise presence, ecosystem richness
- **Comparative Analysis**: Side-by-side facility comparisons
- **Interactive Visualizations**: Charts, maps, and data tables

### 🎯 Specialized Equinix Features
- **Individual Facility Extraction**: Direct access to PA2, NY1, SV1, etc.
- **IBX Highlights**: Business value propositions and market advantages
- **Technical Specifications**: Power capacity, cooling systems, redundancy levels
- **Real-time URL Validation**: Automatic fallback for different URL patterns

## 🛠️ Technology Stack

- **Frontend**: Gradio Web UI with interactive components
- **Backend**: Python with async web scraping
- **Data Processing**: Pandas, JSON parsing, regex pattern matching
- **Visualization**: Plotly charts and graphs
- **Web Scraping**: BeautifulSoup, Requests, custom parsers
- **Database**: PostgreSQL (psycopg2-binary)

## 📁 Project Structure

```
DataRackNews/
├── gradio_ui.py              # Main web application
├── equinix_scraper.py        # Equinix-specific data extraction
├── serp_search.py            # General data center scraping
├── datacenter_tracker.py     # Data center tracking & management
├── db_connection.py          # Database connection utilities
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (API keys)
├── .env.example              # Environment template
├── Dockerfile                # Docker container definition
├── docker-compose.yml        # Multi-service orchestration
├── docker-test.sh            # Docker setup validation script
├── start-docker.sh           # Docker Desktop startup helper (macOS)
├── .dockerignore             # Docker build exclusions
├── init.sql                  # Database initialization
├── data/                     # Persistent data directory
└── README.md                 # This file
```

## 🚀 Quick Start

### Option 1: Docker (Recommended) 🐳

#### Prerequisites
- [Docker Desktop](https://docs.docker.com/desktop/install/mac/) for macOS
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)

**🍎 macOS Setup:**
1. Download Docker Desktop from [docker.com](https://docs.docker.com/desktop/install/mac/)
2. Install and launch Docker Desktop
3. Wait for the whale icon to appear in your menu bar
4. Verify installation: `docker --version && docker compose version`

#### 1. Clone the Repository
```bash
git clone https://github.com/Reetika12795/DataRackNews.git
cd DataRackNews
```

#### 2. Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

Update the `.env` file with your SERP API key:
```env
SERP_API_KEY=your_actual_serpapi_key_here
```

#### 3. Launch with Docker Compose
```bash
# Option A: Automatic Docker startup (macOS)
./start-docker.sh      # Starts Docker Desktop if needed
docker compose up -d   # Launch the application

# Option B: Manual startup
# 1. Start Docker Desktop manually
# 2. Wait for whale icon in menu bar
# 3. Then run:
docker compose up -d

# Option C: Test and validate setup
./docker-test.sh       # Comprehensive setup validation
```

#### 4. Access the Application
Open your browser and navigate to: `http://localhost:7860`

#### 5. Stop the Application
```bash
docker-compose down
```

#### Docker Compose Services
- **datarack-web**: Main Gradio web application (port 7860)
- **postgres**: PostgreSQL database (port 5432) - optional
- **redis**: Redis cache (port 6379) - optional

### Option 2: Local Development 💻

#### 1. Clone the Repository
```bash
git clone https://github.com/Reetika12795/DataRackNews.git
cd DataRackNews
```

#### 2. Set Up Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
SERP_API_KEY=your_serpapi_key_here
```

#### 5. Run the Application
```bash
python gradio_ui.py
```

#### 6. Access the Web Interface
Open your browser and navigate to: `http://127.0.0.1:7860`

## 💻 Usage

### Data Center Search
1. **General Search**: Use the main search tab for broad data center queries
2. **Equinix Search**: Use the specialized Equinix tab for detailed facility information
3. **Location Input**: Enter city names (e.g., "Paris", "New York", "Tokyo")
4. **Analysis**: Click analyze buttons to get comprehensive facility details

### Search Examples
- **City Search**: "Paris" → Returns all Paris data centers including PA2, PA3, PA4, etc.
- **Country Search**: "France" → Returns all French data center locations
- **Provider Search**: "Equinix" → Returns global Equinix facilities

### Understanding Results
- **Facility Codes**: PA2, NY1, SV1 (Equinix facility identifiers)
- **Redundancy Levels**: N+1, 2N (electrical and cooling redundancy)
- **Certifications**: ISO 27001, SOC 2, PCI DSS (compliance standards)
- **Sustainability Scores**: 0-10 rating based on green initiatives

## � Docker Configuration

### Docker Architecture
The application is containerized with a multi-service architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Gradio Web    │    │   PostgreSQL    │    │      Redis      │
│   Application   │◄──►│    Database     │    │     Cache       │
│   (Port 7860)   │    │   (Port 5432)   │    │   (Port 6379)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Docker Services

#### 🌐 Web Application (`datarack-web`)
- **Base Image**: Python 3.11 slim
- **Port**: 7860
- **Health Check**: HTTP endpoint monitoring
- **Volumes**: 
  - Environment variables (`.env`)
  - Persistent data (`./data:/app/data`)

#### 🗄️ PostgreSQL Database (`postgres`)
- **Image**: PostgreSQL 15 Alpine
- **Port**: 5432
- **Features**:
  - Automatic database initialization
  - Persistent data storage
  - Health monitoring
- **Optional**: Can be disabled if database features aren't needed

#### ⚡ Redis Cache (`redis`)
- **Image**: Redis 7 Alpine  
- **Port**: 6379
- **Features**:
  - Data persistence with AOF
  - Health monitoring
- **Optional**: Future-ready for caching functionality

### Docker Commands

#### Development
```bash
# Build and start all services
docker-compose up --build

# Start specific service
docker-compose up datarack-web

# View logs
docker-compose logs -f datarack-web

# Shell access
docker-compose exec datarack-web bash
```

#### Production
```bash
# Start in detached mode
docker-compose up -d

# Monitor health
docker-compose ps

# Update application
docker-compose pull
docker-compose up -d --force-recreate
```

#### Maintenance
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v

# View resource usage
docker stats
```

### Environment Variables

#### Required
- `SERP_API_KEY`: Your SerpAPI key for enhanced search

#### Optional Database
- `POSTGRES_DB`: Database name (default: datarack)
- `POSTGRES_USER`: Database user (default: datarack_user)  
- `POSTGRES_PASSWORD`: Database password (default: changeme)
- `DATABASE_URL`: Full database connection string

#### Application Configuration
- `GRADIO_SERVER_NAME`: Server bind address (default: 0.0.0.0)
- `GRADIO_SERVER_PORT`: Server port (default: 7860)

### Data Persistence

#### Docker Volumes
- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis persistence files
- `./data`: Application data (logs, exports, cache)

#### Backup & Restore
```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U datarack_user datarack > backup.sql

# Restore PostgreSQL  
docker-compose exec -T postgres psql -U datarack_user datarack < backup.sql
```

## 🔧 Configuration & Troubleshooting

### Environment Variables
- `SERP_API_KEY`: Required for enhanced search capabilities
- `DATABASE_URL`: Optional PostgreSQL connection string

### Common Issues

#### Docker Issues

**🚨 Docker daemon not running (most common)**
```bash
# Error: Cannot connect to the Docker daemon
# Solution: Start Docker Desktop
open -a Docker  # Start Docker Desktop on macOS

# Wait for Docker to fully start (whale icon in menu bar)
# Then verify it's running:
docker info
```

**🔧 Docker Desktop troubleshooting:**
```bash
# If Docker Desktop won't start:
1. Quit Docker Desktop completely
2. Restart your Mac
3. Launch Docker Desktop again
4. Wait for full initialization

# Reset Docker Desktop (if needed):
# Go to Docker Desktop -> Troubleshoot -> Reset to factory defaults
```

**🐳 Port and permission issues:**
```bash
# Port 7860 already in use
docker compose down  # Stop existing containers
lsof -i :7860        # Check what's using the port

# Permission issues (Linux/macOS)
sudo docker compose up  # Run with elevated permissions

# Clean Docker system
docker system prune -a  # Remove all unused containers/images
```

**📋 Docker Compose issues:**
```bash
# Version warning (safe to ignore):
# WARN: the attribute `version` is obsolete

# Invalid compose file:
docker compose config  # Validate syntax

# Build failures:
docker build -t datarack-news .  # Test build manually
```

#### Application Issues
```bash
# API key issues
# Check .env file has correct SERP_API_KEY

# Database connection issues
# Verify postgres service is running:
docker compose ps

# View application logs
docker compose logs datarack-web
```

### Customization
- **Search Regions**: Modify `equinix_scraper.py` to add new regions
- **Scraping Patterns**: Update regex patterns in extraction functions
- **UI Themes**: Customize Gradio interface in `gradio_ui.py`
- **Docker Configuration**: Modify `docker-compose.yml` for different setups

## 📊 Data Sources

### Primary Sources
- **Equinix Official Website**: Direct facility page extraction
- **Provider Websites**: Real-time scraping of specifications
- **Search APIs**: Enhanced discovery through SERP APIs

### Data Accuracy
- **Real-time Extraction**: Fresh data on every search
- **Multiple Validation**: Cross-reference across multiple sources
- **Fallback Mechanisms**: Graceful handling of unavailable data

## 🌱 Sustainability Features

### Environmental Tracking
- **Green Certifications**: ISO 14001, LEED tracking
- **Energy Efficiency**: Renewable energy usage monitoring
- **Carbon Footprint**: Sustainability scoring algorithms

### Metrics
- **Green Score**: 0-10 sustainability rating
- **Certification Count**: Number of environmental certifications
- **Energy Sources**: Renewable vs. traditional power usage

## 🔍 Advanced Features

### Equinix Specialization
- **Direct URL Access**: https://www.equinix.com/data-centers/.../pa2
- **Comprehensive Extraction**: Address, redundancy, certifications, amenities
- **IBX Highlights**: Business value and market positioning
- **Technical Specifications**: Power, cooling, space details

### Error Handling
- **Graceful Fallbacks**: Multiple URL patterns attempted
- **Rate Limiting**: Respectful scraping with delays
- **Data Validation**: Quality checks on extracted information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♀️ Support

- **Issues**: Report bugs via GitHub Issues
- **Questions**: Use GitHub Discussions for questions
- **Email**: Contact the maintainer for urgent matters

## 🔮 Roadmap

- [ ] Additional data center providers (AWS, Azure, GCP)
- [ ] Real-time pricing information
- [ ] Mobile-responsive design
- [ ] API endpoint development
- [ ] Machine learning predictions
- [ ] Advanced filtering options
- [ ] Multi-language support
- [ ] Performance monitoring dashboard

## 🚀 Quick Start Summary

**For immediate deployment (macOS):**
```bash
git clone https://github.com/Reetika12795/DataRackNews.git
cd DataRackNews
cp .env.example .env
# Edit .env with your SERP_API_KEY
./start-docker.sh    # Starts Docker Desktop automatically
docker compose up -d
# Open http://localhost:7860
```

**For other platforms:**
```bash
git clone https://github.com/Reetika12795/DataRackNews.git
cd DataRackNews
cp .env.example .env
# Edit .env with your SERP_API_KEY
# Start Docker Desktop manually
docker compose up -d
# Open http://localhost:7860
```

**What you get:**
- 🌐 Web UI for data center search and analysis
- 🏢 Detailed Equinix facility information (PA2, NY1, etc.)
- 📊 Sustainability and connectivity scoring
- 🗄️ Optional PostgreSQL database
- ⚡ Redis caching for performance
- 🐳 Fully containerized with Docker

---

**Made with ❤️ for the AI tinkerer hackathon team **

