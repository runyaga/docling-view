# docling-view

CLI tool for visualizing Docling document processing output.

## Installation

```bash
pip install -e .
pip install -e ".[dev]"  # with dev dependencies
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
pip install -e ".[dev]"         # Install dev dependencies
pre-commit install              # Set up git hooks
pytest                          # Run tests
pytest --cov=docling_view       # With coverage
ruff check src/ && mypy src/    # Lint & type check
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
