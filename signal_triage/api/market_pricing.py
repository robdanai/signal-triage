"""
Market Pricing Client with Switchable Providers.

Unified interface for real-time market data from multiple providers:
- Alpha Vantage (free tier: 25 calls/day, premium: up to 1200/min)
- IEX Cloud (commercial, pay-as-you-go)
- FRED (Federal Reserve Economic Data - Treasury yields)

Automatically selects best available provider based on configuration.
Includes rate limiting, caching, and error handling.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

from signal_triage.config import get_config
from signal_triage.infrastructure.rate_limiter import get_rate_limiter
from signal_triage.infrastructure.cache import get_cache_manager
from signal_triage.infrastructure.circuit_breaker import get_circuit_breaker
from signal_triage.infrastructure.retry import get_retry_strategy


logger = logging.getLogger(__name__)


class PricingProvider(Enum):
    """Available pricing data providers."""
    ALPHA_VANTAGE = "alphavantage"
    IEX_CLOUD = "iexcloud"
    FRED = "fred"


class MarketPricingClient:
    """
    Market pricing client with automatic provider selection.
    
    Provides unified interface for stock prices, yields, spreads, and market data.
    """
    
    def __init__(self, preferred_provider: Optional[str] = None):
        """
        Initialize market pricing client.
        
        Args:
            preferred_provider: Preferred provider ("alphavantage", "iexcloud", "fred").
                                If None or unavailable, auto-select best available.
        """
        if requests is None:
            raise ImportError(
                "Market pricing client requires 'requests' package. "
                "Install: pip install requests"
            )
        
        self.config = get_config()
        self.rate_limiter = get_rate_limiter()
        self.cache = get_cache_manager()
        self.retry_strategy = get_retry_strategy()
        
        self.session = requests.Session()
        
        # Determine available providers
        self.available_providers = self._detect_available_providers()
        
        # Select provider
        if preferred_provider and preferred_provider in self.available_providers:
            self.provider = preferred_provider
        else:
            # Auto-select: IEX Cloud > Alpha Vantage > FRED
            if "iexcloud" in self.available_providers:
                self.provider = "iexcloud"
            elif "alphavantage" in self.available_providers:
                self.provider = "alphavantage"
            elif "fred" in self.available_providers:
                self.provider = "fred"
            else:
                raise RuntimeError(
                    "No market pricing providers available. "
                    "Set ALPHAVANTAGE_API_KEY, IEXCLOUD_API_TOKEN, or FRED_API_KEY."
                )
        
        logger.info(f"MarketPricingClient initialized with provider: {self.provider}")
    
    def _detect_available_providers(self) -> set[str]:
        """Detect which providers are available based on API keys."""
        available = set()
        
        if self.config.api.alphavantage_api_key:
            available.add("alphavantage")
        
        if self.config.api.iexcloud_api_token:
            available.add("iexcloud")
        
        if self.config.api.fred_api_key:
            available.add("fred")
        
        return available
    
    def _api_call(self, provider: str, url: str, params: dict) -> requests.Response:
        """
        Make API call with rate limiting and retry.
        
        Args:
            provider: Provider name for rate limiting.
            url: API endpoint URL.
            params: Query parameters.
        
        Returns:
            Response object.
        """
        # Acquire rate limit token
        self.rate_limiter.acquire(provider)
        
        # Get circuit breaker for provider
        circuit_breaker = get_circuit_breaker(provider)
        
        # Make request with circuit breaker and retry
        def _request():
            timeout = self.config.api.alphavantage_timeout  # Use generic timeout
            resp = self.session.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        
        return circuit_breaker.call(
            lambda: self.retry_strategy.call(_request)
        )
    
    def get_stock_price(self, symbol: str) -> dict[str, Any]:
        """
        Get current stock price.
        
        Args:
            symbol: Stock ticker (e.g., "AAPL").
        
        Returns:
            Dict with price, symbol, volume, market_cap, source, date.
        """
        cache_key = self.cache.make_key(self.provider, "stock_price", symbol=symbol.upper())
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Fetch from provider
        if self.provider == "alphavantage":
            result = self._get_stock_price_alphavantage(symbol)
        elif self.provider == "iexcloud":
            result = self._get_stock_price_iexcloud(symbol)
        else:
            result = {
                "symbol": symbol,
                "price": None,
                "error": f"Provider {self.provider} does not support stock prices",
                "source": self.provider,
            }
        
        # Cache result
        self.cache.set(cache_key, result, ttl=self.config.cache.ttl_stock_prices)
        return result
    
    def _get_stock_price_alphavantage(self, symbol: str) -> dict[str, Any]:
        """Get stock price from Alpha Vantage."""
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.config.api.alphavantage_api_key,
            }
            
            resp = self._api_call("alphavantage", url, params)
            data = resp.json()
            
            quote = data.get("Global Quote", {})
            price = quote.get("05. price")
            trading_day = quote.get("07. latest trading day")
            
            if price:
                return {
                    "symbol": symbol,
                    "price": float(price),
                    "currency": "USD",
                    "trading_day": trading_day,
                    "source": f"Alpha Vantage (Global Quote for {symbol})",
                    "date": self._today_iso(),
                }
        except Exception as e:
            logger.error(f"Alpha Vantage stock price error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "price": None,
                "error": str(e),
                "source": "Alpha Vantage (failed)",
            }
        
        return {
            "symbol": symbol,
            "price": None,
            "source": "Alpha Vantage (no data)",
        }
    
    def _get_stock_price_iexcloud(self, symbol: str) -> dict[str, Any]:
        """Get stock price from IEX Cloud."""
        try:
            url = f"https://cloud.iexapis.com/stable/stock/{symbol}/quote"
            params = {"token": self.config.api.iexcloud_api_token}
            
            resp = self._api_call("iexcloud", url, params)
            data = resp.json()
            
            return {
                "symbol": data.get("symbol", symbol),
                "price": data.get("latestPrice"),
                "volume": data.get("latestVolume"),
                "market_cap": data.get("marketCap"),
                "pe_ratio": data.get("peRatio"),
                "week_52_high": data.get("week52High"),
                "week_52_low": data.get("week52Low"),
                "ytd_change": data.get("ytdChange"),
                "source": f"IEX Cloud (quote for {symbol})",
                "date": self._today_iso(),
            }
        except Exception as e:
            logger.error(f"IEX Cloud stock price error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "price": None,
                "error": str(e),
                "source": "IEX Cloud (failed)",
            }
    
    def get_treasury_yield(self, maturity: str = "10Y") -> dict[str, Any]:
        """
        Get US Treasury yield.
        
        Args:
            maturity: Treasury maturity ("2Y", "5Y", "10Y", "30Y").
        
        Returns:
            Dict with yield_pct, maturity, date, source.
        """
        # FRED is primary source for Treasury yields
        if "fred" not in self.available_providers:
            return {
                "yield_pct": None,
                "maturity": maturity,
                "error": "FRED API key not configured",
                "source": "FRED (unavailable)",
            }
        
        cache_key = self.cache.make_key("fred", "treasury_yield", maturity=maturity)
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            series_map = {
                "2Y": "DGS2",
                "5Y": "DGS5",
                "10Y": "DGS10",
                "30Y": "DGS30",
            }
            series_id = series_map.get(maturity, "DGS10")
            
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                "series_id": series_id,
                "api_key": self.config.api.fred_api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 1,
            }
            
            resp = self._api_call("fred", url, params)
            data = resp.json()
            
            obs = data.get("observations", [])
            if obs:
                latest = obs[0]
                yield_val = latest.get("value")
                obs_date = latest.get("date")
                
                if yield_val and yield_val != ".":
                    result = {
                        "yield_pct": float(yield_val),
                        "maturity": maturity,
                        "date": obs_date,
                        "source": f"FRED (series {series_id})",
                    }
                    self.cache.set(cache_key, result, ttl=self.config.cache.ttl_treasury_yields)
                    return result
        except Exception as e:
            logger.error(f"FRED treasury yield error for {maturity}: {e}")
            return {
                "yield_pct": None,
                "maturity": maturity,
                "error": str(e),
                "source": "FRED (failed)",
            }
        
        return {
            "yield_pct": None,
            "maturity": maturity,
            "source": "FRED (no data)",
        }
    
    def calculate_yield_spread(
        self,
        target_yield: float,
        treasury_maturity: str = "10Y"
    ) -> dict[str, Any]:
        """
        Calculate yield spread over Treasury (OAS approximation).
        
        Args:
            target_yield: Target debt yield (e.g., 12.5% for distressed bond).
            treasury_maturity: Comparable Treasury maturity.
        
        Returns:
            Dict with spread_bps, target_yield, treasury_yield, source.
        """
        treasury = self.get_treasury_yield(treasury_maturity)
        treasury_yield = treasury.get("yield_pct")
        
        if treasury_yield is None:
            return {
                "spread_bps": None,
                "target_yield": target_yield,
                "treasury_yield": None,
                "error": "Treasury yield unavailable",
                "source": "Spread calculation failed",
            }
        
        spread_bps = (target_yield - treasury_yield) * 100
        return {
            "spread_bps": round(spread_bps, 1),
            "target_yield": target_yield,
            "treasury_yield": treasury_yield,
            "maturity": treasury_maturity,
            "source": f"Spread over {treasury_maturity} Treasury (calculated)",
            "date": treasury.get("date"),
        }
    
    def get_company_financials(self, symbol: str) -> dict[str, Any]:
        """
        Get company financials.
        
        Args:
            symbol: Stock ticker.
        
        Returns:
            Dict with revenue, total_debt, ebitda, filing_date, source.
        """
        if self.provider != "iexcloud":
            return {
                "symbol": symbol,
                "error": f"Provider {self.provider} does not support company financials",
                "source": self.provider,
            }
        
        cache_key = self.cache.make_key("iexcloud", "company_financials", symbol=symbol.upper())
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            # Get income statement and balance sheet
            income_url = f"https://cloud.iexapis.com/stable/stock/{symbol}/income"
            balance_url = f"https://cloud.iexapis.com/stable/stock/{symbol}/balance-sheet"
            params = {"token": self.config.api.iexcloud_api_token, "last": 1}
            
            revenue = None
            ebitda = None
            total_debt = None
            filing_date = None
            
            # Income statement
            resp = self._api_call("iexcloud", income_url, params)
            income_data = resp.json()
            
            if income_data and "income" in income_data:
                latest = income_data["income"][0]
                revenue = latest.get("totalRevenue")
                ebitda = latest.get("ebitda")
                filing_date = latest.get("fiscalDate")
            
            # Balance sheet
            resp = self._api_call("iexcloud", balance_url, params)
            balance_data = resp.json()
            
            if balance_data and "balancesheet" in balance_data:
                latest = balance_data["balancesheet"][0]
                total_debt = latest.get("totalDebt") or latest.get("longTermDebt")
            
            result = {
                "symbol": symbol,
                "revenue": revenue,
                "total_debt": total_debt,
                "ebitda": ebitda,
                "filing_date": filing_date,
                "source": f"IEX Cloud (financials for {symbol})",
                "date": self._today_iso(),
            }
            
            self.cache.set(cache_key, result, ttl=self.config.cache.ttl_company_financials)
            return result
            
        except Exception as e:
            logger.error(f"IEX Cloud financials error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "source": "IEX Cloud (failed)",
            }
    
    def _today_iso(self) -> str:
        """Get current date in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
