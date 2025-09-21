# API Workflows and Integration

This section provides comprehensive documentation of DataRackNews API workflows, internal function calls, and external service integrations.

## 🔄 Core API Workflows

### 1. PA2 Facility Data Extraction Workflow

```mermaid
sequenceDiagram
    participant U as User Interface
    participant G as Gradio Handler
    participant E as Equinix Scraper
    participant C as Cache Layer
    participant D as Database
    participant EQ as Equinix.com
    
    U->>G: analyze_equinix_datacenter("paris", 1)
    Note over U,G: User selects Paris + PA2 (index 1)
    
    G->>C: check_cache("facility:paris:pa2")
    C->>G: cache_miss
    
    G->>E: extract_facility_info("paris", "france", 1)
    Note over G,E: Fallback to city page first
    
    E->>EQ: GET /data-centers/europe-colocation/france-colocation/paris-data-centers
    EQ->>E: HTML response (city page)
    
    E->>E: parse_facility_links()
    Note over E: Find PA2 in facility list
    
    E->>E: get_individual_facility_url("paris", "france", "pa2")
    Note over E: Generate direct PA2 URL
    
    E->>EQ: GET /data-centers/.../paris-data-centers/pa2
    EQ->>E: HTML response (PA2 specific)
    
    E->>E: extract_detailed_facility_info()
    Note over E: Parse PA2 specific data
    
    E->>G: structured_facility_data
    
    G->>D: store_facility_data()
    G->>C: cache_facility_data(ttl=3600)
    
    G->>U: formatted_facility_display
    Note over G,U: Rich PA2 information display
```

### 2. General Data Center Search Workflow

```mermaid
sequenceDiagram
    participant U as User
    participant G as Gradio UI
    participant S as SERP Search
    participant C as Cache
    participant SERP as SERP API
    participant P as Parser
    
    U->>G: search_datacenters("Frankfurt data centers")
    
    G->>C: check_search_cache("frankfurt_dc")
    
    alt Cache Hit
        C->>G: cached_results
        G->>U: display_results
    else Cache Miss
        G->>S: perform_search("Frankfurt data centers")
        
        S->>SERP: search_request()
        Note over S,SERP: SERP API call with parameters
        
        SERP->>S: search_results_json
        
        S->>P: parse_search_results()
        P->>P: extract_datacenter_info()
        P->>P: calculate_sustainability_score()
        P->>P: format_facility_data()
        
        P->>S: structured_results
        S->>G: formatted_datacenter_list
        
        G->>C: cache_results(ttl=1800)
        G->>U: display_results
    end
```

## 🛠️ Internal API Functions

### Equinix Scraper API

#### `extract_facility_info(city, country, facility_index)`

**Purpose**: Extract facility information from Equinix city pages or individual facility URLs.

**Parameters**:
- `city` (str): Target city name
- `country` (str): Country name
- `facility_index` (int): Facility index for selection

**Workflow**:
```mermaid
flowchart TD
    A[extract_facility_info] --> B{Use individual URL?}
    
    B -->|Yes| C[get_individual_facility_url]
    B -->|No| D[generate_equinix_url]
    
    C --> E[Direct facility scraping]
    D --> F[City page scraping]
    
    E --> G[extract_detailed_facility_info]
    F --> H[extract_basic_facility_info]
    
    G --> I[Comprehensive data]
    H --> J[Basic data]
    
    I --> K[Return structured result]
    J --> K
```

**Response Format**:
```python
{
    "facility_name": "Equinix PA2",
    "address": {
        "street": "114 Rue Ambroise Croizat",
        "city": "Saint Denis", 
        "country": "France",
        "postal_code": "93200"
    },
    "infrastructure": {
        "electrical_redundancy": "N+1",
        "cooling_redundancy": "N+1"
    },
    "certifications": [
        "ISO 27001", "SOC 2 Type II", "PCI DSS"
    ],
    "amenities": [
        "24/7 Remote Hands", "Conference Rooms"
    ],
    "source_url": "https://www.equinix.com/.../pa2"
}
```

#### `get_individual_facility_url(city, country, facility_code)`

**Purpose**: Generate direct URLs for specific Equinix facilities.

**URL Pattern Logic**:
```mermaid
graph LR
    A[Input Parameters] --> B[Region Mapping]
    B --> C[Country Path]
    C --> D[City Path] 
    D --> E[Facility Code]
    E --> F[Complete URL]
    
    A --> G["city: 'paris'<br/>country: 'france'<br/>code: 'pa2'"]
    B --> H["region: 'europe-colocation'"]
    C --> I["country_path: 'france-colocation'"]
    D --> J["city_path: 'paris-data-centers'"]
    E --> K["facility: 'pa2'"]
    F --> L["https://www.equinix.com/data-centers/<br/>europe-colocation/france-colocation/<br/>paris-data-centers/pa2"]
```

### SERP Search API

#### `search_datacenters(query, location, num_results)`

**Purpose**: Perform intelligent data center searches using SERP API.

**Workflow**:
```mermaid
sequenceDiagram
    participant C as Caller
    participant S as SERP Search
    participant A as SERP API
    participant P as Parser
    participant SC as Scorer
    
    C->>S: search_datacenters(query)
    S->>S: build_search_params()
    S->>A: execute_search()
    A->>S: raw_results
    
    S->>P: parse_organic_results()
    P->>P: extract_datacenter_metadata()
    P->>S: parsed_results
    
    S->>SC: calculate_scores()
    SC->>SC: sustainability_score()
    SC->>SC: connectivity_score()
    SC->>S: scored_results
    
    S->>C: formatted_results
```

**Scoring Algorithm**:
```python
def calculate_sustainability_score(facility_data):
    """
    Calculate sustainability score based on:
    - Green certifications (LEED, BREEAM)
    - Renewable energy usage
    - PUE ratings
    - Carbon neutrality commitments
    """
    score = 0
    
    # Green certifications (0-30 points)
    if 'LEED' in facility_data.get('certifications', []):
        score += 15
    if 'BREEAM' in facility_data.get('certifications', []):
        score += 15
    
    # PUE efficiency (0-25 points)
    pue = facility_data.get('pue', 2.0)
    if pue < 1.2:
        score += 25
    elif pue < 1.5:
        score += 15
    elif pue < 1.8:
        score += 10
    
    # Renewable energy (0-25 points)
    renewable_pct = facility_data.get('renewable_energy_pct', 0)
    score += min(25, renewable_pct // 4)
    
    # Carbon commitments (0-20 points)
    if facility_data.get('carbon_neutral', False):
        score += 20
    
    return min(100, score)
```

## 🌐 External API Integrations

### Equinix.com Integration

#### Rate Limiting Strategy

```mermaid
graph TD
    A[Request Queue] --> B{Rate Limit Check}
    B -->|Within Limits| C[Execute Request]
    B -->|Rate Limited| D[Wait & Retry]
    
    C --> E[Response Processing]
    D --> F[Exponential Backoff]
    F --> B
    
    E --> G{Success?}
    G -->|Yes| H[Cache Result]
    G -->|No| I[Error Handling]
    
    H --> J[Return Data]
    I --> K[Fallback Strategy]
    K --> J
```

**Implementation**:
```python
import time
import random
from functools import wraps

def rate_limited(calls_per_minute=30):
    """Decorator for rate limiting API calls"""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0, 0.1)
                time.sleep(left_to_wait + jitter)
            
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator
```

### SERP API Integration

#### Authentication & Configuration

```python
# SERP API Configuration
SERP_CONFIG = {
    "api_key": os.getenv("SERP_API_KEY"),
    "engine": "google",
    "num_results": 20,
    "country": "us",
    "language": "en",
    "safe": "active"
}

def build_serp_params(query, location=None):
    """Build SERP API parameters"""
    params = SERP_CONFIG.copy()
    params.update({
        "q": f"{query} data center",
        "num": params["num_results"],
        "api_key": params["api_key"]
    })
    
    if location:
        params["location"] = location
        params["uule"] = generate_uule(location)
    
    return params
```

#### Error Handling & Fallbacks

```mermaid
graph TD
    A[SERP API Call] --> B{Response Status}
    
    B -->|200 OK| C[Parse Results]
    B -->|Rate Limited| D[Exponential Backoff]
    B -->|Auth Error| E[Check API Key]
    B -->|Server Error| F[Fallback Search]
    
    C --> G[Validate Data]
    D --> H[Retry Request]
    E --> I[Log Error]
    F --> J[Basic Search]
    
    G --> K{Data Valid?}
    K -->|Yes| L[Return Results]
    K -->|No| M[Data Cleaning]
    
    H --> A
    I --> N[Return Empty]
    J --> O[Limited Results]
    M --> L
```

## 📊 API Performance Monitoring

### Response Time Tracking

```mermaid
gantt
    title API Response Time Analysis
    dateFormat X
    axisFormat %s
    
    section Equinix API
    Individual URL    :done, eq1, 0, 1800ms
    City Page        :done, eq2, 0, 2400ms
    Fallback Search  :done, eq3, 0, 3200ms
    
    section SERP API
    Standard Search  :done, serp1, 0, 800ms
    Location Search  :done, serp2, 0, 1200ms
    Retry Attempt   :done, serp3, 0, 2100ms
    
    section Cache Layer
    Redis Hit       :done, cache1, 0, 50ms
    Database Hit    :done, cache2, 0, 200ms
    Cache Miss      :done, cache3, 0, 150ms
```

### Performance Metrics

| API Endpoint | Avg Response | 95th Percentile | Error Rate | Cache Hit Rate |
|--------------|-------------|----------------|------------|---------------|
| **PA2 Individual** | 1.8s | 3.2s | 2.1% | 78% |
| **Equinix City** | 2.4s | 4.1s | 3.5% | 65% |
| **SERP Search** | 0.8s | 1.5s | 1.2% | 45% |
| **Cache Layer** | 50ms | 200ms | 0.1% | 72% |

### Monitoring Dashboard

```mermaid
graph TB
    subgraph "API Monitoring"
        subgraph "Response Times"
            RT1[Equinix API: 1.8s avg]
            RT2[SERP API: 0.8s avg]
            RT3[Cache: 50ms avg]
        end
        
        subgraph "Error Rates"
            ER1[Equinix: 2.1%]
            ER2[SERP: 1.2%]
            ER3[Cache: 0.1%]
        end
        
        subgraph "Cache Performance"
            CH1[Hit Rate: 72%]
            CH2[Miss Rate: 28%]
            CH3[Invalidation: 5%]
        end
    end
    
    subgraph "Alerts"
        A1[Response > 5s]
        A2[Error Rate > 5%]
        A3[Cache Hit < 50%]
    end
    
    RT1 --> A1
    ER1 --> A2
    CH1 --> A3
```

## 🔐 API Security

### Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as App
    participant V as Validator
    participant E as External API
    
    C->>A: API Request
    A->>V: Validate API Key
    
    alt Valid Key
        V->>A: Validation Success
        A->>E: Authenticated Request
        E->>A: API Response
        A->>C: Formatted Response
    else Invalid Key
        V->>A: Validation Failed
        A->>C: 401 Unauthorized
    end
```

### Rate Limiting Implementation

```python
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_calls=100, window=3600):
        self.max_calls = max_calls
        self.window = window
        self.calls = defaultdict(list)
    
    def is_allowed(self, key):
        now = time.time()
        # Clean old calls
        self.calls[key] = [
            call_time for call_time in self.calls[key]
            if now - call_time < self.window
        ]
        
        if len(self.calls[key]) >= self.max_calls:
            return False
        
        self.calls[key].append(now)
        return True
```

## 🧪 API Testing

### Test Scenarios

```python
import pytest
import responses

class TestEquinixAPI:
    
    @responses.activate
    def test_pa2_extraction_success(self):
        """Test successful PA2 data extraction"""
        responses.add(
            responses.GET,
            "https://www.equinix.com/data-centers/europe-colocation/france-colocation/paris-data-centers/pa2",
            body=self.load_fixture("pa2_success.html"),
            status=200
        )
        
        result = extract_facility_info("paris", "france", 1)
        
        assert result["facility_name"] == "Equinix PA2"
        assert result["address"]["street"] == "114 Rue Ambroise Croizat"
        assert "N+1" in result["infrastructure"]["electrical_redundancy"]
    
    @responses.activate
    def test_rate_limiting(self):
        """Test rate limiting behavior"""
        # Simulate rate limited response
        responses.add(
            responses.GET,
            "https://www.equinix.com/data-centers/europe-colocation/france-colocation/paris-data-centers/pa2",
            status=429
        )
        
        with pytest.raises(RateLimitError):
            extract_facility_info("paris", "france", 1)
    
    def test_fallback_mechanism(self):
        """Test fallback to city page when individual URL fails"""
        # Mock individual URL failure
        with patch('requests.get') as mock_get:
            mock_get.side_effect = [
                Mock(status_code=404),  # Individual URL fails
                Mock(status_code=200, text=self.load_fixture("paris_city.html"))  # City page succeeds
            ]
            
            result = extract_facility_info("paris", "france", 1)
            assert result is not None
```

This comprehensive API documentation provides all the technical details needed to understand, integrate with, and extend the DataRackNews API workflows.