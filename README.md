# Drass - Data Regulation Assistant

A comprehensive Dify project configuration and management system for data regulation compliance applications.

## Overview

Drass is a Dify project that provides a structured approach to configuring and managing Dify applications, particularly focused on data regulation and compliance assistance. The project includes configuration templates, deployment scripts, and validation tools to streamline the development and deployment of Dify applications.

## Project Structure

```
drass/
├── config/                          # Configuration files
│   ├── dify-config.yaml            # Main project configuration
│   └── environments/               # Environment-specific configs
│       ├── development.yaml        # Development environment
│       └── production.yaml         # Production environment
├── apps/                           # Application definitions
│   └── data-regulation-assistant.yaml  # Main application config
├── templates/                      # Reusable configuration templates
│   ├── basic-application.yaml     # Basic app template
│   └── workflow-template.yaml     # Workflow template
├── scripts/                        # Automation and utility scripts
│   ├── deploy.py                  # Deployment automation
│   ├── validate.py                # Configuration validation
│   └── run_qwen3_mlx.sh          # Start local LLM service
├── services/                       # Microservices
│   └── embedding-service/         # Text embedding service
│       ├── app.py                 # FastAPI application
│       ├── requirements.txt       # Python dependencies
│       └── .env                   # Service configuration
├── docs/                          # Documentation
│   ├── TODO                       # Project tasks and progress
│   ├── EMBEDDING_SERVICE_DEPLOYMENT.md  # Embedding setup guide
│   └── LOCAL_LLM_EMBEDDING_SETUP.md     # Local services setup
└── qwen3_api_server.py            # Local LLM API server
```

## Features

- **Environment Management**: Separate configurations for development, staging, and production
- **Application Templates**: Reusable templates for quick application setup
- **Workflow Configuration**: Structured workflow definitions with error handling
- **Automated Deployment**: Python scripts for deploying applications to Dify
- **Configuration Validation**: Tools to validate YAML configuration files
- **Security**: Environment variable support for sensitive configuration
- **Local LLM Service**: Qwen3-8B-MLX model optimized for Apple Silicon (Port 8001)
- **Embedding Service**: Local text embedding with sentence-transformers (Port 8002)

## Quick Start

### 🚀 One-Click Startup (NEW!)

For immediate testing with UI:

```bash
# Start all services with one command (LLM + Backend + Frontend)
./start-simple.sh

# Open browser and navigate to http://localhost:3000
# Stop all services when done
./stop-services.sh
```

For detailed startup options, see [One-Click Startup Guide](docs/ONE_CLICK_STARTUP_GUIDE.md).

### Traditional Setup

### 1. Prerequisites

- Python 3.7+
- Dify platform access
- Required environment variables (see Configuration section)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd drass

# Install Python dependencies
pip install pyyaml requests
```

### 3. Configuration

1. **Set Environment Variables**:
   ```bash
   export DIFY_PLATFORM_URL="your-dify-platform-url"
   export DIFY_API_KEY="your-api-key"
   export DIFY_WORKSPACE_ID="your-workspace-id"
   ```

2. **Customize Configuration**:
   - Edit `config/dify-config.yaml` for project settings
   - Modify `config/environments/` files for environment-specific settings
   - Update `apps/` files for application configurations

### 4. Validation

```bash
# Validate all configurations
python scripts/validate.py --all

# Validate specific file
python scripts/validate.py --file config/dify-config.yaml

# Validate specific directory
python scripts/validate.py --directory apps
```

### 5. Deployment

```bash
# Deploy all applications
python scripts/deploy.py --environment development

# Deploy specific application
python scripts/deploy.py --app apps/data-regulation-assistant.yaml

# Deploy to production
python scripts/deploy.py --environment production
```

## Configuration

### Main Configuration (`config/dify-config.yaml`)

The main configuration file contains:
- Project metadata
- Dify platform settings
- Application defaults
- Security configurations
- Logging settings

### Environment Configurations

Environment-specific files in `config/environments/`:
- **Development**: Local development settings with debug enabled
- **Production**: Production settings with security and performance optimizations

### Application Configuration

Application files in `apps/` define:
- Application metadata
- Workflow configurations
- Knowledge base settings
- API endpoint definitions
- Security and access control

### Templates

Reusable templates in `templates/`:
- **Basic Application**: Starting point for new applications
- **Workflow Template**: Standard workflow structure with error handling

## Scripts

### `scripts/deploy.py`

Deployment automation script with features:
- Environment-specific deployment
- Single or bulk application deployment
- Configuration validation before deployment
- Deployment status reporting

### `scripts/validate.py`

Configuration validation script that checks:
- YAML syntax validity
- Required field presence
- Data type validation
- Configuration structure compliance

## Usage Examples

### Creating a New Application

1. Copy the basic template:
   ```bash
   cp templates/basic-application.yaml apps/my-new-app.yaml
   ```

2. Customize the template variables:
   ```yaml
   application:
     name: "My New App"
     description: "Description of my new application"
     category: "custom"
   ```

3. Validate the configuration:
   ```bash
   python scripts/validate.py --file apps/my-new-app.yaml
   ```

4. Deploy the application:
   ```bash
   python scripts/deploy.py --app apps/my-new-app.yaml
   ```

### Environment-Specific Deployment

```bash
# Development deployment
python scripts/deploy.py --environment development

# Production deployment
python scripts/deploy.py --environment production
```

## Security Considerations

- **Environment Variables**: Sensitive data stored in environment variables
- **Encryption**: Configuration supports encryption for sensitive data
- **Access Control**: Role-based permissions for application access
- **Audit Logging**: Comprehensive logging for compliance requirements

## Contributing

1. Follow the existing configuration structure
2. Validate all configurations before committing
3. Update documentation for new features
4. Test deployments in development environment first

## Troubleshooting

### Common Issues

1. **Configuration Validation Errors**:
   - Check YAML syntax
   - Verify required fields are present
   - Ensure data types are correct

2. **Deployment Failures**:
   - Verify environment variables are set
   - Check Dify platform connectivity
   - Review application configuration

3. **Environment Issues**:
   - Confirm environment file exists
   - Check environment variable references
   - Validate environment-specific settings

### Getting Help

- Run validation scripts to identify issues
- Check configuration file syntax
- Verify environment variable values
- Review Dify platform logs

## License

This project is licensed under the terms specified in the LICENSE file.

## Support

For issues and questions:
1. Check the configuration validation output
2. Review the troubleshooting section
3. Validate environment configurations
4. Check Dify platform status
