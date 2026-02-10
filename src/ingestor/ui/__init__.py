"""Ingestor Gradio web interface.

Modular UI structure (v0.3.0):
- helpers.py: Shared utilities and Azure clients
- components/: Reusable UI components (blob browser, index browser, env editor)
- config_tab.py: Configuration and pipeline execution
- files_tab.py: File management and browsing
- artifacts_tab.py: Processing artifacts viewer
- logs_tab.py: Real-time log streaming
- app.py: Main application assembly

For backward compatibility, the monolithic gradio_app.py is still available.
"""

from .app import create_ui, launch

__all__ = ["create_ui", "launch"]
