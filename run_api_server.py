#!/usr/bin/env python
"""
Signal Triage API Server Launcher.

Production-grade startup script with logging, configuration validation,
and graceful shutdown.

Usage:
    python run_api_server.py                    # Development mode
    python run_api_server.py --production       # Production mode
    python run_api_server.py --help             # Show help
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Main entry point for API server."""
    parser = argparse.ArgumentParser(
        description="Signal Triage API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_api_server.py                          # Development (auto-reload)
  python run_api_server.py --production             # Production (4 workers)
  python run_api_server.py --host 0.0.0.0 --port 8080
  python run_api_server.py --workers 8 --log-level info
        """
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind (default: 8000)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Log level (default: info)"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode (4 workers, no reload)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate configuration and exit"
    )
    
    args = parser.parse_args()
    
    # Import after argparse to avoid slow imports for --help
    from signal_triage.config import get_config
    from signal_triage.logging_config import setup_logging
    
    # Production mode overrides
    if args.production:
        args.host = "0.0.0.0"
        args.workers = 4
        args.reload = False
        args.log_level = "info"
    
    # Setup logging
    setup_logging(
        log_level=args.log_level.upper(),
        log_file="logs/api.log" if args.production else None,
        json_format=args.production
    )
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("Signal Triage API Server")
    logger.info("=" * 70)
    
    # Load and validate configuration
    config = get_config()
    validation_messages = config.validate()
    
    if validation_messages:
        logger.info("\nConfiguration Validation:")
        for msg in validation_messages:
            if msg.startswith("ERROR"):
                logger.error(f"  {msg}")
            else:
                logger.warning(f"  {msg}")
    
    if any(msg.startswith("ERROR") for msg in validation_messages):
        logger.error("\nConfiguration errors found. Cannot start server.")
        return 1
    
    # Show available providers
    providers = config.get_available_providers()
    logger.info("\nAvailable Market Data Providers:")
    for provider, available in providers.items():
        status = "✓" if available else "✗"
        logger.info(f"  [{status}] {provider}")
    
    # Initialize database
    from signal_triage.database import init_db
    logger.info("\nInitializing database...")
    try:
        init_db()
        logger.info("  ✓ Database initialized")
    except Exception as e:
        logger.error(f"  ✗ Database initialization failed: {e}")
        return 1
    
    if args.validate_only:
        logger.info("\nConfiguration valid. Exiting (--validate-only).")
        return 0
    
    # Start server
    logger.info("\nStarting API server...")
    logger.info(f"  Host: {args.host}")
    logger.info(f"  Port: {args.port}")
    logger.info(f"  Workers: {args.workers}")
    logger.info(f"  Reload: {args.reload}")
    logger.info(f"  Log level: {args.log_level.upper()}")
    logger.info(f"\n  API docs: http://{args.host}:{args.port}/docs")
    logger.info(f"  Health check: http://{args.host}:{args.port}/")
    logger.info("\n" + "=" * 70)
    
    import uvicorn
    
    uvicorn.run(
        "signal_triage.fastapi_app.main:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True,
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
