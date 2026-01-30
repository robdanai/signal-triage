"""
Async versions of market data APIs for parallel fetching.

Example:
    # Sequential (slow):
    quote1 = get_stock_quote("AAPL")  # 200ms
    quote2 = get_stock_quote("MSFT")  # 200ms
    # Total: 400ms
    
    # Parallel (fast):
    quotes = await fetch_quotes_async(["AAPL", "MSFT"])
    # Total: 200ms
"""

from __future__ import annotations

import asyncio
from typing import Any

try:
    import aiohttp
except ImportError:
    aiohttp = None  # type: ignore[assignment]


async def fetch_stock_quotes_async(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """
    Fetch stock quotes for multiple symbols in parallel.
    
    Args:
        symbols: List of stock tickers
        
    Returns:
        Dict mapping symbol → quote data
    
    Requires: aiohttp (pip install aiohttp)
    """
    if aiohttp is None:
        raise ImportError("aiohttp required for async support: pip install aiohttp")
    
    # Import sync functions
    from signal_triage.agents.market_data_live import yahoo_get_stock_quote
    
    # For now, run sync functions in thread pool
    # (Full async implementation would use aiohttp directly)
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, yahoo_get_stock_quote, symbol)
        for symbol in symbols
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        symbol: result if not isinstance(result, Exception) else {"error": str(result)}
        for symbol, result in zip(symbols, results)
    }


async def fetch_company_financials_async(
    symbols: list[str],
    ciks: list[str | None] | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Fetch company financials for multiple companies in parallel.
    
    Args:
        symbols: List of stock tickers
        ciks: Optional list of CIKs (parallel to symbols)
        
    Returns:
        Dict mapping symbol → financials data
    """
    if aiohttp is None:
        raise ImportError("aiohttp required for async support")
    
    from signal_triage.agents.market_data_live import get_company_financials_with_fallback
    
    if ciks is None:
        ciks = [None] * len(symbols)
    
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, get_company_financials_with_fallback, symbol, cik)
        for symbol, cik in zip(symbols, ciks)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        symbol: result if not isinstance(result, Exception) else {"error": str(result)}
        for symbol, result in zip(symbols, results)
    }


# Convenience function for common use case
async def fetch_comprehensive_data_async(
    symbols: list[str],
) -> dict[str, dict[str, Any]]:
    """
    Fetch quotes and financials for multiple symbols in parallel.
    
    Args:
        symbols: List of stock tickers
        
    Returns:
        Dict with 'quotes' and 'financials' keys
    """
    quotes_task = fetch_stock_quotes_async(symbols)
    financials_task = fetch_company_financials_async(symbols)
    
    quotes, financials = await asyncio.gather(quotes_task, financials_task)
    
    return {
        "quotes": quotes,
        "financials": financials,
    }
