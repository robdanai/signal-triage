# Contributing to Signal Triage

Thank you for your interest in contributing to Signal Triage! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Agent-Specific Guidelines](#agent-specific-guidelines)

## Code of Conduct

Be professional, respectful, and collaborative. Focus on technical accuracy and constructive feedback.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Docker and docker-compose (optional, for containerized development)
- PostgreSQL 15+ (optional, SQLite works for development)

### First-Time Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/signal-triage.git
   cd signal-triage
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -e .
   pip install -r requirements.txt
   ```

4. **Copy environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run tests to verify setup**
   ```bash
   python -m pytest tests/ -v
   ```

## Development Setup

### Using Docker (Recommended)

```bash
# Start all services (API, database, redis, dashboard)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Local Development

```bash
# Install in editable mode
pip install -e .

# Run API server
python run_api_server.py

# Run dashboard
streamlit run signal_triage/ui/dashboard.py

# Run CLI
python main.py path/to/document.txt --pipeline
```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Make your changes**
   - Follow the code style guidelines below
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests locally**
   ```bash
   # Run all tests
   python -m pytest tests/ -v
   
   # Run specific test file
   python -m pytest tests/test_recovery_engine.py -v
   
   # Run with coverage
   python -m pytest tests/ --cov=signal_triage --cov-report=html
   ```

4. **Check code quality**
   ```bash
   # Format code
   black .
   isort .
   
   # Lint code
   flake8 signal_triage/ tests/
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   # Then create PR on GitHub
   ```

## Testing

### Test Structure

```
tests/
├── test_analyzer.py          # Core analysis tests
├── test_recovery_engine.py   # Waterfall and recovery tests
├── test_lme_parser.py        # LME detection tests
├── test_pipeline.py          # End-to-end pipeline tests
├── test_api_integration.py   # API integration tests
└── fixtures/                 # Test data
```

### Writing Tests

```python
import pytest
from signal_triage.recovery_engine import run_waterfall

def test_waterfall_basic_recovery():
    """Test basic waterfall calculation."""
    tranches = [
        {"name": "Senior", "claim": 100},
        {"name": "Junior", "claim": 50}
    ]
    
    result = run_waterfall(tranches, ev=120)
    
    assert result["tranches"][0]["recovery_pct"] == 100
    assert result["tranches"][1]["recovery_pct"] == 40
    assert result["fulcrum"] == "Junior"
```

### Running Specific Test Categories

```bash
# Unit tests only
python -m pytest tests/test_analyzer.py tests/test_recovery_engine.py -v

# Integration tests
python -m pytest tests/test_pipeline.py tests/test_api_integration.py -v

# Tests for specific agent
python -m pytest tests/test_auditor.py tests/test_benchmarker.py -v
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints for function signatures
- Maximum line length: 127 characters
- Use docstrings for all public functions and classes

### Example

```python
from typing import List, Dict, Optional
from decimal import Decimal

def calculate_recovery(
    tranches: List[Dict[str, any]],
    enterprise_value: Decimal,
    adjustment: Optional[Decimal] = None
) -> Dict[str, any]:
    """
    Calculate recovery percentages for each tranche.
    
    Args:
        tranches: List of debt tranches with name and claim.
        enterprise_value: Total enterprise value available.
        adjustment: Optional EV adjustment (e.g., for LME leakage).
    
    Returns:
        Dictionary with tranches, recoveries, and fulcrum.
    """
    # Implementation here
    pass
```

### Formatting Tools

```bash
# Auto-format with black (required)
black signal_triage/ tests/

# Sort imports with isort (required)
isort signal_triage/ tests/

# Check style with flake8 (warning only)
flake8 signal_triage/ tests/ --max-line-length=127
```

## Commit Messages

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(librarian): add OCR support for scanned PDFs

Implements Tesseract OCR integration for extracting text from
scanned credit agreements. Includes confidence scoring and
fallback to manual review when confidence < 80%.

Closes #123

---

fix(waterfall): correct APR violation detection for pari passu tranches

Previously failed to detect violations when multiple tranches
at same priority level. Now correctly checks pro-rata recoveries.

---

docs(api): update FastAPI endpoint examples

Added examples for webhook configuration and batch processing.
```

## Pull Request Process

1. **Ensure all tests pass**
   ```bash
   python -m pytest tests/ -v
   ```

2. **Update documentation**
   - Add/update docstrings
   - Update relevant markdown files in `docs/`
   - Update CHANGELOG.md with your changes

3. **Check agent handoffs** (if modifying pipeline)
   - See [Agent-Specific Guidelines](#agent-specific-guidelines)
   - Verify handoffs between agents still work
   - Update `.cursor/agents/ORCHESTRATION.md` if needed

4. **Create pull request**
   - Fill out the PR template
   - Link related issues
   - Request review from maintainers

5. **Address review feedback**
   - Make requested changes
   - Push updates to the same branch
   - Re-request review

6. **Merge requirements**
   - All CI checks passing
   - At least one approval from maintainer
   - No merge conflicts
   - CHANGELOG.md updated

## Agent-Specific Guidelines

Signal Triage uses a multi-agent architecture. When modifying agents, follow these rules:

### Agent Responsibilities

| Agent | Objective | Key Outputs |
|-------|-----------|-------------|
| Author | Ingestion, configs, CLI | DocumentChunk with provenance |
| Librarian | Covenant extraction | Baskets, LME flags, section/page |
| Quant | Recovery waterfall | Recoveries, fulcrum, situational summary |
| Benchmarker | Market validation | Multiples, precedent recovery, variance |
| Auditor | Stress-test & gate | Audit trail, pass/fail |
| Comparator | Prior vs current | Score deltas, material changes |
| Reporter | Final report | Auditable report |

### Handoff Rules (DO NOT BREAK)

1. **Author → Librarian**: Must provide `DocumentChunk` with `source`, `page`, `section`
2. **Librarian → Quant**: Must emit `collateral_leakage_flags` in JSON/signals
3. **Quant → Reporter**: Must include `situational_summary` when from signals
4. **Auditor → Reporter**: Must set `published: false` when gate fails
5. **All → Reporter**: Config versions must be in audit trail

### Testing Agent Changes

```bash
# Run agent-specific tests
python -m pytest tests/test_librarian.py -v
python -m pytest tests/test_quant.py -v

# Run full pipeline test
python -m pytest tests/test_pipeline.py -v

# Manual pipeline test
python -m signal_triage.cli tests/fixtures/benchmark_corpus/low_distress.txt --pipeline
```

### Updating Agent Documentation

When modifying an agent, update:
- `.cursor/agents/<agent_name>.md` - Agent prompt and objectives
- `.cursor/agents/ORCHESTRATION.md` - Current implementation
- `docs/ROADMAP.md` - Phase status and todo

## Questions?

- Check existing documentation in `docs/`
- Review `docs/ROADMAP.md` for current priorities
- Look at existing tests for examples
- Open an issue for clarification

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
