"""Chunk locking component for managing chunk lock states."""

import os
import gradio as gr

from ..helpers import (
    get_chunk_lock_state,
    set_chunk_lock_state,
    get_all_chunks_with_locks,
    bulk_lock_chunks,
    bulk_unlock_chunks,
)


def create_chunk_locker() -> tuple:
    """Create chunk locking component.

    Returns:
        Tuple of UI components for chunk lock management
    """
    with gr.Column():
        gr.Markdown("### 🔒 Chunk Lock Management")
        gr.Markdown("Lock chunks to prevent reprocessing or mark for manual review")

        # Artifacts source
        with gr.Row():
            artifacts_mode = gr.Radio(
                choices=["Local", "Blob Storage"],
                value="Local",
                label="Artifacts Location"
            )
            artifacts_path = gr.Textbox(
                label="Artifacts Path",
                value=os.getenv("AZURE_ARTIFACTS_LOCAL_PATH", "./artifacts"),
                placeholder="./artifacts"
            )
            refresh_btn = gr.Button("🔄 Refresh", size="sm")

        # Two tabs: Locked vs All chunks
        with gr.Tabs():
            with gr.Tab("🔒 Locked Chunks"):
                locked_dataframe = gr.Dataframe(
                    headers=["Chunk ID", "Source", "Page", "Locked By", "Locked At", "Reason"],
                    label="Locked Chunks",
                    interactive=False
                )
                unlock_selected_btn = gr.Button("🔓 Unlock Selected", variant="secondary")

            with gr.Tab("📋 All Chunks"):
                all_dataframe = gr.Dataframe(
                    headers=["Chunk ID", "Source", "Page", "Lock Status"],
                    label="All Chunks",
                    interactive=False
                )
                lock_selected_btn = gr.Button("🔒 Lock Selected", variant="primary")

        # Individual lock/unlock
        with gr.Accordion("🔧 Lock/Unlock Individual Chunk", open=False):
            chunk_id_input = gr.Textbox(
                label="Chunk ID",
                placeholder="Enter chunk ID"
            )
            with gr.Row():
                locked_by_input = gr.Textbox(
                    label="Locked By",
                    value="gradio-user"
                )
                lock_reason_input = gr.Textbox(
                    label="Lock Reason",
                    placeholder="e.g., Manual review pending"
                )
            with gr.Row():
                lock_btn = gr.Button("🔒 Lock", variant="primary")
                unlock_btn = gr.Button("🔓 Unlock", variant="secondary")

        # Bulk operations
        with gr.Accordion("📦 Bulk Operations", open=False):
            bulk_chunk_ids = gr.Textbox(
                label="Chunk IDs (comma-separated)",
                lines=3,
                placeholder="chunk_id_1, chunk_id_2, chunk_id_3"
            )
            bulk_locked_by = gr.Textbox(
                label="Locked By",
                value="gradio-user"
            )
            bulk_lock_reason = gr.Textbox(
                label="Lock Reason",
                placeholder="e.g., Batch review"
            )
            with gr.Row():
                bulk_lock_btn = gr.Button("🔒 Bulk Lock", variant="primary")
                bulk_unlock_btn = gr.Button("🔓 Bulk Unlock", variant="secondary")
            bulk_status = gr.Textbox(
                label="Bulk Status",
                value="",
                interactive=False
            )

        status_text = gr.Textbox(
            label="Status",
            value="",
            interactive=False
        )

    # Event handlers
    def refresh_locks(mode, path):
        """Refresh and load all chunks with lock states.

        Args:
            mode: Artifacts storage mode ("Local" or "Blob Storage")
            path: Path to artifacts directory or blob container

        Returns:
            Tuple of (locked_rows, all_rows, status_message)
        """
        if not path or not path.strip():
            return [], [], "Please specify artifacts path"

        is_blob = (mode == "Blob Storage")
        all_chunks = get_all_chunks_with_locks(path, is_blob)

        if not all_chunks:
            return [], [], "No chunks found in artifacts"

        # Separate locked and all chunks
        locked_chunks = [c for c in all_chunks if c.get('locked')]

        locked_rows = [
            [
                c['chunk_id'],
                c['sourcefile'],
                c['page'],
                c['locked_by'],
                c['locked_at'],
                c['lock_reason']
            ]
            for c in locked_chunks
        ]

        all_rows = [
            [
                c['chunk_id'],
                c['sourcefile'],
                c['page'],
                "🔒 Locked" if c.get('locked') else "🔓 Unlocked"
            ]
            for c in all_chunks
        ]

        status = f"Found {len(all_chunks)} chunks, {len(locked_chunks)} locked"
        return locked_rows, all_rows, status

    def lock_chunk(chunk_id, locked_by, reason, mode, path):
        """Lock a single chunk.

        Args:
            chunk_id: ID of the chunk to lock
            locked_by: User/system performing the lock
            reason: Reason for locking the chunk
            mode: Artifacts storage mode
            path: Path to artifacts directory or blob container

        Returns:
            Tuple of (locked_rows, all_rows, status_message)
        """
        if not chunk_id or not chunk_id.strip():
            return ([], [], "Please enter a chunk ID")

        if not path or not path.strip():
            return ([], [], "Please specify artifacts path")

        is_blob = (mode == "Blob Storage")
        success = set_chunk_lock_state(
            chunk_id.strip(),
            True,
            locked_by,
            reason,
            path,
            is_blob
        )

        # Refresh and return updated data
        locked_rows, all_rows, status = refresh_locks(mode, path)

        if success:
            final_status = f"✅ Locked {chunk_id} | {status}"
        else:
            final_status = f"❌ Failed to lock {chunk_id} | {status}"

        return locked_rows, all_rows, final_status

    def unlock_chunk(chunk_id, mode, path):
        """Unlock a single chunk.

        Args:
            chunk_id: ID of the chunk to unlock
            mode: Artifacts storage mode
            path: Path to artifacts directory or blob container

        Returns:
            Tuple of (locked_rows, all_rows, status_message)
        """
        if not chunk_id or not chunk_id.strip():
            return ([], [], "Please enter a chunk ID")

        if not path or not path.strip():
            return ([], [], "Please specify artifacts path")

        is_blob = (mode == "Blob Storage")
        success = set_chunk_lock_state(
            chunk_id.strip(),
            False,
            "",
            "",
            path,
            is_blob
        )

        # Refresh and return updated data
        locked_rows, all_rows, status = refresh_locks(mode, path)

        if success:
            final_status = f"✅ Unlocked {chunk_id} | {status}"
        else:
            final_status = f"❌ Failed to unlock {chunk_id} | {status}"

        return locked_rows, all_rows, final_status

    def bulk_lock(chunk_ids_str, locked_by, reason, mode, path):
        """Lock multiple chunks in bulk.

        Args:
            chunk_ids_str: Comma-separated chunk IDs
            locked_by: User/system performing the lock
            reason: Reason for locking the chunks
            mode: Artifacts storage mode
            path: Path to artifacts directory or blob container

        Returns:
            Tuple of (locked_rows, all_rows, status_message, bulk_result_message)
        """
        if not chunk_ids_str or not chunk_ids_str.strip():
            return [], [], "Please enter chunk IDs", ""

        if not path or not path.strip():
            return [], [], "Please specify artifacts path", ""

        chunk_ids = [id.strip() for id in chunk_ids_str.split(',') if id.strip()]

        if not chunk_ids:
            return [], [], "No valid chunk IDs provided", ""

        is_blob = (mode == "Blob Storage")
        result = bulk_lock_chunks(chunk_ids, locked_by, reason, path, is_blob)

        # Refresh data
        locked_rows, all_rows, status = refresh_locks(mode, path)

        bulk_result = f"✅ Locked {result['succeeded']}, ❌ Failed {result['failed']}"
        if result['errors']:
            bulk_result += f"\nErrors: {'; '.join(result['errors'][:3])}"

        return locked_rows, all_rows, status, bulk_result

    def bulk_unlock(chunk_ids_str, mode, path):
        """Unlock multiple chunks in bulk.

        Args:
            chunk_ids_str: Comma-separated chunk IDs
            mode: Artifacts storage mode
            path: Path to artifacts directory or blob container

        Returns:
            Tuple of (locked_rows, all_rows, status_message, bulk_result_message)
        """
        if not chunk_ids_str or not chunk_ids_str.strip():
            return [], [], "Please enter chunk IDs", ""

        if not path or not path.strip():
            return [], [], "Please specify artifacts path", ""

        chunk_ids = [id.strip() for id in chunk_ids_str.split(',') if id.strip()]

        if not chunk_ids:
            return [], [], "No valid chunk IDs provided", ""

        is_blob = (mode == "Blob Storage")
        result = bulk_unlock_chunks(chunk_ids, path, is_blob)

        # Refresh data
        locked_rows, all_rows, status = refresh_locks(mode, path)

        bulk_result = f"✅ Unlocked {result['succeeded']}, ❌ Failed {result['failed']}"
        if result['errors']:
            bulk_result += f"\nErrors: {'; '.join(result['errors'][:3])}"

        return locked_rows, all_rows, status, bulk_result

    # Wire events
    refresh_btn.click(
        fn=refresh_locks,
        inputs=[artifacts_mode, artifacts_path],
        outputs=[locked_dataframe, all_dataframe, status_text]
    )

    lock_btn.click(
        fn=lock_chunk,
        inputs=[chunk_id_input, locked_by_input, lock_reason_input, artifacts_mode, artifacts_path],
        outputs=[locked_dataframe, all_dataframe, status_text]
    )

    unlock_btn.click(
        fn=unlock_chunk,
        inputs=[chunk_id_input, artifacts_mode, artifacts_path],
        outputs=[locked_dataframe, all_dataframe, status_text]
    )

    bulk_lock_btn.click(
        fn=bulk_lock,
        inputs=[bulk_chunk_ids, bulk_locked_by, bulk_lock_reason, artifacts_mode, artifacts_path],
        outputs=[locked_dataframe, all_dataframe, status_text, bulk_status]
    )

    bulk_unlock_btn.click(
        fn=bulk_unlock,
        inputs=[bulk_chunk_ids, artifacts_mode, artifacts_path],
        outputs=[locked_dataframe, all_dataframe, status_text, bulk_status]
    )

    # Note: lock_selected_btn and unlock_selected_btn would need interactive dataframes
    # For now, users can copy chunk IDs to bulk operations section

    return (
        locked_dataframe,
        all_dataframe,
        status_text,
        artifacts_path,
        refresh_btn
    )
