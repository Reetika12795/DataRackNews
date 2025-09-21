# Data Directory

This directory is used for persistent data storage when running the application in Docker.

## Contents
- **Logs**: Application logs and debugging information
- **Cache**: Cached search results and facility information
- **Exports**: CSV and JSON exports from the application
- **Backups**: Database backups (if using PostgreSQL)

## Docker Volume Mounting
This directory is mounted as a volume in the Docker container to persist data across container restarts.

```bash
# The volume is mounted in docker-compose.yml as:
volumes:
  - ./data:/app/data
```