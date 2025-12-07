# docling-view

CLI tool for visualizing and validating Docling document processing output.

## Installation

```bash
# Install from source
pip install -e .

# For development (includes test dependencies)
pip install -e ".[dev]"
```

## Quick Start

```bash
# Convert PDF to HTML using Docling's native export (includes images)
docling-view document.pdf -o output.html

# Generate interactive visualization with bounding boxes
docling-view document.pdf -m overlay -o visualizer.html

# Process pre-converted Docling JSON
docling-view docling_output.json -m overlay --open
```

## Usage

### Native Mode

Uses Docling's built-in `save_as_html()` for quick HTML export. Images are embedded as base64 by default.

```bash
# Basic conversion
docling-view document.pdf -o output.html

# Open in browser after generation
docling-view document.pdf -o output.html --open

# Verbose output showing processing details
docling-view document.pdf -o output.html -v
```

### Overlay Mode

Generates an interactive SVG visualization with color-coded bounding boxes overlaid on rendered PDF pages.

```bash
# Generate interactive visualization
docling-view document.pdf -m overlay -o visualizer.html

# High-resolution rendering (3x scale)
docling-view document.pdf -m overlay -s 3.0 -o hires.html

# Filter to specific element types
docling-view document.pdf -m overlay -t table,picture -o filtered.html

# Exclude headers/footers (furniture)
docling-view document.pdf -m overlay --no-furniture -o clean.html

# Show only tables and lists
docling-view document.pdf -m overlay -t table,list -o tables.html
```

### Processing JSON Files

If you have pre-processed Docling JSON output, you can visualize it directly:

```bash
# The tool will look for a matching PDF in the same directory
docling-view docling_output.json -m overlay -o visualizer.html
```

**Note:** The tool validates that the JSON and PDF are compatible. You'll see warnings if:
- Page counts don't match
- Page dimensions differ
- The PDF doesn't match the JSON's origin file

## CLI Reference

```
docling-view [OPTIONS] INPUT_FILE
```

### Arguments

| Argument | Description |
|----------|-------------|
| `INPUT_FILE` | Path to PDF or Docling JSON file |

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `<input>.html` | Output HTML file path |
| `--mode` | `-m` | `native` | Visualization mode: `native` or `overlay` |
| `--scale` | `-s` | `2.0` | Image rendering scale (overlay mode) |
| `--open` | | `false` | Open in browser after generation |
| `--no-furniture` | | `false` | Exclude headers/footers |
| `--types` | `-t` | all | Filter element types (comma-separated) |
| `--verbose` | `-v` | `false` | Enable verbose logging |
| `--version` | | | Show version and exit |

### Element Types

Available element types for `--types` filter:
- `text` - Regular text paragraphs
- `heading` - Section headers
- `table` - Tables
- `picture` - Images and figures
- `list` - List items
- `furniture` - Headers, footers, page numbers

## Features

### Native Mode
- Uses Docling's `document.save_as_html()`
- Images embedded as base64 (no external files)
- Fast single-file output

### Overlay Mode
- Interactive SVG visualization
- Color-coded bounding boxes:
  - **Green**: Text
  - **Orange**: Headings
  - **Blue**: Tables
  - **Red**: Pictures
  - **Purple**: Lists
  - **Gray**: Furniture (headers/footers)
- Layer toggles to show/hide element types
- Element inspector panel with JSON metadata
- Multi-page navigation
- Parallel PDF rendering (uses 80% of CPU cores)
- JSON/PDF compatibility validation with warnings

## Development

### Setup

```bash
# Clone and install with dev dependencies
git clone <repo-url>
cd docling-view
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_normalizer.py

# Run tests matching a pattern
pytest -k "coordinate"

# Verbose output
pytest -v
```

### Code Coverage

```bash
# Run with coverage report (terminal)
pytest --cov=docling_view --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=docling_view --cov-report=html
# Open htmlcov/index.html in browser

# Coverage with minimum threshold (fails if below 70%)
pytest --cov=docling_view --cov-fail-under=70
```

### Writing Tests

Tests are organized in `tests/` with the following structure:

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_normalizer.py   # Coordinate normalization tests
│   ├── test_parser.py       # JSON parser tests
│   ├── test_native_renderer.py
│   └── test_overlay_renderer.py
├── integration/             # Integration tests
│   ├── test_cli.py          # CLI end-to-end tests
│   └── test_json_pipeline.py
└── fixtures/                # Test data files
```

#### Example Unit Test

```python
# tests/unit/test_example.py
import pytest
from docling_view.core.normalizer import NormalizedBBox

class TestNormalizedBBox:
    """Tests for NormalizedBBox dataclass."""

    def test_create_bbox(self):
        """Test creating a normalized bbox."""
        bbox = NormalizedBBox(x=10.0, y=20.0, width=100.0, height=50.0)

        assert bbox.x == 10.0
        assert bbox.y == 20.0
        assert bbox.width == 100.0
        assert bbox.height == 50.0

    def test_scale_bbox(self):
        """Test scaling a bbox by a factor."""
        bbox = NormalizedBBox(x=10.0, y=20.0, width=100.0, height=50.0)
        scaled = bbox.scale(2.0)

        assert scaled.x == 20.0
        assert scaled.y == 40.0
```

#### Using Fixtures

Fixtures are defined in `conftest.py` and automatically available to all tests:

```python
# tests/unit/test_parser.py
def test_parse_valid_json(sample_docling_json: dict):
    """Test parsing a valid Docling JSON document."""
    from docling_view.core.parser import DoclingParser

    parser = DoclingParser()
    doc = parser.parse(sample_docling_json)

    assert doc.name == "test_document"
    assert len(doc.pages) == 2

def test_with_temp_file(tmp_json_file: Path):
    """Test with a temporary JSON file."""
    parser = DoclingParser()
    doc = parser.parse_file(tmp_json_file)

    assert doc is not None
```

#### Available Fixtures

| Fixture | Description |
|---------|-------------|
| `sample_docling_json` | Sample Docling JSON document dict |
| `sample_bbox_bottomleft` | Bbox in BOTTOMLEFT coordinates |
| `sample_bbox_topleft` | Bbox in TOPLEFT coordinates |
| `ruler_test_bbox_bottomleft` | 1-inch test box (BOTTOMLEFT) |
| `ruler_test_bbox_topleft` | 1-inch test box (TOPLEFT) |
| `standard_page_height` | US Letter page height (792.0) |
| `tmp_json_file` | Temporary JSON file path |
| `tmp_output_dir` | Temporary output directory |

#### Writing Integration Tests

```python
# tests/integration/test_cli.py
from typer.testing import CliRunner
from docling_view.cli import app

runner = CliRunner()

def test_cli_help():
    """Test help displays correctly."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "docling-view" in result.stdout

def test_cli_version():
    """Test version displays correctly."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout

def test_cli_missing_file():
    """Test error on missing input file."""
    result = runner.invoke(app, ["nonexistent.pdf"])
    assert result.exit_code == 1
    assert "not found" in result.stdout
```

### Code Quality

```bash
# Run linter
ruff check src/

# Run type checker
mypy src/

# Format code
ruff format src/
```

## Architecture

See [DESIGN.md](DESIGN.md) for coordinate system details and [PROJECT.md](PROJECT.md) for implementation specifications.

### Key Components

- **CLI** (`cli.py`): Typer-based command-line interface
- **Processor** (`core/processor.py`): Orchestrates conversion pipeline
- **Parser** (`core/parser.py`): Parses Docling JSON format
- **Normalizer** (`core/normalizer.py`): Coordinate transformation (BOTTOMLEFT → TOPLEFT)
- **Native Renderer** (`renderers/native.py`): Wraps Docling's `save_as_html()`
- **Overlay Renderer** (`renderers/overlay.py`): Generates interactive SVG visualization
- **Asset Renderer** (`renderers/assets.py`): Parallel PDF-to-image conversion

## License

MIT
