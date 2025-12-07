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

docling-view accepts two input types: **PDF files** or **pre-processed Docling JSON**.

### Input Types

#### JSON Input (Recommended)

For practical use, pre-process your PDF with [pdf-splitter](https://github.com/runyaga/pdf-splitter), which efficiently handles large documents by splitting them into chunks, processing each with Docling, and concatenating the results:

```bash
# Step 1: Split PDF into chunks
pdf-splitter chunk document.pdf -o ./chunks

# Step 2: Process chunks and merge into single JSON
pdf-splitter convert ./chunks -o ./output/document.json

# Step 3: Copy original PDF to same folder as JSON (same base name)
cp document.pdf ./output/document.pdf

# Step 4: Visualize with docling-view
docling-view ./output/document.json -m overlay --open
```

**Important**: The JSON and PDF must be in the same folder with the same base name (e.g., `document.json` and `document.pdf`). docling-view uses the PDF to render page backgrounds for the bounding box overlays.

> **Note**: Running Docling directly on large PDFs (via `docling` CLI or passing PDFs to `docling-view`) is impractical due to memory and time constraints. Use pdf-splitter for documents larger than a few pages.

#### PDF Input (Quick Preview)

For quick previews of small documents, pass the PDF directly:

```bash
docling-view document.pdf -o output.html
```

This runs Docling's full conversion pipeline internally, which can be slow for large documents.

### Visualization Modes

```bash
# Native mode (default) - uses Docling's built-in HTML export
docling-view document.json -o output.html

# Overlay mode - interactive SVG with color-coded bounding boxes
docling-view document.json -m overlay -o visualizer.html --open
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
