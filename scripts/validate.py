#!/usr/bin/env python3
"""
Dify Configuration Validation Script
Validates YAML configuration files for syntax and structure.
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

class DifyConfigValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def validate_file(self, file_path: str) -> bool:
        """Validate a single configuration file."""
        try:
            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                self.errors.append(f"{file_path}: File is empty or contains only comments")
                return False
            
            # Validate based on file type
            if "application" in config:
                return self._validate_application_config(config, file_path)
            elif "workflow" in config:
                return self._validate_workflow_config(config, file_path)
            elif "project" in config:
                return self._validate_project_config(config, file_path)
            elif "environment" in config:
                return self._validate_environment_config(config, file_path)
            else:
                self.warnings.append(f"{file_path}: Unknown configuration type")
                return True
                
        except FileNotFoundError:
            self.errors.append(f"{file_path}: File not found")
            return False
        except yaml.YAMLError as e:
            self.errors.append(f"{file_path}: YAML syntax error - {e}")
            return False
        except Exception as e:
            self.errors.append(f"{file_path}: Unexpected error - {e}")
            return False
    
    def _validate_application_config(self, config: Dict[str, Any], file_path: str) -> bool:
        """Validate application configuration."""
        required_fields = ["application", "settings", "workflow"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            self.errors.append(f"{file_path}: Missing required fields: {missing_fields}")
            return False
        
        # Validate application section
        app = config["application"]
        if not isinstance(app.get("name"), str):
            self.errors.append(f"{file_path}: Application name must be a string")
            return False
        
        if not isinstance(app.get("description"), str):
            self.errors.append(f"{file_path}: Application description must be a string")
            return False
        
        # Validate settings section
        settings = config["settings"]
        if not isinstance(settings.get("language"), str):
            self.errors.append(f"{file_path}: Language must be a string")
            return False
        
        if not isinstance(settings.get("default_model"), str):
            self.errors.append(f"{file_path}: Default model must be a string")
            return False
        
        return True
    
    def _validate_workflow_config(self, config: Dict[str, Any], file_path: str) -> bool:
        """Validate workflow configuration."""
        required_fields = ["workflow", "steps"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            self.errors.append(f"{file_path}: Missing required fields: {missing_fields}")
            return False
        
        workflow = config["workflow"]
        if not isinstance(workflow.get("name"), str):
            self.errors.append(f"{file_path}: Workflow name must be a string")
            return False
        
        steps = config["steps"]
        if not isinstance(steps, list):
            self.errors.append(f"{file_path}: Steps must be a list")
            return False
        
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                self.errors.append(f"{file_path}: Step {i} must be a dictionary")
                return False
            
            if "name" not in step:
                self.errors.append(f"{file_path}: Step {i} missing name")
                return False
        
        return True
    
    def _validate_project_config(self, config: Dict[str, Any], file_path: str) -> bool:
        """Validate project configuration."""
        required_fields = ["project", "dify"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            self.errors.append(f"{file_path}: Missing required fields: {missing_fields}")
            return False
        
        project = config["project"]
        if not isinstance(project.get("name"), str):
            self.errors.append(f"{file_path}: Project name must be a string")
            return False
        
        return True
    
    def _validate_environment_config(self, config: Dict[str, Any], file_path: str) -> bool:
        """Validate environment configuration."""
        if "environment" not in config:
            self.errors.append(f"{file_path}: Missing environment field")
            return False
        
        if not isinstance(config["environment"], str):
            self.errors.append(f"{file_path}: Environment must be a string")
            return False
        
        return True
    
    def validate_directory(self, directory: str) -> bool:
        """Validate all YAML files in a directory."""
        dir_path = Path(directory)
        if not dir_path.exists():
            self.errors.append(f"Directory not found: {directory}")
            return False
        
        yaml_files = list(dir_path.glob("*.yaml")) + list(dir_path.glob("*.yml"))
        if not yaml_files:
            self.warnings.append(f"No YAML files found in {directory}")
            return True
        
        print(f"Validating {len(yaml_files)} files in {directory}")
        
        all_valid = True
        for yaml_file in yaml_files:
            if not self.validate_file(str(yaml_file)):
                all_valid = False
        
        return all_valid
    
    def print_results(self):
        """Print validation results."""
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All configurations are valid!")
        elif not self.errors:
            print("\n✅ All configurations are valid (with warnings)")
        else:
            print(f"\n❌ Found {len(self.errors)} error(s)")

def main():
    parser = argparse.ArgumentParser(description="Validate Dify configuration files")
    parser.add_argument("--file", "-f", help="Validate specific file")
    parser.add_argument("--directory", "-d", help="Validate all YAML files in directory")
    parser.add_argument("--all", "-a", action="store_true", 
                       help="Validate all configuration directories")
    
    args = parser.parse_args()
    
    validator = DifyConfigValidator()
    
    if args.file:
        # Validate specific file
        success = validator.validate_file(args.file)
        validator.print_results()
        sys.exit(0 if success else 1)
    
    elif args.directory:
        # Validate specific directory
        success = validator.validate_directory(args.directory)
        validator.print_results()
        sys.exit(0 if success else 1)
    
    elif args.all:
        # Validate all configuration directories
        directories = ["config", "apps", "templates"]
        all_valid = True
        
        for directory in directories:
            if Path(directory).exists():
                if not validator.validate_directory(directory):
                    all_valid = False
        
        validator.print_results()
        sys.exit(0 if all_valid else 1)
    
    else:
        # Default: validate all configuration directories
        directories = ["config", "apps", "templates"]
        all_valid = True
        
        for directory in directories:
            if Path(directory).exists():
                if not validator.validate_directory(directory):
                    all_valid = False
        
        validator.print_results()
        sys.exit(0 if all_valid else 1)

if __name__ == "__main__":
    main()
