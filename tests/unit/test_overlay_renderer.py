"""Unit tests for overlay SVG renderer."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from docling_view.core.normalizer import NormalizedBBox
from docling_view.core.parser import DocumentItem, PageData, ParsedDocument, TableCell, TableItem
from docling_view.renderers.overlay import OverlayRenderer


@pytest.fixture
def sample_parsed_document() -> ParsedDocument:
    """Create a sample parsed document for testing."""
    doc = ParsedDocument(
        name="test_document",
        version="2.64.0",
        pages={
            1: PageData(
                page_no=1,
                width=612.0,
                height=792.0,
                items=[
                    DocumentItem(
                        id="text_1",
                        type="text",
                        bbox=NormalizedBBox(x=72.0, y=72.0, width=468.0, height=30.0),
                        page_no=1,
                        label="text",
                        text="Sample text content",
                    ),
                    DocumentItem(
                        id="heading_1",
                        type="heading",
                        bbox=NormalizedBBox(x=72.0, y=50.0, width=200.0, height=20.0),
                        page_no=1,
                        label="section_header",
                        text="Introduction",
                    ),
                ],
            ),
        },
    )

    for page in doc.pages.values():
        for item in page.items:
            doc.items_by_id[item.id] = item

    return doc


@pytest.fixture
def parsed_doc_with_table() -> ParsedDocument:
    """Create a parsed document with a table for testing."""
    table = TableItem(
        id="table_1",
        type="table",
        bbox=NormalizedBBox(x=72.0, y=200.0, width=468.0, height=150.0),
        page_no=1,
        label="table",
        text="",
        cells=[
            TableCell(
                bbox=NormalizedBBox(x=72.0, y=200.0, width=234.0, height=30.0),
                row=0,
                col=0,
                is_header=True,
                text="Header 1",
            ),
            TableCell(
                bbox=NormalizedBBox(x=306.0, y=200.0, width=234.0, height=30.0),
                row=0,
                col=1,
                is_header=True,
                text="Header 2",
            ),
        ],
        num_rows=3,
        num_cols=2,
    )

    doc = ParsedDocument(
        name="table_document",
        version="2.64.0",
        pages={
            1: PageData(
                page_no=1,
                width=612.0,
                height=792.0,
                items=[table],
            ),
        },
    )
    doc.items_by_id["table_1"] = table
    return doc


class TestOverlayRenderer:
    """Tests for OverlayRenderer."""

    def test_renderer_initialization(self):
        """Test renderer initializes with defaults."""
        renderer = OverlayRenderer()

        assert renderer.scale == 2.0
        assert renderer.verbose is False

    def test_renderer_with_custom_scale(self):
        """Test renderer initializes with custom scale."""
        renderer = OverlayRenderer(scale=3.0)

        assert renderer.scale == 3.0

    def test_scale_item(self, sample_parsed_document: ParsedDocument):
        """Test scaling item coordinates."""
        renderer = OverlayRenderer()
        item = sample_parsed_document.pages[1].items[0]

        scaled = renderer._scale_item(item, 2.0)

        assert scaled["bbox"]["x"] == 144.0
        assert scaled["bbox"]["y"] == 144.0
        assert scaled["bbox"]["width"] == 936.0
        assert scaled["bbox"]["height"] == 60.0

    def test_scale_item_includes_metadata(self, sample_parsed_document: ParsedDocument):
        """Test scaled item includes required metadata."""
        renderer = OverlayRenderer()
        item = sample_parsed_document.pages[1].items[0]

        scaled = renderer._scale_item(item, 1.0)

        assert "id" in scaled
        assert "type" in scaled
        assert "label" in scaled
        assert "text" in scaled
        assert "bbox" in scaled

    def test_scale_table_with_cells(self, parsed_doc_with_table: ParsedDocument):
        """Test scaling table item includes scaled cells."""
        renderer = OverlayRenderer()
        table = parsed_doc_with_table.pages[1].items[0]

        scaled = renderer._scale_item(table, 2.0)

        assert "cells" in scaled
        assert len(scaled["cells"]) == 2
        assert scaled["cells"][0]["bbox"]["x"] == 144.0

    def test_scale_cell(self):
        """Test scaling individual table cell."""
        renderer = OverlayRenderer()
        cell = TableCell(
            bbox=NormalizedBBox(x=72.0, y=200.0, width=234.0, height=30.0),
            row=0,
            col=0,
            is_header=True,
            text="Header",
        )

        scaled = renderer._scale_cell(cell, 2.0)

        assert scaled["bbox"]["x"] == 144.0
        assert scaled["bbox"]["width"] == 468.0
        assert scaled["is_header"] is True
        assert scaled["row"] == 0
        assert scaled["col"] == 0

    def test_prepare_pages_data(self, sample_parsed_document: ParsedDocument):
        """Test preparing pages data for template."""
        renderer = OverlayRenderer()

        pages_data = renderer._prepare_pages_data(
            sample_parsed_document,
            page_images=[],
            include_furniture=True,
            element_types=None,
        )

        assert len(pages_data) == 1
        assert pages_data[0]["page_no"] == 1
        assert len(pages_data[0]["items"]) == 2

    def test_prepare_pages_data_filters_types(self, sample_parsed_document: ParsedDocument):
        """Test filtering pages data by element type."""
        renderer = OverlayRenderer()

        pages_data = renderer._prepare_pages_data(
            sample_parsed_document,
            page_images=[],
            include_furniture=True,
            element_types=["heading"],
        )

        assert len(pages_data[0]["items"]) == 1
        assert pages_data[0]["items"][0]["type"] == "heading"

    def test_generate_html_contains_document_name(self, sample_parsed_document: ParsedDocument):
        """Test generated HTML contains document name."""
        renderer = OverlayRenderer()

        html = renderer._generate_html(
            document_name="test_document",
            pages_data=[],
        )

        assert "test_document" in html

    def test_generate_html_contains_css(self, sample_parsed_document: ParsedDocument):
        """Test generated HTML contains CSS styles."""
        renderer = OverlayRenderer()

        html = renderer._generate_html(
            document_name="test",
            pages_data=[],
        )

        assert ".doc-item" in html
        assert ".text" in html
        assert ".table" in html

    def test_generate_html_contains_javascript(self, sample_parsed_document: ParsedDocument):
        """Test generated HTML contains JavaScript."""
        renderer = OverlayRenderer()

        html = renderer._generate_html(
            document_name="test",
            pages_data=[],
        )

        assert "const docData" in html
        assert "function init()" in html
        assert "function showPage" in html

    def test_render_creates_output_file(
        self, sample_parsed_document: ParsedDocument, tmp_path: Path
    ):
        """Test render creates the output HTML file."""
        renderer = OverlayRenderer()
        output_path = tmp_path / "output" / "index.html"

        renderer.render(
            parsed_doc=sample_parsed_document,
            pdf_path=None,
            output_path=output_path,
        )

        assert output_path.exists()

    def test_render_html_valid_structure(
        self, sample_parsed_document: ParsedDocument, tmp_path: Path
    ):
        """Test rendered HTML has valid structure."""
        renderer = OverlayRenderer()
        output_path = tmp_path / "output.html"

        renderer.render(
            parsed_doc=sample_parsed_document,
            pdf_path=None,
            output_path=output_path,
        )

        content = output_path.read_text()
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "</html>" in content
        assert "<svg" in content

    def test_text_truncation(self, sample_parsed_document: ParsedDocument):
        """Test that long text is truncated in item dict."""
        renderer = OverlayRenderer()

        long_text_item = DocumentItem(
            id="long_text",
            type="text",
            bbox=NormalizedBBox(x=0, y=0, width=100, height=50),
            page_no=1,
            label="text",
            text="A" * 500,
        )

        scaled = renderer._scale_item(long_text_item, 1.0)

        assert len(scaled["text"]) <= 200
