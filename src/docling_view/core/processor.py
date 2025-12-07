"""Document processor orchestrating the conversion pipeline."""

import json
import logging
from pathlib import Path
from typing import Any

from rich.console import Console

from docling_view.core.parser import DoclingParser, ParsedDocument

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Raised when document conversion fails."""

    pass


class DocumentProcessor:
    """
    Orchestrates the document processing pipeline.

    Handles:
    - Detecting input type (PDF vs JSON)
    - Converting PDFs using Docling
    - Loading pre-processed JSON
    - Routing to appropriate renderer
    """

    def __init__(
        self,
        verbose: bool = False,
        console: Console | None = None,
    ):
        """
        Initialize processor.

        Args:
            verbose: Enable verbose logging
            console: Rich console for output
        """
        self.verbose = verbose
        self.console = console or Console()
        self.parser = DoclingParser()

        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)

    def process(
        self,
        input_path: Path,
        output_path: Path,
        mode: str = "native",
        scale: float = 2.0,
        include_furniture: bool = True,
        element_types: list[str] | None = None,
    ) -> None:
        """
        Process a document and generate HTML output.

        Args:
            input_path: Path to PDF or JSON file
            output_path: Path for HTML output
            mode: 'native' or 'overlay'
            scale: Image scale for overlay mode
            include_furniture: Include header/footer elements
            element_types: Filter to specific element types
        """
        is_pdf = input_path.suffix.lower() == ".pdf"

        if mode == "native":
            self._process_native(input_path, output_path, is_pdf)
        else:
            self._process_overlay(
                input_path,
                output_path,
                is_pdf,
                scale,
                include_furniture,
                element_types,
            )

    def _process_native(
        self,
        input_path: Path,
        output_path: Path,
        is_pdf: bool,
    ) -> None:
        """
        Process using Docling's native HTML export.

        Uses conv_result.document.save_as_html() for HTML generation.
        """
        from docling_view.renderers.native import NativeRenderer

        renderer = NativeRenderer(verbose=self.verbose, console=self.console)

        if is_pdf:
            if self.verbose:
                self.console.print("[blue]Converting PDF with Docling...[/blue]")

            document = self._convert_pdf(input_path)
            renderer.render_from_document(document, output_path)
        else:
            if self.verbose:
                self.console.print("[blue]Loading Docling JSON...[/blue]")

            renderer.render_from_json(input_path, output_path)

    def _process_overlay(
        self,
        input_path: Path,
        output_path: Path,
        is_pdf: bool,
        scale: float,
        include_furniture: bool,
        element_types: list[str] | None,
    ) -> None:
        """
        Process using custom SVG overlay visualization.

        Generates interactive HTML with bounding box overlays.
        """
        from docling_view.renderers.overlay import OverlayRenderer

        renderer = OverlayRenderer(
            scale=scale,
            verbose=self.verbose,
            console=self.console,
        )

        if is_pdf:
            if self.verbose:
                self.console.print("[blue]Converting PDF with Docling...[/blue]")

            document = self._convert_pdf(input_path)

            parsed = self._parse_from_document(document)

            renderer.render(
                parsed_doc=parsed,
                pdf_path=input_path,
                output_path=output_path,
                include_furniture=include_furniture,
                element_types=element_types,
            )
        else:
            if self.verbose:
                self.console.print("[blue]Loading Docling JSON...[/blue]")

            # Load raw JSON data for validation
            with open(input_path) as f:
                json_data = json.load(f)

            parsed = self.parser.parse(json_data, name=input_path.stem)

            # Find PDF and validate compatibility
            pdf_path = self._find_source_pdf(input_path, json_data)

            if pdf_path:
                self._validate_json_pdf_compatibility(parsed, pdf_path)

            renderer.render(
                parsed_doc=parsed,
                pdf_path=pdf_path,
                output_path=output_path,
                include_furniture=include_furniture,
                element_types=element_types,
            )

    def _convert_pdf(self, pdf_path: Path) -> Any:
        """
        Convert a PDF using Docling.

        Args:
            pdf_path: Path to PDF file

        Returns:
            DoclingDocument from conversion result
        """
        try:
            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()
            conv_result = converter.convert(pdf_path)

            if self.verbose:
                doc = conv_result.document
                self.console.print(
                    f"[blue]Extracted:[/blue] {len(doc.texts)} texts, "
                    f"{len(doc.tables)} tables, {len(doc.pictures)} pictures"
                )

            return conv_result.document

        except ImportError as e:
            raise ConversionError(
                "Docling is not installed. Install with: pip install docling"
            ) from e
        except Exception as e:
            raise ConversionError(f"Failed to convert PDF: {e}") from e

    def _parse_from_document(self, document: Any) -> ParsedDocument:
        """
        Parse a DoclingDocument into our internal format.

        Args:
            document: DoclingDocument from Docling conversion

        Returns:
            ParsedDocument with normalized items
        """
        doc_dict = document.export_to_dict()
        return self.parser.parse(doc_dict, name=getattr(document, "name", "document"))

    def _find_source_pdf(
        self,
        json_path: Path,
        json_data: dict[str, Any] | None = None,
    ) -> Path | None:
        """
        Attempt to find the source PDF for a JSON file.

        Looks for PDF with same name in same directory.
        Warns if the found PDF may not match the JSON origin.
        """
        # First try exact name match
        pdf_path = json_path.with_suffix(".pdf")
        if pdf_path.exists():
            return pdf_path

        # Fall back to finding any PDF in directory
        found_pdf: Path | None = None
        for pattern in ["*.pdf", "../*.pdf"]:
            pdfs = list(json_path.parent.glob(pattern))
            if len(pdfs) == 1:
                found_pdf = pdfs[0]
                break

        if not found_pdf:
            self.console.print(
                "[yellow]Warning:[/yellow] Could not find source PDF for "
                f"{json_path.name}. Overlay will have no background images."
            )
            return None

        # Check if found PDF might not match the JSON
        if json_data:
            origin = json_data.get("origin", {})
            origin_filename = origin.get("filename", "")

            # Warn if PDF name doesn't appear related to JSON origin
            if origin_filename and found_pdf.name not in origin_filename:
                self.console.print(
                    f"[yellow]Warning:[/yellow] Found PDF '{found_pdf.name}' but JSON "
                    f"was created from '{origin_filename}'. Content may not match!"
                )

        return found_pdf

    def _validate_json_pdf_compatibility(
        self,
        parsed_doc: ParsedDocument,
        pdf_path: Path,
    ) -> None:
        """
        Validate that JSON and PDF are compatible.

        Checks page counts and dimensions, warns if mismatched.
        """
        try:
            import pypdfium2 as pdfium
        except ImportError:
            return  # Can't validate without pypdfium2

        pdf = pdfium.PdfDocument(pdf_path)
        pdf_page_count = len(pdf)
        json_page_count = len(parsed_doc.pages)

        warnings_shown = False

        # Check page count
        if pdf_page_count != json_page_count:
            self.console.print(
                f"[yellow]Warning:[/yellow] Page count mismatch - "
                f"JSON has {json_page_count} pages, PDF has {pdf_page_count} pages. "
                "Bounding boxes may appear on wrong pages!"
            )
            warnings_shown = True

        # Check dimensions for first few pages
        dimension_mismatches = []
        pages_to_check = min(5, pdf_page_count, json_page_count)

        for i in range(pages_to_check):
            page_no = i + 1
            if page_no not in parsed_doc.pages:
                continue

            json_page = parsed_doc.pages[page_no]
            pdf_page = pdf[i]
            pdf_w, pdf_h = pdf_page.get_size()

            # Allow 1pt tolerance for floating point differences
            if abs(json_page.width - pdf_w) > 1 or abs(json_page.height - pdf_h) > 1:
                dimension_mismatches.append(
                    f"Page {page_no}: JSON={json_page.width:.0f}x{json_page.height:.0f}, "
                    f"PDF={pdf_w:.0f}x{pdf_h:.0f}"
                )

        if dimension_mismatches:
            self.console.print(
                "[yellow]Warning:[/yellow] Page dimension mismatch detected. "
                "JSON and PDF may be from different sources:"
            )
            for mismatch in dimension_mismatches[:3]:
                self.console.print(f"  {mismatch}")
            if len(dimension_mismatches) > 3:
                self.console.print(f"  ... and {len(dimension_mismatches) - 3} more")
            warnings_shown = True

        pdf.close()

        if warnings_shown:
            self.console.print(
                "[dim]Hint: Use --pdf option to specify the correct PDF file, "
                "or ensure the JSON was created from this PDF.[/dim]"
            )
