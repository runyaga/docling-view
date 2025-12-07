"""Native HTML renderer using Docling's built-in save_as_html()."""

import json
from pathlib import Path
from typing import Any

from docling_core.types.doc.base import ImageRefMode
from rich.console import Console


class NativeRenderer:
    """
    Renderer that uses Docling's built-in HTML export.

    This provides a quick way to generate HTML from Docling documents
    using the conv_result.document.save_as_html() method.
    """

    def __init__(
        self,
        verbose: bool = False,
        console: Console | None = None,
        image_mode: ImageRefMode = ImageRefMode.EMBEDDED,
    ):
        """
        Initialize native renderer.

        Args:
            verbose: Enable verbose output
            console: Rich console for output
            image_mode: How to handle images (EMBEDDED, PLACEHOLDER, REFERENCED)
        """
        self.verbose = verbose
        self.console = console or Console()
        self.image_mode = image_mode

    def render_from_document(
        self,
        document: Any,
        output_path: Path,
    ) -> None:
        """
        Render HTML from a DoclingDocument using save_as_html().

        This is the primary method that uses Docling's native HTML export.

        Args:
            document: DoclingDocument from conversion result
            output_path: Path to write HTML file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.verbose:
            self.console.print(f"[blue]Rendering HTML to {output_path}...[/blue]")

        document.save_as_html(output_path, image_mode=self.image_mode)

        if self.verbose:
            self.console.print("[green]HTML rendered successfully[/green]")

    def render_from_json(
        self,
        json_path: Path,
        output_path: Path,
    ) -> None:
        """
        Render HTML from a Docling JSON file.

        Loads the JSON and reconstructs a DoclingDocument for export.

        Args:
            json_path: Path to Docling JSON file
            output_path: Path to write HTML file
        """
        try:
            from docling_core.types.doc import DoclingDocument  # type: ignore[attr-defined]
        except ImportError as e:
            raise ImportError(
                "docling-core is required for JSON processing. "
                "Install with: pip install docling-core"
            ) from e

        if self.verbose:
            self.console.print(f"[blue]Loading JSON from {json_path}...[/blue]")

        with open(json_path) as f:
            data = json.load(f)

        document = DoclingDocument.model_validate(data)

        self.render_from_document(document, output_path)
