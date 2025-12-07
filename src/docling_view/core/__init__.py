"""Core modules for document processing."""

from docling_view.core.normalizer import CoordinateNormalizer, NormalizedBBox
from docling_view.core.parser import DoclingParser, DocumentItem, PageData, ParsedDocument
from docling_view.core.processor import DocumentProcessor

__all__ = [
    "CoordinateNormalizer",
    "NormalizedBBox",
    "DoclingParser",
    "DocumentItem",
    "PageData",
    "ParsedDocument",
    "DocumentProcessor",
]
