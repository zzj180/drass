#!/usr/bin/env python3
"""Interactive deployment configuration generator."""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.tree import Tree
    from rich import print as rprint
except ImportError:
    print("Error: Required packages not installed.")
    print("Please install: pip install rich pydantic pyyaml psutil")
    sys.exit(1)

from deployment.scripts.utils.config_models import (
    Config, Metadata, DeploymentConfig, LLMConfig,
    EmbeddingConfig, RerankingConfig, VectorStoreConfig,
    DatabaseConfig, CacheConfig, Services, Infrastructure,
    AWSConfig, DockerConfig, LocalGPUConfig
)
from deployment.scripts.utils.config_loader import ConfigLoader, ConfigValidator
from deployment.scripts.utils.hardware_detector import HardwareDetector


console = Console()


class DeploymentConfigurator:
    """Interactive deployment configuration generator."""

    def __init__(self):
        """Initialize configurator."""
        self.config_loader = ConfigLoader()
        self.validator = ConfigValidator()
        self.hardware_detector = HardwareDetector()
        self.config_data = {}

    def run(self) -> None:
        """Run the interactive configuration process."""
        self._show_welcome()

        # Detect hardware
        hardware_info = self._detect_hardware()

        # Configuration steps
        self._configure_deployment(hardware_info)
        self._configure_infrastructure()
        self._configure_llm()
        self._configure_embedding()
        self._configure_reranking()
        self._configure_storage()
        self._configure_application()

        # Preview and save
        config = self._build_config()
        if self._preview_config(config):
            self._save_config(config)

    def _show_welcome(self) -> None:
        """Show welcome message."""
        console.clear()
        panel = Panel.fit(
            "[bold cyan]Drass Deployment Configurator[/bold cyan]\n"
            "Version 1.0.0\n\n"
            "This wizard will help you create a deployment configuration\n"
            "for your Drass Compliance Assistant.",
            title="Welcome",
            border_style="cyan"
        )
        console.print(panel)
        console.print()

    def _detect_hardware(self) -> Dict[str, Any]:
        """Detect and display hardware information."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Detecting hardware...", total=None)
            hardware_info = self.hardware_detector.detect()
            progress.stop()

        # Display hardware info
        table = Table(title="Hardware Information", show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("System", hardware_info["system"])
        table.add_row("Processor", hardware_info["processor"])
        table.add_row("CPU Cores", f"{hardware_info['cpu_count']} ({hardware_info['cpu_count_logical']} logical)")
        table.add_row("Memory", f"{hardware_info['memory_gb']} GB")

        if hardware_info.get("gpu_type"):
            table.add_row("GPU Type", hardware_info["gpu_type"])
            if hardware_info.get("gpu_info"):
                table.add_row("GPU Info", hardware_info["gpu_info"])
            if hardware_info.get("cuda_version"):
                table.add_row("CUDA Version", hardware_info["cuda_version"])
            if hardware_info.get("mlx_available"):
                table.add_row("MLX Available", "✅ Yes")

        table.add_row("", "")
        table.add_row("[bold]Recommendation[/bold]",
                     f"[bold yellow]{hardware_info['recommended_deployment']}[/bold yellow]")

        console.print(table)
        console.print()

        return hardware_info

    def _configure_deployment(self, hardware_info: Dict[str, Any]) -> None:
        """Configure deployment settings."""
        console.print("[bold cyan]Step 1: Deployment Configuration[/bold cyan]")

        # Deployment type
        deployment_types = [
            ("aws", "AWS Cloud (ECS/EC2)", "☁️"),
            ("docker-compose", "Docker Compose", "🐳"),
            ("local-gpu", "Local GPU (NVIDIA/Apple Silicon)", "🎮"),
            ("local-cpu", "Local CPU Only", "💻"),
        ]

        console.print("\nSelect deployment type:")
        for i, (key, name, icon) in enumerate(deployment_types, 1):
            recommended = "⭐" if key == hardware_info["recommended_deployment"] else "  "
            console.print(f"{recommended} {i}) {icon} {name}")

        choice = IntPrompt.ask(
            "Your choice",
            default=next(i for i, (k, _, _) in enumerate(deployment_types, 1)
                        if k == hardware_info["recommended_deployment"])
        )
        deployment_type = deployment_types[choice - 1][0]

        # Environment
        environments = ["development", "staging", "production"]
        console.print("\nSelect environment:")
        for i, env in enumerate(environments, 1):
            console.print(f"  {i}) {env}")

        env_choice = IntPrompt.ask("Your choice", default=1)
        environment = environments[env_choice - 1]

        # Configuration name
        config_name = Prompt.ask(
            "\nConfiguration name",
            default=f"{deployment_type}-{environment}"
        )

        self.config_data["deployment"] = {
            "type": deployment_type,
            "environment": environment
        }
        self.config_data["metadata"] = {
            "name": config_name,
            "description": Prompt.ask("Description (optional)", default=""),
        }

    def _configure_infrastructure(self) -> None:
        """Configure infrastructure based on deployment type."""
        deployment_type = self.config_data["deployment"]["type"]

        if deployment_type == "aws":
            self._configure_aws()
        elif deployment_type == "docker-compose":
            self._configure_docker()
        elif deployment_type == "local-gpu":
            self._configure_local_gpu()

    def _configure_aws(self) -> None:
        """Configure AWS infrastructure."""
        console.print("\n[bold cyan]AWS Configuration[/bold cyan]")

        aws_config = {}
        aws_config["region"] = Prompt.ask("AWS Region", default="us-west-2")

        if Confirm.ask("Do you have existing VPC/Subnet IDs?", default=False):
            aws_config["vpc_id"] = Prompt.ask("VPC ID")
            subnet_count = IntPrompt.ask("Number of subnets", default=2)
            aws_config["subnet_ids"] = [
                Prompt.ask(f"Subnet ID {i+1}") for i in range(subnet_count)
            ]

        aws_config["ecs_cluster"] = Prompt.ask("ECS Cluster name", default="drass-cluster")
        aws_config["s3_bucket"] = Prompt.ask("S3 Bucket for storage", default="drass-storage")

        self.config_data["infrastructure"] = {"aws": aws_config}

    def _configure_docker(self) -> None:
        """Configure Docker infrastructure."""
        console.print("\n[bold cyan]Docker Configuration[/bold cyan]")

        docker_config = {
            "compose_file": "docker-compose.yml",
            "network": Prompt.ask("Docker network name", default="drass-network")
        }

        self.config_data["infrastructure"] = {"docker": docker_config}

    def _configure_local_gpu(self) -> None:
        """Configure local GPU infrastructure."""
        console.print("\n[bold cyan]Local GPU Configuration[/bold cyan]")

        hardware_info = self.hardware_detector.detect()

        local_gpu_config = {
            "gpu_type": hardware_info.get("gpu_type", "cpu")
        }

        if hardware_info.get("gpu_type") == "apple_silicon":
            local_gpu_config["metal_enabled"] = True
            local_gpu_config["mlx_enabled"] = hardware_info.get("mlx_available", False)
        elif hardware_info.get("gpu_type") == "nvidia":
            local_gpu_config["cuda_version"] = hardware_info.get("cuda_version")

        self.config_data["infrastructure"] = {"local_gpu": local_gpu_config}

    def _configure_llm(self) -> None:
        """Configure LLM service."""
        console.print("\n[bold cyan]Step 2: LLM Service Configuration[/bold cyan]")

        # Get hardware recommendations
        hw_recommendations = self.hardware_detector.get_recommended_config()
        recommended_llm = hw_recommendations.get("llm", {})

        # LLM providers
        providers = [
            ("openrouter", "OpenRouter (Cloud API)", "☁️"),
            ("openai", "OpenAI (GPT-4/GPT-3.5)", "🤖"),
            ("local-mlx", "Local MLX (Apple Silicon)", "🍎"),
            ("vllm", "vLLM (NVIDIA GPU)", "🎮"),
            ("ollama", "Ollama (Easy Local)", "🦙"),
        ]

        console.print("\nSelect LLM provider:")
        for i, (key, name, icon) in enumerate(providers, 1):
            recommended = "⭐" if key == recommended_llm.get("provider") else "  "
            console.print(f"{recommended} {i}) {icon} {name}")

        choice = IntPrompt.ask("Your choice", default=1)
        provider = providers[choice - 1][0]

        llm_config = {"provider": provider}

        # Provider-specific configuration
        if provider == "openrouter":
            llm_config["model"] = Prompt.ask(
                "Model",
                default="anthropic/claude-3.5-sonnet"
            )
            llm_config["api_key"] = Prompt.ask(
                "API Key (or ${ENV_VAR})",
                default="${OPENROUTER_API_KEY}"
            )
            llm_config["base_url"] = "https://openrouter.ai/api/v1"

        elif provider == "openai":
            models = ["gpt-4-turbo-preview", "gpt-3.5-turbo"]
            console.print("\nSelect model:")
            for i, model in enumerate(models, 1):
                console.print(f"  {i}) {model}")
            model_choice = IntPrompt.ask("Your choice", default=1)
            llm_config["model"] = models[model_choice - 1]
            llm_config["api_key"] = Prompt.ask(
                "API Key (or ${ENV_VAR})",
                default="${OPENAI_API_KEY}"
            )

        elif provider == "local-mlx":
            # Check for available models
            available_models = self.hardware_detector.get_available_models()
            if available_models:
                console.print("\nDetected local models:")
                for i, model_path in enumerate(available_models[:5], 1):
                    console.print(f"  {i}) {model_path}")
                console.print(f"  {len(available_models[:5]) + 1}) Enter custom path")

                model_choice = IntPrompt.ask("Your choice", default=1)
                if model_choice <= len(available_models[:5]):
                    llm_config["mlx_model_path"] = available_models[model_choice - 1]
                else:
                    llm_config["mlx_model_path"] = Prompt.ask("Model path")
            else:
                llm_config["mlx_model_path"] = Prompt.ask(
                    "Model path",
                    default="${HOME}/.lmstudio/models/Qwen/Qwen3-8B-MLX-bf16"
                )

            llm_config["model"] = "Qwen3-8B-MLX-bf16"
            llm_config["base_url"] = "http://localhost:8001/v1"

        elif provider == "vllm":
            llm_config["model"] = Prompt.ask(
                "Model",
                default="Qwen/Qwen2.5-7B-Instruct"
            )
            llm_config["base_url"] = "http://localhost:8001/v1"

        elif provider == "ollama":
            llm_config["model"] = Prompt.ask("Model", default="qwen2.5:7b")
            llm_config["base_url"] = "http://localhost:11434"

        # Common settings
        llm_config["temperature"] = float(Prompt.ask("Temperature", default="0.7"))
        llm_config["max_tokens"] = IntPrompt.ask("Max tokens", default=4096)

        self.config_data["llm"] = llm_config

    def _configure_embedding(self) -> None:
        """Configure embedding service."""
        console.print("\n[bold cyan]Step 3: Embedding Service Configuration[/bold cyan]")

        providers = [
            ("local", "Local (Sentence Transformers)", "🏠"),
            ("openai", "OpenAI Embeddings", "🤖"),
            ("huggingface", "HuggingFace API", "🤗"),
        ]

        console.print("\nSelect embedding provider:")
        for i, (key, name, icon) in enumerate(providers, 1):
            console.print(f"  {i}) {icon} {name}")

        choice = IntPrompt.ask("Your choice", default=1)
        provider = providers[choice - 1][0]

        embedding_config = {"provider": provider}

        if provider == "local":
            embedding_config["model"] = Prompt.ask(
                "Model",
                default="BAAI/bge-base-en-v1.5"
            )
            embedding_config["api_base"] = "http://localhost:8002"

            # Device selection based on hardware
            hw_info = self.hardware_detector.detect()
            if hw_info.get("gpu_type") == "apple_silicon":
                embedding_config["device"] = "mps"
            elif hw_info.get("cuda_available"):
                embedding_config["device"] = "cuda"
            else:
                embedding_config["device"] = "cpu"

        elif provider == "openai":
            embedding_config["model"] = Prompt.ask(
                "Model",
                default="text-embedding-3-small"
            )
            embedding_config["api_key"] = Prompt.ask(
                "API Key (or ${ENV_VAR})",
                default="${OPENAI_API_KEY}"
            )

        self.config_data["embedding"] = embedding_config

    def _configure_reranking(self) -> None:
        """Configure reranking service."""
        console.print("\n[bold cyan]Step 4: Reranking Service Configuration[/bold cyan]")

        if not Confirm.ask("Enable reranking?", default=True):
            self.config_data["reranking"] = {"enabled": False}
            return

        providers = [
            ("local", "Local (Cross-Encoder)", "🏠"),
            ("cohere", "Cohere Rerank API", "☁️"),
        ]

        console.print("\nSelect reranking provider:")
        for i, (key, name, icon) in enumerate(providers, 1):
            console.print(f"  {i}) {icon} {name}")

        choice = IntPrompt.ask("Your choice", default=1)
        provider = providers[choice - 1][0]

        reranking_config = {
            "enabled": True,
            "provider": provider
        }

        if provider == "local":
            reranking_config["model"] = Prompt.ask(
                "Model",
                default="BAAI/bge-reranker-base"
            )
            reranking_config["api_base"] = "http://localhost:8004"
        elif provider == "cohere":
            reranking_config["model"] = "rerank-english-v2.0"
            reranking_config["api_key"] = Prompt.ask(
                "API Key (or ${ENV_VAR})",
                default="${COHERE_API_KEY}"
            )

        reranking_config["top_k"] = IntPrompt.ask("Top K results", default=10)

        self.config_data["reranking"] = reranking_config

    def _configure_storage(self) -> None:
        """Configure storage services."""
        console.print("\n[bold cyan]Step 5: Storage Configuration[/bold cyan]")

        # Vector store
        vector_stores = [
            ("chromadb", "ChromaDB (Easy Local)", "🎨"),
            ("pinecone", "Pinecone (Managed Cloud)", "🌲"),
            ("weaviate", "Weaviate", "🔮"),
            ("qdrant", "Qdrant", "🔷"),
        ]

        console.print("\nSelect vector store:")
        for i, (key, name, icon) in enumerate(vector_stores, 1):
            console.print(f"  {i}) {icon} {name}")

        choice = IntPrompt.ask("Your choice", default=1)
        vector_type = vector_stores[choice - 1][0]

        vector_config = {"type": vector_type}

        if vector_type == "chromadb":
            vector_config["host"] = "localhost"
            vector_config["port"] = 8000
        elif vector_type == "pinecone":
            vector_config["api_key"] = Prompt.ask(
                "API Key",
                default="${PINECONE_API_KEY}"
            )
            vector_config["pinecone_environment"] = Prompt.ask(
                "Environment",
                default="us-west1-gcp"
            )
            vector_config["pinecone_index_name"] = Prompt.ask(
                "Index name",
                default="drass-docs"
            )

        vector_config["collection_name"] = Prompt.ask(
            "Collection name",
            default="drass_docs"
        )

        self.config_data["vector_store"] = vector_config

        # Database
        if self.config_data["deployment"]["type"] in ["local-gpu", "local-cpu"]:
            db_type = "sqlite"
            db_config = {
                "type": "sqlite",
                "sqlite_path": "./data/drass.db",
                "database": "compliance_assistant"
            }
        else:
            db_type = "postgresql"
            db_config = {
                "type": "postgresql",
                "host": Prompt.ask("Database host", default="localhost"),
                "port": IntPrompt.ask("Database port", default=5432),
                "database": Prompt.ask("Database name", default="compliance_assistant"),
                "user": Prompt.ask("Database user", default="postgres"),
                "password": Prompt.ask("Database password (or ${ENV_VAR})",
                                     default="${DB_PASSWORD}"),
            }

        self.config_data["database"] = db_config

        # Cache
        if self.config_data["deployment"]["type"] in ["local-gpu", "local-cpu"]:
            cache_type = "memory"
            cache_config = {"type": "memory", "ttl": 3600}
        else:
            cache_type = "redis"
            cache_config = {
                "type": "redis",
                "host": Prompt.ask("Redis host", default="localhost"),
                "port": IntPrompt.ask("Redis port", default=6379),
                "ttl": 3600
            }

        self.config_data["cache"] = cache_config

    def _configure_application(self) -> None:
        """Configure application settings."""
        console.print("\n[bold cyan]Step 6: Application Settings[/bold cyan]")

        # Quick settings for common scenarios
        if self.config_data["deployment"]["environment"] == "development":
            self.config_data["application"] = {
                "main_app": {
                    "port": 8000,
                    "workers": 2,
                    "enable_docs": True,
                    "cors_origins": ["http://localhost:5173"],
                    "jwt_enabled": False
                },
                "frontend": {
                    "port": 5173,
                    "build_mode": "development",
                    "api_base": "http://localhost:8000"
                }
            }
            self.config_data["logging"] = {
                "level": "DEBUG",
                "format": "text"
            }
        else:
            # Production settings need more configuration
            app_port = IntPrompt.ask("API port", default=8000)
            frontend_port = IntPrompt.ask("Frontend port", default=5173)

            self.config_data["application"] = {
                "main_app": {
                    "port": app_port,
                    "workers": IntPrompt.ask("Worker processes", default=4),
                    "enable_docs": False,
                    "cors_origins": [Prompt.ask("Frontend URL",
                                               default="https://drass.example.com")],
                    "jwt_enabled": True
                },
                "frontend": {
                    "port": frontend_port,
                    "build_mode": "production",
                    "api_base": Prompt.ask("API URL", default="https://api.drass.example.com")
                }
            }
            self.config_data["logging"] = {
                "level": "INFO",
                "format": "json"
            }

    def _build_config(self) -> Config:
        """Build the configuration object."""
        # Merge with base template
        deployment_type = self.config_data["deployment"]["type"]
        template = self.config_loader.load_template(deployment_type.replace("-", "_"))

        # Deep merge user config with template
        merged = self.config_loader.merge_configs(template, self.config_data)

        # Create Config object
        config = Config(**merged)
        return config

    def _preview_config(self, config: Config) -> bool:
        """Preview configuration and confirm."""
        console.print("\n[bold cyan]Configuration Preview[/bold cyan]")

        # Create tree view
        tree = Tree("[bold]Deployment Configuration[/bold]")

        # Metadata
        meta_branch = tree.add("📋 Metadata")
        meta_branch.add(f"Name: {config.metadata.name}")
        meta_branch.add(f"Created: {config.metadata.created_at}")

        # Deployment
        deploy_branch = tree.add("🚀 Deployment")
        deploy_branch.add(f"Type: {config.deployment.type}")
        deploy_branch.add(f"Environment: {config.deployment.environment}")

        # Services
        services_branch = tree.add("⚙️ Services")
        services_branch.add(f"LLM: {config.services.llm.provider} ({config.services.llm.model})")
        services_branch.add(f"Embedding: {config.services.embedding.provider}")
        if config.services.reranking and config.services.reranking.enabled:
            services_branch.add(f"Reranking: {config.services.reranking.provider}")
        services_branch.add(f"Vector Store: {config.services.vector_store.type}")
        services_branch.add(f"Database: {config.services.database.type}")

        console.print(tree)

        # Validate
        console.print("\n[bold cyan]Validation[/bold cyan]")
        if self.validator.validate(config):
            console.print("[green]✅ Configuration is valid[/green]")
        else:
            console.print("[red]❌ Configuration has issues:[/red]")
            console.print(self.validator.get_report())

        return Confirm.ask("\nSave this configuration?", default=True)

    def _save_config(self, config: Config) -> None:
        """Save configuration to file."""
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"config_{config.metadata.name}_{timestamp}.yaml"
        filepath = Path("deployment/configs/user") / filename

        # Save configuration
        self.config_loader.save(config, filepath)
        console.print(f"\n[green]✅ Configuration saved to:[/green] {filepath}")

        # Generate .env file
        if Confirm.ask("Generate .env file?", default=True):
            env_vars = config.to_env()
            env_path = Path(".env.generated")
            with open(env_path, "w") as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            console.print(f"[green]✅ Environment variables saved to:[/green] {env_path}")

        # Show next steps
        console.print("\n[bold cyan]Next Steps:[/bold cyan]")
        console.print("1. Review and set any environment variables marked with ${}")
        console.print(f"2. Run deployment: [cyan]python deployment/scripts/deploy.py --config {filepath}[/cyan]")
        console.print("3. Check service status: [cyan]python deployment/scripts/deploy.py status[/cyan]")


def main():
    """Main entry point."""
    try:
        configurator = DeploymentConfigurator()
        configurator.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Configuration cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()