# Docker Deployment Guide

Deploy DataRackNews using Docker for a consistent, scalable, and production-ready environment. This guide covers everything from basic setup to advanced production configurations.

## 🐳 Quick Start with Docker

### Prerequisites

=== "macOS"
    ```bash
    # Install Docker Desktop
    brew install --cask docker
    
    # Start Docker Desktop
    open -a Docker
    
    # Verify installation
    docker --version
    docker compose --version
    ```

=== "Ubuntu/Debian"
    ```bash
    # Update package index
    sudo apt update
    
    # Install Docker
    sudo apt install docker.io docker-compose-plugin
    
    # Start Docker service
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    newgrp docker
    ```

=== "CentOS/RHEL"
    ```bash
    # Install Docker
    sudo yum install -y docker docker-compose
    
    # Start Docker service
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    newgrp docker
    ```

### 🚀 One-Command Deployment

```bash
# Clone the repository
git clone https://github.com/Reetika12795/DataRackNews.git
cd DataRackNews

# Quick deployment with our helper script
./start-docker.sh
```

The `start-docker.sh` script automatically:
- Checks Docker Desktop status on macOS
- Creates necessary environment files
- Builds and starts all containers
- Displays connection information

## 🏗️ Docker Architecture

```mermaid
graph TB
    subgraph "Docker Host"
        subgraph "DataRackNews Network"
            subgraph "App Container"
                APP[DataRackNews App<br/>python:3.11-slim]
                GRAD[Gradio Server<br/>0.0.0.0:7860]
            end
            
            subgraph "Database Container"
                PG[PostgreSQL 15<br/>postgres:5432]
                PGVOL[postgres_data volume]
            end
            
            subgraph "Cache Container"
                REDIS[Redis 7<br/>redis:6379]
                REDISVOL[redis_data volume]
            end
        end
        
        subgraph "Host Ports"
            PORT7860[Host:7860]
            PORT5432[Host:5432]
            PORT6379[Host:6379]
        end
    end
    
    subgraph "External"
        BROWSER[Browser]
        PGCLIENT[Database Client]
        REDISCLI[Redis CLI]
    end
    
    BROWSER --> PORT7860
    PGCLIENT --> PORT5432
    REDISCLI --> PORT6379
    
    PORT7860 --> GRAD
    PORT5432 --> PG
    PORT6379 --> REDIS
    
    APP --> PG
    APP --> REDIS
    
    PGVOL --> PG
    REDISVOL --> REDIS
    
    classDef container fill:#e3f2fd
    classDef volume fill:#f1f8e9
    classDef port fill:#fff3e0
    classDef external fill:#fce4ec
    
    class APP,GRAD,PG,REDIS container
    class PGVOL,REDISVOL volume
    class PORT7860,PORT5432,PORT6379 port
    class BROWSER,PGCLIENT,REDISCLI external
```

## 📋 Configuration Files

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "7860:7860"
    environment:
      - DATABASE_URL=postgresql://datarack:datarack123@postgres:5432/datarack_db
      - REDIS_URL=redis://redis:6379/0
      - SERP_API_KEY=${SERP_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./:/app
    networks:
      - datarack-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: datarack_db
      POSTGRES_USER: datarack
      POSTGRES_PASSWORD: datarack123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - datarack-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U datarack -d datarack_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - datarack-network
    command: redis-server --appendonly yes

volumes:
  postgres_data:
  redis_data:

networks:
  datarack-network:
    driver: bridge
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860 || exit 1

# Run application
CMD ["python", "gradio_ui.py"]
```

## 🛠️ Environment Configuration

### Environment Variables

Create a `.env` file for local development:

```bash
# .env
SERP_API_KEY=your_serp_api_key_here
DATABASE_URL=postgresql://datarack:datarack123@localhost:5432/datarack_db
REDIS_URL=redis://localhost:6379/0
DEBUG=True
LOG_LEVEL=INFO
```

### Production Environment

```bash
# .env.production
SERP_API_KEY=your_production_serp_api_key
DATABASE_URL=postgresql://datarack:secure_password@postgres:5432/datarack_db
REDIS_URL=redis://redis:6379/0
DEBUG=False
LOG_LEVEL=WARNING
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

## 🚦 Deployment Commands

### Development Deployment

```bash
# Start all services in development mode
docker compose up -d

# View logs
docker compose logs -f

# Restart specific service
docker compose restart app

# Stop all services
docker compose down
```

### Production Deployment

```bash
# Build with production config
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale the application
docker compose up -d --scale app=3

# Update application
docker compose build app
docker compose up -d app
```

### Maintenance Commands

```bash
# Check service health
docker compose ps

# Access container shell
docker compose exec app bash
docker compose exec postgres psql -U datarack -d datarack_db

# View resource usage
docker stats

# Clean up unused resources
docker system prune -f
```

## 📊 Monitoring and Health Checks

### Service Health Status

```mermaid
graph TD
    subgraph "Health Check Flow"
        A[Docker Compose Start] --> B[Wait for Dependencies]
        B --> C{PostgreSQL Ready?}
        C -->|No| D[Wait 10s]
        D --> C
        C -->|Yes| E{Redis Ready?}
        E -->|No| F[Wait 5s]
        F --> E
        E -->|Yes| G[Start App Container]
        G --> H{App Health Check}
        H -->|Fail| I[Retry 3x]
        I --> H
        H -->|Pass| J[Service Ready]
    end
    
    classDef wait fill:#fff3e0
    classDef check fill:#e3f2fd
    classDef ready fill:#e8f5e8
    classDef retry fill:#ffebee
    
    class D,F wait
    class C,E,H check
    class J ready
    class I retry
```

### Health Check Endpoints

| Service | Endpoint | Expected Response |
|---------|----------|------------------|
| **App** | `http://localhost:7860` | HTTP 200 |
| **PostgreSQL** | `pg_isready -U datarack` | Ready status |
| **Redis** | `redis-cli ping` | PONG |

### Monitoring Commands

```bash
# Real-time logs
docker compose logs -f app

# PostgreSQL connection test
docker compose exec postgres pg_isready -U datarack -d datarack_db

# Redis connection test
docker compose exec redis redis-cli ping

# Application health check
curl -f http://localhost:7860/health

# Resource monitoring
docker compose top
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Docker Desktop Not Running (macOS)

```bash
# Error: Cannot connect to the Docker daemon
# Solution: Start Docker Desktop
open -a Docker

# Wait for Docker to start, then retry
docker compose up -d
```

#### 2. Port Already in Use

```bash
# Error: Port 7860 is already allocated
# Check what's using the port
lsof -i :7860

# Kill the process or change the port in docker-compose.yml
# ports:
#   - "7861:7860"  # Use different host port
```

#### 3. Database Connection Issues

```bash
# Check PostgreSQL logs
docker compose logs postgres

# Reset database
docker compose down -v  # Remove volumes
docker compose up -d
```

#### 4. Memory/Performance Issues

```bash
# Check resource usage
docker stats

# Allocate more memory to Docker Desktop
# Docker Desktop → Settings → Resources → Advanced
# Increase Memory to 4GB or more
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Add to .env file
DEBUG=True
LOG_LEVEL=DEBUG

# Restart with debug logging
docker compose down
docker compose up -d

# Follow debug logs
docker compose logs -f app | grep DEBUG
```

## 🏭 Production Best Practices

### Security Hardening

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    environment:
      - DEBUG=False
      - LOG_LEVEL=WARNING
    restart: unless-stopped
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

  postgres:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    secrets:
      - postgres_password
    restart: unless-stopped

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
```

### Backup Strategy

```bash
# Database backup script
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Create backup
docker compose exec -T postgres pg_dump -U datarack datarack_db > \
    "${BACKUP_DIR}/datarack_${DATE}.sql"

# Compress backup
gzip "${BACKUP_DIR}/datarack_${DATE}.sql"

# Clean old backups (keep last 7 days)
find "${BACKUP_DIR}" -name "datarack_*.sql.gz" -mtime +7 -delete
```

### Load Balancing

```yaml
# nginx.conf for load balancing
upstream datarack_app {
    server app1:7860;
    server app2:7860;
    server app3:7860;
}

server {
    listen 80;
    location / {
        proxy_pass http://datarack_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📈 Performance Optimization

### Resource Allocation

```yaml
# Optimized resource limits
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  postgres:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### Caching Configuration

```yaml
# Redis optimization
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  sysctls:
    - net.core.somaxconn=65535
```

This comprehensive Docker deployment guide ensures you can deploy DataRackNews reliably in any environment, from local development to production scale.