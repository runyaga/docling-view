"""Asset renderer for PDF to image conversion."""

import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console

logger = logging.getLogger(__name__)


def _render_page_worker(args: tuple[str, int, float, str]) -> dict[str, Any]:
    """
    Worker function to render a single PDF page.

    Must be a module-level function for pickling in multiprocessing.

    Args:
        args: Tuple of (pdf_path, page_index, scale, output_dir)

    Returns:
        Dict with page image metadata
    """
    import pypdfium2 as pdfium

    pdf_path, page_index, scale, output_dir = args
    page_no = page_index + 1

    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[page_index]

    bitmap = page.render(scale=scale, rotation=0)
    pil_image = bitmap.to_pil()

    image_filename = f"page_{page_no}.png"
    image_path = Path(output_dir) / "assets" / image_filename
    pil_image.save(image_path, "PNG")

    width_px, height_px = pil_image.size
    width_pt, height_pt = page.get_size()

    pdf.close()

    return {
        "page_no": page_no,
        "filename": image_filename,
        "width_px": width_px,
        "height_px": height_px,
        "width_pt": width_pt,
        "height_pt": height_pt,
        "scale_factor": width_px / width_pt,
    }


@dataclass
class PageImage:
    """Information about a rendered page image."""

    page_no: int
    filename: str
    width_px: int
    height_px: int
    width_pt: float
    height_pt: float
    scale_factor: float

    @property
    def path(self) -> str:
        """Relative path for use in HTML."""
        return f"assets/{self.filename}"


class AssetRenderer:
    """
    Converts PDF pages to images using pypdfium2.

    Generates high-resolution PNG images for use as background
    in the overlay visualization.
    """

    def __init__(
        self,
        scale: float = 2.0,
        verbose: bool = False,
        console: Console | None = None,
    ):
        """
        Initialize asset renderer.

        Args:
            scale: Rendering scale (1.0 = 72 DPI, 2.0 = 144 DPI)
            verbose: Enable verbose output
            console: Rich console for output
        """
        self.scale = scale
        self.verbose = verbose
        self.console = console or Console()

    def render_pdf_pages(
        self,
        pdf_path: Path,
        output_dir: Path,
    ) -> list[PageImage]:
        """
        Render all pages of a PDF to PNG images using parallel processing.

        Args:
            pdf_path: Path to source PDF
            output_dir: Directory to write images

        Returns:
            List of PageImage objects with metadata
        """
        try:
            import pypdfium2 as pdfium
        except ImportError as e:
            raise ImportError(
                "pypdfium2 is required for PDF rendering. " "Install with: pip install pypdfium2"
            ) from e

        assets_dir = output_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Get page count
        pdf = pdfium.PdfDocument(pdf_path)
        num_pages = len(pdf)
        pdf.close()

        # Calculate worker count (80% of CPUs)
        cpu_count = os.cpu_count() or 1
        max_workers = max(1, int(cpu_count * 0.8))

        if self.verbose:
            self.console.print(
                f"[blue]Rendering {num_pages} PDF pages at {self.scale}x scale "
                f"using {max_workers} workers...[/blue]"
            )

        # Prepare arguments for each page
        worker_args = [(str(pdf_path), i, self.scale, str(output_dir)) for i in range(num_pages)]

        images_info: list[PageImage] = []
        completed = 0

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_render_page_worker, args): args[1] for args in worker_args}

            for future in as_completed(futures):
                result = future.result()
                page_image = PageImage(
                    page_no=result["page_no"],
                    filename=result["filename"],
                    width_px=result["width_px"],
                    height_px=result["height_px"],
                    width_pt=result["width_pt"],
                    height_pt=result["height_pt"],
                    scale_factor=result["scale_factor"],
                )
                images_info.append(page_image)
                completed += 1

                if self.verbose:
                    self.console.print(
                        f"  [{completed}/{num_pages}] Page {result['page_no']}: "
                        f"{result['width_px']}x{result['height_px']}px "
                        f"(scale: {result['scale_factor']:.2f})"
                    )

        # Sort by page number
        images_info.sort(key=lambda x: x.page_no)

        if self.verbose:
            self.console.print(f"[green]Rendered {len(images_info)} pages[/green]")

        return images_info

    def get_page_dimensions(self, pdf_path: Path) -> dict[int, tuple[float, float]]:
        """
        Extract page dimensions from PDF without rendering.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict mapping page number to (width, height) in points
        """
        try:
            import pypdfium2 as pdfium
        except ImportError as e:
            raise ImportError(
                "pypdfium2 is required for PDF processing. " "Install with: pip install pypdfium2"
            ) from e

        pdf = pdfium.PdfDocument(pdf_path)
        dimensions: dict[int, tuple[float, float]] = {}

        for i in range(len(pdf)):
            page = pdf[i]
            width_pt, height_pt = page.get_size()
            dimensions[i + 1] = (width_pt, height_pt)

        pdf.close()
        return dimensions
