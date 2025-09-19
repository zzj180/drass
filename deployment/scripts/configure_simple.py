#!/usr/bin/env python3
"""
Simple interactive deployment configuration generator
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import yaml
import json

# Add script directory to path
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

try:
    from utils.config_loader import ConfigLoader
    from utils.config_models import DeploymentConfiguration
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you are running from the correct directory")
    sys.exit(1)


def get_input(prompt, default=None):
    """Get user input with optional default value"""
    if default:
        response = input(f"{prompt} [{default}]: ").strip()
        return response if response else default
    else:
        response = input(f"{prompt}: ").strip()
        while not response:
            print("This field is required.")
            response = input(f"{prompt}: ").strip()
        return response


def choose_option(prompt, options, default=0):
    """Let user choose from a list of options"""
    print(f"\n{prompt}")
    for i, option in enumerate(options):
        marker = " *" if i == default else ""
        print(f"  {i+1}. {option}{marker}")

    while True:
        choice = input(f"Choose [1-{len(options)}] (default: {default+1}): ").strip()
        if not choice:
            return default
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return idx
            else:
                print(f"Please choose a number between 1 and {len(options)}")
        except ValueError:
            print("Please enter a valid number")


def configure_deployment():
    """Configure basic deployment settings"""
    print("\n=== Deployment Configuration ===")

    deployment_types = ["docker-compose", "local-gpu", "aws"]
    deployment_type = deployment_types[choose_option(
        "Select deployment type:",
        ["Docker Compose (Local containers)", "Local GPU (Hardware acceleration)", "AWS (Cloud deployment)"],
        default=0
    )]

    environments = ["development", "staging", "production"]
    environment = environments[choose_option(
        "Select environment:",
        ["Development", "Staging", "Production"],
        default=0
    )]

    name = get_input("Deployment name", f"{deployment_type}-{environment}")

    config = {
        "deployment": {
            "type": deployment_type,
            "name": name,
            "environment": environment
        }
    }

    if deployment_type == "aws":
        config["deployment"]["region"] = get_input("AWS Region", "us-west-2")

    return config


def configure_llm():
    """Configure LLM service"""
    print("\n=== LLM Service Configuration ===")

    providers = ["openrouter", "openai", "local-mlx", "ollama"]
    provider = providers[choose_option(
        "Select LLM provider:",
        ["OpenRouter (Recommended)", "OpenAI", "Local MLX (Apple Silicon)", "Ollama"],
        default=0
    )]

    config = {
        "provider": provider,
        "temperature": 0.7,
        "max_tokens": 2048
    }

    if provider == "openrouter":
        config["model"] = get_input("Model name", "gpt-3.5-turbo")
        config["api_key"] = get_input("API Key (use ${VAR} for env var)", "${OPENROUTER_API_KEY}")
    elif provider == "openai":
        config["model"] = get_input("Model name", "gpt-3.5-turbo")
        config["api_key"] = get_input("API Key (use ${VAR} for env var)", "${OPENAI_API_KEY}")
    elif provider == "local-mlx":
        config["model"] = "qwen3-8b-mlx"
        config["base_url"] = "http://localhost:8001/v1"
    elif provider == "ollama":
        config["model"] = get_input("Model name", "qwen2.5:7b")
        config["base_url"] = "http://localhost:11434"

    return config


def configure_storage():
    """Configure storage services"""
    print("\n=== Storage Configuration ===")

    # Vector store
    vector_providers = ["chromadb", "weaviate", "pinecone"]
    vector_provider = vector_providers[choose_option(
        "Select vector store:",
        ["ChromaDB (Local)", "Weaviate", "Pinecone (Cloud)"],
        default=0
    )]

    vector_config = {"provider": vector_provider}

    if vector_provider == "chromadb":
        vector_config["connection"] = {
            "host": "localhost",
            "port": 8005
        }
    elif vector_provider == "pinecone":
        vector_config["connection"] = {
            "api_key": get_input("Pinecone API Key", "${PINECONE_API_KEY}"),
            "index_name": get_input("Index name", "drass-docs")
        }

    # Database
    db_providers = ["postgresql", "mysql"]
    db_provider = db_providers[choose_option(
        "Select database:",
        ["PostgreSQL (Recommended)", "MySQL"],
        default=0
    )]

    db_config = {
        "provider": db_provider,
        "connection": {
            "host": get_input("Database host", "localhost"),
            "port": 5432 if db_provider == "postgresql" else 3306,
            "username": get_input("Database username", "postgres" if db_provider == "postgresql" else "root"),
            "password": get_input("Database password (use ${VAR} for env var)", "${DB_PASSWORD}"),
            "database": get_input("Database name", "drass")
        }
    }

    # Cache
    cache_config = {
        "provider": "redis",
        "connection": {
            "host": get_input("Redis host", "localhost"),
            "port": 6379,
            "password": get_input("Redis password (use ${VAR} for env var)", "${REDIS_PASSWORD}"),
            "db": 0
        }
    }

    return {
        "vector_store": vector_config,
        "database": db_config,
        "cache": cache_config
    }


def main():
    """Main configuration flow"""
    print("=" * 60)
    print("Drass Deployment Configuration Generator")
    print("=" * 60)

    try:
        # Initialize loader
        loader = ConfigLoader()

        # Basic deployment config
        config = configure_deployment()

        # Load template based on deployment type
        template_name = config["deployment"]["type"].replace("-", "_")
        try:
            template = loader.load_template(config["deployment"]["type"])
        except FileNotFoundError:
            print(f"\nUsing default configuration template")
            template = {}

        # Configure services
        print("\n=== Service Configuration ===")

        # LLM
        if input("\nConfigure LLM service? [Y/n]: ").lower() != 'n':
            llm_config = configure_llm()
            config.setdefault("services", {})["llm"] = llm_config

        # Storage
        if input("\nConfigure storage services? [Y/n]: ").lower() != 'n':
            storage_config = configure_storage()
            config.setdefault("services", {}).update(storage_config)

        # Embedding (use defaults)
        config.setdefault("services", {})["embedding"] = {
            "provider": "local",
            "model": "all-MiniLM-L6-v2",
            "port": 8002
        }

        # Environment variables
        config["environment"] = {
            "variables": {
                "NODE_ENV": config["deployment"]["environment"],
                "DEPLOYMENT_TYPE": config["deployment"]["type"]
            }
        }

        # Merge with template
        final_config = loader.merge_configs(template, config)

        # Preview
        print("\n=== Configuration Preview ===")
        print(yaml.dump(final_config, default_flow_style=False, sort_keys=False))

        # Save
        if input("\nSave this configuration? [Y/n]: ").lower() != 'n':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{config['deployment']['name']}_{timestamp}.yaml"
            filepath = loader.user_path / filename

            loader.save_yaml(final_config, filepath)
            print(f"\n✅ Configuration saved to: {filepath}")

            # Generate env variables
            env_vars = loader.load_environment_variables(final_config)
            env_file = Path(".env.generated")
            with open(env_file, "w") as f:
                f.write("# Generated environment variables\n")
                f.write(f"# Created: {datetime.now()}\n\n")
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            print(f"✅ Environment variables saved to: {env_file}")

            print("\n=== Next Steps ===")
            print(f"1. Review and update environment variables in {env_file}")
            print(f"2. Validate configuration: python deployment/scripts/validate.py --config {filepath}")
            print(f"3. Deploy: python deployment/scripts/deploy.py --config {filepath}")

    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()