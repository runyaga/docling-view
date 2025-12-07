"""Unit tests for coordinate normalizer."""

import pytest

from docling_view.core.normalizer import (
    CoordinateNormalizer,
    CoordOrigin,
    NormalizedBBox,
)


class TestNormalizedBBox:
    """Tests for NormalizedBBox dataclass."""

    def test_create_bbox(self):
        """Test creating a normalized bbox."""
        bbox = NormalizedBBox(x=10.0, y=20.0, width=100.0, height=50.0)

        assert bbox.x == 10.0
        assert bbox.y == 20.0
        assert bbox.width == 100.0
        assert bbox.height == 50.0

    def test_scale_bbox(self):
        """Test scaling a bbox by a factor."""
        bbox = NormalizedBBox(x=10.0, y=20.0, width=100.0, height=50.0)
        scaled = bbox.scale(2.0)

        assert scaled.x == 20.0
        assert scaled.y == 40.0
        assert scaled.width == 200.0
        assert scaled.height == 100.0

    def test_to_dict(self):
        """Test converting bbox to dictionary."""
        bbox = NormalizedBBox(x=10.0, y=20.0, width=100.0, height=50.0)
        d = bbox.to_dict()

        assert d == {"x": 10.0, "y": 20.0, "width": 100.0, "height": 50.0}

    def test_is_valid_positive_dimensions(self):
        """Test validity check with positive dimensions."""
        bbox = NormalizedBBox(x=10.0, y=20.0, width=100.0, height=50.0)
        assert bbox.is_valid() is True

    def test_is_valid_zero_width(self):
        """Test validity check with zero width."""
        bbox = NormalizedBBox(x=10.0, y=20.0, width=0.0, height=50.0)
        assert bbox.is_valid() is False

    def test_is_valid_negative_height(self):
        """Test validity check with negative height."""
        bbox = NormalizedBBox(x=10.0, y=20.0, width=100.0, height=-50.0)
        assert bbox.is_valid() is False


class TestCoordinateNormalizer:
    """Tests for CoordinateNormalizer."""

    def test_normalize_bottomleft_origin(
        self, sample_bbox_bottomleft: dict, standard_page_height: float
    ):
        """Test normalizing a BOTTOMLEFT coordinate bbox."""
        bbox = CoordinateNormalizer.normalize_bbox(
            sample_bbox_bottomleft, standard_page_height
        )

        assert bbox.x == 72.0
        assert bbox.y == 792.0 - 720.0
        assert bbox.width == 300.0 - 72.0
        assert bbox.height == 720.0 - 650.0

    def test_normalize_topleft_origin(
        self, sample_bbox_topleft: dict, standard_page_height: float
    ):
        """Test normalizing a TOPLEFT coordinate bbox (passthrough)."""
        bbox = CoordinateNormalizer.normalize_bbox(
            sample_bbox_topleft, standard_page_height
        )

        assert bbox.x == 72.0
        assert bbox.y == 72.0
        assert bbox.width == 300.0 - 72.0
        assert bbox.height == 142.0 - 72.0

    def test_normalize_default_origin_is_bottomleft(self, standard_page_height: float):
        """Test that missing coord_origin defaults to BOTTOMLEFT."""
        bbox_dict = {
            "l": 72.0,
            "t": 720.0,
            "r": 300.0,
            "b": 650.0,
        }

        bbox = CoordinateNormalizer.normalize_bbox(bbox_dict, standard_page_height)

        assert bbox.y == 792.0 - 720.0
        assert bbox.height == 720.0 - 650.0

    def test_ruler_test_bottomleft(
        self, ruler_test_bbox_bottomleft: dict, standard_page_height: float
    ):
        """
        Validate coordinate transformation with known geometry.

        1-inch box at (72, 72) from bottom-left.
        In BOTTOMLEFT: l=72, b=72, r=144, t=144
        Expected in TOPLEFT: y = 792 - 144 = 648
        """
        bbox = CoordinateNormalizer.normalize_bbox(
            ruler_test_bbox_bottomleft, standard_page_height
        )

        assert bbox.x == 72.0
        assert bbox.y == 792.0 - 144.0
        assert bbox.width == 72.0
        assert bbox.height == 72.0

    def test_ruler_test_topleft(
        self, ruler_test_bbox_topleft: dict, standard_page_height: float
    ):
        """
        Validate coordinate transformation with known geometry.

        1-inch box at (72, 72) from top-left.
        In TOPLEFT: l=72, t=72, r=144, b=144
        Expected: coordinates unchanged.
        """
        bbox = CoordinateNormalizer.normalize_bbox(
            ruler_test_bbox_topleft, standard_page_height
        )

        assert bbox.x == 72.0
        assert bbox.y == 72.0
        assert bbox.width == 72.0
        assert bbox.height == 72.0

    def test_scale_bbox_method(self):
        """Test the scale_bbox static method."""
        original = NormalizedBBox(x=10.0, y=20.0, width=100.0, height=50.0)
        scaled = CoordinateNormalizer.scale_bbox(original, 2.0)

        assert scaled.x == 20.0
        assert scaled.y == 40.0
        assert scaled.width == 200.0
        assert scaled.height == 100.0

    def test_validate_positive_dimensions(self):
        """Test validation of positive dimensions."""
        valid_bbox = NormalizedBBox(x=10.0, y=20.0, width=100.0, height=50.0)
        assert CoordinateNormalizer.validate_bbox(valid_bbox) is True

    def test_validate_negative_dimensions(self):
        """Test validation rejects negative dimensions."""
        invalid_bbox = NormalizedBBox(x=10.0, y=20.0, width=-100.0, height=50.0)
        assert CoordinateNormalizer.validate_bbox(invalid_bbox) is False

    def test_normalize_with_string_origin(self, standard_page_height: float):
        """Test normalizing with string coord_origin value."""
        bbox_dict = {
            "l": 72.0,
            "t": 720.0,
            "r": 300.0,
            "b": 650.0,
            "coord_origin": "bottomleft",
        }

        bbox = CoordinateNormalizer.normalize_bbox(bbox_dict, standard_page_height)
        assert bbox.is_valid()

    def test_normalize_at_page_boundary(self, standard_page_height: float):
        """Test bbox at the top of page (y close to page height)."""
        bbox_dict = {
            "l": 0.0,
            "t": 792.0,
            "r": 100.0,
            "b": 750.0,
            "coord_origin": "BOTTOMLEFT",
        }

        bbox = CoordinateNormalizer.normalize_bbox(bbox_dict, standard_page_height)

        assert bbox.y == 0.0
        assert bbox.height == 42.0


class TestCoordOriginEnum:
    """Tests for CoordOrigin enum."""

    def test_bottomleft_value(self):
        """Test BOTTOMLEFT enum value."""
        assert CoordOrigin.BOTTOMLEFT.value == "BOTTOMLEFT"

    def test_topleft_value(self):
        """Test TOPLEFT enum value."""
        assert CoordOrigin.TOPLEFT.value == "TOPLEFT"

    def test_enum_from_string(self):
        """Test creating enum from string."""
        origin = CoordOrigin("BOTTOMLEFT")
        assert origin == CoordOrigin.BOTTOMLEFT
