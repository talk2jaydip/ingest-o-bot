"""Environment variable editor component."""

import os
import gradio as gr
from typing import Dict, Tuple
from pathlib import Path

from ..helpers import get_env_var_safe, mask_sensitive_value


# Environment variable groups
ENV_GROUPS = {
    "Azure Credentials": [
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
        "KEY_VAULT_URI",
    ],
    "Azure AI Search": [
        "AZURE_SEARCH_SERVICE",
        "AZURE_SEARCH_KEY",
        "AZURE_SEARCH_INDEX",
    ],
    "Document Intelligence": [
        "AZURE_DOC_INT_ENDPOINT",
        "AZURE_DOC_INT_KEY",
        "AZURE_DI_MAX_CONCURRENCY",
    ],
    "Azure OpenAI": [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        "AZURE_OPENAI_EMBEDDING_MODEL",
        "AZURE_OPENAI_EMBEDDING_DIMENSIONS",
        "AZURE_OPENAI_CHAT_DEPLOYMENT",
        "AZURE_OPENAI_MODEL_NAME",
        "AZURE_OPENAI_MAX_CONCURRENCY",
        "AZURE_OPENAI_MAX_RETRIES",
    ],
    "Azure Storage Account": [
        "AZURE_STORAGE_ACCOUNT",
        "AZURE_STORAGE_ACCOUNT_KEY",
        "AZURE_CONNECTION_STRING",
        "AZURE_STORAGE_CONTAINER",
    ],
    "Input: Local Files": [
        "AZURE_INPUT_MODE",
        "AZURE_LOCAL_GLOB",
    ],
    "Input: Blob Storage": [
        "AZURE_BLOB_CONTAINER_IN",
        "AZURE_BLOB_PREFIX",
    ],
    "Artifacts: Output Containers": [
        "AZURE_ARTIFACTS_MODE",
        "AZURE_ARTIFACTS_DIR",
        "AZURE_STORE_ARTIFACTS_TO_BLOB",
        "AZURE_BLOB_CONTAINER_PREFIX",
        "AZURE_BLOB_CONTAINER_OUT_PAGES",
        "AZURE_BLOB_CONTAINER_OUT_CHUNKS",
        "AZURE_BLOB_CONTAINER_OUT_IMAGES",
        "AZURE_BLOB_CONTAINER_CITATIONS",
    ],
    "Processing Options": [
        "AZURE_DOCUMENT_ACTION",
        "AZURE_MEDIA_DESCRIBER",
        "AZURE_TABLE_RENDER",
        "AZURE_TABLE_SUMMARIES",
        "AZURE_USE_INTEGRATED_VECTORIZATION",
    ],
    "Chunking": [
        "AZURE_CHUNKING_MAX_CHARS",
        "AZURE_CHUNKING_MAX_TOKENS",
        "AZURE_CHUNKING_OVERLAP_PERCENT",
        "AZURE_CHUNKING_CROSS_PAGE_OVERLAP",
        "AZURE_CHUNKING_DISABLE_CHAR_LIMIT",
    ],
    "Performance": [
        "AZURE_MAX_WORKERS",
        "AZURE_INNER_ANALYZE_WORKERS",
        "AZURE_UPLOAD_DELAY",
        "AZURE_EMBED_BATCH_SIZE",
        "AZURE_UPLOAD_BATCH_SIZE",
    ],
    "Office Extraction": [
        "AZURE_OFFICE_EXTRACTOR_MODE",
        "AZURE_OFFICE_MAX_FILE_SIZE_MB",
        "AZURE_OFFICE_OFFLINE_FALLBACK",
        "AZURE_OFFICE_EQUATION_EXTRACTION",
        "AZURE_OFFICE_LIBREOFFICE_PATH",
        "AZURE_OFFICE_VERBOSE",
    ],
}


def create_env_editor() -> Tuple:
    """Create environment variable editor UI components.

    Returns:
        Tuple of UI components
    """
    with gr.Column():
        gr.Markdown("### ⚙️ Environment Variables")
        gr.Markdown("View and edit environment variables. Changes are temporary unless saved to .env file.")

        # Tabs for each group
        with gr.Tabs():
            all_textboxes = {}

            for group_name, var_names in ENV_GROUPS.items():
                with gr.Tab(group_name):
                    for var_name in var_names:
                        value = get_env_var_safe(var_name, mask=True)
                        textbox = gr.Textbox(
                            label=var_name,
                            value=value,
                            placeholder=f"Enter {var_name}",
                            type="password" if any(s in var_name.upper() for s in ["KEY", "SECRET", "PASSWORD"]) else "text"
                        )
                        all_textboxes[var_name] = textbox

        # Action buttons
        with gr.Row():
            save_btn = gr.Button("💾 Save to .env", variant="primary")
            reload_btn = gr.Button("🔄 Reload from .env")
            validate_btn = gr.Button("✅ Validate")

        status_text = gr.Textbox(
            label="Status",
            value="",
            interactive=False,
            lines=3
        )

    # Event handlers
    def save_to_env(**kwargs):
        """Save environment variables to .env file."""
        try:
            env_file = Path.cwd() / ".env"

            # Read existing .env
            existing = {}
            if env_file.exists():
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            existing[key.strip()] = value.strip()

            # Update with new values
            for var_name, value in kwargs.items():
                if value:  # Only save non-empty values
                    existing[var_name] = value
                    os.environ[var_name] = value  # Update runtime env

            # Write back to .env
            with open(env_file, "w") as f:
                for key, value in existing.items():
                    f.write(f"{key}={value}\n")

            return f"✅ Saved {len(kwargs)} variables to {env_file}"

        except Exception as e:
            return f"❌ Error saving to .env: {str(e)}"

    def reload_from_env():
        """Reload environment variables from .env file."""
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)

            # Return updated values for all textboxes
            updates = {}
            for var_name in all_textboxes.keys():
                updates[var_name] = get_env_var_safe(var_name, mask=True)

            return {
                **{all_textboxes[k]: v for k, v in updates.items()},
                status_text: "✅ Reloaded from .env file"
            }

        except Exception as e:
            return {status_text: f"❌ Error reloading: {str(e)}"}

    def validate_config(**kwargs):
        """Validate environment variable configuration."""
        issues = []
        warnings = []

        # Check required variables
        required = {
            "AZURE_SEARCH_SERVICE": "Azure AI Search",
            "AZURE_SEARCH_KEY": "Azure AI Search",
            "AZURE_SEARCH_INDEX": "Azure AI Search",
            "AZURE_DOC_INT_ENDPOINT": "Document Intelligence",
            "AZURE_OPENAI_ENDPOINT": "Azure OpenAI",
            "AZURE_OPENAI_KEY": "Azure OpenAI",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "Azure OpenAI Embeddings",
        }

        for var, service in required.items():
            value = kwargs.get(var) or os.getenv(var)
            if not value:
                issues.append(f"❌ Missing {var} ({service})")

        # Check input mode specific requirements
        input_mode = kwargs.get("AZURE_INPUT_MODE") or os.getenv("AZURE_INPUT_MODE", "local")
        if input_mode == "blob":
            # Check for input container (explicit or via AZURE_STORAGE_CONTAINER base)
            blob_container_in = kwargs.get("AZURE_BLOB_CONTAINER_IN") or os.getenv("AZURE_BLOB_CONTAINER_IN")
            storage_container = kwargs.get("AZURE_STORAGE_CONTAINER") or os.getenv("AZURE_STORAGE_CONTAINER")

            if not blob_container_in and not storage_container:
                issues.append("❌ Missing AZURE_BLOB_CONTAINER_IN or AZURE_STORAGE_CONTAINER (required for blob input)")

            storage_account = kwargs.get("AZURE_STORAGE_ACCOUNT") or os.getenv("AZURE_STORAGE_ACCOUNT")
            if not storage_account:
                issues.append("❌ Missing AZURE_STORAGE_ACCOUNT (required for blob input)")

            # Check for output container config (explicit or via AZURE_STORAGE_CONTAINER base)
            artifacts_mode = kwargs.get("AZURE_ARTIFACTS_MODE") or os.getenv("AZURE_ARTIFACTS_MODE")
            store_to_blob = (kwargs.get("AZURE_STORE_ARTIFACTS_TO_BLOB") or os.getenv("AZURE_STORE_ARTIFACTS_TO_BLOB", "false")).lower() == "true"
            artifacts_dir = kwargs.get("AZURE_ARTIFACTS_DIR") or os.getenv("AZURE_ARTIFACTS_DIR")

            # Only check output containers if storing artifacts to blob
            if (artifacts_mode == "blob" or store_to_blob) and not artifacts_dir:
                out_pages = kwargs.get("AZURE_BLOB_CONTAINER_OUT_PAGES") or os.getenv("AZURE_BLOB_CONTAINER_OUT_PAGES")
                out_chunks = kwargs.get("AZURE_BLOB_CONTAINER_OUT_CHUNKS") or os.getenv("AZURE_BLOB_CONTAINER_OUT_CHUNKS")

                if not out_pages and not out_chunks and not storage_container:
                    warnings.append("⚠️  Missing output container config (AZURE_BLOB_CONTAINER_OUT_* or AZURE_STORAGE_CONTAINER)")
        elif input_mode == "local":
            local_glob = kwargs.get("AZURE_LOCAL_GLOB") or os.getenv("AZURE_LOCAL_GLOB")
            if not local_glob:
                issues.append("❌ Missing AZURE_LOCAL_GLOB (required for local input)")

        # Check optional but recommended
        recommended = {
            "AZURE_DOC_INT_KEY": "Document Intelligence API authentication",
            "AZURE_OPENAI_CHAT_DEPLOYMENT": "chat/GPT-4 functionality",
            "AZURE_TABLE_RENDER": "table rendering format",
        }

        for var, purpose in recommended.items():
            value = kwargs.get(var) or os.getenv(var)
            if not value:
                warnings.append(f"⚠️  {var} not set (needed for {purpose})")

        # Build status message
        if issues:
            status = "\n".join(issues)
            if warnings:
                status += "\n\n" + "\n".join(warnings)
            return status
        elif warnings:
            return "✅ Required variables configured\n\n" + "\n".join(warnings)
        else:
            return "✅ All required and recommended variables configured!"

    # Wire up events
    save_btn.click(
        fn=save_to_env,
        inputs=list(all_textboxes.values()),
        outputs=[status_text]
    )

    reload_btn.click(
        fn=reload_from_env,
        outputs=[*all_textboxes.values(), status_text]
    )

    validate_btn.click(
        fn=validate_config,
        inputs=list(all_textboxes.values()),
        outputs=[status_text]
    )

    return (
        all_textboxes,
        save_btn,
        reload_btn,
        validate_btn,
        status_text
    )
