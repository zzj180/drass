#!/usr/bin/env python3
"""
Configuration validation script for deployment configurations
"""
import argparse
import sys
import logging
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from deployment.scripts.utils.config_loader import ConfigLoader
from deployment.scripts.utils.config_models import DeploymentConfiguration

console = Console()
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def validate_config_file(file_path: Path, loader: ConfigLoader) -> tuple[bool, list]:
    """
    Validate a configuration file

    Args:
        file_path: Path to configuration file
        loader: ConfigLoader instance

    Returns:
        Tuple of (is_valid, errors/warnings)
    """
    try:
        # Load configuration
        config = loader.load_yaml(file_path)

        # Schema validation
        schema_errors = loader.validate_schema(config)

        # Pydantic validation
        is_valid, pydantic_result = loader.validate_pydantic(config)

        all_errors = []
        warnings = []

        if schema_errors:
            all_errors.extend(schema_errors)

        if not is_valid:
            all_errors.extend(pydantic_result)
        else:
            # Check completeness if valid
            warnings = pydantic_result.validate_completeness()

        return len(all_errors) == 0, all_errors + warnings

    except Exception as e:
        return False, [str(e)]


def display_validation_results(file_path: Path, is_valid: bool, messages: list):
    """
    Display validation results in a formatted table

    Args:
        file_path: Configuration file path
        is_valid: Whether configuration is valid
        messages: List of error/warning messages
    """
    # Create results table
    table = Table(
        title=f"Validation Results for {file_path.name}",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Message", style="white")

    if is_valid:
        if not messages:
            table.add_row("✅ Success", "Configuration is valid and complete")
        else:
            table.add_row("✅ Valid", "Configuration is valid with warnings")
            for message in messages:
                table.add_row("⚠️ Warning", message)
    else:
        for message in messages:
            if "Warning" in message or "not configured" in message:
                table.add_row("⚠️ Warning", message)
            else:
                table.add_row("❌ Error", message)

    console.print(table)


def validate_deployment_requirements(config: dict) -> list:
    """
    Validate deployment-specific requirements

    Args:
        config: Configuration dictionary

    Returns:
        List of validation messages
    """
    messages = []
    deployment = config.get("deployment", {})
    services = config.get("services", {})

    deployment_type = deployment.get("type")

    # Check service requirements based on deployment type
    if deployment_type == "docker-compose":
        if not services.get("database"):
            messages.append("Docker Compose deployment requires database service")
        if not services.get("cache"):
            messages.append("Docker Compose deployment requires cache service")

    elif deployment_type == "local-gpu":
        resources = config.get("resources", {})
        gpu = resources.get("gpu", {})
        if not gpu.get("enabled"):
            messages.append("Local GPU deployment requires GPU to be enabled")

        llm = services.get("llm", {})
        if llm.get("provider") not in ["local-mlx", "vllm", "ollama"]:
            messages.append("Local GPU deployment should use local LLM provider")

    elif deployment_type == "aws":
        if not deployment.get("region"):
            messages.append("AWS deployment requires region to be specified")

        networking = config.get("networking", {})
        if not networking.get("domain"):
            messages.append("AWS deployment should specify a domain")

    # Check for production requirements
    if deployment.get("environment") == "production":
        monitoring = config.get("monitoring", {})
        if not monitoring.get("enabled"):
            messages.append("Production environment should have monitoring enabled")

        security = config.get("security", {})
        if not security.get("encryption"):
            messages.append("Production environment should have encryption enabled")

        scaling = config.get("scaling", {})
        if not scaling.get("enabled"):
            messages.append("Production environment should have auto-scaling enabled")

    return messages


def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Validate deployment configuration")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to configuration file to validate"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all configurations in user directory"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Initialize config loader
    loader = ConfigLoader()

    if args.all:
        # Validate all user configurations
        user_configs = loader.list_user_configs()
        if not user_configs:
            console.print("[yellow]No user configurations found[/yellow]")
            return 0

        all_valid = True
        for config_name in user_configs:
            config_path = loader.user_path / f"{config_name}.yaml"
            is_valid, messages = validate_config_file(config_path, loader)
            display_validation_results(config_path, is_valid, messages)

            if not is_valid or (args.strict and messages):
                all_valid = False

        return 0 if all_valid else 1

    else:
        # Validate single configuration
        config_path = Path(args.config)

        if not config_path.exists():
            console.print(f"[red]Configuration file not found: {config_path}[/red]")
            return 1

        is_valid, messages = validate_config_file(config_path, loader)

        # Additional deployment validation
        try:
            config = loader.load_yaml(config_path)
            deployment_messages = validate_deployment_requirements(config)
            messages.extend(deployment_messages)
        except:
            pass

        display_validation_results(config_path, is_valid, messages)

        # Check environment variables
        if is_valid:
            try:
                config = loader.load_yaml(config_path)
                env_vars = loader.load_environment_variables(config)

                if env_vars and args.verbose:
                    env_table = Table(
                        title="Generated Environment Variables",
                        box=box.SIMPLE,
                        show_header=True
                    )
                    env_table.add_column("Variable", style="cyan")
                    env_table.add_column("Value", style="green")

                    for key, value in sorted(env_vars.items()):
                        # Mask sensitive values
                        display_value = value
                        if any(sensitive in key.lower() for sensitive in ["key", "password", "secret"]):
                            display_value = "***" + value[-4:] if len(value) > 4 else "****"
                        env_table.add_row(key, display_value)

                    console.print(env_table)
            except:
                pass

        # Return status
        if not is_valid:
            return 1
        if args.strict and messages:
            return 1

        return 0


if __name__ == "__main__":
    sys.exit(main())