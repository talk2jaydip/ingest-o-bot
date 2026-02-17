"""Media describer implementations for figure captioning."""

import base64
from abc import ABC, abstractmethod
from typing import Optional

from openai import AsyncAzureOpenAI
from openai import RateLimitError, APITimeoutError, APIConnectionError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .config import AzureOpenAIConfig, ContentUnderstandingConfig, MediaDescriberMode
from .logging_utils import get_logger

logger = get_logger(__name__)


class MediaDescriber(ABC):
    """Abstract base class for media description services."""
    
    @abstractmethod
    async def describe_image(self, image_bytes: bytes) -> Optional[str]:
        """Generate text description for an image."""
        pass


class GPT4oMediaDescriber(MediaDescriber):
    """Media describer using Azure OpenAI GPT-4o vision."""

    def __init__(self, config: AzureOpenAIConfig):
        """Initialize GPT-4o vision media describer.

        Args:
            config: Azure OpenAI configuration with vision deployment

        Raises:
            ValueError: If vision deployment is not configured
        """
        self.config = config

        # Safety check (should already be validated by factory)
        if not config.vision_deployment:
            raise ValueError(
                "vision_deployment is required for GPT-4o media describer.\n"
                "Set AZURE_OPENAI_VISION_DEPLOYMENT in your .env file."
            )

        if not config.endpoint:
            raise ValueError(
                "Azure OpenAI endpoint is required.\n"
                "Set AZURE_OPENAI_ENDPOINT in your .env file."
            )

        if not config.api_key:
            raise ValueError(
                "Azure OpenAI API key is required.\n"
                "Set AZURE_OPENAI_KEY in your .env file."
            )

        # Create Azure OpenAI client
        # Use the same API version for vision as embeddings
        api_version = config.api_version
        logger.info(f"Initializing GPT-4o vision client: {config.endpoint} (API version: {api_version})")

        self.client = AsyncAzureOpenAI(
            api_key=config.api_key,
            azure_endpoint=config.endpoint,
            api_version=api_version
        )
        self.deployment = config.vision_deployment
        logger.info(f"GPT-4o media describer ready: deployment={self.deployment}")
    
    async def describe_image(self, image_bytes: bytes) -> Optional[str]:
        """Generate description AND extract text from image using GPT-4o vision.
        
        Returns a combined output with both AI description and extracted text:
        - DESCRIPTION: What the image shows (chart type, diagram, key insights)
        - TEXT IN IMAGE: All visible text (labels, values, legends, annotations)
        """
        try:
            # Encode image as base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # Enhanced prompt to extract BOTH description AND text
            user_prompt = """Analyze this image and provide TWO things:

1. DESCRIPTION: Describe what the image shows (chart type, diagram type, photo content, main message, key insights)
2. TEXT CONTENT: Extract ALL visible text in the image (titles, labels, values, legends, axis labels, annotations, captions, any other text)

Format your response EXACTLY as:
DESCRIPTION: [your description here]

TEXT IN IMAGE: [all visible text here, separated by spaces or commas]

If no text is visible, write "TEXT IN IMAGE: None"
"""
            
            # Call GPT-4o with vision with retry logic for transient errors
            def log_retry(retry_state):
                exception = retry_state.outcome.exception()
                if isinstance(exception, RateLimitError):
                    logger.info(
                        f"Rate limited on GPT-4o (attempt {retry_state.attempt_number}/5), "
                        f"waiting before retry..."
                    )
                else:
                    logger.info(
                        f"Transient error on GPT-4o: {type(exception).__name__} "
                        f"(attempt {retry_state.attempt_number}/5), retrying..."
                    )

            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
                wait=wait_random_exponential(min=5, max=60),
                stop=stop_after_attempt(5),
                before_sleep=log_retry
            ):
                with attempt:
                    response = await self.client.chat.completions.create(
                        model=self.deployment,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert at analyzing images from documents. Extract all visible text accurately and describe visual content clearly. Be thorough in capturing all text elements."
                            },
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": user_prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{base64_image}",
                                            "detail": "high"  # Use high detail for better text recognition
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=500,  # Increased to handle more text extraction
                        temperature=0.0  # Low temperature for consistency and accuracy
                    )
            
            if response.choices:
                content = response.choices[0].message.content
                return content.strip() if content else None
            
            return None
        
        except Exception as e:
            logger.error(f"Error describing image with GPT-4o: {e}")
            return None
    
    async def close(self):
        """Close the OpenAI client."""
        await self.client.close()


class ContentUnderstandingDescriber(MediaDescriber):
    """Media describer using Azure Content Understanding."""
    
    def __init__(self, config: ContentUnderstandingConfig):
        self.config = config
        # TODO: Implement Content Understanding client when needed
        raise NotImplementedError("Content Understanding describer not yet implemented")
    
    async def describe_image(self, image_bytes: bytes) -> Optional[str]:
        """Generate description using Content Understanding."""
        # TODO: Implement actual Content Understanding API call
        raise NotImplementedError("Content Understanding describer not yet implemented")


class DisabledMediaDescriber(MediaDescriber):
    """No-op media describer that returns None."""
    
    async def describe_image(self, image_bytes: bytes) -> Optional[str]:
        """Return None (descriptions disabled)."""
        return None


def create_media_describer(
    mode: MediaDescriberMode,
    aoai_config: Optional[AzureOpenAIConfig] = None,
    cu_config: Optional[ContentUnderstandingConfig] = None
) -> MediaDescriber:
    """Factory function to create media describer from configuration.

    Args:
        mode: Media describer mode (disabled, gpt4o, content_understanding)
        aoai_config: Azure OpenAI configuration (required for gpt4o mode)
        cu_config: Content Understanding configuration (required for content_understanding mode)

    Returns:
        MediaDescriber instance

    Raises:
        ValueError: If required configuration is missing for the selected mode
    """
    if mode == MediaDescriberMode.DISABLED:
        logger.info("Media description disabled - images will be extracted but not described")
        return DisabledMediaDescriber()

    elif mode == MediaDescriberMode.GPT4O:
        # Validate Azure OpenAI configuration
        if not aoai_config:
            raise ValueError(
                "Media describer configuration error:\n"
                "  MEDIA_DESCRIBER_MODE=gpt4o requires Azure OpenAI configuration.\n"
                "  \n"
                "  Missing: Azure OpenAI config\n"
                "  \n"
                "  Required environment variables:\n"
                "    AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/\n"
                "    AZURE_OPENAI_KEY=your-key\n"
                "    AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4o\n"
                "    AZURE_OPENAI_VISION_MODEL=gpt-4o\n"
                "  \n"
                "  Or disable media description:\n"
                "    MEDIA_DESCRIBER_MODE=disabled\n"
                "  \n"
                "  See: envs/.env.azure-local-input.example"
            )

        if not aoai_config.vision_deployment:
            raise ValueError(
                "Media describer configuration error:\n"
                "  MEDIA_DESCRIBER_MODE=gpt4o requires vision deployment configuration.\n"
                "  \n"
                "  Missing: AZURE_OPENAI_VISION_DEPLOYMENT\n"
                "  \n"
                "  Add to your .env file:\n"
                "    AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4o\n"
                "    AZURE_OPENAI_VISION_MODEL=gpt-4o\n"
                "  \n"
                "  Recommended: Use gpt-4o-mini for 5x lower cost:\n"
                "    AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4o-mini\n"
                "    AZURE_OPENAI_VISION_MODEL=gpt-4o-mini\n"
                "  \n"
                "  Or disable media description:\n"
                "    MEDIA_DESCRIBER_MODE=disabled\n"
                "  \n"
                "  See: envs/.env.azure-local-input.example"
            )

        logger.info(f"Media description enabled: GPT-4o Vision ({aoai_config.vision_deployment})")
        return GPT4oMediaDescriber(aoai_config)

    elif mode == MediaDescriberMode.CONTENT_UNDERSTANDING:
        # Validate Content Understanding configuration
        if not cu_config or not cu_config.endpoint:
            raise ValueError(
                "Media describer configuration error:\n"
                "  MEDIA_DESCRIBER_MODE=content_understanding requires Content Understanding configuration.\n"
                "  \n"
                "  Missing: AZURE_CONTENT_UNDERSTANDING_ENDPOINT\n"
                "  \n"
                "  NOTE: Content Understanding mode is not yet fully implemented.\n"
                "  \n"
                "  Alternatives:\n"
                "    1. Use GPT-4o Vision instead:\n"
                "       MEDIA_DESCRIBER_MODE=gpt4o\n"
                "       AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4o\n"
                "  \n"
                "    2. Disable media description:\n"
                "       MEDIA_DESCRIBER_MODE=disabled\n"
                "  \n"
                "  See: envs/.env.azure-local-input.example"
            )

        logger.warning(
            "Content Understanding mode selected but not yet fully implemented. "
            "Consider using MEDIA_DESCRIBER_MODE=gpt4o instead."
        )
        return ContentUnderstandingDescriber(cu_config)

    else:
        raise ValueError(
            f"Unsupported media describer mode: {mode}\n"
            f"Valid options: disabled | gpt4o | content_understanding\n"
            f"Set MEDIA_DESCRIBER_MODE in your .env file."
        )

