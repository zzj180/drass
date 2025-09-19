#!/usr/bin/env python3
"""
Patch the main app to handle proxy configuration issues
"""

import os
import sys

def create_config_patch():
    """Create a configuration patch file"""

    patch_content = '''import os
import sys

# Proxy configuration fix
# Remove SOCKS proxy which causes issues with HTTP libraries
if 'all_proxy' in os.environ:
    print(f"Removing all_proxy: {os.environ['all_proxy']}")
    del os.environ['all_proxy']
if 'ALL_PROXY' in os.environ:
    del os.environ['ALL_PROXY']

# Ensure localhost bypasses proxy
if 'NO_PROXY' not in os.environ:
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1,0.0.0.0'
else:
    no_proxy = os.environ['NO_PROXY']
    if 'localhost' not in no_proxy:
        os.environ['NO_PROXY'] = f"{no_proxy},localhost,127.0.0.1,::1,0.0.0.0"

# If HTTPS_PROXY is SOCKS, convert or remove it
for proxy_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    if proxy_var in os.environ:
        proxy_value = os.environ[proxy_var]
        if proxy_value.startswith('socks'):
            print(f"Removing SOCKS proxy from {proxy_var}: {proxy_value}")
            del os.environ[proxy_var]
            # Optionally set HTTP proxy if available
            # os.environ[proxy_var] = 'http://127.0.0.1:7890'

print(f"Proxy configuration adjusted:")
print(f"  NO_PROXY: {os.environ.get('NO_PROXY', 'not set')}")
print(f"  HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'not set')}")
print(f"  HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'not set')}")
'''

    return patch_content

def create_patched_config():
    """Create a patched configuration file"""

    config_content = '''"""
Patched configuration for handling proxy issues
"""

from pydantic import BaseSettings, Field
from typing import Optional
import os

# Apply proxy fixes before importing other modules
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Clear problematic proxy settings
for key in ['all_proxy', 'ALL_PROXY']:
    if key in os.environ:
        del os.environ[key]

# Ensure localhost bypasses proxy
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1,0.0.0.0'

class Settings(BaseSettings):
    # API Configuration
    api_title: str = "Drass Compliance Assistant API"
    api_version: str = "1.0.0"
    api_description: str = "LangChain-based compliance assistant with RAG capabilities"

    # CORS
    cors_origins: list = ["*"]

    # LLM Configuration
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-3.5-turbo", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_api_key: Optional[str] = Field(default=None, env="LLM_API_KEY")
    llm_base_url: Optional[str] = Field(default="http://localhost:8001/v1", env="LLM_BASE_URL")

    # Use local LLM service
    use_local_llm: bool = Field(default=True, env="USE_LOCAL_LLM")
    local_llm_url: str = Field(default="http://localhost:8001/v1", env="LOCAL_LLM_URL")
    local_llm_model: str = Field(default="vllm", env="LOCAL_LLM_MODEL")
    local_llm_api_key: str = Field(default="123456", env="LOCAL_LLM_API_KEY")

    # Database
    database_url: str = Field(
        default="postgresql://drass_user:drass_password@localhost:5432/drass_production",
        env="DATABASE_URL"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # ChromaDB
    chromadb_host: str = Field(default="localhost", env="CHROMADB_HOST")
    chromadb_port: int = Field(default=8005, env="CHROMADB_PORT")
    chromadb_path: str = Field(default="/home/qwkj/drass/data/chromadb", env="CHROMADB_PATH")

    # Embeddings
    embedding_provider: str = Field(default="local", env="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    embedding_api_base: Optional[str] = Field(default="http://localhost:8010/v1", env="EMBEDDING_API_BASE")

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
'''

    return config_content

def main():
    base_dir = "/home/qwkj/drass"

    # Create proxy fix module
    proxy_fix_path = f"{base_dir}/services/main-app/app/proxy_fix.py"
    print(f"Creating proxy fix module at {proxy_fix_path}")

    os.makedirs(os.path.dirname(proxy_fix_path), exist_ok=True)

    with open(proxy_fix_path, 'w') as f:
        f.write(create_config_patch())

    print(f"✓ Created {proxy_fix_path}")

    # Create patched config
    config_path = f"{base_dir}/services/main-app/app/config_patched.py"
    print(f"Creating patched config at {config_path}")

    with open(config_path, 'w') as f:
        f.write(create_patched_config())

    print(f"✓ Created {config_path}")

    # Create startup script that uses the fixes
    startup_script = f"{base_dir}/services/main-app/run_api.py"

    startup_content = '''#!/usr/bin/env python3
"""
Startup script with proxy fixes
"""

import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Apply proxy fixes
import proxy_fix

# Now import and run the app
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
'''

    with open(startup_script, 'w') as f:
        f.write(startup_content)

    os.chmod(startup_script, 0o755)
    print(f"✓ Created {startup_script}")

    print("\nProxy patches created successfully!")
    print("\nTo use the patched configuration:")
    print(f"1. Import the proxy fix in your main.py:")
    print(f"   from app import proxy_fix")
    print(f"2. Or run the API using the patched startup script:")
    print(f"   python3 {startup_script}")

if __name__ == "__main__":
    main()