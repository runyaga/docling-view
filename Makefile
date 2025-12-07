.PHONY: install dev test lint format typecheck check clean

install:
	uv sync

dev:
	uv sync --extra dev
	uv run pre-commit install

test:
	uv run pytest

test-cov:
	uv run pytest --cov=docling_view --cov-report=term-missing

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/

check: lint typecheck test

clean:
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
