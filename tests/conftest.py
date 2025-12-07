"""Pytest fixtures for docling-view tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_docling_json() -> dict:
    """Sample Docling JSON document structure."""
    return {
        "schema_name": "DoclingDocument",
        "version": "2.64.0",
        "name": "test_document",
        "pages": {
            "1": {
                "size": {"width": 612.0, "height": 792.0},
                "page_no": 1,
            },
            "2": {
                "size": {"width": 612.0, "height": 792.0},
                "page_no": 2,
            },
        },
        "texts": [
            {
                "self_ref": "#/texts/0",
                "label": "section_header",
                "text": "Introduction",
                "prov": [
                    {
                        "page_no": 1,
                        "bbox": {
                            "l": 72.0,
                            "t": 720.0,
                            "r": 300.0,
                            "b": 700.0,
                            "coord_origin": "BOTTOMLEFT",
                        },
                    }
                ],
            },
            {
                "self_ref": "#/texts/1",
                "label": "text",
                "text": "This is a sample paragraph with some content.",
                "prov": [
                    {
                        "page_no": 1,
                        "bbox": {
                            "l": 72.0,
                            "t": 680.0,
                            "r": 540.0,
                            "b": 620.0,
                            "coord_origin": "BOTTOMLEFT",
                        },
                    }
                ],
            },
            {
                "self_ref": "#/texts/2",
                "label": "text",
                "text": "Second page content.",
                "prov": [
                    {
                        "page_no": 2,
                        "bbox": {
                            "l": 72.0,
                            "t": 720.0,
                            "r": 400.0,
                            "b": 700.0,
                            "coord_origin": "BOTTOMLEFT",
                        },
                    }
                ],
            },
        ],
        "tables": [
            {
                "self_ref": "#/tables/0",
                "label": "table",
                "prov": [
                    {
                        "page_no": 1,
                        "bbox": {
                            "l": 72.0,
                            "t": 500.0,
                            "r": 540.0,
                            "b": 350.0,
                            "coord_origin": "BOTTOMLEFT",
                        },
                    }
                ],
                "data": {
                    "num_rows": 3,
                    "num_cols": 2,
                    "grid": [
                        {
                            "row": 0,
                            "col": 0,
                            "text": "Header 1",
                            "column_header": True,
                            "bbox": {
                                "l": 72.0,
                                "t": 500.0,
                                "r": 306.0,
                                "b": 470.0,
                                "coord_origin": "BOTTOMLEFT",
                            },
                        },
                        {
                            "row": 0,
                            "col": 1,
                            "text": "Header 2",
                            "column_header": True,
                            "bbox": {
                                "l": 306.0,
                                "t": 500.0,
                                "r": 540.0,
                                "b": 470.0,
                                "coord_origin": "BOTTOMLEFT",
                            },
                        },
                    ],
                },
            }
        ],
        "pictures": [
            {
                "self_ref": "#/pictures/0",
                "label": "figure",
                "prov": [
                    {
                        "page_no": 1,
                        "bbox": {
                            "l": 150.0,
                            "t": 300.0,
                            "r": 450.0,
                            "b": 100.0,
                            "coord_origin": "BOTTOMLEFT",
                        },
                    }
                ],
            }
        ],
        "furniture": {
            "children": [],
        },
    }


@pytest.fixture
def sample_bbox_bottomleft() -> dict:
    """Sample bounding box in BOTTOMLEFT coordinate system."""
    return {
        "l": 72.0,
        "t": 720.0,
        "r": 300.0,
        "b": 650.0,
        "coord_origin": "BOTTOMLEFT",
    }


@pytest.fixture
def sample_bbox_topleft() -> dict:
    """Sample bounding box in TOPLEFT coordinate system."""
    return {
        "l": 72.0,
        "t": 72.0,
        "r": 300.0,
        "b": 142.0,
        "coord_origin": "TOPLEFT",
    }


@pytest.fixture
def ruler_test_bbox_bottomleft() -> dict:
    """1-inch box at (72, 72) from bottom-left (1 inch = 72 points)."""
    return {
        "l": 72.0,
        "t": 144.0,
        "r": 144.0,
        "b": 72.0,
        "coord_origin": "BOTTOMLEFT",
    }


@pytest.fixture
def ruler_test_bbox_topleft() -> dict:
    """1-inch box at (72, 72) from top-left."""
    return {
        "l": 72.0,
        "t": 72.0,
        "r": 144.0,
        "b": 144.0,
        "coord_origin": "TOPLEFT",
    }


@pytest.fixture
def standard_page_height() -> float:
    """Standard US Letter page height in points."""
    return 792.0


@pytest.fixture
def tmp_json_file(tmp_path: Path, sample_docling_json: dict) -> Path:
    """Create a temporary JSON file with sample data."""
    json_path = tmp_path / "test_document.json"
    with open(json_path, "w") as f:
        json.dump(sample_docling_json, f)
    return json_path


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
