# System Overview

DataRackNews is built on a modern, containerized architecture that provides real-time data center intelligence through sophisticated web scraping and data processing capabilities.

## 🏗️ High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Gradio Web UI<br/>:7860]
        BR[Browser Client]
    end
    
    subgraph "Application Layer"
        GU[gradio_ui.py<br/>Main Application]
        ES[equinix_scraper.py<br/>Facility Extractor]
        GS[serp_search.py<br/>General Scraper]
        DC[datacenter_tracker.py<br/>Data Tracker]
    end
    
    subgraph "Data Processing Layer"
        EP[Extract Patterns]
        TP[Transform Data]
        VP[Validate & Process]
    end
    
    subgraph "Storage Layer"
        PG[(PostgreSQL<br/>:5432)]
        RD[(Redis Cache<br/>:6379)]
        FS[File System<br/>Static Assets]
    end
    
    subgraph "External Services"
        EQ[Equinix.com<br/>Official Source]
        SERP[SERP API<br/>Search Results]
        Maps[Location APIs]
    end
    
    BR --> UI
    UI --> GU
    
    GU --> ES
    GU --> GS
    GU --> DC
    
    ES --> EP
    GS --> EP
    DC --> EP
    
    EP --> TP
    TP --> VP
    
    VP --> PG
    VP --> RD
    VP --> FS
    
    ES --> EQ
    GS --> SERP
    GU --> Maps
    
    classDef ui fill:#e1f5fe
    classDef app fill:#f3e5f5
    classDef data fill:#e8f5e8
    classDef storage fill:#fff3e0
    classDef external fill:#fce4ec
    
    class UI,BR ui
    class GU,ES,GS,DC app
    class EP,TP,VP data
    class PG,RD,FS storage
    class EQ,SERP,Maps external
```

## 🔄 Data Flow Architecture

```mermaid
sequenceDiagram
    participant U as User
    participant G as Gradio UI
    participant E as Equinix Scraper
    participant S as SERP Search
    participant D as Database
    participant C as Cache
    
    U->>G: Search "Paris PA2"
    G->>C: Check cache
    
    alt Cache Hit
        C->>G: Return cached data
    else Cache Miss
        G->>E: Extract facility data
        E->>+Equinix.com: GET facility page
        Equinix.com->>-E: HTML response
        E->>E: Parse & extract
        E->>G: Structured data
        G->>D: Store data
        G->>C: Cache results
    end
    
    G->>U: Display facility info
    
    Note over G,E: PA2 Enhancement:<br/>Direct URL access for<br/>accurate data extraction
```

## 🏢 Component Architecture

### Core Components

#### 1. Gradio Web Interface (`gradio_ui.py`)

```mermaid
graph LR
    subgraph "Gradio Components"
        SI[Search Interface]
        RI[Results Interface]
        CI[Configuration Interface]
    end
    
    subgraph "Core Functions"
        AE[analyze_equinix_datacenter]
        AF[analyze_facility_by_index]
        SD[search_datacenters]
    end
    
    subgraph "Data Processing"
        DP[Data Parser]
        FR[Format Renderer]
        ER[Error Handler]
    end
    
    SI --> AE
    SI --> AF
    SI --> SD
    
    AE --> DP
    AF --> DP
    SD --> DP
    
    DP --> FR
    DP --> ER
    
    FR --> RI
    ER --> RI
```

**Key Features:**
- Interactive search interface with location and facility dropdowns
- Real-time facility analysis with comprehensive data display
- Error handling and user feedback systems
- Responsive design with modern UI components

#### 2. Equinix Scraper (`equinix_scraper.py`)

```mermaid
graph TD
    subgraph "URL Generation"
        UG[generate_equinix_url]
        IU[get_individual_facility_url]
    end
    
    subgraph "Data Extraction"
        FI[extract_facility_info]
        DI[extract_detailed_facility_info]
        BI[extract_basic_info]
    end
    
    subgraph "Pattern Matching"
        AP[Address Patterns]
        RP[Redundancy Patterns]
        CP[Certification Patterns]
        AM[Amenity Patterns]
    end
    
    UG --> FI
    IU --> DI
    
    FI --> BI
    DI --> AP
    DI --> RP
    DI --> CP
    DI --> AM
    
    classDef generation fill:#e3f2fd
    classDef extraction fill:#f1f8e9
    classDef patterns fill:#fff8e1
    
    class UG,IU generation
    class FI,DI,BI extraction
    class AP,RP,CP,AM patterns
```

**Enhanced PA2 Capabilities:**
- Direct facility URL access: `https://www.equinix.com/data-centers/europe-colocation/france-colocation/paris-data-centers/pa2`
- Comprehensive pattern matching for all data fields
- Intelligent fallback mechanisms
- Rate limiting and error handling

#### 3. General Search Engine (`serp_search.py`)

```mermaid
graph LR
    subgraph "Search Interface"
        SQ[Search Query]
        SP[Search Parameters]
        SF[Search Filters]
    end
    
    subgraph "SERP Integration"
        API[SERP API Client]
        RP[Result Parser]
        RV[Result Validator]
    end
    
    subgraph "Data Processing"
        DF[Data Formatter]
        DS[Data Scorer]
        DR[Data Ranker]
    end
    
    SQ --> API
    SP --> API
    SF --> API
    
    API --> RP
    RP --> RV
    
    RV --> DF
    DF --> DS
    DS --> DR
```

## 🐳 Docker Architecture

```mermaid
graph TB
    subgraph "Docker Environment"
        subgraph "Application Container"
            APP[DataRackNews App<br/>Python 3.11]
            GRAD[Gradio Server<br/>:7860]
        end
        
        subgraph "Database Container"
            PG[PostgreSQL 15<br/>:5432]
            PGDATA[/var/lib/postgresql/data]
        end
        
        subgraph "Cache Container"
            REDIS[Redis 7<br/>:6379]
            REDISDATA[/data]
        end
        
        subgraph "Volumes"
            APPVOL[app_data]
            PGVOL[postgres_data]
            REDISVOL[redis_data]
        end
    end
    
    subgraph "Host System"
        HOST[Host Machine]
        BROWSER[Browser :7860]
    end
    
    APP --> GRAD
    GRAD --> PG
    GRAD --> REDIS
    
    APPVOL --> APP
    PGVOL --> PGDATA
    REDISVOL --> REDISDATA
    
    HOST --> BROWSER
    BROWSER --> GRAD
    
    classDef container fill:#e3f2fd
    classDef volume fill:#f1f8e9
    classDef host fill:#fff3e0
    
    class APP,GRAD,PG,REDIS container
    class APPVOL,PGVOL,REDISVOL,PGDATA,REDISDATA volume
    class HOST,BROWSER host
```

### Container Specifications

| Container | Base Image | Ports | Volumes | Purpose |
|-----------|------------|-------|---------|---------|
| **app** | python:3.11-slim | 7860:7860 | ./:/app | Main application |
| **postgres** | postgres:15 | 5432:5432 | postgres_data:/var/lib/postgresql/data | Database |
| **redis** | redis:7-alpine | 6379:6379 | redis_data:/data | Caching |

## 🔐 Security Architecture

```mermaid
graph TD
    subgraph "Security Layers"
        subgraph "Application Security"
            ENV[Environment Variables]
            API[API Key Management]
            VAL[Input Validation]
        end
        
        subgraph "Network Security"
            CORS[CORS Configuration]
            RATE[Rate Limiting]
            PROXY[Reverse Proxy Ready]
        end
        
        subgraph "Data Security"
            ENC[Data Encryption]
            HASH[Password Hashing]
            BACKUP[Secure Backups]
        end
    end
    
    subgraph "External Connections"
        HTTPS[HTTPS Only]
        CERT[SSL Certificates]
        AUTH[API Authentication]
    end
    
    ENV --> API
    API --> VAL
    
    CORS --> RATE
    RATE --> PROXY
    
    ENC --> HASH
    HASH --> BACKUP
    
    HTTPS --> CERT
    CERT --> AUTH
```

## 📊 Performance Architecture

### Caching Strategy

```mermaid
graph LR
    subgraph "Cache Layers"
        L1[L1: In-Memory<br/>Function Cache]
        L2[L2: Redis<br/>Session Cache]
        L3[L3: Database<br/>Persistent Storage]
    end
    
    subgraph "Cache Policies"
        TTL[TTL: 1 hour]
        LRU[LRU Eviction]
        INV[Cache Invalidation]
    end
    
    REQUEST[User Request] --> L1
    L1 --> L2
    L2 --> L3
    
    L1 --> TTL
    L2 --> LRU
    L3 --> INV
```

### Scalability Design

- **Horizontal Scaling**: Multiple app containers behind load balancer
- **Vertical Scaling**: Resource allocation via Docker Compose
- **Database Scaling**: Read replicas and connection pooling
- **Cache Scaling**: Redis cluster for high availability

## 🔄 Integration Points

### External APIs

| Service | Purpose | Rate Limits | Fallback |
|---------|---------|-------------|----------|
| **Equinix.com** | Primary facility data | Respectful delays | Cache + Manual |
| **SERP API** | Search intelligence | API key limits | Basic search |
| **Maps API** | Geolocation data | Standard limits | Static coordinates |

### Data Synchronization

```mermaid
sequenceDiagram
    participant S as Scheduler
    participant A as App
    participant E as External APIs
    participant D as Database
    participant C as Cache
    
    S->>A: Trigger sync job
    A->>E: Fetch latest data
    E->>A: Return updates
    A->>D: Update database
    A->>C: Invalidate cache
    A->>S: Report completion
    
    Note over A,E: Sync frequency:<br/>Hourly for critical data<br/>Daily for static data
```

This architecture ensures reliable, scalable, and maintainable data center intelligence with a focus on the enhanced PA2 extraction capabilities that make DataRackNews unique in the market.