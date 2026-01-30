"""
Production Configuration Management for Signal Triage Market Data Layer.

Centralized configuration for API keys, rate limits, timeouts, and caching.
Environment-based settings with validation and secure defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class APIConfig:
    """Configuration for external API clients."""
    
    # SEC EDGAR (Free)
    # NOTE: SEC requires a valid User-Agent with contact info
    # Set SEC_USER_AGENT environment variable with your email:
    # Example: "YourCompany/1.0 (your.email@example.com)"
    sec_user_agent: str = field(
        default_factory=lambda: os.getenv(
            "SEC_USER_AGENT", 
            "SignalTriage/1.0 (+https://github.com/yourusername/Signal-Triage; sample@example.com)"
        )
    )
    sec_rate_limit: int = 10  # requests per second (SEC guidelines: 10 req/sec max)
    sec_timeout: int = 30
    
    # FRED (Free with API key)
    fred_api_key: Optional[str] = field(default_factory=lambda: os.getenv("FRED_API_KEY"))
    fred_rate_limit: int = 120  # requests per minute (free tier)
    fred_timeout: int = 30
    
    # Alpha Vantage (Free tier: 25 calls/day, Premium: up to 1200/min)
    alphavantage_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ALPHAVANTAGE_API_KEY"))
    alphavantage_rate_limit: int = 5  # requests per minute (conservative for free tier)
    alphavantage_timeout: int = 30
    
    # IEX Cloud (Commercial, pay-as-you-go)
    iexcloud_api_token: Optional[str] = field(default_factory=lambda: os.getenv("IEXCLOUD_API_TOKEN"))
    iexcloud_rate_limit: int = 100  # requests per second (varies by plan)
    iexcloud_timeout: int = 30
    
    # 9fin (Commercial)
    ninefin_api_key: Optional[str] = field(default_factory=lambda: os.getenv("NINEFIN_API_KEY"))
    ninefin_rate_limit: int = 60  # requests per minute (estimated)
    ninefin_timeout: int = 30
    
    # Bloomberg Terminal
    bloomberg_api_key: Optional[str] = field(default_factory=lambda: os.getenv("BLOOMBERG_API_KEY"))
    bloomberg_rate_limit: int = 100  # requests per minute (estimated)
    bloomberg_timeout: int = 60
    
    # Credit Rating Agencies (Commercial subscriptions required)
    sp_capital_iq_api_key: Optional[str] = field(default_factory=lambda: os.getenv("SP_CAPITAL_IQ_API_KEY"))
    moodys_api_key: Optional[str] = field(default_factory=lambda: os.getenv("MOODYS_API_KEY"))
    fitch_api_key: Optional[str] = field(default_factory=lambda: os.getenv("FITCH_API_KEY"))
    
    # Retry configuration
    max_retries: int = 3
    retry_backoff_factor: float = 2.0  # Exponential backoff: 1s, 2s, 4s
    retry_statuses: tuple = (429, 500, 502, 503, 504)  # HTTP codes to retry
    
    # Circuit breaker configuration
    circuit_breaker_failure_threshold: int = 5  # Open circuit after N failures
    circuit_breaker_recovery_timeout: int = 60  # Seconds before retry
    circuit_breaker_expected_exception: type = Exception


@dataclass
class CacheConfig:
    """Configuration for caching layer."""
    
    # Cache backend: "redis", "file", "memory"
    backend: str = field(default_factory=lambda: os.getenv("CACHE_BACKEND", "file"))
    
    # Redis configuration (if backend = "redis")
    redis_host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    redis_port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    redis_db: int = field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))
    redis_password: Optional[str] = field(default_factory=lambda: os.getenv("REDIS_PASSWORD"))
    
    # File cache configuration (if backend = "file")
    file_cache_dir: str = field(default_factory=lambda: os.getenv("CACHE_DIR", ".cache"))
    
    # TTL (time-to-live) for different data types in seconds
    ttl_sec_filings: int = 3600  # 1 hour (filings don't change frequently)
    ttl_treasury_yields: int = 900  # 15 minutes (updated throughout trading day)
    ttl_stock_prices: int = 300  # 5 minutes (real-time pricing)
    ttl_credit_ratings: int = 86400  # 24 hours (ratings change infrequently)
    ttl_company_financials: int = 21600  # 6 hours (quarterly updates)
    ttl_default: int = 1800  # 30 minutes (conservative default)
    
    # Cache size limits
    max_memory_cache_items: int = 1000
    max_file_cache_size_mb: int = 500


@dataclass
class DatabaseConfig:
    """Configuration for database persistence layer."""
    
    # Database URL (SQLAlchemy format)
    # Examples:
    #   SQLite: sqlite:///signal_triage.db
    #   PostgreSQL: postgresql://user:pass@localhost:5432/signal_triage
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", 
            "sqlite:///signal_triage.db"
        )
    )
    
    # Connection pool settings
    pool_size: int = 5
    pool_max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600  # Recycle connections after 1 hour
    
    # Echo SQL statements (debug mode)
    echo_sql: bool = field(default_factory=lambda: os.getenv("SQL_ECHO", "false").lower() == "true")


@dataclass
class FastAPIConfig:
    """Configuration for FastAPI application."""
    
    # Server settings
    host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    workers: int = field(default_factory=lambda: int(os.getenv("API_WORKERS", "4")))
    
    # Security
    api_key_header: str = "X-API-Key"
    api_keys: list[str] = field(
        default_factory=lambda: os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else []
    )
    cors_origins: list[str] = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(",")
    )
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    # Webhook configuration
    webhook_timeout: int = 30
    webhook_retry_attempts: int = 3
    
    # Job processing
    max_concurrent_jobs: int = 10
    job_timeout_seconds: int = 300  # 5 minutes max per analysis job


@dataclass
class Config:
    """Master configuration object."""
    
    api: APIConfig = field(default_factory=APIConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    fastapi: FastAPIConfig = field(default_factory=FastAPIConfig)
    
    # Environment
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    def validate(self) -> list[str]:
        """
        Validate configuration and return list of warnings/errors.
        
        Returns:
            List of validation messages (warnings for optional features, errors for critical issues).
        """
        messages = []
        
        # Check SEC EDGAR (required for core functionality)
        if not self.api.sec_user_agent:
            messages.append("ERROR: SEC User-Agent is required for EDGAR API compliance.")
        
        # Check optional API keys (warnings only)
        if not self.api.fred_api_key:
            messages.append("WARNING: FRED_API_KEY not set. Treasury yield data will be unavailable.")
        
        if not self.api.alphavantage_api_key:
            messages.append("WARNING: ALPHAVANTAGE_API_KEY not set. Stock price data will be limited.")
        
        if not self.api.iexcloud_api_token:
            messages.append("WARNING: IEXCLOUD_API_TOKEN not set. IEX Cloud data will be unavailable.")
        
        if not self.api.ninefin_api_key:
            messages.append("WARNING: NINEFIN_API_KEY not set. 9fin recovery benchmarks unavailable.")
        
        # Database validation
        if self.database.database_url.startswith("sqlite") and self.environment == "production":
            messages.append("WARNING: SQLite not recommended for production. Use PostgreSQL.")
        
        # Cache validation
        if self.cache.backend == "redis":
            if not self.cache.redis_host:
                messages.append("ERROR: REDIS_HOST required when CACHE_BACKEND=redis.")
        
        # FastAPI security validation
        if self.environment == "production" and not self.fastapi.api_keys:
            messages.append("WARNING: No API keys configured. API will be open (not recommended for production).")
        
        return messages
    
    def get_available_providers(self) -> dict[str, bool]:
        """
        Check which market data providers are available based on configuration.
        
        Returns:
            Dict mapping provider name to availability status.
        """
        return {
            "sec_edgar": True,  # Always available (no API key required)
            "fred": bool(self.api.fred_api_key),
            "alphavantage": bool(self.api.alphavantage_api_key),
            "iexcloud": bool(self.api.iexcloud_api_token),
            "ninefin": bool(self.api.ninefin_api_key),
            "bloomberg": bool(self.api.bloomberg_api_key),
            "sp_capital_iq": bool(self.api.sp_capital_iq_api_key),
            "moodys": bool(self.api.moodys_api_key),
            "fitch": bool(self.api.fitch_api_key),
        }


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance (singleton pattern).
    
    Returns:
        Config instance loaded from environment.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """
    Force reload configuration from environment.
    
    Returns:
        Fresh Config instance.
    """
    global _config
    _config = Config()
    return _config
