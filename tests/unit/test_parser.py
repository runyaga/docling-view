"""Unit tests for Docling JSON parser."""

from docling_view.core.parser import (
    DoclingParser,
    DocumentItem,
    PageData,
    ParsedDocument,
    TableItem,
)


class TestDoclingParser:
    """Tests for DoclingParser."""

    def test_parse_valid_json(self, sample_docling_json: dict):
        """Test parsing well-formed Docling JSON."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json, name="test")

        assert isinstance(doc, ParsedDocument)
        assert doc.name == "test"
        assert len(doc.pages) == 2

    def test_parse_extracts_page_dimensions(self, sample_docling_json: dict):
        """Test that page dimensions are extracted correctly."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        assert 1 in doc.pages
        assert doc.pages[1].width == 612.0
        assert doc.pages[1].height == 792.0

    def test_extract_text_items(self, sample_docling_json: dict):
        """Test extracting text elements."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        page1_items = doc.get_page_items(1)
        text_items = [i for i in page1_items if i.type in ("text", "heading")]

        assert len(text_items) >= 2

    def test_extract_table_items(self, sample_docling_json: dict):
        """Test extracting table elements with cell data."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        page1_items = doc.get_page_items(1)
        tables = [i for i in page1_items if i.type == "table"]

        assert len(tables) == 1
        table = tables[0]
        assert isinstance(table, TableItem)
        assert table.num_rows == 3
        assert table.num_cols == 2
        assert len(table.cells) == 2

    def test_extract_picture_items(self, sample_docling_json: dict):
        """Test extracting picture elements."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        page1_items = doc.get_page_items(1)
        pictures = [i for i in page1_items if i.type == "picture"]

        assert len(pictures) == 1
        assert pictures[0].bbox.is_valid()

    def test_classify_heading(self, sample_docling_json: dict):
        """Test that section headers are classified as headings."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        page1_items = doc.get_page_items(1)
        headings = [i for i in page1_items if i.type == "heading"]

        assert len(headings) >= 1
        assert headings[0].text == "Introduction"

    def test_items_have_normalized_bbox(self, sample_docling_json: dict):
        """Test that items have normalized bounding boxes."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        page1_items = doc.get_page_items(1)

        for item in page1_items:
            assert item.bbox is not None
            assert item.bbox.x >= 0
            assert item.bbox.y >= 0
            assert item.bbox.width > 0
            assert item.bbox.height > 0

    def test_items_indexed_by_page(self, sample_docling_json: dict):
        """Test that items are correctly indexed by page."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        page1_items = doc.get_page_items(1)
        page2_items = doc.get_page_items(2)

        page1_ids = {i.id for i in page1_items}
        page2_ids = {i.id for i in page2_items}

        assert len(page1_ids & page2_ids) == 0

    def test_filter_by_element_type(self, sample_docling_json: dict):
        """Test filtering items by element type."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        tables_only = doc.get_page_items(1, element_types=["table"])

        assert all(i.type == "table" for i in tables_only)
        assert len(tables_only) == 1

    def test_table_cells_have_header_flag(self, sample_docling_json: dict):
        """Test that table cells have correct header flag."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        tables = [i for i in doc.get_page_items(1) if isinstance(i, TableItem)]
        table = tables[0]

        header_cells = [c for c in table.cells if c.is_header]
        assert len(header_cells) == 2

    def test_parse_empty_document(self):
        """Test parsing document with no content."""
        parser = DoclingParser()
        doc = parser.parse(
            {
                "schema_name": "DoclingDocument",
                "version": "2.64.0",
                "pages": {"1": {"size": {"width": 612, "height": 792}}},
                "texts": [],
                "tables": [],
                "pictures": [],
            }
        )

        assert len(doc.pages) == 1
        assert len(doc.get_page_items(1)) == 0

    def test_parse_missing_prov_gracefully(self):
        """Test that items without provenance are handled gracefully."""
        parser = DoclingParser()
        doc = parser.parse(
            {
                "schema_name": "DoclingDocument",
                "version": "2.64.0",
                "pages": {"1": {"size": {"width": 612, "height": 792}}},
                "texts": [
                    {
                        "self_ref": "#/texts/0",
                        "label": "text",
                        "text": "No provenance",
                    }
                ],
                "tables": [],
                "pictures": [],
            }
        )

        assert len(doc.get_page_items(1)) == 0


class TestParsedDocument:
    """Tests for ParsedDocument dataclass."""

    def test_get_page_items_nonexistent_page(self, sample_docling_json: dict):
        """Test getting items from non-existent page returns empty list."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        items = doc.get_page_items(999)
        assert items == []

    def test_get_page_items_exclude_furniture(self, sample_docling_json: dict):
        """Test excluding furniture items."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        items_with = doc.get_page_items(1, include_furniture=True)
        items_without = doc.get_page_items(1, include_furniture=False)

        assert len(items_without) <= len(items_with)

    def test_items_by_id_lookup(self, sample_docling_json: dict):
        """Test looking up items by ID."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        assert "#/texts/0" in doc.items_by_id
        item = doc.items_by_id["#/texts/0"]
        assert item.type == "heading"


class TestPageData:
    """Tests for PageData dataclass."""

    def test_page_data_creation(self):
        """Test creating PageData."""
        page = PageData(page_no=1, width=612.0, height=792.0)

        assert page.page_no == 1
        assert page.width == 612.0
        assert page.height == 792.0
        assert page.items == []

    def test_page_data_with_items(self):
        """Test PageData with items."""
        from docling_view.core.normalizer import NormalizedBBox

        page = PageData(page_no=1, width=612.0, height=792.0)
        item = DocumentItem(
            id="test",
            type="text",
            bbox=NormalizedBBox(x=0, y=0, width=100, height=50),
            page_no=1,
            label="text",
        )
        page.items.append(item)

        assert len(page.items) == 1
