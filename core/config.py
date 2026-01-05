"""
Configuration management for STOCKTRADE platform.

Provides secure loading of configuration and secrets from environment variables.
Validates required settings and provides defaults where appropriate.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from pydantic import BaseModel, Field, validator


logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION MODELS
# ============================================================================

class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(default="sqlite:///./data/crypto_quant.db", description="Database connection URL")
    pool_size: int = Field(default=5, ge=1, le=100, description="Database connection pool size")
    max_overflow: int = Field(default=10, ge=0, le=50, description="Maximum pool overflow connections")
    pool_pre_ping: bool = Field(default=True, description="Validate connections before use")
    echo: bool = Field(default=False, description="Echo SQL queries for debugging")

    @validator('url')
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v:
            raise ValueError("Database URL cannot be empty")
        if not any(v.startswith(prefix) for prefix in ['sqlite://', 'postgresql://', 'mysql://']):
            raise ValueError(f"Unsupported database URL prefix: {v}")
        return v


class SecurityConfig(BaseModel):
    """Security configuration."""
    secret_key: str = Field(..., description="Secret key for JWT signing and encryption")
    api_key: Optional[str] = Field(default=None, description="Optional API key for middleware authentication")
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expiration_hours: int = Field(default=24, ge=1, le=168, description="JWT token expiration in hours")
    password_min_length: int = Field(default=8, ge=8, description="Minimum password length")
    require_https: bool = Field(default=False, description="Require HTTPS in production")

    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Validate secret key is strong enough."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v


class APIConfig(BaseModel):
    """API configuration."""
    title: str = Field(default="Crypto Quant Laboratory API", description="API title")
    version: str = Field(default="1.0.0", description="API version")
    description: str = Field(default="", description="API description")
    docs_enabled: bool = Field(default=True, description="Enable OpenAPI documentation")
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, ge=1, description="Rate limit per minute")

    @validator('cors_origins')
    def validate_cors_origins(cls, v):
        """Validate CORS origins format."""
        if not v:
            return ["*"]
        return v


class ExternalAPIConfig(BaseModel):
    """External API configuration."""
    coingecko_api_key: Optional[str] = Field(default=None, description="CoinGecko API key (optional for free tier)")
    binance_api_key: Optional[str] = Field(default=None, description="Binance API key")
    binance_api_secret: Optional[str] = Field(default=None, description="Binance API secret")
    kraken_api_key: Optional[str] = Field(default=None, description="Kraken API key")
    kraken_api_secret: Optional[str] = Field(default=None, description="Kraken API secret")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    file: Optional[str] = Field(default=None, description="Log file path (None for stdout)")
    max_bytes: int = Field(default=10 * 1024 * 1024, description="Max log file size before rotation")
    backup_count: int = Field(default=5, description="Number of backup log files to keep")

    @validator('level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper


class AppConfig(BaseModel):
    """Application configuration."""
    environment: str = Field(default="development", description="Environment name (development, staging, production)")
    debug: bool = Field(default=False, description="Debug mode")
    testing: bool = Field(default=False, description="Testing mode")
    max_workers: int = Field(default=4, ge=1, le=32, description="Maximum worker threads")
    timezone: str = Field(default="UTC", description="Application timezone")

    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment name."""
        valid_envs = ['development', 'staging', 'production']
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v_lower


# ============================================================================
# MAIN CONFIGURATION CLASS
# ============================================================================

class Config:
    """
    Central configuration manager for the application.

    Loads settings from environment variables and provides typed access.
    Validates all required settings on initialization.
    """

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load environment-specific settings
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.debug = self.environment == "development" or os.getenv("DEBUG", "false").lower() == "true"
        self.testing = os.getenv("TESTING", "false").lower() == "true"

        # Initialize sub-configurations
        self.database = self._load_database_config()
        self.security = self._load_security_config()
        self.api = self._load_api_config()
        self.external_apis = self._load_external_api_config()
        self.logging = self._load_logging_config()
        self.app = self._load_app_config()

        # Log configuration status (without exposing secrets)
        self._log_config_status()

    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration."""
        return DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///./data/crypto_quant.db"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_pre_ping=os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )

    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration."""
        secret_key = os.getenv("SECRET_KEY")

        # Generate a warning if using default secret key
        if not secret_key:
            if self.environment == "production":
                raise ValueError("SECRET_KEY environment variable must be set in production")
            logger.warning("Using default SECRET_KEY for development. Set SECRET_KEY environment variable in production!")
            secret_key = "dev-secret-key-change-in-production-min-32-chars-long"

        return SecurityConfig(
            secret_key=secret_key,
            api_key=os.getenv("API_KEY"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
            password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
            require_https=self.environment == "production",
        )

    def _load_api_config(self) -> APIConfig:
        """Load API configuration."""
        cors_origins_str = os.getenv("CORS_ORIGINS", "*")
        cors_origins = [origin.strip() for origin in cors_origins_str.split(",")] if cors_origins_str != "*" else ["*"]

        return APIConfig(
            title=os.getenv("API_TITLE", "Crypto Quant Laboratory API"),
            version=os.getenv("API_VERSION", "1.0.0"),
            description=os.getenv("API_DESCRIPTION", ""),
            docs_enabled=os.getenv("API_DOCS_ENABLED", "true").lower() == "true",
            cors_origins=cors_origins,
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
        )

    def _load_external_api_config(self) -> ExternalAPIConfig:
        """Load external API configuration."""
        return ExternalAPIConfig(
            coingecko_api_key=os.getenv("COINGECKO_API_KEY"),
            binance_api_key=os.getenv("BINANCE_API_KEY"),
            binance_api_secret=os.getenv("BINANCE_API_SECRET"),
            kraken_api_key=os.getenv("KRAKEN_API_KEY"),
            kraken_api_secret=os.getenv("KRAKEN_API_SECRET"),
        )

    def _load_logging_config(self) -> LoggingConfig:
        """Load logging configuration."""
        return LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file=os.getenv("LOG_FILE"),
            max_bytes=int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024))),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
        )

    def _load_app_config(self) -> AppConfig:
        """Load application configuration."""
        return AppConfig(
            environment=self.environment,
            debug=self.debug,
            testing=self.testing,
            max_workers=int(os.getenv("MAX_WORKERS", "4")),
            timezone=os.getenv("TIMEZONE", "UTC"),
        )

    def _log_config_status(self):
        """Log configuration status without exposing secrets."""
        logger.info(f"Configuration loaded for environment: {self.environment}")
        logger.info(f"Debug mode: {self.debug}")
        logger.info(f"Testing mode: {self.testing}")
        logger.info(f"Database: {self.database.url.split('://')[0] if '://' in self.database.url else 'unknown'}")
        logger.info(f"Security: Secret key {'set' if self.security.secret_key else 'not set'}")
        logger.info(f"API Docs: {'enabled' if self.api.docs_enabled else 'disabled'}")
        logger.info(f"Rate Limiting: {'enabled' if self.api.rate_limit_enabled else 'disabled'}")

    def validate(self) -> bool:
        """
        Validate all configuration settings.

        Returns:
            True if all settings are valid

        Raises:
            ValueError: If any required setting is missing or invalid
        """
        try:
            # Validate each config section
            self.database = DatabaseConfig(**self.database.dict())
            self.security = SecurityConfig(**self.security.dict())
            self.api = APIConfig(**self.api.dict())
            self.external_apis = ExternalAPIConfig(**self.external_apis.dict())
            self.logging = LoggingConfig(**self.logging.dict())
            self.app = AppConfig(**self.app.dict())

            logger.info("Configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Invalid configuration: {e}")

    def get_safe_config(self) -> Dict[str, Any]:
        """
        Get configuration dict with secrets masked.

        Returns:
            Dictionary with safe configuration values
        """
        return {
            "environment": self.environment,
            "debug": self.debug,
            "testing": self.testing,
            "database": {
                "url": self.database.url.split('://')[0] + '://***' if '://' in self.database.url else '***',
                "pool_size": self.database.pool_size,
            },
            "security": {
                "secret_key": "***" if self.security.secret_key else "NOT SET",
                "api_key": "***" if self.security.api_key else None,
                "jwt_algorithm": self.security.jwt_algorithm,
            },
            "api": {
                "title": self.api.title,
                "version": self.api.version,
                "docs_enabled": self.api.docs_enabled,
                "rate_limit_enabled": self.api.rate_limit_enabled,
            },
            "external_apis": {
                "coingecko": "set" if self.external_apis.coingecko_api_key else None,
                "binance": "set" if self.external_apis.binance_api_key else None,
                "kraken": "set" if self.external_apis.kraken_api_key else None,
            },
        }


# ============================================================================
# GLOBAL CONFIGURATION INSTANCE
# ============================================================================

_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance (singleton)
    """
    global _config
    if _config is None:
        _config = Config()
        _config.validate()
    return _config


def reload_config() -> Config:
    """
    Reload configuration from environment variables.

    Returns:
        New Config instance
    """
    global _config
    _config = Config()
    _config.validate()
    return _config


# ============================================================================
# ENVIRONMENT VARIABLE VALIDATION
# ============================================================================

def validate_required_env_vars() -> bool:
    """
    Validate that all required environment variables are set.

    Returns:
        True if all required vars are set

    Raises:
        ValueError: If any required environment variable is missing
    """
    config = get_config()

    # Required for production
    if config.environment == "production":
        required_vars = ["SECRET_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables for production: {', '.join(missing_vars)}"
            )

    return True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_production() -> bool:
    """Check if running in production environment."""
    return get_config().environment == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return get_config().environment == "development"


def is_testing() -> bool:
    """Check if running in testing mode."""
    return get_config().testing


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a secret value from environment variables.

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Secret value or default
    """
    value = os.getenv(key, default)

    if value and key.lower() in ['secret', 'password', 'key', 'token']:
        # Don't log secret values
        logger.debug(f"Retrieved secret: {key[:3]}***")

    return value
