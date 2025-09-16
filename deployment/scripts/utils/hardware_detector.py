"""Hardware detection and recommendation utilities."""

import platform
import subprocess
import os
import psutil
from typing import Dict, Any, Optional, List
from pathlib import Path


class HardwareDetector:
    """Detect hardware capabilities and recommend configurations."""

    def __init__(self):
        """Initialize hardware detector."""
        self.system = platform.system()
        self.machine = platform.machine()
        self.processor = platform.processor()

    def detect(self) -> Dict[str, Any]:
        """Detect hardware capabilities.

        Returns:
            Dictionary with hardware information
        """
        info = {
            "system": self.system,
            "machine": self.machine,
            "processor": self.processor,
            "cpu_count": psutil.cpu_count(logical=False),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "gpu_type": None,
            "gpu_info": None,
            "cuda_available": False,
            "cuda_version": None,
            "metal_available": False,
            "mlx_available": False,
            "recommended_deployment": None
        }

        # Detect GPU
        if self.system == "Darwin":  # macOS
            info.update(self._detect_apple_silicon())
        elif self.system == "Linux" or self.system == "Windows":
            info.update(self._detect_nvidia())

        # Set recommended deployment
        info["recommended_deployment"] = self._recommend_deployment(info)

        return info

    def _detect_apple_silicon(self) -> Dict[str, Any]:
        """Detect Apple Silicon capabilities.

        Returns:
            Apple Silicon information
        """
        info = {}

        # Check if running on Apple Silicon
        if "arm64" in self.machine.lower() or "aarch64" in self.machine.lower():
            info["gpu_type"] = "apple_silicon"

            # Get chip information
            try:
                result = subprocess.run(
                    ["system_profiler", "SPHardwareDataType"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output = result.stdout

                # Parse chip model
                if "Apple M1" in output:
                    info["gpu_info"] = "Apple M1"
                elif "Apple M2" in output:
                    info["gpu_info"] = "Apple M2"
                elif "Apple M3" in output:
                    info["gpu_info"] = "Apple M3"
                else:
                    for line in output.split('\n'):
                        if 'Chip:' in line or 'Processor Name:' in line:
                            info["gpu_info"] = line.split(':')[1].strip()
                            break

                info["metal_available"] = True

                # Check for MLX availability
                try:
                    import mlx
                    info["mlx_available"] = True
                except ImportError:
                    # Check if MLX can be installed
                    info["mlx_available"] = self._check_mlx_installable()

            except Exception:
                info["gpu_info"] = "Apple Silicon (Unknown Model)"
                info["metal_available"] = True

        return info

    def _detect_nvidia(self) -> Dict[str, Any]:
        """Detect NVIDIA GPU capabilities.

        Returns:
            NVIDIA GPU information
        """
        info = {}

        # Try nvidia-smi
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                info["gpu_type"] = "nvidia"
                output = result.stdout.strip()
                if output:
                    parts = output.split(',')
                    info["gpu_info"] = f"{parts[0].strip()} ({parts[1].strip()})"

                # Check CUDA version
                cuda_result = subprocess.run(
                    ["nvidia-smi"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                for line in cuda_result.stdout.split('\n'):
                    if 'CUDA Version:' in line:
                        cuda_version = line.split('CUDA Version:')[1].strip().split()[0]
                        info["cuda_available"] = True
                        info["cuda_version"] = cuda_version
                        break

        except (subprocess.SubprocessError, FileNotFoundError):
            # No NVIDIA GPU or nvidia-smi not available
            pass

        # Fallback: check for AMD GPU on Linux
        if not info.get("gpu_type") and self.system == "Linux":
            try:
                result = subprocess.run(
                    ["lspci"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "AMD" in result.stdout and ("VGA" in result.stdout or "Display" in result.stdout):
                    info["gpu_type"] = "amd"
                    info["gpu_info"] = "AMD GPU detected"
            except:
                pass

        return info

    def _check_mlx_installable(self) -> bool:
        """Check if MLX can be installed.

        Returns:
            True if MLX is installable
        """
        # MLX requires Apple Silicon and macOS 13.3+
        if self.system != "Darwin":
            return False

        try:
            import platform
            mac_version = platform.mac_ver()[0]
            major, minor = map(int, mac_version.split('.')[:2])
            return major > 13 or (major == 13 and minor >= 3)
        except:
            return False

    def _recommend_deployment(self, info: Dict[str, Any]) -> str:
        """Recommend deployment type based on hardware.

        Args:
            info: Hardware information

        Returns:
            Recommended deployment type
        """
        gpu_type = info.get("gpu_type")
        memory_gb = info.get("memory_gb", 0)

        if gpu_type == "apple_silicon":
            if memory_gb >= 16:
                return "local-gpu"  # Use MLX
            else:
                return "docker-compose"  # Use containers with cloud LLM

        elif gpu_type == "nvidia":
            if info.get("cuda_available"):
                return "local-gpu"  # Use vLLM or similar
            else:
                return "docker-compose"

        else:
            # No GPU detected
            if memory_gb >= 32:
                return "docker-compose"  # Can run some local services
            else:
                return "aws"  # Recommend cloud deployment

    def get_recommended_config(self) -> Dict[str, Any]:
        """Get recommended configuration based on hardware.

        Returns:
            Recommended configuration settings
        """
        info = self.detect()
        gpu_type = info.get("gpu_type")
        memory_gb = info.get("memory_gb", 0)

        config = {
            "deployment_type": info["recommended_deployment"],
            "llm": {},
            "embedding": {},
            "reranking": {}
        }

        if gpu_type == "apple_silicon":
            if info.get("mlx_available") or info.get("metal_available"):
                config["llm"] = {
                    "provider": "local-mlx",
                    "model": "Qwen3-8B-MLX-bf16" if memory_gb >= 32 else "Qwen3-8B-MLX-q8",
                    "precision": "bfloat16" if memory_gb >= 32 else "int8"
                }
                config["embedding"] = {
                    "provider": "local",
                    "device": "mps"
                }
                config["reranking"] = {
                    "provider": "local",
                    "device": "mps"
                }
            else:
                # Fallback to cloud services
                config["llm"] = {
                    "provider": "openrouter",
                    "model": "anthropic/claude-3.5-sonnet"
                }

        elif gpu_type == "nvidia" and info.get("cuda_available"):
            config["llm"] = {
                "provider": "vllm",
                "model": "Qwen/Qwen2.5-7B-Instruct"
            }
            config["embedding"] = {
                "provider": "local",
                "device": "cuda"
            }
            config["reranking"] = {
                "provider": "local",
                "device": "cuda"
            }

        else:
            # No GPU - use cloud services
            config["llm"] = {
                "provider": "openrouter",
                "model": "anthropic/claude-3.5-sonnet"
            }
            config["embedding"] = {
                "provider": "openai",
                "model": "text-embedding-3-small"
            }
            config["reranking"] = {
                "provider": "cohere",
                "model": "rerank-english-v2.0"
            }

        return config

    def check_dependencies(self) -> Dict[str, bool]:
        """Check for required dependencies.

        Returns:
            Dictionary of dependency availability
        """
        deps = {
            "docker": self._check_command("docker"),
            "docker-compose": self._check_command("docker-compose"),
            "python3": self._check_command("python3"),
            "pip": self._check_command("pip"),
            "git": self._check_command("git"),
            "node": self._check_command("node"),
            "npm": self._check_command("npm"),
        }

        # Platform specific
        if self.system == "Darwin":
            deps["brew"] = self._check_command("brew")
            deps["xcode"] = self._check_xcode()

        return deps

    def _check_command(self, command: str) -> bool:
        """Check if a command is available.

        Args:
            command: Command to check

        Returns:
            True if command is available
        """
        try:
            subprocess.run(
                [command, "--version"],
                capture_output=True,
                timeout=5
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _check_xcode(self) -> bool:
        """Check if Xcode command line tools are installed.

        Returns:
            True if Xcode CLT is installed
        """
        try:
            result = subprocess.run(
                ["xcode-select", "-p"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def get_available_models(self) -> List[str]:
        """Get list of locally available models.

        Returns:
            List of available model paths
        """
        models = []

        # Check common model directories
        model_dirs = [
            Path.home() / ".lmstudio" / "models",
            Path.home() / ".cache" / "huggingface",
            Path("./models"),
            Path("/usr/local/models"),
        ]

        for model_dir in model_dirs:
            if model_dir.exists():
                # Look for model files
                for pattern in ["*.gguf", "*.bin", "*.safetensors", "config.json"]:
                    for model_file in model_dir.rglob(pattern):
                        model_path = str(model_file.parent)
                        if model_path not in models:
                            models.append(model_path)

        return models