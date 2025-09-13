#!/usr/bin/env python3
"""
Configuration Manager
Central configuration management for all services
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Central configuration manager"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or self._get_default_config_file()
        self._config = self._load_config()
    
    def _get_default_config_file(self) -> str:
        """Get default config file path"""
        project_root = Path(__file__).parent.parent
        return str(project_root / "config" / "app.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_file} not found, using defaults")
            return self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "environment": "development",
            "ports": {
                "frontend": 3000,
                "backend": 8000,
                "llm": 8001,
                "embedding": 8002,
                "reranking": 8003,
                "document_processor": 8004,
                "chroma": 8005,
                "postgres": 5432,
                "redis": 6379
            },
            "api": {
                "base_url": "http://localhost",
                "frontend_url": "http://localhost:3000",
                "backend_url": "http://localhost:8000",
                "llm_url": "http://localhost:8001"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_port(self, service: str) -> int:
        """Get port for a specific service"""
        return self.get(f"ports.{service}", 8000)
    
    def get_url(self, service: str) -> str:
        """Get URL for a specific service"""
        return self.get(f"api.{service}_url", f"http://localhost:{self.get_port(service)}")
    
    def get_websocket_url(self, service: str) -> str:
        """Get WebSocket URL for a specific service"""
        ws_enabled = self.get("websocket.enabled", True)
        if not ws_enabled:
            return ""
        
        base_url = self.get("websocket.backend_url", "ws://localhost:8000")
        if service == "frontend":
            base_url = self.get("websocket.frontend_url", "ws://localhost:3000")
        
        return base_url
    
    def get_upload_config(self) -> Dict[str, Any]:
        """Get file upload configuration"""
        return self.get("upload", {
            "max_file_size": 10485760,
            "allowed_types": ["application/pdf", "text/plain"]
        })
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self.get("llm", {
            "provider": "local",
            "model_name": "qwen3-8b-mlx",
            "temperature": 0.7,
            "max_tokens": 1000,
            "timeout": 60
        })
    
    def get_database_config(self, db_type: str = "postgres") -> Dict[str, Any]:
        """Get database configuration"""
        return self.get(f"database.{db_type}", {})
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration"""
        return self.get("security.cors", {
            "allowed_origins": ["http://localhost:3000"],
            "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allowed_headers": ["*"]
        })
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.get(f"features.{feature}", False)
    
    def get_environment(self) -> str:
        """Get current environment"""
        return self.get("environment", "development")
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.get_environment() == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.get_environment() == "production"
    
    def reload(self):
        """Reload configuration from file"""
        self._config = self._load_config()
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary"""
        return self._config.copy()

# Global config instance
config = ConfigManager()

# Convenience functions
def get_config() -> ConfigManager:
    """Get global config instance"""
    return config

def get_port(service: str) -> int:
    """Get port for service"""
    return config.get_port(service)

def get_url(service: str) -> str:
    """Get URL for service"""
    return config.get_url(service)

def get_websocket_url(service: str) -> str:
    """Get WebSocket URL for service"""
    return config.get_websocket_url(service)

def is_feature_enabled(feature: str) -> bool:
    """Check if feature is enabled"""
    return config.is_feature_enabled(feature)

if __name__ == "__main__":
    # Test configuration
    print("Configuration Test:")
    print(f"Frontend Port: {get_port('frontend')}")
    print(f"Backend Port: {get_port('backend')}")
    print(f"Backend URL: {get_url('backend')}")
    print(f"WebSocket URL: {get_websocket_url('backend')}")
    print(f"File Upload Enabled: {is_feature_enabled('file_upload')}")
    print(f"Environment: {config.get_environment()}")
