"""Integration tests for JSON processing pipeline."""

import json
from pathlib import Path

from docling_view.core.parser import DoclingParser
from docling_view.renderers.overlay import OverlayRenderer


class TestJsonToOverlay:
    """Tests for JSON to overlay HTML pipeline."""

    def test_json_to_parsed_document(self, sample_docling_json: dict):
        """Test parsing JSON to ParsedDocument."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        assert doc.name == "document"
        assert len(doc.pages) == 2
        assert len(doc.get_page_items(1)) > 0

    def test_json_file_to_parsed_document(self, tmp_json_file: Path):
        """Test parsing JSON file to ParsedDocument."""
        parser = DoclingParser()
        doc = parser.parse_file(tmp_json_file)

        assert doc.name == "test_document"
        assert len(doc.pages) > 0

    def test_parsed_document_to_html(self, sample_docling_json: dict, tmp_path: Path):
        """Test rendering ParsedDocument to HTML."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        renderer = OverlayRenderer()
        output_path = tmp_path / "output.html"

        renderer.render(
            parsed_doc=doc,
            pdf_path=None,
            output_path=output_path,
        )

        assert output_path.exists()
        content = output_path.read_text()
        assert "<!DOCTYPE html>" in content
        assert "docData" in content

    def test_full_json_pipeline(self, tmp_json_file: Path, tmp_path: Path):
        """Test full JSON to HTML pipeline."""
        parser = DoclingParser()
        doc = parser.parse_file(tmp_json_file)

        renderer = OverlayRenderer()
        output_path = tmp_path / "visualizer" / "index.html"

        renderer.render(
            parsed_doc=doc,
            pdf_path=None,
            output_path=output_path,
        )

        assert output_path.exists()

        content = output_path.read_text()

        assert "Introduction" in content or "text_1" in content or "docData" in content

    def test_json_with_all_element_types(self, tmp_path: Path):
        """Test JSON with text, tables, and pictures."""
        complex_json = {
            "schema_name": "DoclingDocument",
            "version": "2.64.0",
            "pages": {"1": {"size": {"width": 612, "height": 792}}},
            "texts": [
                {
                    "self_ref": "#/texts/0",
                    "label": "section_header",
                    "text": "Title",
                    "prov": [{"page_no": 1, "bbox": {"l": 72, "t": 720, "r": 300, "b": 700}}],
                },
                {
                    "self_ref": "#/texts/1",
                    "label": "text",
                    "text": "Paragraph",
                    "prov": [{"page_no": 1, "bbox": {"l": 72, "t": 680, "r": 540, "b": 620}}],
                },
            ],
            "tables": [
                {
                    "self_ref": "#/tables/0",
                    "label": "table",
                    "prov": [{"page_no": 1, "bbox": {"l": 72, "t": 500, "r": 540, "b": 350}}],
                    "data": {"num_rows": 2, "num_cols": 2, "grid": []},
                }
            ],
            "pictures": [
                {
                    "self_ref": "#/pictures/0",
                    "label": "figure",
                    "prov": [{"page_no": 1, "bbox": {"l": 150, "t": 300, "r": 450, "b": 100}}],
                }
            ],
        }

        json_path = tmp_path / "complex.json"
        with open(json_path, "w") as f:
            json.dump(complex_json, f)

        parser = DoclingParser()
        doc = parser.parse_file(json_path)

        page1_items = doc.get_page_items(1)

        types_found = {item.type for item in page1_items}
        assert "heading" in types_found
        assert "text" in types_found
        assert "table" in types_found
        assert "picture" in types_found


class TestJsonFiltering:
    """Tests for filtering elements from JSON."""

    def test_filter_by_single_type(self, sample_docling_json: dict):
        """Test filtering to single element type."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        tables = doc.get_page_items(1, element_types=["table"])

        assert all(item.type == "table" for item in tables)

    def test_filter_by_multiple_types(self, sample_docling_json: dict):
        """Test filtering to multiple element types."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        filtered = doc.get_page_items(1, element_types=["heading", "table"])

        types_found = {item.type for item in filtered}
        assert types_found <= {"heading", "table"}

    def test_exclude_furniture(self, sample_docling_json: dict):
        """Test excluding furniture elements."""
        parser = DoclingParser()
        doc = parser.parse(sample_docling_json)

        items = doc.get_page_items(1, include_furniture=False)

        assert all(not item.is_furniture for item in items)


class TestJsonErrorHandling:
    """Tests for error handling in JSON processing."""

    def test_empty_pages(self, tmp_path: Path):
        """Test handling JSON with empty pages."""
        empty_json = {
            "schema_name": "DoclingDocument",
            "version": "2.64.0",
            "pages": {"1": {"size": {"width": 612, "height": 792}}},
            "texts": [],
            "tables": [],
            "pictures": [],
        }

        json_path = tmp_path / "empty.json"
        with open(json_path, "w") as f:
            json.dump(empty_json, f)

        parser = DoclingParser()
        doc = parser.parse_file(json_path)

        assert len(doc.pages) == 1
        assert len(doc.get_page_items(1)) == 0

    def test_missing_bbox_data(self, tmp_path: Path):
        """Test handling items with missing bbox data."""
        bad_json = {
            "schema_name": "DoclingDocument",
            "version": "2.64.0",
            "pages": {"1": {"size": {"width": 612, "height": 792}}},
            "texts": [
                {
                    "self_ref": "#/texts/0",
                    "label": "text",
                    "text": "No bbox",
                    "prov": [{"page_no": 1}],
                }
            ],
            "tables": [],
            "pictures": [],
        }

        json_path = tmp_path / "bad.json"
        with open(json_path, "w") as f:
            json.dump(bad_json, f)

        parser = DoclingParser()
        doc = parser.parse_file(json_path)

        assert len(doc.get_page_items(1)) == 0

    def test_default_page_dimensions(self, tmp_path: Path):
        """Test default page dimensions when not specified."""
        minimal_json = {
            "schema_name": "DoclingDocument",
            "version": "2.64.0",
            "pages": {},
            "texts": [],
            "tables": [],
            "pictures": [],
        }

        json_path = tmp_path / "minimal.json"
        with open(json_path, "w") as f:
            json.dump(minimal_json, f)

        parser = DoclingParser()
        doc = parser.parse_file(json_path)

        assert 1 in doc.pages
        assert doc.pages[1].width == 612
        assert doc.pages[1].height == 792
