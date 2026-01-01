# Multi-stage build for production deployment

# Stage 1: Build stage
FROM python:3.11-slim-bullseye as builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim-bullseye as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create non-root user for security
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --create-home appuser

# Set working directory
WORKDIR /app

# Install system dependencies for runtime
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser api/ ./api/
COPY --chown=appuser:appuser core/ ./core/
COPY --chown=appuser:appuser database/ ./database/
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=appuser:appuser services/ ./services/
COPY --chown=appuser:appuser pyproject.toml ./
COPY --chown=appuser:appfile requirements.txt ./

# Create data directory for database
RUN mkdir -p /app/data && chown appuser:appuser /app/data

# Update PATH to include user's local bin
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]