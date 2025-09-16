"""Configuration loader and validator utilities."""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import ValidationError

from .config_models import Config


class ConfigError(Exception):
    """Configuration related errors."""
    pass


class ConfigLoader:
    """Load and validate configuration files."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config loader.

        Args:
            config_dir: Base directory for configurations
        """
        self.config_dir = config_dir or Path(__file__).parent.parent.parent / "configs"

    def load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML content

        Raises:
            ConfigError: If file cannot be loaded
        """
        try:
            with open(file_path, 'r') as f:
                content = yaml.safe_load(f)
                return content or {}
        except FileNotFoundError:
            raise ConfigError(f"Configuration file not found: {file_path}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading {file_path}: {e}")

    def load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON content

        Raises:
            ConfigError: If file cannot be loaded
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ConfigError(f"Configuration file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading {file_path}: {e}")

    def load(self, file_path: Path) -> Config:
        """Load and validate configuration file.

        Args:
            file_path: Path to configuration file

        Returns:
            Validated Config object

        Raises:
            ConfigError: If configuration is invalid
        """
        # Determine file type
        if file_path.suffix in ['.yaml', '.yml']:
            data = self.load_yaml(file_path)
        elif file_path.suffix == '.json':
            data = self.load_json(file_path)
        else:
            raise ConfigError(f"Unsupported file format: {file_path.suffix}")

        # Apply environment variable substitutions
        data = self._substitute_env_vars(data)

        # Validate with Pydantic
        try:
            config = Config(**data)
            return config
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                msg = error['msg']
                errors.append(f"  - {field}: {msg}")
            raise ConfigError(f"Configuration validation failed:\n" + '\n'.join(errors))

    def _substitute_env_vars(self, data: Any) -> Any:
        """Recursively substitute environment variables.

        Args:
            data: Configuration data

        Returns:
            Data with environment variables substituted
        """
        if isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(v) for v in data]
        elif isinstance(data, str):
            # Replace ${VAR_NAME} with environment variable value
            import re
            pattern = r'\$\{([^}]+)\}'

            def replacer(match):
                var_name = match.group(1)
                # Check for default value syntax: ${VAR_NAME:-default_value}
                if ':-' in var_name:
                    var_name, default_value = var_name.split(':-', 1)
                    return os.environ.get(var_name, default_value)
                else:
                    value = os.environ.get(var_name)
                    if value is None:
                        # Keep original if env var not found (for optional vars)
                        return match.group(0)
                    return value

            return re.sub(pattern, replacer, data)
        else:
            return data

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """Load a configuration template.

        Args:
            template_name: Name of the template (without extension)

        Returns:
            Template configuration data

        Raises:
            ConfigError: If template not found
        """
        template_path = self.config_dir / "templates" / f"{template_name}.yaml"
        if not template_path.exists():
            raise ConfigError(f"Template not found: {template_name}")
        return self.load_yaml(template_path)

    def load_preset(self, preset_name: str) -> Config:
        """Load a preset configuration.

        Args:
            preset_name: Name of the preset (without extension)

        Returns:
            Validated Config object

        Raises:
            ConfigError: If preset not found or invalid
        """
        preset_path = self.config_dir / "presets" / f"{preset_name}.yaml"
        if not preset_path.exists():
            raise ConfigError(f"Preset not found: {preset_name}")
        return self.load(preset_path)

    def merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Merged configuration
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def save(self, config: Config, file_path: Path, format: str = "yaml") -> None:
        """Save configuration to file.

        Args:
            config: Config object to save
            file_path: Path to save file
            format: Output format ('yaml' or 'json')

        Raises:
            ConfigError: If save fails
        """
        try:
            # Convert to dictionary
            data = config.model_dump(exclude_none=True)

            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if format == "yaml":
                with open(file_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            elif format == "json":
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                raise ConfigError(f"Unsupported format: {format}")

        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {e}")


class ConfigValidator:
    """Validate configuration for deployment readiness."""

    def __init__(self):
        """Initialize validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, config: Config) -> bool:
        """Validate configuration for deployment.

        Args:
            config: Configuration to validate

        Returns:
            True if valid, False otherwise
        """
        self.errors = []
        self.warnings = []

        # Validate deployment type specific requirements
        self._validate_deployment(config)

        # Validate service configurations
        self._validate_services(config)

        # Validate infrastructure
        self._validate_infrastructure(config)

        # Check for security issues
        self._validate_security(config)

        return len(self.errors) == 0

    def _validate_deployment(self, config: Config) -> None:
        """Validate deployment configuration."""
        deployment = config.deployment

        if deployment.type == "aws":
            if not config.infrastructure.aws:
                self.errors.append("AWS infrastructure configuration required for AWS deployment")
            elif not config.infrastructure.aws.region:
                self.errors.append("AWS region is required")

        elif deployment.type == "docker-compose":
            if not config.infrastructure.docker:
                self.errors.append("Docker configuration required for Docker Compose deployment")

        elif deployment.type == "local-gpu":
            if not config.infrastructure.local_gpu:
                self.errors.append("Local GPU configuration required for local GPU deployment")

    def _validate_services(self, config: Config) -> None:
        """Validate service configurations."""
        # LLM validation
        llm = config.services.llm
        if llm.provider in ["openai", "openrouter", "azure"] and not llm.api_key:
            if not llm.api_key or llm.api_key == "${LLM_API_KEY}":
                self.warnings.append(f"API key not set for {llm.provider} provider")

        if llm.provider == "local-mlx" and not llm.mlx_model_path:
            self.warnings.append("Model path not specified for local MLX")

        # Embedding validation
        emb = config.services.embedding
        if emb.provider == "openai" and not emb.api_key:
            if not emb.api_key or emb.api_key == "${EMBEDDING_API_KEY}":
                self.warnings.append("API key not set for OpenAI embeddings")

        # Database validation
        db = config.services.database
        if db.type != "sqlite" and not db.password:
            self.warnings.append("Database password not set")

    def _validate_infrastructure(self, config: Config) -> None:
        """Validate infrastructure configuration."""
        if config.deployment.type == "local-gpu" and config.infrastructure.local_gpu:
            gpu = config.infrastructure.local_gpu
            if gpu.gpu_type == "nvidia" and not gpu.cuda_version:
                self.warnings.append("CUDA version not specified for NVIDIA GPU")
            elif gpu.gpu_type == "apple_silicon" and not gpu.mlx_enabled:
                self.warnings.append("MLX not enabled for Apple Silicon")

    def _validate_security(self, config: Config) -> None:
        """Check for security issues."""
        # Check for hardcoded credentials
        if config.services.llm.api_key and not config.services.llm.api_key.startswith("${"):
            self.warnings.append("API key appears to be hardcoded - use environment variables")

        # Check for insecure defaults
        if config.deployment.environment == "production":
            if not config.application.main_app.jwt_enabled:
                self.errors.append("JWT authentication must be enabled in production")

            if config.monitoring and config.monitoring.grafana:
                if config.monitoring.grafana.admin_password == "admin":
                    self.warnings.append("Default Grafana admin password in use")

    def get_report(self) -> str:
        """Get validation report.

        Returns:
            Formatted validation report
        """
        report = []

        if self.errors:
            report.append("❌ ERRORS:")
            for error in self.errors:
                report.append(f"  - {error}")

        if self.warnings:
            if report:
                report.append("")
            report.append("⚠️  WARNINGS:")
            for warning in self.warnings:
                report.append(f"  - {warning}")

        if not self.errors and not self.warnings:
            report.append("✅ Configuration is valid")

        return "\n".join(report)