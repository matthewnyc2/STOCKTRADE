#!/bin/bash

# Production Deployment Script for Crypto Quant Laboratory
# This script automates the deployment process with health checks and rollback capability

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="crypto-quant-lab"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
BACKUP_DIR="backups"
LOG_FILE="deployment.log"

# Global variables
DEPLOYMENT_ID=""
BACKUP_SUCCESSFUL=false
ROLLBACK_NEEDED=false

# Logging function
log() {
    local level=$1
    shift
    local message=$@
    echo -e "${level}[$(date '+%Y-%m-%d %H:%M:%S')] ${message}${NC}" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    log $RED "ERROR: Deployment failed!"
    if [ "$ROLLBACK_NEEDED" = true ]; then
        log $YELLOW "Attempting rollback to previous version..."
        rollback
    fi
    exit 1
}

# Set up error trap
trap handle_error ERR

# Check prerequisites
check_prerequisites() {
    log $GREEN "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log $RED "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log $RED "Docker Compose is not installed"
        exit 1
    fi

    # Check if .env.production exists
    if [ ! -f "$ENV_FILE" ]; then
        log $RED "Production environment file $ENV_FILE not found"
        log $YELLOW "Please copy .env.production to .env and configure your values"
        exit 1
    fi

    # Check if .env exists
    if [ ! -f ".env" ]; then
        log $YELLOW "Creating .env from template..."
        cp "$ENV_FILE" ".env"
        log $YELLOW "Please edit .env with your actual configuration values before continuing"
        read -p "Press Enter after editing .env..."
    fi

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    log $GREEN "Prerequisites check passed"
}

# Create backup of current deployment
create_backup() {
    log $GREEN "Creating backup of current deployment..."
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="backup_${timestamp}"

    # Stop services and create backup
    docker-compose -f "$COMPOSE_FILE" down
    docker run --rm \
        -v "$(pwd)/$BACKUP_DIR":/backups \
        -v crypto_quant_postgres_data:/data/postgres \
        -v crypto_quant_redis_data:/data/redis \
        alpine:latest \
        tar czf "/backups/${backup_name}.tar.gz" -C /data .

    # Create deployment info file
    cat > "$BACKUP_DIR/${backup_name}_info.json" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "deployment_id": "$DEPLOYMENT_ID",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "services": "$(docker images | grep crypto-quant-lab | awk '{print $1":"$2}' | tr '\n' ',' | sed 's/,$//')",
    "backup_file": "${backup_name}.tar.gz"
}
EOF

    BACKUP_SUCCESSFUL=true
    log $GREEN "Backup created: $backup_name.tar.gz"
}

# Deploy new version
deploy() {
    log $GREEN "Starting deployment..."

    # Set deployment ID
    DEPLOYMENT_ID="deploy_$(date +%Y%m%d_%H%M%S)"
    export DEPLOYMENT_ID

    # Build and pull images
    log $GREEN "Building and pulling images..."
    docker-compose -f "$COMPOSE_FILE" pull
    docker-compose -f "$COMPOSE_FILE" build --no-cache

    # Run database migrations if needed
    run_migrations

    # Start services with health checks
    log $GREEN "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d

    # Wait for services to be healthy
    log $GREEN "Waiting for services to be healthy..."
    wait_for_healthy

    # Run health checks
    log $GREEN "Running health checks..."
    run_health_checks

    # Run post-deployment tests
    log $GREEN "Running post-deployment tests..."
    run_tests

    log $GREEN "Deployment completed successfully!"
    ROLLBACK_NEEDED=false
}

# Run database migrations
run_migrations() {
    log $GREEN "Checking for database migrations..."

    # Check if migration script exists
    if [ -f "database/migrate.py" ]; then
        log $GREEN "Running database migrations..."
        docker-compose -f "$COMPOSE_FILE" run --rm backend \
            python database/migrate.py
    else
        log $YELLOW "No migration script found, using automatic schema creation"
    fi
}

# Wait for services to be healthy
wait_for_healthy() {
    local max_attempts=60
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        local healthy=true

        # Check backend
        if ! docker-compose -f "$COMPOSE_FILE" ps -q backend | xargs -r docker inspect --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy"; then
            healthy=false
        fi

        # Check database
        if ! docker-compose -f "$COMPOSE_FILE" ps -q database | xargs -r docker inspect --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy"; then
            healthy=false
        fi

        # Check redis
        if ! docker-compose -f "$COMPOSE_FILE" ps -q redis | xargs -r docker inspect --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy"; then
            healthy=false
        fi

        if [ "$healthy" = true ]; then
            log $GREEN "All services are healthy!"
            return 0
        fi

        log $YELLOW "Waiting for services... ($attempt/$max_attempts)"
        sleep 10
        attempt=$((attempt + 1))
    done

    log $RED "Services did not become healthy within $max_attempts attempts"
    exit 1
}

# Run health checks
run_health_checks() {
    # Test API endpoint
    local attempts=0
    local max_attempts=5
    local success=false

    while [ $attempts -lt $max_attempts ]; do
        if curl -f http://localhost:8000/ > /dev/null 2>&1; then
            log $GREEN "Health check passed: API endpoint responding"
            success=true
            break
        fi

        attempts=$((attempts + 1))
        log $YELLOW "Health check attempt $attempts failed, retrying..."
        sleep 5
    done

    if [ "$success" = false ]; then
        log $RED "Health check failed: API endpoint not responding"
        exit 1
    fi

    # Test database connection
    if docker-compose -f "$COMPOSE_FILE" exec -T database pg_isready -U crypto_user -d crypto_quant_prod > /dev/null 2>&1; then
        log $GREEN "Database connection successful"
    else
        log $RED "Database connection failed"
        exit 1
    fi

    # Test Redis connection
    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
        log $GREEN "Redis connection successful"
    else
        log $RED "Redis connection failed"
        exit 1
    fi
}

# Run post-deployment tests
run_tests() {
    # Run basic smoke tests
    if curl -f http://localhost:8000/api/strategies > /dev/null 2>&1; then
        log $GREEN "Smoke test passed: API routes accessible"
    else
        log $RED "Smoke test failed: API routes not accessible"
    fi

    # Test WebSocket endpoint if needed
    # Additional tests can be added here
}

# Rollback to previous deployment
rollback() {
    log $GREEN "Starting rollback..."

    # Find the latest backup
    local latest_backup=$(ls -t "$BACKUP_DIR"/backup_*.tar.gz | head -1)

    if [ -z "$latest_backup" ]; then
        log $RED "No backup found for rollback"
        return 1
    fi

    log $GREEN "Restoring from backup: $(basename "$latest_backup")"

    # Stop all services
    docker-compose -f "$COMPOSE_FILE" down

    # Restore backup
    docker run --rm \
        -v "$(pwd)/$BACKUP_DIR":/backups \
        -v crypto_quant_postgres_data:/data/postgres \
        -v crypto_quant_redis_data:/data/redis \
        alpine:latest \
        tar xzf "/backups/$(basename "$latest_backup")" -C /data

    # Restart services with old version
    docker-compose -f "$COMPOSE_FILE" up -d

    log $GREEN "Rollback completed"
}

# Main deployment workflow
main() {
    echo "========================================="
    echo "Crypto Quant Laboratory Deployment Script"
    echo "========================================="

    # Check prerequisites
    check_prerequisites

    # Create backup before deployment
    create_backup

    # Set rollback flag
    ROLLBACK_NEEDED=true

    # Deploy new version
    deploy

    # Clean up old backups (keep last 7 days)
    log $GREEN "Cleaning up old backups..."
    find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete

    log $GREEN "Deployment workflow completed successfully!"
    echo ""
    echo "Services are running:"
    docker-compose -f "$COMPOSE_FILE" ps
}

# Run main function
main "$@"