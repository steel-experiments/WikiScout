.PHONY: help install install-dev test lint format type-check clean run-search run-summary docker-build docker-run

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package in production mode
	pip install -e .

install-dev:  ## Install package with development dependencies
	pip install -e .[dev]

test:  ## Run tests with pytest
	pytest --cov --cov-report=term-missing --cov-report=html

test-fast:  ## Run tests without coverage
	pytest -v

test-watch:  ## Run tests in watch mode
	pytest --watch

lint:  ## Run ruff linter
	ruff check .

format:  ## Format code with ruff
	ruff format .

fix:  ## Auto-fix linting issues
	ruff check --fix .
	ruff format .

type-check:  ## Run mypy type checker
	mypy modules/ agent.py

check-all: lint type-check test  ## Run all checks (lint, type-check, test)

clean:  ## Clean up cache and build artifacts
	rm -rf build/ dist/ *.egg-info __pycache__ .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete

run-search:  ## Quick test: Search for Python programming
	python cli.py search "Python programming"

run-summary:  ## Quick test: Summarize Machine Learning
	python cli.py summarize "Machine Learning" --bullets 5

run-compare:  ## Quick test: Compare Python vs JavaScript
	python cli.py compare --topic1 "Python" --topic2 "JavaScript" --bullets 3

run-example:  ## Run test examples
	python test_example.py

run-api:  ## Start FastAPI server
	uvicorn api:app --reload

run-api-prod:  ## Start FastAPI server (production)
	uvicorn api:app --host 0.0.0.0 --port 8000

docker-build:  ## Build Docker image
	docker build -t wikiscout:latest .

docker-build-dev:  ## Build Docker image (dev)
	docker build -t wikiscout:dev --target dev .

docker-run:  ## Run WikiScout in Docker
	docker run --rm -v $$(pwd)/cache:/app/cache wikiscout:latest status

docker-search:  ## Docker: Search example
	docker run --rm -v $$(pwd)/cache:/app/cache wikiscout:latest search -q "Python programming"

docker-compose-up:  ## Start services with docker-compose
	docker-compose up -d

docker-compose-down:  ## Stop services
	docker-compose down

docker-compose-logs:  ## View logs
	docker-compose logs -f

build:  ## Build Python package
	python -m build

publish-test:  ## Publish to TestPyPI
	python -m twine upload --repository testpypi dist/*

publish:  ## Publish to PyPI
	python -m twine upload dist/*

pre-commit-install:  ## Install pre-commit hooks
	pre-commit install

pre-commit-run:  ## Run pre-commit on all files
	pre-commit run --all-files

update-deps:  ## Update dependencies
	pip install --upgrade pip
	pip install --upgrade -e .[dev]

freeze:  ## Freeze current dependencies
	pip freeze > requirements-frozen.txt

benchmark:  ## Run performance benchmarks
	@echo "Cold cache search..."
	@time python agent.py search -q "Quantum Computing" --format json > /dev/null
	@echo "\nCached search..."
	@time python agent.py search -q "Quantum Computing" --format json > /dev/null

status:  ## Show WikiScout status
	python agent.py status

version:  ## Show version info
	@python -c "import sys; print(f'Python {sys.version}')"
	@python agent.py --version || echo "WikiScout v1.1.0"
