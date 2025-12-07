# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

docling-view is a CLI tool for visualizing and validating Docling document processing output. It converts PDFs or pre-processed Docling JSON files into HTML visualizations.

## Commands

### Installation
```bash
pip install -e .           # Install from source
pip install -e ".[dev]"    # With dev dependencies (pytest, ruff, mypy)
```

### Running the CLI
```bash
docling-view document.pdf -o output.html                    # Native mode (default)
docling-view document.pdf -m overlay -o visualizer.html     # Overlay mode with bounding boxes
```

### Testing
```bash
pytest                                  # Run all tests
pytest tests/unit/                      # Unit tests only
pytest tests/integration/               # Integration tests only
pytest tests/unit/test_normalizer.py    # Single file
pytest -k "coordinate"                  # Pattern matching
pytest --cov=docling_view --cov-report=term-missing   # With coverage
```

### Code Quality
```bash
ruff check src/        # Linting
ruff format src/       # Formatting
mypy src/              # Type checking
```

## Architecture

The CLI has two visualization modes:
- **Native mode**: Uses Docling's built-in `save_as_html()` for quick HTML export
- **Overlay mode**: Generates interactive SVG visualization with color-coded bounding boxes

### Source Structure
```
src/docling_view/
├── cli.py              # Typer-based CLI entry point
├── core/
│   ├── processor.py    # Orchestrates pipeline (PDF detection, routing to renderers)
│   ├── parser.py       # Parses Docling JSON into ParsedDocument/DocumentItem/TableItem
│   └── normalizer.py   # BOTTOMLEFT → TOPLEFT coordinate transformation
├── renderers/
│   ├── native.py       # Wraps Docling's save_as_html()
│   ├── overlay.py      # Interactive SVG visualization with Jinja2 template
│   └── assets.py       # Parallel PDF-to-image conversion via pypdfium2
├── templates/          # HTML/CSS for overlay renderer
└── utils/
    └── browser.py      # Browser launch utility
```

### Key Concepts

**Coordinate Systems**: Docling JSON uses BOTTOMLEFT coordinates (PDF standard), but HTML/SVG uses TOPLEFT. The normalizer handles this transformation.

**Element Types**: text, heading, table, picture, list, furniture (headers/footers)

**Bounding Box Format**: `{l, t, r, b, coord_origin}` where l=left, t=top, r=right, b=bottom

## Testing Fixtures

Key fixtures in `tests/conftest.py`:
- `sample_docling_json`: Complete document with texts, tables, pictures
- `sample_bbox_bottomleft` / `sample_bbox_topleft`: Bounding box samples
- `ruler_test_bbox_*`: 1-inch test boxes (72 points = 1 inch)
- `standard_page_height`: US Letter = 792.0 points
- `tmp_json_file`, `tmp_output_dir`: Temporary test paths
