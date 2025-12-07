"""HTML templates for visualization."""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent


def get_template_path(name: str) -> Path:
    """Get path to a template file."""
    return TEMPLATES_DIR / name
