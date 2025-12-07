"""Coordinate normalization for bounding boxes."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CoordOrigin(str, Enum):
    """Coordinate system origin."""

    BOTTOMLEFT = "BOTTOMLEFT"
    TOPLEFT = "TOPLEFT"


@dataclass
class NormalizedBBox:
    """
    Normalized bounding box in TOPLEFT coordinate system.

    All coordinates are in the same units as the source (typically PDF points).
    The origin (0, 0) is at the top-left corner.
    """

    x: float
    y: float
    width: float
    height: float

    def scale(self, factor: float) -> "NormalizedBBox":
        """Return a new bbox scaled by the given factor."""
        return NormalizedBBox(
            x=self.x * factor,
            y=self.y * factor,
            width=self.width * factor,
            height=self.height * factor,
        )

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

    def is_valid(self) -> bool:
        """Check if bbox has positive dimensions."""
        return self.width > 0 and self.height > 0


class CoordinateNormalizer:
    """
    Transforms bounding boxes to a normalized TOPLEFT coordinate system.

    PDF documents use BOTTOMLEFT origin (y increases upward).
    Web/HTML uses TOPLEFT origin (y increases downward).
    This class handles the transformation between these systems.
    """

    @staticmethod
    def normalize_bbox(
        bbox: dict[str, Any],
        page_height: float,
        default_origin: CoordOrigin = CoordOrigin.BOTTOMLEFT,
    ) -> NormalizedBBox:
        """
        Transform a bounding box to TOPLEFT coordinate system.

        Args:
            bbox: Dictionary with l, r, t, b keys and optional coord_origin
            page_height: Height of the page in the same units as bbox
            default_origin: Origin to assume if not specified in bbox

        Returns:
            NormalizedBBox in TOPLEFT coordinates

        The transformation handles two cases:
        - BOTTOMLEFT: origin at bottom-left, y increases upward
          t = max y (top of box from bottom), b = min y (bottom of box from bottom)
        - TOPLEFT: origin at top-left, y increases downward
          t = min y (top of box from top), b = max y (bottom of box from top)
        """
        left = float(bbox.get("l", 0))
        right = float(bbox.get("r", 0))
        top = float(bbox.get("t", 0))
        bottom = float(bbox.get("b", 0))

        origin_str = bbox.get("coord_origin", default_origin.value)
        origin = CoordOrigin(origin_str.upper()) if isinstance(origin_str, str) else origin_str

        if origin == CoordOrigin.BOTTOMLEFT:
            x = left
            y = page_height - top
            width = right - left
            height = top - bottom
        else:
            x = left
            y = top
            width = right - left
            height = bottom - top

        return NormalizedBBox(x=x, y=y, width=width, height=height)

    @staticmethod
    def scale_bbox(bbox: NormalizedBBox, scale_factor: float) -> NormalizedBBox:
        """
        Scale a bounding box by the given factor.

        Args:
            bbox: Normalized bounding box
            scale_factor: Multiplier for all dimensions

        Returns:
            Scaled NormalizedBBox
        """
        return bbox.scale(scale_factor)

    @staticmethod
    def validate_bbox(bbox: NormalizedBBox) -> bool:
        """
        Validate that a bounding box has positive dimensions.

        Args:
            bbox: Normalized bounding box to validate

        Returns:
            True if valid, False otherwise
        """
        return bbox.is_valid()


def normalize_from_docling_bbox(
    docling_bbox: Any,
    page_height: float,
) -> NormalizedBBox:
    """
    Normalize a BoundingBox object from docling-core.

    Args:
        docling_bbox: BoundingBox instance from docling_core.types.doc
        page_height: Height of the page

    Returns:
        NormalizedBBox in TOPLEFT coordinates
    """
    bbox_dict = {
        "l": docling_bbox.l,
        "r": docling_bbox.r,
        "t": docling_bbox.t,
        "b": docling_bbox.b,
        "coord_origin": getattr(docling_bbox, "coord_origin", "BOTTOMLEFT"),
    }
    return CoordinateNormalizer.normalize_bbox(bbox_dict, page_height)
