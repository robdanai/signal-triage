"""
Market Data API Configuration Management

Centralized configuration for API priorities, rate limits, and fallback behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class APIConfig:
    """Configuration for a single API."""
    name: str
    enabled: bool = True
    priority: int = 50  # Lower = higher priority
    rate_limit_per_day: int | None = None
    rate_limit_per_minute: int | None = None
    requires_key: bool = False
    is_free: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes default


# API Priority Configuration
# Lower priority number = tried first in fallback chain

STOCK_QUOTE_APIS = {
    "yahoo": APIConfig(
        name="Yahoo Finance",
        priority=10,  # Try first (fast, free, no key)
        rate_limit_per_minute=60,
        requires_key=False,
        is_free=True,
        cache_ttl_seconds=300,
    ),
    "alphavantage": APIConfig(
        name="Alpha Vantage",
        priority=20,
        rate_limit_per_day=25,  # Free tier limit
        requires_key=True,
        is_free=True,
        cache_ttl_seconds=300,
    ),
    "polygon": APIConfig(
        name="Polygon.io",
        priority=30,
        rate_limit_per_minute=5,  # Free tier limit
        requires_key=True,
        is_free=True,
        cache_ttl_seconds=300,
    ),
    "iexcloud": APIConfig(
        name="IEX Cloud",
        priority=40,
        rate_limit_per_day=50000,  # Depends on plan
        requires_key=True,
        is_free=False,
        cache_ttl_seconds=60,  # Shorter cache for paid API
    ),
}

COMPANY_FINANCIALS_APIS = {
    "sec_edgar": APIConfig(
        name="SEC EDGAR",
        priority=5,  # Highest priority (most reliable for US companies)
        rate_limit_per_minute=10,  # SEC rate limiting
        requires_key=False,
        is_free=True,
        cache_ttl_seconds=3600,  # 1 hour (financials don't change often)
    ),
    "yahoo": APIConfig(
        name="Yahoo Finance",
        priority=10,
        rate_limit_per_minute=60,
        requires_key=False,
        is_free=True,
        cache_ttl_seconds=3600,
    ),
    "iexcloud": APIConfig(
        name="IEX Cloud",
        priority=20,
        requires_key=True,
        is_free=False,
        cache_ttl_seconds=1800,
    ),
    "fmp": APIConfig(
        name="Financial Modeling Prep",
        priority=30,
        rate_limit_per_day=250,
        requires_key=True,
        is_free=True,
        cache_ttl_seconds=3600,
    ),
}

NEWS_SENTIMENT_APIS = {
    "finnhub": APIConfig(
        name="Finnhub",
        priority=10,
        rate_limit_per_minute=60,
        requires_key=True,
        is_free=True,
        cache_ttl_seconds=1800,  # 30 minutes
    ),
}

MACRO_DATA_APIS = {
    "fred": APIConfig(
        name="FRED",
        priority=10,
        requires_key=True,
        is_free=True,
        cache_ttl_seconds=3600,  # 1 hour
    ),
    "worldbank": APIConfig(
        name="World Bank",
        priority=20,
        requires_key=False,
        is_free=True,
        cache_ttl_seconds=86400,  # 24 hours (macro data changes slowly)
    ),
    "bls": APIConfig(
        name="BLS",
        priority=20,
        requires_key=False,
        is_free=True,
        cache_ttl_seconds=86400,  # 24 hours
    ),
}


def get_api_priority_order(api_category: str) -> list[str]:
    """
    Get API names in priority order for a given category.

    Args:
        api_category: "stock_quotes", "financials", "sentiment", "macro"

    Returns:
        List of API names sorted by priority (lowest first)
    """
    category_map = {
        "stock_quotes": STOCK_QUOTE_APIS,
        "financials": COMPANY_FINANCIALS_APIS,
        "sentiment": NEWS_SENTIMENT_APIS,
        "macro": MACRO_DATA_APIS,
    }
    
    apis = category_map.get(api_category, {})
    return sorted(apis.keys(), key=lambda k: apis[k].priority)


def get_cache_ttl(api_name: str, api_category: str) -> int:
    """
    Get recommended cache TTL for an API.

    Args:
        api_name: API identifier (e.g., "yahoo", "sec_edgar")
        api_category: Category of data

    Returns:
        Cache TTL in seconds
    """
    category_map = {
        "stock_quotes": STOCK_QUOTE_APIS,
        "financials": COMPANY_FINANCIALS_APIS,
        "sentiment": NEWS_SENTIMENT_APIS,
        "macro": MACRO_DATA_APIS,
    }
    
    apis = category_map.get(api_category, {})
    config = apis.get(api_name)
    return config.cache_ttl_seconds if config else 300


def should_use_api(api_name: str, api_category: str) -> tuple[bool, str]:
    """
    Check if an API should be used (enabled, key available if required).

    Args:
        api_name: API identifier
        api_category: Category of data

    Returns:
        (should_use, reason) tuple
    """
    import os
    
    category_map = {
        "stock_quotes": STOCK_QUOTE_APIS,
        "financials": COMPANY_FINANCIALS_APIS,
        "sentiment": NEWS_SENTIMENT_APIS,
        "macro": MACRO_DATA_APIS,
    }
    
    apis = category_map.get(api_category, {})
    config = apis.get(api_name)
    
    if not config:
        return False, "API not found in configuration"
    
    if not config.enabled:
        return False, "API disabled in configuration"
    
    if config.requires_key:
        key_map = {
            "alphavantage": "ALPHAVANTAGE_API_KEY",
            "polygon": "POLYGON_API_KEY",
            "iexcloud": "IEXCLOUD_API_TOKEN",
            "fmp": "FMP_API_KEY",
            "finnhub": "FINNHUB_API_KEY",
            "fred": "FRED_API_KEY",
        }
        
        env_var = key_map.get(api_name)
        if env_var and not os.environ.get(env_var, "").strip():
            return False, f"API key {env_var} not set"
    
    return True, "OK"
