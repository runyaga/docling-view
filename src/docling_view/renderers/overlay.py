"""Overlay renderer with SVG bounding box visualization."""

import json
from pathlib import Path
from typing import Any

from jinja2 import Template
from rich.console import Console

from docling_view.core.normalizer import NormalizedBBox
from docling_view.core.parser import DocumentItem, ParsedDocument, TableCell, TableItem
from docling_view.renderers.assets import AssetRenderer, PageImage


class OverlayRenderer:
    """
    Renderer that generates interactive SVG overlay visualization.

    Creates an HTML page with:
    - PDF pages rendered as background images
    - SVG overlays with bounding boxes for each element
    - Interactive features (hover, click, layer toggles)
    """

    def __init__(
        self,
        scale: float = 2.0,
        verbose: bool = False,
        console: Console | None = None,
    ):
        """
        Initialize overlay renderer.

        Args:
            scale: Image rendering scale
            verbose: Enable verbose output
            console: Rich console for output
        """
        self.scale = scale
        self.verbose = verbose
        self.console = console or Console()
        self.asset_renderer = AssetRenderer(
            scale=scale,
            verbose=verbose,
            console=console,
        )

    def render(
        self,
        parsed_doc: ParsedDocument,
        pdf_path: Path | None,
        output_path: Path,
        include_furniture: bool = True,
        element_types: list[str] | None = None,
    ) -> None:
        """
        Render the overlay visualization.

        Args:
            parsed_doc: Parsed document with normalized items
            pdf_path: Path to source PDF (for rendering images)
            output_path: Path to write HTML output
            include_furniture: Include furniture elements
            element_types: Filter to specific element types
        """
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        page_images: list[PageImage] = []
        if pdf_path and pdf_path.exists():
            if self.verbose:
                self.console.print("[blue]Rendering PDF pages to images...[/blue]")
            page_images = self.asset_renderer.render_pdf_pages(pdf_path, output_dir)

        if self.verbose:
            self.console.print("[blue]Preparing visualization data...[/blue]")

        pages_data = self._prepare_pages_data(
            parsed_doc,
            page_images,
            include_furniture,
            element_types,
        )

        if self.verbose:
            self.console.print("[blue]Generating HTML...[/blue]")

        html_content = self._generate_html(
            document_name=parsed_doc.name,
            pages_data=pages_data,
        )

        with open(output_path, "w") as f:
            f.write(html_content)

        if self.verbose:
            total_items = sum(len(p["items"]) for p in pages_data)
            self.console.print(
                f"[green]Generated visualization with {len(pages_data)} pages, "
                f"{total_items} items[/green]"
            )

    def _prepare_pages_data(
        self,
        parsed_doc: ParsedDocument,
        page_images: list[PageImage],
        include_furniture: bool,
        element_types: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Prepare page data for template injection."""
        pages_data: list[dict[str, Any]] = []

        image_map = {img.page_no: img for img in page_images}

        for page_no, page_data in sorted(parsed_doc.pages.items()):
            items = parsed_doc.get_page_items(
                page_no,
                element_types=element_types,
                include_furniture=include_furniture,
            )

            page_image = image_map.get(page_no)

            # Calculate scale factors that map JSON coordinates to rendered image pixels.
            # The bbox coordinates are in JSON page coordinate space, so we need to
            # scale from JSON dimensions to image pixel dimensions.
            # This handles cases where JSON page size differs from PDF page size
            # (e.g., JSON created from a different PDF than the one being rendered).
            if page_image:
                # Scale factor = image pixels / JSON page points
                # This correctly maps JSON coordinates to image pixels regardless
                # of whether the PDF page dimensions match the JSON page dimensions.
                x_scale = page_image.width_px / page_data.width
                y_scale = page_image.height_px / page_data.height
            else:
                x_scale = self.scale
                y_scale = self.scale

            scaled_items = [self._scale_item_xy(item, x_scale, y_scale) for item in items]

            # Use actual image dimensions for the SVG viewBox
            view_width: float
            view_height: float
            if page_image:
                view_width = float(page_image.width_px)
                view_height = float(page_image.height_px)
            else:
                view_width = page_data.width * self.scale
                view_height = page_data.height * self.scale

            page_dict: dict[str, Any] = {
                "page_no": page_no,
                "width": view_width,
                "height": view_height,
                "image": page_image.path if page_image else None,
                "items": scaled_items,
            }
            pages_data.append(page_dict)

        return pages_data

    def _scale_item(
        self,
        item: DocumentItem,
        scale_factor: float,
    ) -> dict[str, Any]:
        """Scale item coordinates and prepare for JSON serialization."""
        return self._scale_item_xy(item, scale_factor, scale_factor)

    def _scale_item_xy(
        self,
        item: DocumentItem,
        x_scale: float,
        y_scale: float,
    ) -> dict[str, Any]:
        """Scale item coordinates with separate x/y factors for JSON serialization."""
        scaled_bbox = self._scale_bbox_xy(item.bbox, x_scale, y_scale)

        item_dict: dict[str, Any] = {
            "id": item.id,
            "type": item.type,
            "label": item.label,
            "text": item.text[:200] if item.text else "",
            "bbox": scaled_bbox,
            "is_furniture": item.is_furniture,
        }

        if isinstance(item, TableItem) and item.cells:
            item_dict["cells"] = [
                self._scale_cell_xy(cell, x_scale, y_scale) for cell in item.cells
            ]
            item_dict["num_rows"] = item.num_rows
            item_dict["num_cols"] = item.num_cols

        return item_dict

    def _scale_bbox_xy(
        self,
        bbox: NormalizedBBox,
        x_scale: float,
        y_scale: float,
    ) -> dict[str, float]:
        """Scale a bbox with separate x/y factors."""
        return {
            "x": bbox.x * x_scale,
            "y": bbox.y * y_scale,
            "width": bbox.width * x_scale,
            "height": bbox.height * y_scale,
        }

    def _scale_cell(
        self,
        cell: TableCell,
        scale_factor: float,
    ) -> dict[str, Any]:
        """Scale table cell coordinates."""
        return self._scale_cell_xy(cell, scale_factor, scale_factor)

    def _scale_cell_xy(
        self,
        cell: TableCell,
        x_scale: float,
        y_scale: float,
    ) -> dict[str, Any]:
        """Scale table cell coordinates with separate x/y factors."""
        scaled_bbox = self._scale_bbox_xy(cell.bbox, x_scale, y_scale)

        return {
            "bbox": scaled_bbox,
            "row": cell.row,
            "col": cell.col,
            "row_span": cell.row_span,
            "col_span": cell.col_span,
            "is_header": cell.is_header,
            "text": cell.text[:100] if cell.text else "",
        }

    def _generate_html(
        self,
        document_name: str,
        pages_data: list[dict[str, Any]],
    ) -> str:
        """Generate the final HTML with embedded data."""
        template = Template(HTML_TEMPLATE)

        result: str = template.render(
            document_name=document_name,
            pages_data_json=json.dumps(pages_data, indent=2),
            styles=CSS_STYLES,
        )
        return result


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Docling Visualizer - {{ document_name }}</title>
    <style>
{{ styles }}
    </style>
</head>
<body>
    <div id="app">
        <nav id="sidebar">
            <h1>Docling Viewer</h1>
            <h2>{{ document_name }}</h2>

            <div class="section">
                <h3>Pages</h3>
                <ul id="page-list"></ul>
            </div>

            <div class="section">
                <h3>Layers</h3>
                <div id="layer-toggles">
                    <label><input type="checkbox" data-type="text" checked> Text</label>
                    <label><input type="checkbox" data-type="heading" checked> Headings</label>
                    <label><input type="checkbox" data-type="table" checked> Tables</label>
                    <label><input type="checkbox" data-type="picture" checked> Pictures</label>
                    <label><input type="checkbox" data-type="list" checked> Lists</label>
                    <label><input type="checkbox" data-type="furniture"> Furniture</label>
                </div>
            </div>

            <div class="section">
                <h3>Statistics</h3>
                <div id="stats"></div>
            </div>
        </nav>

        <main id="viewer">
            <div id="page-container">
                <img id="page-image" src="" alt="Page">
                <svg id="overlay"></svg>
            </div>
        </main>

        <aside id="inspector">
            <h2>Element Details</h2>
            <div id="element-info">
                <p class="hint">Hover over an element to see details</p>
            </div>
            <h3>JSON</h3>
            <pre id="element-json"></pre>
        </aside>
    </div>

    <script>
        const docData = {{ pages_data_json }};

        let currentPage = 1;
        let visibleTypes = new Set(['text', 'heading', 'table', 'picture', 'list']);

        function init() {
            buildPageList();
            setupLayerToggles();
            if (docData.length > 0) {
                showPage(1);
            }
            updateStats();
        }

        function buildPageList() {
            const list = document.getElementById('page-list');
            list.innerHTML = '';

            docData.forEach((page, idx) => {
                const li = document.createElement('li');
                li.textContent = `Page ${page.page_no}`;
                li.dataset.page = page.page_no;
                li.onclick = () => showPage(page.page_no);
                if (idx === 0) li.classList.add('active');
                list.appendChild(li);
            });
        }

        function setupLayerToggles() {
            document.querySelectorAll('#layer-toggles input').forEach(cb => {
                cb.onchange = () => {
                    const type = cb.dataset.type;
                    if (cb.checked) {
                        visibleTypes.add(type);
                    } else {
                        visibleTypes.delete(type);
                    }
                    renderOverlay();
                };
            });
        }

        function showPage(pageNo) {
            currentPage = pageNo;
            const page = docData.find(p => p.page_no === pageNo);
            if (!page) return;

            // Update page list active state
            document.querySelectorAll('#page-list li').forEach(li => {
                li.classList.toggle('active', parseInt(li.dataset.page) === pageNo);
            });

            // Update image
            const img = document.getElementById('page-image');
            if (page.image) {
                img.src = page.image;
                img.style.display = 'block';
            } else {
                img.style.display = 'none';
            }

            // Update SVG - use 100% width/height to scale with image
            // viewBox handles coordinate mapping, preserveAspectRatio ensures proper fit
            const svg = document.getElementById('overlay');
            svg.setAttribute('viewBox', `0 0 ${page.width} ${page.height}`);
            svg.setAttribute('preserveAspectRatio', 'xMinYMin meet');
            svg.style.width = '100%';
            svg.style.height = '100%';

            renderOverlay();
        }

        function renderOverlay() {
            const page = docData.find(p => p.page_no === currentPage);
            if (!page) return;

            const svg = document.getElementById('overlay');
            svg.innerHTML = '';

            page.items.forEach(item => {
                if (!visibleTypes.has(item.type)) return;

                // Main bounding box
                const rect = createRect(item.bbox, item.type, item);
                svg.appendChild(rect);

                // Table cells
                if (item.cells) {
                    item.cells.forEach(cell => {
                        const cellRect = createCellRect(cell.bbox, cell.is_header);
                        svg.appendChild(cellRect);
                    });
                }
            });
        }

        function createRect(bbox, type, item) {
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('x', bbox.x);
            rect.setAttribute('y', bbox.y);
            rect.setAttribute('width', bbox.width);
            rect.setAttribute('height', bbox.height);
            rect.setAttribute('class', `doc-item ${type}`);
            rect.dataset.item = JSON.stringify(item);

            rect.onmouseenter = () => showElementInfo(item);
            rect.onmouseleave = () => clearElementInfo();
            rect.onclick = () => showElementJson(item);

            return rect;
        }

        function createCellRect(bbox, isHeader) {
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('x', bbox.x);
            rect.setAttribute('y', bbox.y);
            rect.setAttribute('width', bbox.width);
            rect.setAttribute('height', bbox.height);
            rect.setAttribute('class', `table-cell ${isHeader ? 'header' : ''}`);
            return rect;
        }

        function showElementInfo(item) {
            const info = document.getElementById('element-info');
            const b = item.bbox;
            const txt = item.text ? escapeHtml(item.text.substring(0, 150)) : '';
            const ellip = item.text && item.text.length > 150 ? '...' : '';
            info.innerHTML = `
                <p><strong>Type:</strong> ${item.type}</p>
                <p><strong>Label:</strong> ${item.label}</p>
                ${item.text ? `<p><strong>Text:</strong> ${txt}${ellip}</p>` : ''}
                <p><strong>Pos:</strong> (${Math.round(b.x)}, ${Math.round(b.y)})</p>
                <p><strong>Size:</strong> ${Math.round(b.width)} x ${Math.round(b.height)}</p>
            `;
        }

        function clearElementInfo() {
            const info = document.getElementById('element-info');
            info.innerHTML = '<p class="hint">Hover over an element to see details</p>';
        }

        function showElementJson(item) {
            const json = document.getElementById('element-json');
            json.textContent = JSON.stringify(item, null, 2);
        }

        function updateStats() {
            let totalItems = 0;
            const typeCounts = {};

            docData.forEach(page => {
                page.items.forEach(item => {
                    totalItems++;
                    typeCounts[item.type] = (typeCounts[item.type] || 0) + 1;
                });
            });

            const stats = document.getElementById('stats');
            stats.innerHTML = `
                <p><strong>Pages:</strong> ${docData.length}</p>
                <p><strong>Total Items:</strong> ${totalItems}</p>
                ${Object.entries(typeCounts).map(([type, count]) =>
                    `<p><strong>${type}:</strong> ${count}</p>`
                ).join('')}
            `;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
"""

CSS_STYLES = """
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #1a1a2e;
    color: #eee;
    height: 100vh;
    overflow: hidden;
}

#app {
    display: grid;
    grid-template-columns: 250px 1fr 300px;
    height: 100vh;
}

/* Sidebar */
#sidebar {
    background: #16213e;
    padding: 20px;
    overflow-y: auto;
    border-right: 1px solid #0f3460;
}

#sidebar h1 {
    font-size: 1.2rem;
    color: #e94560;
    margin-bottom: 5px;
}

#sidebar h2 {
    font-size: 0.9rem;
    color: #888;
    margin-bottom: 20px;
    word-break: break-all;
}

#sidebar h3 {
    font-size: 0.85rem;
    color: #aaa;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.section {
    margin-bottom: 25px;
}

#page-list {
    list-style: none;
}

#page-list li {
    padding: 8px 12px;
    cursor: pointer;
    border-radius: 4px;
    margin-bottom: 4px;
    transition: background 0.2s;
}

#page-list li:hover {
    background: #0f3460;
}

#page-list li.active {
    background: #e94560;
    color: white;
}

#layer-toggles label {
    display: block;
    padding: 6px 0;
    cursor: pointer;
}

#layer-toggles input {
    margin-right: 8px;
}

#stats p {
    font-size: 0.85rem;
    margin-bottom: 5px;
    color: #aaa;
}

#stats strong {
    color: #ddd;
}

/* Main Viewer */
#viewer {
    background: #2a2a4a;
    overflow: auto;
    padding: 20px;
    display: flex;
    justify-content: center;
    align-items: flex-start;
}

#page-container {
    position: relative;
    background: white;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}

#page-image {
    display: block;
    max-width: 100%;
    height: auto;
}

#overlay {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: none;
}

#overlay rect {
    pointer-events: all;
    cursor: pointer;
    transition: opacity 0.2s;
}

/* Element Types */
.doc-item {
    fill: transparent;
    stroke-width: 2;
}

.doc-item.text {
    stroke: #28a745;
}

.doc-item.heading {
    stroke: #fd7e14;
    stroke-dasharray: 5,3;
}

.doc-item.table {
    stroke: #007bff;
    fill: rgba(0, 123, 255, 0.1);
}

.doc-item.picture {
    stroke: #dc3545;
    fill: rgba(220, 53, 69, 0.1);
}

.doc-item.list {
    stroke: #6f42c1;
}

.doc-item.furniture {
    stroke: #6c757d;
    stroke-dasharray: 3,3;
}

.doc-item:hover {
    stroke-width: 3;
    fill: rgba(255, 255, 255, 0.2);
}

.table-cell {
    fill: transparent;
    stroke: #17a2b8;
    stroke-width: 1;
}

.table-cell.header {
    fill: rgba(23, 162, 184, 0.15);
    stroke-width: 2;
}

/* Inspector */
#inspector {
    background: #16213e;
    padding: 20px;
    overflow-y: auto;
    border-left: 1px solid #0f3460;
}

#inspector h2 {
    font-size: 1rem;
    margin-bottom: 15px;
    color: #e94560;
}

#inspector h3 {
    font-size: 0.85rem;
    color: #aaa;
    margin: 15px 0 10px;
    text-transform: uppercase;
}

#element-info {
    font-size: 0.9rem;
    line-height: 1.6;
}

#element-info p {
    margin-bottom: 8px;
}

#element-info .hint {
    color: #666;
    font-style: italic;
}

#element-json {
    background: #0a0a1a;
    padding: 15px;
    border-radius: 4px;
    font-size: 0.75rem;
    overflow-x: auto;
    max-height: 400px;
    overflow-y: auto;
    color: #88d498;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #1a1a2e;
}

::-webkit-scrollbar-thumb {
    background: #0f3460;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #e94560;
}
"""
