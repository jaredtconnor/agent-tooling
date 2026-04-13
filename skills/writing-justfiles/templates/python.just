# Python module justfile
# Package manager: uv

# Show available commands
default:
    @just --list

# Install dependencies
install:
    uv venv
    uv pip install -e ".[dev]"

# Format code
format:
    black src/ tests/
    ruff check --fix src/ tests/

# Lint code
lint:
    ruff check src/ tests/
    mypy src/

# Run unit tests (optionally specify path)
test PATH="tests/unit/":
    pytest {{PATH}} -v

# Run integration tests
test-integration:
    pytest tests/integration/ -v

# Run all tests
test-full:
    pytest tests/ --cov=src --cov-report=term-missing

# Run tests with watch mode
test-watch:
    pytest-watch tests/unit/

# Build (if package)
build: lint test
    python -m build

# Run development server
dev:
    uvicorn src.main:app --reload --port 8000

# Clean build artifacts
clean:
    rm -rf dist/ build/ *.egg-info
    rm -rf .pytest_cache .mypy_cache .ruff_cache
    find . -type d -name __pycache__ -exec rm -rf {} +
