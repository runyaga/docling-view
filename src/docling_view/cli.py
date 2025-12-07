"""CLI entry point for docling-view."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from docling_view import __version__
from docling_view.core.processor import DocumentProcessor

app = typer.Typer(
    name="docling-view",
    help="CLI tool for visualizing and validating Docling document processing output.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"docling-view version {__version__}")
        raise typer.Exit()


def validate_input_file(path: Path) -> Path:
    """Validate input file exists and has correct extension."""
    if not path.exists():
        console.print(f"[red]Error:[/red] File '{path}' not found")
        raise typer.Exit(1)

    suffix = path.suffix.lower()
    if suffix not in (".pdf", ".json"):
        console.print(f"[red]Error:[/red] Unsupported file format '{suffix}'. Use .pdf or .json")
        raise typer.Exit(1)

    return path


def resolve_output_path(input_path: Path, output: Path | None, mode: str) -> Path:
    """Resolve output path, using input filename if not specified."""
    if output:
        return output

    if mode == "overlay":
        output_dir = input_path.parent / f"{input_path.stem}_visualizer"
        return output_dir / "index.html"

    return input_path.with_suffix(".html")


@app.command()  # type: ignore[misc]
def main(
    input_file: Annotated[
        Path,
        typer.Argument(
            help="Path to PDF or Docling JSON file",
            exists=False,
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output HTML file path",
        ),
    ] = None,
    mode: Annotated[
        str,
        typer.Option(
            "--mode",
            "-m",
            help="Visualization mode: 'native' (Docling HTML) or 'overlay' (SVG visualization)",
        ),
    ] = "native",
    scale: Annotated[
        float,
        typer.Option(
            "--scale",
            "-s",
            help="Image rendering scale for overlay mode",
        ),
    ] = 2.0,
    open_browser: Annotated[
        bool,
        typer.Option(
            "--open",
            help="Open HTML in browser after generation",
        ),
    ] = False,
    no_furniture: Annotated[
        bool,
        typer.Option(
            "--no-furniture",
            help="Exclude headers/footers from visualization",
        ),
    ] = False,
    types: Annotated[
        str | None,
        typer.Option(
            "--types",
            "-t",
            help="Filter types: text,table,picture,heading,list,furniture",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose logging",
        ),
    ] = False,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
) -> None:
    """
    Generate HTML visualization from Docling-processed documents.

    Examples:

        docling-view document.pdf -o output.html

        docling-view document.pdf -m overlay -o visualizer.html

        docling-view docling_output.json -m overlay --open
    """
    if mode not in ("native", "overlay"):
        console.print(f"[red]Error:[/red] Invalid mode '{mode}'. Use 'native' or 'overlay'")
        raise typer.Exit(2)

    input_path = validate_input_file(input_file)
    output_path = resolve_output_path(input_path, output, mode)

    element_types: list[str] | None = None
    if types:
        element_types = [t.strip().lower() for t in types.split(",")]
        valid_types = {"text", "table", "picture", "heading", "list", "furniture"}
        invalid = set(element_types) - valid_types
        if invalid:
            console.print(f"[red]Error:[/red] Invalid element types: {invalid}")
            raise typer.Exit(2)

    if verbose:
        console.print(f"[blue]Processing:[/blue] {input_path}")
        console.print(f"[blue]Mode:[/blue] {mode}")
        console.print(f"[blue]Output:[/blue] {output_path}")

    processor = DocumentProcessor(
        verbose=verbose,
        console=console,
    )

    try:
        processor.process(
            input_path=input_path,
            output_path=output_path,
            mode=mode,
            scale=scale,
            include_furniture=not no_furniture,
            element_types=element_types,
        )

        console.print(f"[green]Success:[/green] Output written to {output_path}")

        if open_browser:
            from docling_view.utils.browser import open_in_browser

            open_in_browser(output_path)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
