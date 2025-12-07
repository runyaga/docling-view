"""Parser for Docling JSON documents."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from docling_view.core.normalizer import CoordinateNormalizer, NormalizedBBox

logger = logging.getLogger(__name__)

SUPPORTED_VERSION = "2.64.0"


class VersionMismatchError(Exception):
    """Raised when Docling JSON version is not supported."""

    pass


class ParseError(Exception):
    """Raised when parsing fails."""

    pass


@dataclass
class DocumentItem:
    """Represents a single document element with normalized coordinates."""

    id: str
    type: str
    bbox: NormalizedBBox
    page_no: int
    label: str
    text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    children: list[str] = field(default_factory=list)
    is_furniture: bool = False


@dataclass
class TableCell:
    """Represents a cell within a table."""

    bbox: NormalizedBBox
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False
    text: str = ""


@dataclass
class TableItem(DocumentItem):
    """Extended document item for tables with cell data."""

    cells: list[TableCell] = field(default_factory=list)
    num_rows: int = 0
    num_cols: int = 0


@dataclass
class PageData:
    """Container for all items on a single page."""

    page_no: int
    width: float
    height: float
    items: list[DocumentItem] = field(default_factory=list)


@dataclass
class ParsedDocument:
    """Container for a fully parsed Docling document."""

    name: str
    version: str
    pages: dict[int, PageData] = field(default_factory=dict)
    items_by_id: dict[str, DocumentItem] = field(default_factory=dict)

    def get_page_items(
        self,
        page_no: int,
        element_types: list[str] | None = None,
        include_furniture: bool = True,
    ) -> list[DocumentItem]:
        """
        Get items for a specific page, optionally filtered.

        Args:
            page_no: Page number (1-indexed)
            element_types: List of types to include (None = all)
            include_furniture: Whether to include furniture items

        Returns:
            List of DocumentItems matching the filters
        """
        if page_no not in self.pages:
            return []

        items = self.pages[page_no].items

        if element_types:
            items = [i for i in items if i.type in element_types]

        if not include_furniture:
            items = [i for i in items if not i.is_furniture]

        return items


class DoclingParser:
    """
    Parser for Docling JSON format.

    Handles parsing of DoclingDocument JSON structure, extracting
    all content items and normalizing their coordinates.
    """

    def __init__(self, normalizer: CoordinateNormalizer | None = None):
        """Initialize parser with optional custom normalizer."""
        self.normalizer = normalizer or CoordinateNormalizer()

    def parse_file(self, json_path: Path) -> ParsedDocument:
        """
        Parse a Docling JSON file.

        Args:
            json_path: Path to the JSON file

        Returns:
            ParsedDocument with all items normalized
        """
        with open(json_path) as f:
            data = json.load(f)

        return self.parse(data, name=json_path.stem)

    def parse(self, data: dict[str, Any], name: str = "document") -> ParsedDocument:
        """
        Parse Docling JSON data.

        Args:
            data: Parsed JSON dictionary
            name: Document name

        Returns:
            ParsedDocument with all items normalized
        """
        version = data.get("schema_name", data.get("version", "unknown"))

        page_dimensions = self._extract_page_dimensions(data)

        doc = ParsedDocument(
            name=name,
            version=version,
            pages={
                page_no: PageData(page_no=page_no, width=dims["width"], height=dims["height"])
                for page_no, dims in page_dimensions.items()
            },
        )

        self._collect_texts(data, doc, page_dimensions)
        self._collect_tables(data, doc, page_dimensions)
        self._collect_pictures(data, doc, page_dimensions)
        self._collect_furniture(data, doc, page_dimensions)

        return doc

    def _extract_page_dimensions(self, data: dict[str, Any]) -> dict[int, dict[str, float]]:
        """Extract page dimensions from the document."""
        dimensions: dict[int, dict[str, float]] = {}

        pages = data.get("pages", {})
        if isinstance(pages, dict):
            for page_key, page_data in pages.items():
                page_no = int(page_key) if isinstance(page_key, str) else page_key
                size = page_data.get("size", {})
                dimensions[page_no] = {
                    "width": float(size.get("width", 612)),
                    "height": float(size.get("height", 792)),
                }
        elif isinstance(pages, list):
            for i, page_data in enumerate(pages, 1):
                size = page_data.get("size", {})
                dimensions[i] = {
                    "width": float(size.get("width", 612)),
                    "height": float(size.get("height", 792)),
                }

        if not dimensions:
            dimensions[1] = {"width": 612, "height": 792}

        return dimensions

    def _extract_provenance(
        self,
        item: dict[str, Any],
        page_dimensions: dict[int, dict[str, float]],
    ) -> list[tuple[int, NormalizedBBox]]:
        """Extract and normalize bounding boxes from provenance."""
        results: list[tuple[int, NormalizedBBox]] = []

        prov_list = item.get("prov", [])
        if not prov_list:
            return results

        for prov in prov_list:
            page_no = prov.get("page_no", prov.get("page", 1))
            bbox_data = prov.get("bbox", {})

            if not bbox_data:
                continue

            page_height = page_dimensions.get(page_no, {"height": 792})["height"]

            try:
                bbox = self.normalizer.normalize_bbox(bbox_data, page_height)
                if bbox.is_valid():
                    results.append((page_no, bbox))
                else:
                    logger.warning(f"Invalid bbox for item on page {page_no}: {bbox_data}")
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to normalize bbox: {e}")

        return results

    def _classify_item_type(self, item: dict[str, Any]) -> str:
        """Determine the semantic type of an item."""
        label = item.get("label", "").lower()
        item_type = item.get("type", "").lower()

        if "section" in label or "heading" in label or "title" in label:
            return "heading"
        if "table" in label or item_type == "table":
            return "table"
        if "picture" in label or "figure" in label or "image" in label:
            return "picture"
        if "list" in label:
            return "list"
        if any(f in label for f in ["header", "footer", "page_number"]):
            return "furniture"

        return "text"

    def _collect_texts(
        self,
        data: dict[str, Any],
        doc: ParsedDocument,
        page_dimensions: dict[int, dict[str, float]],
    ) -> None:
        """Collect text items from the document."""
        texts = data.get("texts", [])

        for item in texts:
            item_id = item.get("self_ref", item.get("id", f"text_{id(item)}"))
            label = item.get("label", "text")
            text = item.get("text", "")
            item_type = self._classify_item_type(item)

            for page_no, bbox in self._extract_provenance(item, page_dimensions):
                doc_item = DocumentItem(
                    id=item_id,
                    type=item_type,
                    bbox=bbox,
                    page_no=page_no,
                    label=label,
                    text=text,
                    metadata={"orig_label": label},
                )

                doc.items_by_id[item_id] = doc_item
                if page_no in doc.pages:
                    doc.pages[page_no].items.append(doc_item)

    def _collect_tables(
        self,
        data: dict[str, Any],
        doc: ParsedDocument,
        page_dimensions: dict[int, dict[str, float]],
    ) -> None:
        """Collect table items with cell data."""
        tables = data.get("tables", [])

        for item in tables:
            item_id = item.get("self_ref", item.get("id", f"table_{id(item)}"))
            label = item.get("label", "table")

            for page_no, bbox in self._extract_provenance(item, page_dimensions):
                table_item = TableItem(
                    id=item_id,
                    type="table",
                    bbox=bbox,
                    page_no=page_no,
                    label=label,
                    text="",
                    metadata={"orig_label": label},
                )

                table_data = item.get("data", {})
                grid = table_data.get("grid", table_data.get("table_cells", []))
                page_height = page_dimensions.get(page_no, {"height": 792})["height"]

                # Handle both 2D grid (list of rows) and flat list of cells
                cells_to_process: list[dict[str, Any]] = []
                if grid and isinstance(grid[0], list):
                    # 2D grid: flatten rows into single list
                    for row in grid:
                        cells_to_process.extend(row)
                else:
                    # Flat list of cells
                    cells_to_process = grid

                for cell_data in cells_to_process:
                    cell_bbox_data = cell_data.get("bbox", {})
                    if cell_bbox_data:
                        cell_bbox = self.normalizer.normalize_bbox(cell_bbox_data, page_height)
                        cell = TableCell(
                            bbox=cell_bbox,
                            row=cell_data.get("row", cell_data.get("start_row_offset_idx", 0)),
                            col=cell_data.get("col", cell_data.get("start_col_offset_idx", 0)),
                            row_span=cell_data.get("row_span", 1),
                            col_span=cell_data.get("col_span", 1),
                            is_header=cell_data.get("column_header", False)
                            or cell_data.get("row_header", False),
                            text=cell_data.get("text", ""),
                        )
                        table_item.cells.append(cell)

                table_item.num_rows = table_data.get("num_rows", 0)
                table_item.num_cols = table_data.get("num_cols", 0)

                doc.items_by_id[item_id] = table_item
                if page_no in doc.pages:
                    doc.pages[page_no].items.append(table_item)

    def _collect_pictures(
        self,
        data: dict[str, Any],
        doc: ParsedDocument,
        page_dimensions: dict[int, dict[str, float]],
    ) -> None:
        """Collect picture/image items."""
        pictures = data.get("pictures", [])

        for item in pictures:
            item_id = item.get("self_ref", item.get("id", f"picture_{id(item)}"))
            label = item.get("label", "picture")

            for page_no, bbox in self._extract_provenance(item, page_dimensions):
                doc_item = DocumentItem(
                    id=item_id,
                    type="picture",
                    bbox=bbox,
                    page_no=page_no,
                    label=label,
                    text="",
                    metadata={"orig_label": label},
                )

                doc.items_by_id[item_id] = doc_item
                if page_no in doc.pages:
                    doc.pages[page_no].items.append(doc_item)

    def _collect_furniture(
        self,
        data: dict[str, Any],
        doc: ParsedDocument,
        page_dimensions: dict[int, dict[str, float]],
    ) -> None:
        """Collect furniture items (headers, footers)."""
        furniture = data.get("furniture", {})
        if not furniture:
            return

        children = furniture.get("children", [])
        for child_ref in children:
            ref = child_ref.get("$ref", "") if isinstance(child_ref, dict) else str(child_ref)

            for item in data.get("texts", []):
                item_ref = item.get("self_ref", "")
                if item_ref == ref or ref.endswith(item_ref):
                    item_id = item.get("self_ref", item.get("id", f"furniture_{id(item)}"))
                    label = item.get("label", "furniture")
                    text = item.get("text", "")

                    for page_no, bbox in self._extract_provenance(item, page_dimensions):
                        doc_item = DocumentItem(
                            id=item_id,
                            type="furniture",
                            bbox=bbox,
                            page_no=page_no,
                            label=label,
                            text=text,
                            metadata={"orig_label": label},
                            is_furniture=True,
                        )

                        doc.items_by_id[item_id] = doc_item
                        if page_no in doc.pages:
                            doc.pages[page_no].items.append(doc_item)
