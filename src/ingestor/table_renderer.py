"""Table rendering implementations for robust text representation."""

import html
from typing import Optional

from .config import TableRenderMode
from .di_extractor import ExtractedTable
from .logging_utils import get_logger

logger = get_logger(__name__)


class TableRenderer:
    """Renders tables as text for chunking and embeddings."""
    
    def __init__(self, mode: TableRenderMode = TableRenderMode.PLAIN):
        self.mode = mode
    
    def render(self, table: ExtractedTable) -> str:
        """Render table to text based on configured mode."""
        # Render table content
        if self.mode == TableRenderMode.HTML:
            table_content = self._render_html(table)
        elif self.mode == TableRenderMode.MARKDOWN:
            table_content = self._render_markdown(table)
        else:  # PLAIN (default)
            table_content = self._render_plain(table)

        # Prepend caption if present (e.g., "Figure 3. LIR snippet...")
        if table.caption:
            return f"{table.caption}\n\n{table_content}"

        return table_content
    
    def _render_plain(self, table: ExtractedTable) -> str:
        """Render table as plain text grid with robust handling of merged cells."""
        # Build a grid to handle row/column spans
        grid: list[list[Optional[str]]] = [
            [None for _ in range(table.column_count)]
            for _ in range(table.row_count)
        ]
        
        # Fill grid with cell contents, handling spans
        for cell in table.cells:
            row = cell["row_index"]
            col = cell["column_index"]
            content = cell["content"].strip()
            row_span = cell["row_span"]
            col_span = cell["column_span"]
            
            # Place content in top-left cell of span
            grid[row][col] = content
            
            # Mark spanned cells as occupied
            for r in range(row, min(row + row_span, table.row_count)):
                for c in range(col, min(col + col_span, table.column_count)):
                    if r != row or c != col:
                        grid[r][c] = ""  # Occupied by span
        
        # Calculate column widths
        col_widths = [0] * table.column_count
        for col in range(table.column_count):
            for row in range(table.row_count):
                if grid[row][col] is not None and grid[row][col] != "":
                    col_widths[col] = max(col_widths[col], len(grid[row][col]))
        
        # Ensure minimum width
        col_widths = [max(w, 3) for w in col_widths]
        
        # Build text representation
        lines = []
        separator = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
        
        lines.append(separator)
        for row_idx, row in enumerate(grid):
            cells = []
            for col_idx, cell in enumerate(row):
                content = cell if cell is not None else ""
                cells.append(f" {content:<{col_widths[col_idx]}} ")
            lines.append("|" + "|".join(cells) + "|")
            
            # Add separator after header row (heuristic: first row)
            if row_idx == 0:
                lines.append(separator)
        
        lines.append(separator)
        return "\n".join(lines)
    
    def _render_markdown(self, table: ExtractedTable) -> str:
        """Render table as Markdown (best-effort, may not handle complex spans perfectly)."""
        # Build row structure
        rows: list[list[str]] = [[] for _ in range(table.row_count)]
        
        # Sort cells by row/column
        sorted_cells = sorted(
            table.cells,
            key=lambda c: (c["row_index"], c["column_index"])
        )
        
        # Fill rows
        for row_idx in range(table.row_count):
            row_cells = [c for c in sorted_cells if c["row_index"] == row_idx]
            rows[row_idx] = [c["content"].strip() for c in row_cells]
        
        if not rows:
            return ""
        
        # Build markdown
        lines = []
        
        # Header row
        if rows:
            header_cells = rows[0]
            lines.append("| " + " | ".join(header_cells) + " |")
            lines.append("| " + " | ".join(["---"] * len(header_cells)) + " |")
        
        # Data rows
        for row in rows[1:]:
            lines.append("| " + " | ".join(row) + " |")
        
        return "\n".join(lines)
    
    def _render_html(self, table: ExtractedTable) -> str:
        """Render table as HTML."""
        table_html = "<table>"
        
        # Build rows sorted by row index
        rows = [
            sorted([cell for cell in table.cells if cell["row_index"] == i], 
                   key=lambda cell: cell["column_index"])
            for i in range(table.row_count)
        ]
        
        for row_cells in rows:
            table_html += "<tr>"
            for cell in row_cells:
                # Determine tag type
                tag = "th" if cell["kind"] in ["columnHeader", "rowHeader"] else "td"
                
                # Handle spans
                cell_spans = ""
                if cell.get("column_span") and cell["column_span"] > 1:
                    cell_spans += f' colSpan={cell["column_span"]}'
                if cell.get("row_span") and cell["row_span"] > 1:
                    cell_spans += f' rowSpan={cell["row_span"]}'
                
                # Escape content
                content = html.escape(cell["content"])
                table_html += f"<{tag}{cell_spans}>{content}</{tag}>"
            table_html += "</tr>"
        
        table_html += "</table>"
        return table_html


def create_table_renderer(mode: TableRenderMode = TableRenderMode.PLAIN) -> TableRenderer:
    """Factory function to create table renderer."""
    return TableRenderer(mode)

