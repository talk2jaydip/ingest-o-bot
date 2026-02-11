"""Hugging Face embeddings provider implementation.

This module implements embeddings using sentence-transformers library,
supporting local model execution with CPU/GPU acceleration and various
multilingual and specialized models.
"""

from typing import Optional
import asyncio

from ..embeddings_provider import EmbeddingsProvider

try:
    from sentence_transformers import SentenceTransformer
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class HuggingFaceEmbeddingsProvider(EmbeddingsProvider):
    """Hugging Face embeddings using sentence-transformers.

    Supports local model execution with CPU/GPU acceleration and various
    multilingual and specialized models.

    Models are downloaded from HuggingFace Hub and cached locally in
    ~/.cache/huggingface/
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        batch_size: int = 32,
        normalize_embeddings: bool = True,
        max_seq_length: Optional[int] = None,
        trust_remote_code: bool = False
    ):
        """Initialize Hugging Face embeddings provider.

        Args:
            model_name: HuggingFace model identifier
            device: Device to run on ("cpu", "cuda", "mps")
            batch_size: Batch size for encoding
            normalize_embeddings: Whether to normalize embeddings
            max_seq_length: Maximum sequence length (None = model default)
            trust_remote_code: Trust remote code for custom models

        Raises:
            ImportError: If sentence-transformers is not installed
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for Hugging Face embeddings. "
                "Install with: pip install sentence-transformers"
            )

        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings

        # Load model (downloads if not cached)
        self.model = SentenceTransformer(
            model_name,
            device=device,
            trust_remote_code=trust_remote_code
        )

        # Set max sequence length if specified
        if max_seq_length:
            self.model.max_seq_length = max_seq_length

        # Get dimensions from model
        self._dimensions = self.model.get_sentence_embedding_dimension()

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector as list of floats
        """
        # sentence-transformers is CPU-bound, run in executor
        embedding = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.model.encode(
                text,
                normalize_embeddings=self.normalize_embeddings,
                convert_to_numpy=True
            )
        )
        return embedding.tolist()

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batch.

        Automatically handles batching based on configured batch_size.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors, one for each input text
        """
        # Process all texts at once - model handles batching internally
        embeddings = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.model.encode(
                texts,
                batch_size=self.batch_size,
                normalize_embeddings=self.normalize_embeddings,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100  # Show progress for large batches
            )
        )
        return embeddings.tolist()

    def get_dimensions(self) -> int:
        """Get embedding dimensions.

        Returns:
            Number of dimensions in embedding vectors
        """
        return self._dimensions

    def get_model_name(self) -> str:
        """Get model name.

        Returns:
            Model name/identifier
        """
        return self.model_name

    def get_max_seq_length(self) -> int:
        """Get maximum sequence length supported by this model.

        Returns the model's max_seq_length property, which indicates the maximum
        number of tokens the model can process. Text exceeding this limit will be
        truncated, causing information loss.

        Returns:
            Maximum sequence length in tokens

        Example:
            - all-MiniLM-L6-v2: 256 tokens
            - all-mpnet-base-v2: 384 tokens
            - multilingual-e5-large: 512 tokens
        """
        return self.model.max_seq_length

    async def close(self):
        """Cleanup resources.

        Clears model from memory and frees GPU memory if applicable.
        """
        # Clear model from memory if needed
        if hasattr(self, 'model'):
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
