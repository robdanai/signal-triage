"""
Setup configuration for Signal Triage.
Allows the package to be installed with: pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="signal-triage",
    version="0.1.0",
    description="Production-grade distressed debt analysis platform with CLI, API, and web UI",
    author="Signal Triage Team",
    author_email="contact@example.com",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        # Core dependencies
        "pypdf>=4.0.0",
        "pdfplumber>=0.10.0",
        "pytesseract>=0.3.10",
        "Pillow>=10.0.0",
        "requests>=2.28.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "tabulate>=0.9.0",
        
        # Web UI
        "streamlit>=1.30.0",
        "plotly>=5.18.0",
        
        # API & Web Server
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.4.0",
        "python-multipart>=0.0.6",
        
        # Database
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "alembic>=1.12.0",
        
        # Caching
        "redis>=5.0.0",
        
        # Security
        "pyjwt>=2.8.0",
        "cryptography>=41.0.0",
        
        # Monitoring
        "python-json-logger>=2.0.7",
        
        # Async & Background Jobs
        "pytest-asyncio>=0.21.0",
        "aiohttp>=3.9.0",
        
        # Testing
        "pytest>=7.0.0",
        "pytest-cov>=4.1.0",
        
        # Code Quality
        "black>=23.0.0",
        "flake8>=6.0.0",
    ],
    extras_require={
        "dev": [
            "pre-commit>=3.0.0",
            "isort>=5.12.0",
            "bandit>=1.7.5",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "signal-triage=signal_triage.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
