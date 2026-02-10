"""Real-time logging tab for the Gradio UI."""

import gradio as gr
import time
from typing import List

from .helpers import log_queue


def create_logs_tab() -> dict:
    """Create the real-time logs tab.

    Returns:
        Dictionary of component references
    """
    components = {}

    with gr.Column():
        gr.Markdown("### 📝 Real-Time Logs")
        gr.Markdown("View pipeline execution logs in real-time")

        # Log controls
        with gr.Row():
            log_level = gr.Dropdown(
                choices=["ALL", "DEBUG", "INFO", "WARNING", "ERROR"],
                label="Log Level",
                value="INFO"
            )
            auto_scroll = gr.Checkbox(
                label="Auto-scroll",
                value=True
            )
            clear_btn = gr.Button("🗑️ Clear", size="sm")

        # Log display
        log_output = gr.Textbox(
            label="Logs",
            lines=25,
            max_lines=25,
            interactive=False,
            show_copy_button=True
        )

        # Log statistics
        log_stats = gr.Textbox(
            label="Statistics",
            value="0 log entries",
            interactive=False
        )

    # Event handlers
    def get_logs(level_filter: str, current_logs: str) -> tuple:
        """Get new logs from the queue."""
        new_lines = []
        count = 0

        # Drain queue
        while not log_queue.empty():
            try:
                log_entry = log_queue.get_nowait()
                count += 1

                # Filter by level
                if level_filter != "ALL":
                    if level_filter not in log_entry:
                        continue

                new_lines.append(log_entry)
            except:
                break

        if new_lines:
            updated_logs = current_logs + "\n".join(new_lines) + "\n"
            # Keep last 10000 lines to prevent memory issues
            lines = updated_logs.split("\n")
            if len(lines) > 10000:
                updated_logs = "\n".join(lines[-10000:])

            total_lines = len(updated_logs.split("\n"))
            stats = f"{total_lines} log entries ({count} new)"
            return updated_logs, stats
        else:
            return current_logs, log_stats.value or "0 log entries"

    def clear_logs():
        """Clear the log display."""
        # Drain queue
        while not log_queue.empty():
            try:
                log_queue.get_nowait()
            except:
                break
        return "", "0 log entries"

    # Wire up events
    clear_btn.click(
        fn=clear_logs,
        outputs=[log_output, log_stats]
    )

    # Auto-refresh logs every 1 second
    # Note: This would need to be set up in the main app with gr.Timer
    # For now, we'll provide a manual refresh pattern

    # Store components
    components["log_level"] = log_level
    components["auto_scroll"] = auto_scroll
    components["clear_btn"] = clear_btn
    components["log_output"] = log_output
    components["log_stats"] = log_stats
    components["get_logs_fn"] = get_logs  # Export function for main app to wire up

    return components
