# docling-view

[![CI](https://github.com/runyaga/docling-view/actions/workflows/ci.yml/badge.svg)](https://github.com/runyaga/docling-view/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/runyaga/docling-view/graph/badge.svg)](https://codecov.io/gh/runyaga/docling-view)

CLI tool for visualizing Docling document processing output.

## Installation

```bash
# Using pip
pip install -e .

# Using uv (recommended)
uv sync
```

## Usage

```bash
# Native mode - uses Docling's save_as_html()
docling-view document.pdf -o output.html

# Overlay mode - interactive SVG with bounding boxes
docling-view document.pdf -m overlay -o visualizer.html

# Process pre-converted JSON
docling-view docling_output.json -m overlay --open
```

### How Overlay Mode Works

In overlay mode, the tool renders PDF pages as background images and draws bounding boxes as SVG overlays:

1. **PDF → Images**: Each PDF page is rendered to PNG using pypdfium2
2. **JSON → Bounding Boxes**: Element coordinates from Docling JSON are transformed from PDF coordinates (BOTTOMLEFT origin) to screen coordinates (TOPLEFT origin)
3. **HTML Output**: An interactive HTML page with page images and SVG overlays

**PDF Location**: When processing a `.json` file, the tool looks for the source PDF:
- First checks for `<filename>.pdf` in the same directory
- Falls back to any single PDF in the directory
- Without a PDF, bounding boxes display without background images

```
my_documents/
├── report.json      # Docling output
└── report.pdf       # Source PDF (same name)
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | `<input>.html` | Output HTML file |
| `-m, --mode` | `native` | `native` or `overlay` |
| `-s, --scale` | `2.0` | Image scale (overlay mode) |
| `-t, --types` | all | Filter: text,heading,table,picture,list,furniture |
| `--no-furniture` | false | Exclude headers/footers |
| `--open` | false | Open in browser |
| `-v, --verbose` | false | Verbose output |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"   # Or: uv sync --all-extras

make dev          # Install dev dependencies + pre-commit hooks
make test         # Run tests
make test-cov     # Run tests with coverage
make lint         # Run linter
make format       # Format code
make typecheck    # Run type checker
make check        # Run lint + typecheck + test
make clean        # Remove build artifacts
```

## Architecture

- **CLI** (`cli.py`): Typer-based entry point
- **Processor** (`core/processor.py`): Pipeline orchestration
- **Parser** (`core/parser.py`): Docling JSON parsing
- **Normalizer** (`core/normalizer.py`): BOTTOMLEFT → TOPLEFT coordinates
- **Native Renderer** (`renderers/native.py`): Docling HTML export
- **Overlay Renderer** (`renderers/overlay.py`): Interactive SVG visualization
- **Asset Renderer** (`renderers/assets.py`): Parallel PDF-to-image conversion

## License

MIT
