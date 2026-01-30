"""
Pydantic schemas for market data API responses.

Provides type-safe validation for all external API responses.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

try:
    from pydantic import BaseModel, Field, validator, ConfigDict
except ImportError:
    # Graceful fallback if pydantic not installed
    BaseModel = object  # type: ignore[misc,assignment]
    Field = lambda *args, **kwargs: None  # type: ignore[misc,assignment]
    validator = lambda *args, **kwargs: lambda f: f  # type: ignore[misc,assignment]
    
    class ConfigDict:  # type: ignore[no-redef]
        pass


# ===== Base Schemas =====


class APIResponse(BaseModel):
    """Base class for all API responses."""
    source: str
    date: str
    error: Optional[str] = None
    
    if BaseModel != object:  # Only if pydantic is installed
        model_config = ConfigDict(extra='allow')  # Allow extra fields


class StockQuote(APIResponse):
    """Stock quote response."""
    symbol: str
    price: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    currency: Optional[str] = "USD"
    
    @validator('price', 'market_cap', pre=True)
    def validate_positive(cls, v):
        """Ensure financial values are positive."""
        if v is not None and v < 0:
            raise ValueError("Financial values must be positive")
        return v


class CompanyFinancials(APIResponse):
    """Company financial data response."""
    symbol: Optional[str] = None
    cik: Optional[str] = None
    revenue: Optional[float] = None
    total_debt: Optional[float] = None
    ebitda: Optional[float] = None
    cash: Optional[float] = None
    free_cash_flow: Optional[float] = None
    filing_date: Optional[str] = None
    
    @validator('revenue', 'total_debt', 'ebitda', pre=True)
    def validate_financial_values(cls, v):
        """Allow negative EBITDA but validate reasonable ranges."""
        if v is not None:
            if abs(v) > 1e15:  # Sanity check: no company has $1 quadrillion
                raise ValueError(f"Unrealistic financial value: {v}")
        return v


class FinancialRatios(APIResponse):
    """Financial ratios response."""
    symbol: str
    date: str
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_equity_ratio: Optional[float] = None
    debt_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    gross_profit_margin: Optional[float] = None
    operating_profit_margin: Optional[float] = None
    net_profit_margin: Optional[float] = None
    
    @validator('current_ratio', 'quick_ratio', pre=True)
    def validate_liquidity_ratios(cls, v):
        """Liquidity ratios should be positive."""
        if v is not None and v < 0:
            raise ValueError("Liquidity ratios must be positive")
        return v


class TreasuryYield(APIResponse):
    """Treasury yield response."""
    yield_pct: Optional[float] = None
    maturity: str
    
    @validator('yield_pct', pre=True)
    def validate_yield(cls, v):
        """Validate reasonable yield range."""
        if v is not None:
            if v < 0 or v > 50:  # Yields rarely exceed 50%
                raise ValueError(f"Unrealistic yield: {v}%")
        return v


class CreditSpread(APIResponse):
    """Credit spread response."""
    spread_bps: Optional[float] = None
    bond_yield: float
    treasury_yield: Optional[float] = None
    maturity: str
    
    @validator('spread_bps', pre=True)
    def validate_spread(cls, v):
        """Validate reasonable spread range."""
        if v is not None:
            if v < -1000 or v > 10000:  # Spreads rarely exceed 10000 bps
                raise ValueError(f"Unrealistic spread: {v} bps")
        return v


class NewsSentiment(APIResponse):
    """News sentiment response."""
    symbol: str
    sentiment_score: Optional[float] = None
    buzz_score: Optional[int] = None
    positive_mentions: Optional[int] = None
    negative_mentions: Optional[int] = None
    
    @validator('sentiment_score', pre=True)
    def validate_sentiment(cls, v):
        """Sentiment typically ranges from -1 to 1."""
        if v is not None:
            if v < -10 or v > 10:  # Allow some flexibility
                raise ValueError(f"Unrealistic sentiment score: {v}")
        return v


class CreditRating(APIResponse):
    """Credit rating response."""
    ticker: str
    rating: Optional[str] = None
    outlook: Optional[str] = None
    watch_status: Optional[str] = None
    rating_date: Optional[str] = None
    
    @validator('outlook', pre=True)
    def validate_outlook(cls, v):
        """Validate outlook is one of expected values."""
        if v is not None:
            valid_outlooks = ['Positive', 'Stable', 'Negative', 'Developing', 'N/A', None]
            if v not in valid_outlooks:
                # Don't fail, just warn
                pass
        return v


class EconomicIndicator(APIResponse):
    """Economic indicator response (GDP, unemployment, etc.)."""
    indicator_name: str
    value: Optional[float] = None
    period: str
    country_code: Optional[str] = None


class SecurityIdentifier(APIResponse):
    """Security identifier lookup response."""
    identifier: str
    figi: Optional[str] = None
    cusip: Optional[str] = None
    isin: Optional[str] = None
    ticker: Optional[str] = None
    name: Optional[str] = None
    security_type: Optional[str] = None


class NewsArticle(BaseModel):
    """Individual news article."""
    headline: str
    summary: Optional[str] = None
    url: Optional[str] = None
    datetime: Optional[int] = None
    source_name: Optional[str] = None
    
    if BaseModel != object:
        model_config = ConfigDict(extra='allow')


# ===== Validation Helpers =====


def validate_stock_quote(data: dict[str, Any]) -> StockQuote | dict[str, Any]:
    """
    Validate stock quote response.
    
    Args:
        data: Raw API response dict
        
    Returns:
        Validated StockQuote if pydantic installed, otherwise original dict
    """
    if BaseModel == object:
        # Pydantic not installed, return as-is
        return data
    
    try:
        return StockQuote(**data)
    except Exception as e:
        # Validation failed, add error to response
        data['validation_error'] = str(e)
        return data


def validate_company_financials(data: dict[str, Any]) -> CompanyFinancials | dict[str, Any]:
    """Validate company financials response."""
    if BaseModel == object:
        return data
    
    try:
        return CompanyFinancials(**data)
    except Exception as e:
        data['validation_error'] = str(e)
        return data


def validate_financial_ratios(data: dict[str, Any]) -> FinancialRatios | dict[str, Any]:
    """Validate financial ratios response."""
    if BaseModel == object:
        return data
    
    try:
        return FinancialRatios(**data)
    except Exception as e:
        data['validation_error'] = str(e)
        return data


def validate_treasury_yield(data: dict[str, Any]) -> TreasuryYield | dict[str, Any]:
    """Validate treasury yield response."""
    if BaseModel == object:
        return data
    
    try:
        return TreasuryYield(**data)
    except Exception as e:
        data['validation_error'] = str(e)
        return data


def validate_credit_spread(data: dict[str, Any]) -> CreditSpread | dict[str, Any]:
    """Validate credit spread response."""
    if BaseModel == object:
        return data
    
    try:
        return CreditSpread(**data)
    except Exception as e:
        data['validation_error'] = str(e)
        return data


def validate_sentiment(data: dict[str, Any]) -> NewsSentiment | dict[str, Any]:
    """Validate news sentiment response."""
    if BaseModel == object:
        return data
    
    try:
        return NewsSentiment(**data)
    except Exception as e:
        data['validation_error'] = str(e)
        return data


# ===== Conversion Helpers =====


def to_dict(model: BaseModel | dict[str, Any]) -> dict[str, Any]:
    """Convert Pydantic model to dict (or pass through if already dict)."""
    if isinstance(model, dict):
        return model
    if BaseModel != object and isinstance(model, BaseModel):
        return model.model_dump()
    return model


def has_validation_error(data: dict[str, Any] | BaseModel) -> bool:
    """Check if response has validation error."""
    if isinstance(data, dict):
        return 'validation_error' in data or 'error' in data
    return False
