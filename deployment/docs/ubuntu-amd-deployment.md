# Ubuntu AMD GPU Deployment Guide

This guide explains how to deploy the Drass system on Ubuntu 22.04 with AMD GPUs using existing vLLM model services.

## System Requirements

- Ubuntu 22.04 LTS
- 2x AMD GPUs (ROCm compatible)
- 32GB+ RAM
- 200GB+ SSD storage
- Python 3.8+
- Node.js 16+

## Pre-deployed Services

Your server already has three vLLM services running:

1. **LLM Service (Port 8001)**
   - Model: DeepSeek-R1-0528-Qwen3-8B
   - GPU Memory: 45%
   - Tensor Parallel: 2 GPUs
   - Max Model Length: 12288 tokens

2. **Embedding Service (Port 8010)**
   - Model: Qwen3-Embedding-8B
   - GPU Memory: 30%
   - Tensor Parallel: 2 GPUs
   - Task: Embeddings

3. **Reranking Service (Port 8012)**
   - Model: Qwen3-Reranker-8B
   - GPU Memory: 30%
   - Tensor Parallel: 2 GPUs
   - Task: Reranking/Scoring

## Deployment Steps

### 1. Prerequisites Installation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install -y python3-pip python3-venv python3-dev

# Install Node.js (if not installed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install Redis
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Install other dependencies
sudo apt install -y git curl wget build-essential
```

### 2. Database Setup

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE USER drass_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE drass_production OWNER drass_user;
GRANT ALL PRIVILEGES ON DATABASE drass_production TO drass_user;
EOF
```

### 3. Clone and Setup Drass

```bash
# Clone repository
cd /home/qwkj
git clone https://github.com/renzhichao/drass.git
cd drass

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r services/main-app/requirements.txt
pip install chromadb

# Install frontend dependencies
cd frontend
npm install
npm run build
cd ..
```

### 4. Configuration

Create environment file `.env.production`:

```bash
# LLM Configuration (using existing vLLM service)
LLM_PROVIDER=vllm
LLM_MODEL=vllm
LLM_BASE_URL=http://localhost:8001/v1
LLM_API_KEY=123456

# Embedding Configuration (using existing service)
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=Qwen3-Embedding-8B
EMBEDDING_API_KEY=123456
EMBEDDING_API_BASE=http://localhost:8010/v1

# Reranking Configuration (using existing service)
RERANKING_ENABLED=true
RERANKING_PROVIDER=local
RERANKING_MODEL=Qwen3-Reranker-8B
RERANKING_API_KEY=123456
RERANKING_API_BASE=http://localhost:8012/v1

# Database Configuration
DATABASE_URL=postgresql://drass_user:your_secure_password@localhost:5432/drass_production
DB_PASSWORD=your_secure_password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password

# Vector Store Configuration
VECTOR_STORE_TYPE=chromadb
CHROMA_PERSIST_DIRECTORY=/home/qwkj/drass/data/chromadb

# Security Keys (generate secure random values)
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
ENCRYPTION_KEY=your-encryption-key-here

# Application Settings
DEPLOYMENT_ENV=production
NODE_ENV=production
LOG_LEVEL=INFO
```

### 5. Start Services

Use the provided startup script:

```bash
cd /home/qwkj/drass
chmod +x deployment/scripts/start-ubuntu-services.sh
./deployment/scripts/start-ubuntu-services.sh
```

Or manually start services:

```bash
# Start ChromaDB
python -m chromadb.app --path /home/qwkj/drass/data/chromadb --port 8005 --host 0.0.0.0 &

# Start Backend API
cd services/main-app
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 &

# Serve Frontend
cd frontend
npx serve -s dist -l 5173 &
```

### 6. Verify Deployment

Check all services are running:

```bash
# Check service ports
lsof -i :8001  # vLLM LLM
lsof -i :8010  # Embedding
lsof -i :8012  # Reranking
lsof -i :8005  # ChromaDB
lsof -i :8000  # API
lsof -i :5173  # Frontend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Test API health
curl http://localhost:8000/health

# Test LLM service
curl -X POST http://localhost:8001/v1/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 123456" \
  -d '{
    "model": "vllm",
    "prompt": "Hello, how are you?",
    "max_tokens": 50
  }'
```

### 7. Service Management

#### Start All Services
```bash
/home/qwkj/drass/deployment/scripts/start-ubuntu-services.sh
```

#### Stop Services
```bash
# Stop Drass services
pkill -f "uvicorn app.main:app"
pkill -f "chromadb.app"
pkill -f "serve -s dist"

# Stop vLLM services (if needed)
pkill -f "vllm serve"
pkill -f "vllm.entrypoints.openai.api_server"
```

#### Monitor Logs
```bash
# View logs
tail -f /home/qwkj/drass/logs/drass-api.log
tail -f /home/qwkj/drass/logs/vllm-llm.log
tail -f /home/qwkj/drass/logs/chromadb.log

# System resource monitoring
rocm-smi  # AMD GPU monitoring
htop      # CPU and memory
```

### 8. Performance Optimization

#### GPU Memory Management

The current setup uses:
- LLM: 45% GPU memory (both GPUs)
- Embedding: 30% GPU memory (both GPUs)
- Reranking: 30% GPU memory (both GPUs)

Total GPU utilization is managed to prevent OOM errors.

#### Database Optimization

```sql
-- Optimize PostgreSQL for production
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET max_connections = 200;

-- Reload configuration
SELECT pg_reload_conf();
```

#### Redis Optimization

Edit `/etc/redis/redis.conf`:

```conf
maxmemory 4gb
maxmemory-policy allkeys-lru
save ""  # Disable persistence for better performance
```

### 9. Security Considerations

1. **Firewall Configuration**
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 5173/tcp   # Frontend
sudo ufw allow 8000/tcp   # API
sudo ufw enable
```

2. **API Keys**
- Keep vLLM API keys secure
- Use environment variables for sensitive data
- Rotate keys regularly

3. **SSL/TLS Setup** (Optional)
```bash
# Install Nginx for reverse proxy with SSL
sudo apt install nginx certbot python3-certbot-nginx

# Configure Nginx (see nginx config below)
sudo certbot --nginx -d your-domain.com
```

### 10. Monitoring Setup

#### Prometheus + Grafana (Optional)
```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvf prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64
./prometheus --config.file=prometheus.yml &

# Install Grafana
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
sudo apt-get update
sudo apt-get install grafana
sudo systemctl start grafana-server
```

## Troubleshooting

### Common Issues

1. **GPU Memory Errors**
   - Reduce `gpu_memory_utilization` in vLLM services
   - Restart services to free memory

2. **Port Already in Use**
   ```bash
   # Find and kill process using port
   lsof -ti:PORT | xargs kill -9
   ```

3. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql

   # Check connection
   psql -U drass_user -h localhost -d drass_production
   ```

4. **vLLM Service Failures**
   - Check ROCm installation: `rocm-smi`
   - Verify model paths exist
   - Check GPU visibility: `echo $HIP_VISIBLE_DEVICES`

## Maintenance

### Daily Tasks
- Monitor log files for errors
- Check service health endpoints
- Monitor GPU memory usage

### Weekly Tasks
- Database backup
- Log rotation
- Update dependencies

### Backup Script
```bash
#!/bin/bash
# Backup database
pg_dump -U drass_user drass_production > /backup/drass_$(date +%Y%m%d).sql

# Backup vector store
tar czf /backup/chromadb_$(date +%Y%m%d).tar.gz /home/qwkj/drass/data/chromadb

# Backup configuration
tar czf /backup/config_$(date +%Y%m%d).tar.gz /home/qwkj/drass/.env* /home/qwkj/drass/deployment/configs/
```

## Support

For issues specific to this deployment:
1. Check logs in `/home/qwkj/drass/logs/`
2. Verify all services are running
3. Check GPU memory with `rocm-smi`
4. Review environment variables in `.env.production`