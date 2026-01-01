# Deployment Guide

This guide covers deployment of the Crypto Quant Laboratory platform in various environments, from development to production.

## Table of Contents

1. [Environment Overview](#environment-overview)
2. [Development Setup](#development-setup)
3. [Production Deployment](#production-deployment)
4. [Database Configuration](#database-configuration)
5. [Environment Variables](#environment-variables)
6. [Docker Deployment](#docker-deployment)
7. [Cloud Deployment](#cloud-deployment)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Backup and Recovery](#backup-and-recovery)
10. [Performance Optimization](#performance-optimization)

## Environment Overview

### Development
- Local development with hot-reload
- SQLite database
- No rate limiting
- Debug logging enabled

### Staging
- Production-like environment
- PostgreSQL database
- Limited rate limiting
- Monitoring enabled

### Production
- High-availability deployment
- PostgreSQL/TimescaleDB database
- Full rate limiting
- Comprehensive monitoring
- SSL/TLS encryption

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Git

### Backend Setup

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd STOCKTRADE
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # Activate on Windows
   source venv/Scripts/activate

   # Activate on Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt  # If exists
   ```

5. **Environment configuration**
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```env
   DEBUG=true
   DATABASE_URL=sqlite:///./data/crypto_quant.db
   LOG_LEVEL=DEBUG
   HOST=0.0.0.0
   PORT=8000
   ```

6. **Initialize database**
   ```bash
   # Create data directory
   mkdir -p data

   # The app will auto-create the database on first run
   ```

7. **Start development server**
   ```bash
   # Using the provided script
   ./run_dev.sh

   # Or directly
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

### Access Points

- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Frontend: http://localhost:3000
- WebSocket Test: http://localhost:8000/ws/test

## Production Deployment

### Requirements

- Ubuntu 20.04+ or CentOS 8+
- Python 3.10+
- PostgreSQL 13+
- Nginx (for reverse proxy)
- Supervisor (for process management)
- Redis (optional, for caching)

### Step 1: System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv nginx supervisor postgresql redis-server

# Create application user
sudo useradd -m -s /bin/bash stocktrade
sudo -i -u stocktrade
```

### Step 2: Application Setup

```bash
# Switch to application user
sudo -i -u stocktrade

# Clone repository
git clone <repository-url> /home/stocktrade/app
cd /home/stocktrade/app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server

# Install Node.js dependencies for frontend
cd frontend
npm install
npm run build
cd ..

# Create directories
mkdir -p data logs
chmod 755 data logs
```

### Step 3: Database Setup

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE crypto_quant;
CREATE USER stocktrade_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE crypto_quant TO stocktrade_user;
\q

# Configure database connection
nano .env
```

Update `.env` for production:
```env
DEBUG=false
DATABASE_URL=postgresql+asyncpg://stocktrade_user:secure_password_here@localhost:5432/crypto_quant
API_KEY=your-secure-api-key-here
JWT_SECRET_KEY=your-secure-jwt-secret-here
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
```

### Step 4: Database Migration (PostgreSQL)

1. **Install Alembic**
   ```bash
   pip install alembic
   ```

2. **Initialize Alembic**
   ```bash
   alembic init alembic
   ```

3. **Configure Alembic**
   Edit `alembic.ini`:
   ```ini
   [alembic]
   # path to migration scripts
   script_location = alembic

   # database connection string
   sqlalchemy.url = postgresql+asyncpg://stocktrade_user:secure_password_here@localhost:5432/crypto_quant
   ```

4. **Create initial migration**
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   ```

5. **Apply migration**
   ```bash
   alembic upgrade head
   ```

### Step 5: Gunicorn Configuration

Create `gunicorn.conf.py`:
```python
import multiprocessing
import os

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
graceful_timeout = 30
errorlog = "/home/stocktrade/logs/gunicorn.error.log"
accesslog = "/home/stocktrade/logs/gunicorn.access.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
```

### Step 6: Supervisor Configuration

Create `/etc/supervisor/conf.d/stocktrade.conf`:
```ini
[program:stocktrade]
command=/home/stocktrade/app/venv/bin/gunicorn -c gunicorn.conf.py api.main:app
directory=/home/stocktrade/app
user=stocktrade
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/stocktrade/logs/supervisor.log
environment=PATH="/home/stocktrade/app/venv/bin",PYTHONPATH="/home/stocktrade/app"
```

Start supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start stocktrade
```

### Step 7: Nginx Configuration

Create `/etc/nginx/sites-available/stocktrade`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options "nosniff";
    add_header Referrer-Policy "no-referrer-when-downgrade";
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if serving frontend from same domain)
    location /static {
        alias /home/stocktrade/app/frontend/build/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate max-age=0 auth;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # SSL configuration (when using HTTPS)
    # listen 443 ssl http2;
    # ssl_certificate /path/to/your/certificate.crt;
    # ssl_certificate_key /path/to/your/private.key;
    # ssl_protocols TLSv1.2 TLSv1.3;
    # ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/stocktrade /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Database Configuration

### SQLite (Development)

```env
DATABASE_URL=sqlite:///./data/crypto_quant.db
```

### PostgreSQL (Production)

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/crypto_quant
```

For TimescaleDB (time-series optimized):

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/crypto_quant
# Additional TimescaleDB settings in database.py
```

### Database Optimization

PostgreSQL configuration (`postgresql.conf`):
```ini
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 200

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Enable query logging
log_statement = 'all'
log_duration = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

Create indexes for performance:
```sql
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_market_data_time ON market_data(time, symbol);
CREATE INDEX idx_signals_timestamp ON signals(timestamp);
CREATE INDEX idx_positions_symbol ON positions(symbol);
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./data/crypto_quant.db` |
| `API_KEY` | API key for authentication | `your-secure-api-key` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `HOST` | Server bind host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | JWT secret key | - |
| `RATE_LIMIT_MAX_REQUESTS` | Max requests per window | `100` |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate limit window | `60` |
| `EMAIL_HOST` | SMTP server | - |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_USER` | SMTP username | - |
| `EMAIL_PASSWORD` | SMTP password | - |

## Docker Deployment

### Development with Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - DATABASE_URL=sqlite:///./data/crypto_quant.db
      - DEBUG=true
    depends_on:
      - redis
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directories
RUN mkdir -p data logs

# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker-compose up --build
```

### Production Docker Deployment

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://stocktrade:password@db:5432/crypto_quant
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=false
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=crypto_quant
      - POSTGRES_USER=stocktrade
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  redis:
    image: redis:alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
```

## Cloud Deployment

### AWS Deployment

#### Using AWS Elastic Beanstalk

1. **Create application**
   ```bash
   eb init
   eb create prod
   ```

2. **Configure environment**
   - Set instance type (t3.medium recommended)
   - Configure load balancer
   - Set auto scaling

#### Using AWS ECS

1. **Create task definition**
   ```json
   {
     "family": "stocktrade",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "256",
     "memory": "512",
     "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "stocktrade",
         "image": "your-account.dkr.ecr.region.amazonaws.com/stocktrade:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "DATABASE_URL",
             "value": "postgresql://..."
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/stocktrade",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and push image**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT-ID/stocktrade
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy stocktrade \
     --image gcr.io/PROJECT-ID/stocktrade \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="DATABASE_URL=postgresql://..."
   ```

### Azure Deployment

#### Using Azure Container Instances

1. **Create container group**
   ```bash
   az container create \
     --resource-group MyResourceGroup \
     --name stocktrade \
     --image your-container-image \
     --ports 8000 \
     --environment-variables 'DATABASE_URL=postgresql://...' \
     --dns-name-label stocktrade
   ```

## Monitoring and Logging

### Application Logging

Configure logging in `core/config.py`:
```python
import logging
from logging.handlers import RotatingFileHandler

if not DEBUG:
    handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
```

### Health Checks

The application includes health check endpoints:
- `/` - Basic health check
- `/health` - Detailed health check
- `/metrics` - Prometheus metrics

### Monitoring Tools

#### Prometheus + Grafana

1. **Configure Prometheus**
   ```yaml
   scrape_configs:
     - job_name: 'stocktrade'
       static_configs:
         - targets: ['localhost:8000']
       metrics_path: '/metrics'
   ```

2. **Grafana Dashboard**
   - Import pre-built dashboard or create custom
   - Track:
     - Request rate and latency
     - Error rates
     - Database connections
     - Memory usage

#### Structured Logging

Enable JSON logging:
```python
import json
import sys

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        return json.dumps(log_entry)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

## Backup and Recovery

### Database Backups

#### PostgreSQL Backups

1. **Automated backup script**
   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   pg_dump -U stocktrade_user -h localhost crypto_quant > /backups/crypto_quant_$DATE.sql

   # Compress
   gzip /backups/crypto_quant_$DATE.sql

   # Keep only last 30 days
   find /backups -name "*.sql.gz" -mtime +30 -delete
   ```

2. **Cron job**
   ```bash
   0 2 * * * /home/stocktrade/scripts/backup_db.sh
   ```

### Application Backups

1. **Backup script**
   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   tar -czf /backups/app_$DATE.tar.gz \
     --exclude=venv \
     --exclude=node_modules \
     --exclude=data/crypto_quant.db \
     /home/stocktrade/app
   ```

2. **Recovery procedure**
   ```bash
   # Stop services
   sudo supervisorctl stop stocktrade
   sudo systemctl stop nginx

   # Restore application
   cd /home/stocktrade
   tar -xzf /backups/app_$DATE.tar.gz
   chown -R stocktrade:stocktrade app

   # Restore database
   gunzip < /backups/crypto_quant_$DATE.sql.gz | psql -U stocktrade_user crypto_quant

   # Start services
   sudo systemctl start nginx
   sudo supervisorctl start stocktrade
   ```

## Performance Optimization

### Application Optimization

1. **Caching**
   - Redis for API response caching
   - Database query caching
   - Frontend static file caching

2. **Database Optimization**
   - Add appropriate indexes
   - Use connection pooling
   - Optimize queries

3. **WebSocket Optimization**
   - Connection pooling
   - Message batching
   - Subscription management

### Server Optimization

1. **Nginx Optimization**
   ```nginx
   # worker processes
   worker_processes auto;

   # keepalive connections
   keepalive_timeout 30;
   keepalive_requests 1000;

   # enable gzip
   gzip on;
   gzip_comp_level 6;
   ```

2. **Kernel Tuning**
   ```bash
   # Increase file descriptors
   echo '* soft nofile 65536' >> /etc/security/limits.conf
   echo '* hard nofile 65536' >> /etc/security/limits.conf

   # TCP optimization
   echo 'net.core.somaxconn = 65536' >> /etc/sysctl.conf
   echo 'net.ipv4.tcp_tw_reuse = 1' >> /etc/sysctl.conf
   sysctl -p
   ```

3. **Gunicorn Optimization**
   ```python
   # gunicorn.conf.py
   workers = multiprocessing.cpu_count() * 2 + 1
   worker_connections = 1000
   max_requests = 1000
   max_requests_jitter = 100
   timeout = 30
   keepalive = 2
   ```

### SSL/TLS Configuration

1. **Let's Encrypt SSL**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

2. **Strong SSL Configuration**
   ```nginx
   ssl_protocols TLSv1.2 TLSv1.3;
   ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
   ssl_prefer_server_ciphers off;
   ssl_session_cache shared:SSL:10m;
   ssl_session_timeout 1d;
   ssl_session_tickets off;

   # HSTS
   add_header Strict-Transport-Security "max-age=63072000" always;
   ```

## Deployment Checklist

### Pre-Deployment

- [ ] Update application version
- [ ] Run all tests
- [ ] Update database migration
- [ ] Check environment variables
- [ ] Backup existing data
- [ ] Review security settings

### Deployment

- [ ] Deploy to staging environment
- [ ] Run smoke tests
- [ ] Check application logs
- [ ] Verify database connections
- [ ] Test WebSocket connections
- [ ] Check API endpoints
- [ ] Monitor performance metrics

### Post-Deployment

- [ ] Verify monitoring alerts
- [ ] Check error rates
- [ ] Monitor database performance
- [ ] Verify backup procedures
- [ ] Update documentation
- [ ] Notify stakeholders

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check database service status
   - Verify connection string
   - Check firewall rules

2. **High Memory Usage**
   - Check application logs for memory leaks
   - Monitor database queries
   - Optimize WebSocket connections

3. **Slow API Responses**
   - Check database query performance
   - Enable caching
   - Monitor server resources

4. **WebSocket Connection Drops**
   - Check network stability
   - Monitor server load
   - Check proxy configuration

### Debug Commands

```bash
# Check service status
sudo supervisorctl status

# View logs
tail -f /home/stocktrade/logs/app.log

# Check database connections
psql -h localhost -U stocktrade_user -d crypto_quant -c "SELECT count(*) FROM pg_stat_activity;"

# Check system resources
htop
df -h
free -h
```

For additional help, refer to the [Developer Guide](./DEVELOPER.md) or create an issue in the project repository.