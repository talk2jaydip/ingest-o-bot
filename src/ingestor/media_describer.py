"""Media describer implementations for figure captioning."""

import base64
from abc import ABC, abstractmethod
from typing import Optional

from openai import AsyncAzureOpenAI
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
        self.config = config
        
        if not config.chat_deployment:
            raise ValueError("chat_deployment is required for GPT-4o media describer")
        
        # Create Azure OpenAI client
        self.client = AsyncAzureOpenAI(
            api_key=config.api_key,
            azure_endpoint=config.endpoint,
            api_version=config.api_version
        )
        self.deployment = config.chat_deployment
    
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
            
            # Call GPT-4o with vision
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(Exception),
                wait=wait_random_exponential(min=1, max=20),
                stop=stop_after_attempt(3),
                before_sleep=lambda retry_state: logger.info(
                    "Rate limited on GPT-4o, retrying..."
                )
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
    """Factory function to create media describer from configuration."""
    if mode == MediaDescriberMode.GPT4O:
        if not aoai_config:
            raise ValueError("Azure OpenAI config is required for GPT-4o describer")
        return GPT4oMediaDescriber(aoai_config)
    elif mode == MediaDescriberMode.CONTENT_UNDERSTANDING:
        if not cu_config:
            raise ValueError("Content Understanding config is required for CU describer")
        return ContentUnderstandingDescriber(cu_config)
    elif mode == MediaDescriberMode.DISABLED:
        return DisabledMediaDescriber()
    else:
        raise ValueError(f"Unsupported media describer mode: {mode}")

