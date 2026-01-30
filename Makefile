.PHONY: help install test lint format clean docker-build docker-up docker-down docs

help:
	@echo "Signal Triage - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies"
	@echo "  make dev-setup     Setup development environment"
	@echo ""
	@echo "Development:"
	@echo "  make test          Run all tests"
	@echo "  make lint          Run linters"
	@echo "  make format        Format code with black and isort"
	@echo "  make typecheck     Run type checking"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-up     Start all services"
	@echo "  make docker-down   Stop all services"
	@echo "  make docker-logs   View logs"
	@echo ""
	@echo "Other:"
	@echo "  make clean         Remove build artifacts"
	@echo "  make security      Run security checks"

install:
	pip install --upgrade pip
	pip install -e .
	pip install -r requirements.txt

dev-setup: install
	pip install pre-commit black flake8 isort pytest-cov
	pre-commit install
	@echo "Development environment ready!"

test:
	python -m pytest tests/ -v --tb=short

test-coverage:
	python -m pytest tests/ --cov=signal_triage --cov-report=html --cov-report=term

test-integration:
	python -m pytest tests/test_pipeline.py tests/test_api_integration.py -v

lint:
	flake8 signal_triage/ tests/ --max-line-length=127
	black --check signal_triage/ tests/
	isort --check-only signal_triage/ tests/

format:
	black signal_triage/ tests/
	isort signal_triage/ tests/

typecheck:
	mypy signal_triage/ --ignore-missing-imports

security:
	bandit -r signal_triage/ -f json -o bandit-report.json
	safety check

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "Services started. API: http://localhost:8000/docs"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
	docker system prune -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

run-api:
	python run_api_server.py

run-dashboard:
	streamlit run signal_triage/ui/dashboard.py

pipeline-test:
	python -m signal_triage.cli tests/fixtures/benchmark_corpus/low_distress.txt --pipeline

docs:
	@echo "Documentation available in docs/"
	@echo "Main docs:"
	@echo "  - README.md"
	@echo "  - docs/ROADMAP.md"
	@echo "  - docs/DEPLOYMENT.md"
	@echo "  - docs/MONITORING.md"
	@echo "  - CONTRIBUTING.md"
