"""
Configuration loader and manager for deployment configurations
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from jsonschema import validate, ValidationError, Draft7Validator
import logging

from .config_models import DeploymentConfiguration

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and manage deployment configurations"""

    def __init__(self, base_path: str = None):
        """
        Initialize configuration loader

        Args:
            base_path: Base path for configuration files
        """
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent.parent
        self.configs_path = self.base_path / "configs"
        self.templates_path = self.configs_path / "templates"
        self.presets_path = self.configs_path / "presets"
        self.user_path = self.configs_path / "user"
        self.schema_path = self.base_path / "schemas" / "config-schema.yaml"

        # Create directories if they don't exist
        for path in [self.configs_path, self.templates_path, self.presets_path, self.user_path]:
            path.mkdir(parents=True, exist_ok=True)

        # Load schema if available
        self.schema = self._load_schema()

    def _load_schema(self) -> Optional[Dict]:
        """Load YAML schema for validation"""
        if self.schema_path.exists():
            try:
                with open(self.schema_path, "r") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Failed to load schema: {e}")
                return None
        return None

    def load_yaml(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load YAML configuration file

        Args:
            file_path: Path to YAML file

        Returns:
            Dictionary containing configuration

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
                if data is None:
                    return {}
                return data
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML file {file_path}: {e}")

    def save_yaml(self, config: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """
        Save configuration to YAML file

        Args:
            config: Configuration dictionary
            file_path: Path to save YAML file
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
        logger.info(f"Configuration saved to {file_path}")

    def load_json(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load JSON configuration file

        Args:
            file_path: Path to JSON file

        Returns:
            Dictionary containing configuration
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, "r") as f:
            return json.load(f)

    def save_json(self, config: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """
        Save configuration to JSON file

        Args:
            config: Configuration dictionary
            file_path: Path to save JSON file
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {file_path}")

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """
        Load configuration template

        Args:
            template_name: Name of template (without extension)

        Returns:
            Template configuration dictionary
        """
        template_file = self.templates_path / f"{template_name}.yaml"
        if not template_file.exists():
            # Try with .yml extension
            template_file = self.templates_path / f"{template_name}.yml"
            if not template_file.exists():
                raise FileNotFoundError(f"Template not found: {template_name}")

        return self.load_yaml(template_file)

    def load_preset(self, preset_name: str) -> Dict[str, Any]:
        """
        Load configuration preset

        Args:
            preset_name: Name of preset (without extension)

        Returns:
            Preset configuration dictionary
        """
        preset_file = self.presets_path / f"{preset_name}.yaml"
        if not preset_file.exists():
            preset_file = self.presets_path / f"{preset_name}.yml"
            if not preset_file.exists():
                raise FileNotFoundError(f"Preset not found: {preset_name}")

        return self.load_yaml(preset_file)

    def list_templates(self) -> List[str]:
        """
        List available configuration templates

        Returns:
            List of template names
        """
        templates = []
        for file in self.templates_path.glob("*.yaml"):
            templates.append(file.stem)
        for file in self.templates_path.glob("*.yml"):
            if file.stem not in templates:
                templates.append(file.stem)
        return sorted(templates)

    def list_presets(self) -> List[str]:
        """
        List available configuration presets

        Returns:
            List of preset names
        """
        presets = []
        for file in self.presets_path.glob("*.yaml"):
            presets.append(file.stem)
        for file in self.presets_path.glob("*.yml"):
            if file.stem not in presets:
                presets.append(file.stem)
        return sorted(presets)

    def list_user_configs(self) -> List[str]:
        """
        List user configurations

        Returns:
            List of user configuration names
        """
        configs = []
        for file in self.user_path.glob("*.yaml"):
            configs.append(file.stem)
        for file in self.user_path.glob("*.yml"):
            if file.stem not in configs:
                configs.append(file.stem)
        return sorted(configs)

    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple configuration dictionaries

        Args:
            *configs: Configuration dictionaries to merge

        Returns:
            Merged configuration dictionary
        """
        result = {}
        for config in configs:
            result = self._deep_merge(result, config)
        return result

    def _deep_merge(self, dict1: Dict, dict2: Dict) -> Dict:
        """
        Deep merge two dictionaries

        Args:
            dict1: Base dictionary
            dict2: Dictionary to merge

        Returns:
            Merged dictionary
        """
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def validate_schema(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration against schema

        Args:
            config: Configuration dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        if not self.schema:
            logger.warning("No schema loaded for validation")
            return errors

        try:
            validate(config, self.schema)
        except ValidationError as e:
            errors.append(str(e))
            # Get all validation errors
            validator = Draft7Validator(self.schema)
            for error in validator.iter_errors(config):
                error_path = " -> ".join(str(p) for p in error.path)
                errors.append(f"At '{error_path}': {error.message}")

        return errors

    def validate_pydantic(self, config: Dict[str, Any]) -> tuple[bool, Union[DeploymentConfiguration, List[str]]]:
        """
        Validate configuration using Pydantic models

        Args:
            config: Configuration dictionary

        Returns:
            Tuple of (is_valid, result) where result is either DeploymentConfiguration or list of errors
        """
        try:
            deployment_config = DeploymentConfiguration(**config)
            return True, deployment_config
        except Exception as e:
            # Parse pydantic validation errors
            errors = []
            if hasattr(e, 'errors'):
                for error in e.errors():
                    loc = " -> ".join(str(l) for l in error['loc'])
                    errors.append(f"At '{loc}': {error['msg']}")
            else:
                errors.append(str(e))
            return False, errors

    def load_environment_variables(self, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract environment variables from configuration

        Args:
            config: Configuration dictionary

        Returns:
            Dictionary of environment variables
        """
        env_vars = {}

        # Get direct environment variables
        if "environment" in config and "variables" in config["environment"]:
            env_vars.update(config["environment"]["variables"])

        # Extract service-specific environment variables
        services = config.get("services", {})
        for service_name, service_config in services.items():
            if isinstance(service_config, dict) and "environment" in service_config:
                for key, value in service_config["environment"].items():
                    # Prefix with service name to avoid conflicts
                    env_key = f"{service_name.upper()}_{key}"
                    env_vars[env_key] = value

        # Map common configuration to environment variables
        mappings = self._get_env_mappings(config)
        env_vars.update(mappings)

        return env_vars

    def _get_env_mappings(self, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Map configuration values to standard environment variables

        Args:
            config: Configuration dictionary

        Returns:
            Dictionary of environment variable mappings
        """
        mappings = {}
        services = config.get("services", {})

        # LLM service mappings
        if "llm" in services:
            llm = services["llm"]
            if "provider" in llm:
                mappings["LLM_PROVIDER"] = llm["provider"]
            if "model" in llm:
                mappings["LLM_MODEL"] = llm["model"]
            if "api_key" in llm:
                mappings["LLM_API_KEY"] = llm["api_key"]
            if "base_url" in llm:
                mappings["LLM_BASE_URL"] = llm["base_url"]

        # Database service mappings
        if "database" in services:
            db = services["database"]
            if "connection" in db:
                conn = db["connection"]
                db_url = f"{db['provider']}://"
                if "username" in conn and "password" in conn:
                    db_url += f"{conn['username']}:{conn['password']}@"
                if "host" in conn:
                    db_url += conn["host"]
                if "port" in conn:
                    db_url += f":{conn['port']}"
                if "database" in conn:
                    db_url += f"/{conn['database']}"
                mappings["DATABASE_URL"] = db_url

        # Vector store mappings
        if "vector_store" in services:
            vs = services["vector_store"]
            if "provider" in vs:
                mappings["VECTOR_STORE_TYPE"] = vs["provider"]
            if "connection" in vs:
                if "host" in vs["connection"]:
                    mappings["VECTOR_STORE_HOST"] = vs["connection"]["host"]
                if "port" in vs["connection"]:
                    mappings["VECTOR_STORE_PORT"] = str(vs["connection"]["port"])

        # Cache service mappings
        if "cache" in services:
            cache = services["cache"]
            if cache.get("provider") == "redis" and "connection" in cache:
                conn = cache["connection"]
                redis_url = "redis://"
                if "password" in conn:
                    redis_url += f":{conn['password']}@"
                if "host" in conn:
                    redis_url += conn["host"]
                if "port" in conn:
                    redis_url += f":{conn['port']}"
                if "db" in conn:
                    redis_url += f"/{conn['db']}"
                else:
                    redis_url += "/0"
                mappings["REDIS_URL"] = redis_url

        # Deployment environment
        if "deployment" in config:
            if "environment" in config["deployment"]:
                mappings["DEPLOYMENT_ENV"] = config["deployment"]["environment"]
            if "name" in config["deployment"]:
                mappings["DEPLOYMENT_NAME"] = config["deployment"]["name"]

        return mappings

    def save_user_config(self, name: str, config: Dict[str, Any]) -> Path:
        """
        Save user configuration

        Args:
            name: Configuration name
            config: Configuration dictionary

        Returns:
            Path to saved configuration file
        """
        file_path = self.user_path / f"{name}.yaml"
        self.save_yaml(config, file_path)
        return file_path

    def load_user_config(self, name: str) -> Dict[str, Any]:
        """
        Load user configuration

        Args:
            name: Configuration name

        Returns:
            Configuration dictionary
        """
        file_path = self.user_path / f"{name}.yaml"
        if not file_path.exists():
            file_path = self.user_path / f"{name}.yml"
            if not file_path.exists():
                raise FileNotFoundError(f"User configuration not found: {name}")

        return self.load_yaml(file_path)