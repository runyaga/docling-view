# PROJECT.md

Steps to apply best practices and add CI pipeline.

## Phase 1: Pre-commit Hooks

### 1.1 Install pre-commit
```bash
pip install pre-commit
```

### 1.2 Create `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.2
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies:
          - types-Pillow
        args: [--strict]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### 1.3 Install hooks
```bash
pre-commit install
pre-commit run --all-files  # Initial run
```

## Phase 2: GitHub Actions CI

### 2.1 Create `.github/workflows/ci.yml`
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --dev
      - run: uv run ruff check src/
      - run: uv run ruff format --check src/

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --dev
      - run: uv run mypy src/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --dev
      - run: uv run pytest --cov=docling_view --cov-report=xml --cov-fail-under=70
      - uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
        if: github.event_name == 'push'

  test-matrix:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv sync --dev
      - run: uv run pytest
```

## Phase 3: Code Quality Improvements

### 3.1 Add type stubs to dev dependencies
Update `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
    "pre-commit>=4.0.0",
    "types-Pillow",
]
```

### 3.2 Configure strict mypy in `pyproject.toml`
```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = ["docling.*", "pypdfium2.*"]
ignore_missing_imports = true
```

### 3.3 Add ruff rules
```toml
[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "W",    # pycodestyle warnings
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "SIM",  # flake8-simplify
]
```

## Phase 4: Documentation

### 4.1 Add docstring coverage check
```bash
pip install interrogate
interrogate -v src/
```

### 4.2 Add to CI (optional)
```yaml
- run: uv run interrogate -v --fail-under=80 src/
```

## Phase 5: Release Automation

### 5.1 Create `.github/workflows/release.yml`
```yaml
name: Release

on:
  push:
    tags: ["v*"]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

## Checklist

- [ ] Install pre-commit hooks
- [ ] Create `.github/workflows/ci.yml`
- [ ] Update `pyproject.toml` with stricter config
- [ ] Fix any linting/type errors
- [ ] Ensure tests pass with 70%+ coverage
- [ ] Add branch protection rules on GitHub
- [ ] (Optional) Set up Codecov
- [ ] (Optional) Add release workflow
