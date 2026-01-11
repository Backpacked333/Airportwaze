# AirportWaze Deployment Guide

Comprehensive guide for deploying AirportWaze to production environments using Docker, Docker Compose, and Kubernetes.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Database Migration](#database-migration)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Scaling Strategies](#scaling-strategies)
- [Security Checklist](#security-checklist)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Docker**: 20.10+ with Docker Compose v2+
- **PostgreSQL**: 16+ (or managed service like AWS RDS, Google Cloud SQL)
- **Redis**: 7+ (or managed service like AWS ElastiCache, Redis Cloud)
- **Nginx**: 1.25+ (for production reverse proxy)
- **Git**: For source code management

### Required Knowledge

- Basic understanding of Docker and containers
- Familiarity with environment variables
- Understanding of database migrations
- Basic Linux/Unix command line skills

### Cloud Provider Options

- **AWS**: EC2, RDS, ElastiCache, ECS/EKS
- **Google Cloud**: Compute Engine, Cloud SQL, Memorystore, GKE
- **Azure**: Virtual Machines, Azure Database, Azure Cache, AKS
- **DigitalOcean**: Droplets, Managed Databases, Kubernetes
- **Self-hosted**: Any VPS or dedicated server

## Environment Setup

### 1. Server Requirements

#### Minimum Production Requirements

- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **Network**: 100 Mbps
- **OS**: Ubuntu 22.04 LTS, Debian 12, or CentOS 8+

#### Recommended Production Requirements

- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Storage**: 50+ GB SSD
- **Network**: 1 Gbps
- **OS**: Ubuntu 22.04 LTS

### 2. Environment Variables

Create production environment file:

```bash
# /opt/airportwaze/.env.production
# Copy this to your production server

# Application
APP_NAME="AirportWaze API"
APP_VERSION="2.0.0"
DEBUG=False
ENV=production

# Database (Use secure password!)
DATABASE_URL=postgresql+psycopg://airportwaze:STRONG_PASSWORD_HERE@postgres:5432/airportwaze
DB_ECHO=False
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://redis:6379/0
CACHE_TTL=300
PREDICTION_CACHE_TTL=600

# Security (MUST CHANGE IN PRODUCTION!)
SECRET_KEY=generate-a-secure-random-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (Add your production domains)
CORS_ORIGINS=https://airportwaze.com,https://www.airportwaze.com
CORS_ALLOW_CREDENTIALS=True

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=5000

# Monte Carlo Simulation
SIMULATION_RUNS=10000
SIMULATION_RUNS_FAST=5000

# Logging
LOG_LEVEL=INFO
LOG_JSON=True

# Sentry Error Tracking (optional but recommended)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# External APIs
TSA_API_URL=https://www.tsa.gov/data/apcp.xml
TSA_API_TIMEOUT=10

# Database Password (for docker-compose)
DB_PASSWORD=STRONG_PASSWORD_HERE
```

### 3. Generate Secure Secrets

```bash
# Generate SECRET_KEY (Python)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate SECRET_KEY (OpenSSL)
openssl rand -base64 32

# Generate DB_PASSWORD
openssl rand -base64 24
```

## Docker Compose Deployment

### Production docker-compose.yml

Create `/opt/airportwaze/docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    container_name: airportwaze-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: airportwaze
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: airportwaze
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U airportwaze"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - airportwaze-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: airportwaze-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "127.0.0.1:6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - airportwaze-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Backend API
  backend:
    build:
      context: ./airport-waze-backend
      dockerfile: Dockerfile
      args:
        BUILD_ENV: production
    image: airportwaze/backend:latest
    container_name: airportwaze-backend
    restart: unless-stopped
    env_file:
      - .env.production
    environment:
      DATABASE_URL: postgresql+psycopg://airportwaze:${DB_PASSWORD}@postgres:5432/airportwaze
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - airportwaze-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"

  # Frontend
  frontend:
    build:
      context: ./airport-waze-frontend
      dockerfile: Dockerfile
      args:
        VITE_API_BASE_URL: https://api.airportwaze.com
    image: airportwaze/frontend:latest
    container_name: airportwaze-frontend
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    depends_on:
      - backend
    networks:
      - airportwaze-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 30s
      timeout: 3s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Nginx Reverse Proxy
  nginx:
    image: nginx:1.25-alpine
    container_name: airportwaze-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - backend
      - frontend
    networks:
      - airportwaze-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  airportwaze-network:
    driver: bridge
```

### Deployment Steps

```bash
# 1. Clone repository
cd /opt
git clone https://github.com/yourusername/airportwaze.git
cd airportwaze

# 2. Create production environment file
cp .env.example .env.production
nano .env.production  # Edit with your values

# 3. Build images
docker-compose -f docker-compose.prod.yml build

# 4. Start services
docker-compose -f docker-compose.prod.yml up -d

# 5. Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 6. Verify services
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f

# 7. Test endpoints
curl http://localhost:8000/healthz
curl http://localhost:8080/
```

### Managing the Deployment

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f [service]

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop services
docker-compose -f docker-compose.prod.yml down

# Update deployment
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run migrations after update
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Kubernetes Deployment

### Basic Kubernetes Configuration

Create `k8s/` directory with the following files:

#### 1. Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: airportwaze
```

#### 2. ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: airportwaze-config
  namespace: airportwaze
data:
  APP_NAME: "AirportWaze API"
  ENV: "production"
  LOG_LEVEL: "INFO"
  LOG_JSON: "True"
```

#### 3. Secrets

```bash
# Create secrets
kubectl create secret generic airportwaze-secrets \
  --from-literal=db-password='YOUR_DB_PASSWORD' \
  --from-literal=secret-key='YOUR_SECRET_KEY' \
  --from-literal=redis-password='YOUR_REDIS_PASSWORD' \
  --namespace=airportwaze
```

#### 4. PostgreSQL Deployment

```yaml
# k8s/postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: airportwaze
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_USER
          value: "airportwaze"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: airportwaze-secrets
              key: db-password
        - name: POSTGRES_DB
          value: "airportwaze"
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: airportwaze
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: airportwaze
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

#### 5. Backend Deployment

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: airportwaze
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: airportwaze/backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: airportwaze-config
        env:
        - name: DATABASE_URL
          value: "postgresql+psycopg://airportwaze:$(DB_PASSWORD)@postgres:5432/airportwaze"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: airportwaze-secrets
              key: db-password
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: airportwaze-secrets
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: airportwaze
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

#### 6. Frontend Deployment

```yaml
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: airportwaze
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: airportwaze/frontend:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: airportwaze
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

#### Deploy to Kubernetes

```bash
# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Check deployment status
kubectl get pods -n airportwaze
kubectl get services -n airportwaze

# Run migrations
kubectl exec -it deployment/backend -n airportwaze -- alembic upgrade head

# View logs
kubectl logs -f deployment/backend -n airportwaze
```

## Database Migration

### Initial Setup

```bash
# Run migrations on first deployment
docker-compose exec backend alembic upgrade head

# Or for Kubernetes
kubectl exec -it deployment/backend -n airportwaze -- alembic upgrade head
```

### Zero-Downtime Migration Strategy

```bash
# 1. Backup database before migration
./scripts/backup-db.sh

# 2. Run migrations
docker-compose exec backend alembic upgrade head

# 3. Verify migration success
docker-compose exec backend alembic current

# 4. If issues, rollback
docker-compose exec backend alembic downgrade -1
```

### Automated Migration in CI/CD

```yaml
# .github/workflows/deploy.yml
- name: Run Database Migrations
  run: |
    kubectl exec deployment/backend -n airportwaze -- \
      alembic upgrade head
```

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificates
sudo certbot --nginx -d airportwaze.com -d www.airportwaze.com

# Auto-renewal (cron)
sudo crontab -e
# Add: 0 0 * * * certbot renew --quiet
```

### Nginx SSL Configuration

```nginx
# /opt/airportwaze/nginx/nginx.conf
server {
    listen 443 ssl http2;
    server_name airportwaze.com www.airportwaze.com;

    ssl_certificate /etc/letsencrypt/live/airportwaze.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/airportwaze.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        proxy_pass http://frontend:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS headers
        add_header Access-Control-Allow-Origin "https://airportwaze.com" always;
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name airportwaze.com www.airportwaze.com;
    return 301 https://$server_name$request_uri;
}
```

## Monitoring & Logging

### Application Logs

```bash
# Docker Compose logs
docker-compose logs -f --tail=100 [service]

# Kubernetes logs
kubectl logs -f deployment/backend -n airportwaze --tail=100

# Export logs to file
docker-compose logs > logs/$(date +%Y%m%d).log
```

### Health Checks

```bash
# Backend health
curl https://api.airportwaze.com/healthz

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping
```

### Sentry Integration

Already configured in `.env` - just add your DSN:

```bash
SENTRY_DSN=https://your-key@sentry.io/project-id
```

## Backup & Recovery

### Database Backup Script

```bash
#!/bin/bash
# scripts/backup-db.sh

BACKUP_DIR="/opt/airportwaze/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/postgres_backup_$DATE.sql.gz"

docker-compose exec -T postgres pg_dump -U airportwaze airportwaze | gzip > "$BACKUP_FILE"

# Keep only last 7 days
find "$BACKUP_DIR" -name "postgres_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

### Automated Backups

```bash
# Add to crontab
0 2 * * * /opt/airportwaze/scripts/backup-db.sh

# Or weekly full backup
0 3 * * 0 /opt/airportwaze/scripts/backup-full.sh
```

### Database Restore

```bash
# Restore from backup
gunzip < backup_file.sql.gz | docker-compose exec -T postgres psql -U airportwaze airportwaze
```

## Scaling Strategies

### Horizontal Scaling

```bash
# Scale backend containers
docker-compose up -d --scale backend=3

# Kubernetes scaling
kubectl scale deployment/backend --replicas=5 -n airportwaze
```

### Load Balancing

Use Nginx or cloud load balancer (AWS ALB, GCP Load Balancer).

### Database Scaling

- **Read replicas** for read-heavy workloads
- **Connection pooling** with PgBouncer
- **Vertical scaling** (larger instance)

### Redis Scaling

- **Redis Cluster** for high availability
- **Redis Sentinel** for automatic failover

## Security Checklist

- [ ] Changed all default passwords
- [ ] Generated secure SECRET_KEY
- [ ] Enabled HTTPS/SSL
- [ ] Configured firewall (UFW/iptables)
- [ ] Set up automated backups
- [ ] Enabled rate limiting
- [ ] Configured CORS properly
- [ ] Set up monitoring/alerts
- [ ] Enabled database encryption
- [ ] Regular security updates
- [ ] Implemented secrets management
- [ ] Set up intrusion detection

## Troubleshooting

### Common Issues

#### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Common causes:
# - Database connection failed
# - Redis connection failed
# - Invalid environment variables
# - Port already in use
```

#### Database Connection Error

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec backend python -c "from app.core.database import engine; engine.connect()"
```

#### High Memory Usage

```bash
# Check container stats
docker stats

# Adjust Docker memory limits in docker-compose.yml
```

#### 502 Bad Gateway

```bash
# Backend not responding
# Check backend health
docker-compose exec backend curl localhost:8000/healthz

# Check nginx logs
docker-compose logs nginx
```

## Support

For deployment issues:
- Check logs first
- Review this guide
- Open GitHub issue
- Contact: devops@airportwaze.com
