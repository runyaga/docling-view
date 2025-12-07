"""Browser utility for opening HTML files."""

import webbrowser
from pathlib import Path


def open_in_browser(path: Path) -> bool:
    """
    Open a file in the default web browser.

    Args:
        path: Path to the HTML file to open

    Returns:
        True if browser was opened successfully
    """
    url = path.absolute().as_uri()
    return webbrowser.open(url)
