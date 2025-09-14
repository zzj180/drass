"""
Factory for creating reranking providers
"""
from typing import Dict, Any, Optional
import logging

from config import RerankingProvider
from .base import BaseRerankingProvider
from .sentence_transformers_provider import SentenceTransformersProvider

logger = logging.getLogger(__name__)

class ProviderFactory:
    """
    Factory for creating reranking providers based on configuration
    """

    def __init__(self):
        """
        Initialize the provider factory
        """
        self.providers = {}
        self._register_providers()

    def _register_providers(self):
        """
        Register available providers
        """
        self.providers[RerankingProvider.SENTENCE_TRANSFORMERS] = SentenceTransformersProvider
        # Future providers can be registered here
        # self.providers[RerankingProvider.OPENAI] = OpenAIProvider
        # self.providers[RerankingProvider.COHERE] = CohereProvider

    async def create_provider(
        self,
        provider_type: RerankingProvider,
        model_name: str,
        device: str = "cpu",
        **kwargs
    ) -> BaseRerankingProvider:
        """
        Create and initialize a reranking provider

        Args:
            provider_type: Type of provider to create
            model_name: Name of the model to use
            device: Device to run on
            **kwargs: Additional provider-specific configuration

        Returns:
            Initialized reranking provider

        Raises:
            ValueError: If provider type is not supported
            RuntimeError: If provider initialization fails
        """
        if provider_type not in self.providers:
            raise ValueError(f"Unsupported provider: {provider_type}")

        provider_class = self.providers[provider_type]

        try:
            logger.info(f"Creating provider: {provider_type} with model: {model_name}")

            # Create provider instance
            provider = provider_class(
                model_name=model_name,
                device=device,
                **kwargs
            )

            # Initialize the provider
            await provider.initialize()

            logger.info(f"Provider {provider_type} initialized successfully")
            return provider

        except Exception as e:
            logger.error(f"Failed to create provider {provider_type}: {e}")
            raise RuntimeError(f"Provider initialization failed: {e}")

    def get_available_providers(self) -> Dict[str, Any]:
        """
        Get list of available providers

        Returns:
            Dictionary with provider information
        """
        return {
            "available": list(self.providers.keys()),
            "providers": {
                RerankingProvider.SENTENCE_TRANSFORMERS: {
                    "name": "Sentence Transformers",
                    "description": "Local cross-encoder models from HuggingFace",
                    "requires_api_key": False
                },
                RerankingProvider.OPENAI: {
                    "name": "OpenAI",
                    "description": "OpenAI's reranking API",
                    "requires_api_key": True,
                    "status": "planned"
                },
                RerankingProvider.COHERE: {
                    "name": "Cohere",
                    "description": "Cohere's reranking API",
                    "requires_api_key": True,
                    "status": "planned"
                },
                RerankingProvider.LOCAL: {
                    "name": "Local",
                    "description": "Custom local models",
                    "requires_api_key": False,
                    "status": "planned"
                }
            }
        }