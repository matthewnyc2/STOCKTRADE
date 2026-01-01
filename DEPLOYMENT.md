# Production Deployment Configuration

## Overview

This document describes the production deployment configuration for the Crypto Quant Laboratory backend service. The deployment includes containerization, orchestration, monitoring, and automated deployment workflows.

## Architecture

### Services
1. **Backend API** (FastAPI)
   - Multi-stage Docker build
   - Health checks enabled
   - Non-root user execution
   - Resource limits configured

2. **Database** (TimescaleDB)
   - PostgreSQL with time-series extensions
   - Persistent storage
   - Automated backups
   - Hypertables for time-series data

3. **Redis** (Caching)
   - Persistent cache
   - Password protected
   - Memory limits configured

4. **Monitoring** (Optional)
   - Prometheus metrics
   - Grafana dashboards
   - Logging aggregation

## Files Created

### 1. Dockerfile
- **Location**: `Dockerfile`
- **Features**:
  - Multi-stage build (builder + production)
  - Non-root user (appuser:1001)
  - Health check endpoint
  - Production optimizations
  - Size-conscious build

### 2. Docker Compose Files
- **Development**: `docker-compose.yml`
- **Production**: `docker-compose.prod.yml`
- **Features**:
  - Service orchestration
  - Network isolation
  - Volume management
  - Health checks
  - Resource limits

### 3. Environment Configuration
- **Template**: `.env.production`
- **Features**:
  - Production environment variables
  - Security settings
  - Database configuration
  - API keys and secrets

### 4. Deployment Script
- **Location**: `deployment/deploy.sh`
- **Features**:
  - Automated deployment
  - Pre-deployment checks
  - Database migrations
  - Health checks
  - Backup and rollback
  - Error handling

### 5. Database Migration
- **Location**: `database/migrate.py`
- **Features**:
  - Schema versioning
  - TimescaleDB hypertables
  - Performance indexes
  - Compression policies
  - Retention policies

### 6. Kubernetes Manifests (Optional)
- **Location**: `deployment/k8s/`
- **Files**:
  - `namespace.yaml` - Kubernetes namespace
  - `configmap.yaml` - Application configuration
  - `secret.yaml` - Secret management
  - `backend-deployment.yaml` - Backend deployment
  - `database-deployment.yaml` - TimescaleDB deployment
  - `redis-deployment.yaml` - Redis deployment
  - `services.yaml` - Kubernetes services
  - `pvc.yaml` - Persistent volumes
  - `rbac.yaml` - Role-based access control

## Deployment Commands

### Docker Compose (Development)
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Compose (Production)
```bash
# Start production services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Scale backend
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Automated Deployment
```bash
# Make script executable
chmod +x deployment/deploy.sh

# Run deployment
./deployment/deploy.sh
```

### Kubernetes Deployment
```bash
# Create namespace
kubectl apply -f deployment/k8s/namespace.yaml

# Apply configurations
kubectl apply -f deployment/k8s/

# Check status
kubectl get pods -n crypto-quant-lab

# View logs
kubectl logs -f deployment/backend -n crypto-quant-lab
```

## Health Checks

### Endpoints
- **API Health**: `GET /`
  ```json
  {
    "status": "healthy",
    "service": "crypto-quant-lab"
  }
  ```

- **WebSocket Info**: `GET /ws`
  - Returns WebSocket channel information

### Service Health
- Backend: HTTP health check every 30 seconds
- Database: PostgreSQL readiness check
- Redis: Redis ping check

## Monitoring

### Metrics
- Prometheus metrics available at `/metrics`
- Application metrics
- Database metrics
- System metrics

### Logging
- Structured JSON logging
- Log rotation configured
- Centralized logging setup

## Security Considerations

1. **Non-root User**: All containers run as non-root users
2. **Secret Management**: All secrets stored in Kubernetes secrets or environment files
3. **Network Policies**: Restrict inter-service communication
4. **Resource Limits**: CPU and memory limits configured
5. **Health Checks**: Regular health monitoring

## Backup and Recovery

### Database Backups
- Automated daily backups
- 30-day retention
- Volume snapshots

### Application Backups
- Pre-deployment backups
- Rollback capability
- State preservation

## Scaling

### Horizontal Scaling
- Backend: Load balancer, multiple replicas
- Database: Read replicas planned
- Redis: Redis cluster setup

### Vertical Scaling
- Resource limits configured
- Node affinity for dedicated resources
- Priority classes for critical services

## Requirements

1. **Docker** and **Docker Compose**
2. **Kubernetes** (optional, for K8s deployment)
3. **TimescaleDB** (for production database)
4. **Persistent storage** for databases
5. **Load balancer** (for production)

## Testing

The deployment includes comprehensive tests:
- `tests/deployment/test_docker_build.py` - Docker build verification
- `tests/deployment/test_compose_orchestration.py` - Compose orchestration tests

Run tests with:
```bash
pytest tests/deployment/ -v
```

## Troubleshooting

### Common Issues
1. **Port Conflicts**: Ensure ports are available
2. **Permission Issues**: Verify volume permissions
3. **Memory Issues**: Check resource limits
4. **Network Issues**: Verify network configuration

### Debug Commands
```bash
# Check container logs
docker logs <container-name>

# Enter container for debugging
docker exec -it <container-name> /bin/bash

# Check network connectivity
docker network ls
docker network inspect <network-name>
```

## Maintenance

### Regular Tasks
1. Monitor logs and metrics
2. Update images regularly
3. Rotate database backups
4. Update security patches
5. Review resource usage

### Update Process
1. Update Docker image
2. Update deployment manifest
3. Run deployment script
4. Monitor health after update

## Support

For issues related to:
- **Application**: Check application logs
- **Database**: Check TimescaleDB logs
- **Infrastructure**: Check Kubernetes/Docker logs
- **Performance**: Review metrics and resource usage

## Additional Resources

- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)