"""
Model loader and manager for reranking models
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import torch
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class ModelLoader:
    """
    Manages loading and caching of reranking models
    """
    
    # Supported models with their configurations
    SUPPORTED_MODELS = {
        "BAAI/bge-reranker-large": {
            "max_length": 512,
            "description": "BGE Large Reranker - High accuracy, slower",
            "size": "1.1GB"
        },
        "BAAI/bge-reranker-base": {
            "max_length": 512,
            "description": "BGE Base Reranker - Balanced performance",
            "size": "400MB"
        },
        "BAAI/bge-reranker-v2-m3": {
            "max_length": 8192,
            "description": "BGE v2 M3 - Multilingual, long context",
            "size": "1.5GB"
        },
        "cross-encoder/ms-marco-MiniLM-L-12-v2": {
            "max_length": 512,
            "description": "MS MARCO MiniLM - Fast, good for English",
            "size": "140MB"
        },
        "cross-encoder/ms-marco-electra-base": {
            "max_length": 512,
            "description": "MS MARCO ELECTRA - High quality for English",
            "size": "440MB"
        }
    }
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize model loader
        
        Args:
            cache_dir: Directory to cache downloaded models
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./models")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_models: Dict[str, CrossEncoder] = {}
        
    def load_model(
        self,
        model_name: str,
        device: Optional[str] = None,
        max_length: Optional[int] = None,
        force_reload: bool = False
    ) -> CrossEncoder:
        """
        Load a reranking model
        
        Args:
            model_name: Name or path of the model
            device: Device to load model on
            max_length: Maximum sequence length
            force_reload: Force reload even if cached
            
        Returns:
            Loaded CrossEncoder model
        """
        # Check if model is already loaded
        if not force_reload and model_name in self._loaded_models:
            logger.info(f"Using cached model: {model_name}")
            return self._loaded_models[model_name]
        
        # Get model configuration
        model_config = self.SUPPORTED_MODELS.get(model_name, {})
        
        # Use provided max_length or default from config
        if max_length is None:
            max_length = model_config.get("max_length", 512)
        
        # Auto-detect device if not specified
        if device is None:
            device = self._get_best_device()
        
        logger.info(f"Loading model {model_name} on {device}")
        
        try:
            # Set cache directory for transformers
            os.environ["TRANSFORMERS_CACHE"] = str(self.cache_dir)
            
            # Load the model
            model = CrossEncoder(
                model_name,
                max_length=max_length,
                device=device
            )
            
            # Cache the loaded model
            self._loaded_models[model_name] = model
            
            logger.info(f"Model {model_name} loaded successfully")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {str(e)}")
            raise
    
    def preload_models(self, model_names: list, device: Optional[str] = None):
        """
        Preload multiple models for faster inference
        
        Args:
            model_names: List of model names to preload
            device: Device to load models on
        """
        for model_name in model_names:
            try:
                self.load_model(model_name, device=device)
                logger.info(f"Preloaded model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to preload {model_name}: {str(e)}")
    
    def get_loaded_models(self) -> list:
        """Get list of currently loaded models"""
        return list(self._loaded_models.keys())
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get information about a model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with model information
        """
        if model_name in self.SUPPORTED_MODELS:
            info = self.SUPPORTED_MODELS[model_name].copy()
            info["loaded"] = model_name in self._loaded_models
            return info
        else:
            return {
                "description": "Custom model",
                "loaded": model_name in self._loaded_models
            }
    
    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        """List all available models with their info"""
        models = {}
        for name, info in self.SUPPORTED_MODELS.items():
            models[name] = info.copy()
            models[name]["loaded"] = name in self._loaded_models
        return models
    
    def clear_cache(self, model_name: Optional[str] = None):
        """
        Clear loaded models from memory
        
        Args:
            model_name: Specific model to clear, or None to clear all
        """
        if model_name:
            if model_name in self._loaded_models:
                del self._loaded_models[model_name]
                logger.info(f"Cleared model from cache: {model_name}")
        else:
            self._loaded_models.clear()
            logger.info("Cleared all models from cache")
    
    def _get_best_device(self) -> str:
        """Determine the best available device"""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def get_cache_size(self) -> Dict[str, Any]:
        """Get information about cache usage"""
        cache_info = {
            "cache_directory": str(self.cache_dir),
            "loaded_models": len(self._loaded_models),
            "models": self.get_loaded_models()
        }
        
        # Calculate disk usage if cache directory exists
        if self.cache_dir.exists():
            total_size = sum(
                f.stat().st_size for f in self.cache_dir.rglob("*") if f.is_file()
            )
            cache_info["disk_usage_mb"] = round(total_size / (1024 * 1024), 2)
        
        return cache_info