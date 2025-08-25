#!/usr/bin/env python3
"""
Docker Manager Script for Drass Dify Application
Manages Docker containers, services, and deployment operations.
"""

import os
import sys
import subprocess
import argparse
import yaml
from pathlib import Path
from typing import List, Dict, Any

class DockerManager:
    def __init__(self, compose_file: str = "docker-compose.yml"):
        self.compose_file = compose_file
        self.project_name = "drass"
        
    def run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command and return the result."""
        try:
            result = subprocess.run(command, check=check, capture_output=True, text=True)
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(command)}")
            print(f"Error: {e.stderr}")
            if check:
                sys.exit(1)
            return e
    
    def build_images(self, service: str = None) -> bool:
        """Build Docker images."""
        print("🔨 Building Docker images...")
        
        cmd = ["docker-compose", "-f", self.compose_file, "build"]
        if service:
            cmd.append(service)
        
        result = self.run_command(cmd, check=False)
        if result.returncode == 0:
            print("✅ Images built successfully")
            return True
        else:
            print("❌ Failed to build images")
            return False
    
    def start_services(self, profile: str = None) -> bool:
        """Start Docker services."""
        print("🚀 Starting Docker services...")
        
        cmd = ["docker-compose", "-f", self.compose_file, "up", "-d"]
        if profile:
            cmd.extend(["--profile", profile])
        
        result = self.run_command(cmd, check=False)
        if result.returncode == 0:
            print("✅ Services started successfully")
            return True
        else:
            print("❌ Failed to start services")
            return False
    
    def stop_services(self) -> bool:
        """Stop Docker services."""
        print("🛑 Stopping Docker services...")
        
        cmd = ["docker-compose", "-f", self.compose_file, "down"]
        result = self.run_command(cmd, check=False)
        if result.returncode == 0:
            print("✅ Services stopped successfully")
            return True
        else:
            print("❌ Failed to stop services")
            return False
    
    def restart_services(self) -> bool:
        """Restart Docker services."""
        print("🔄 Restarting Docker services...")
        
        if self.stop_services():
            return self.start_services()
        return False
    
    def show_status(self) -> None:
        """Show status of Docker services."""
        print("📊 Docker services status:")
        
        cmd = ["docker-compose", "-f", self.compose_file, "ps"]
        result = self.run_command(cmd, check=False)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("❌ Failed to get service status")
    
    def show_logs(self, service: str = None, follow: bool = False) -> None:
        """Show logs for services."""
        cmd = ["docker-compose", "-f", self.compose_file, "logs"]
        
        if follow:
            cmd.append("-f")
        if service:
            cmd.append(service)
        
        # For logs, we don't want to capture output
        try:
            subprocess.run(cmd, check=False)
        except KeyboardInterrupt:
            print("\n📝 Log viewing stopped")
    
    def clean_up(self) -> bool:
        """Clean up Docker resources."""
        print("🧹 Cleaning up Docker resources...")
        
        # Stop and remove containers
        self.stop_services()
        
        # Remove volumes
        cmd = ["docker-compose", "-f", self.compose_file, "down", "-v"]
        result = self.run_command(cmd, check=False)
        
        # Remove images
        cmd = ["docker", "image", "prune", "-f"]
        self.run_command(cmd, check=False)
        
        print("✅ Cleanup completed")
        return True
    
    def deploy(self, environment: str = "development") -> bool:
        """Deploy the application."""
        print(f"🚀 Deploying to {environment} environment...")
        
        # Build images
        if not self.build_images():
            return False
        
        # Start services with appropriate profile
        profile_map = {
            "development": None,  # No profile restriction
            "production": "app",
            "monitoring": "monitoring"
        }
        
        profile = profile_map.get(environment)
        if not self.start_services(profile):
            return False
        
        print(f"✅ Deployment to {environment} completed successfully")
        return True

def main():
    parser = argparse.ArgumentParser(description="Docker Manager for Drass Dify Application")
    parser.add_argument("action", choices=[
        "build", "start", "stop", "restart", "status", "logs", "cleanup", "deploy"
    ], help="Action to perform")
    parser.add_argument("--service", "-s", help="Specific service name")
    parser.add_argument("--profile", "-p", help="Docker Compose profile")
    parser.add_argument("--environment", "-e", default="development", 
                       choices=["development", "production", "monitoring"],
                       help="Deployment environment")
    parser.add_argument("--follow", "-f", action="store_true", help="Follow logs")
    parser.add_argument("--compose-file", "-c", default="docker-compose.yml",
                       help="Docker Compose file to use")
    
    args = parser.parse_args()
    
    manager = DockerManager(args.compose_file)
    
    if args.action == "build":
        manager.build_images(args.service)
    elif args.action == "start":
        manager.start_services(args.profile)
    elif args.action == "stop":
        manager.stop_services()
    elif args.action == "restart":
        manager.restart_services()
    elif args.action == "status":
        manager.show_status()
    elif args.action == "logs":
        manager.show_logs(args.service, args.follow)
    elif args.action == "cleanup":
        manager.clean_up()
    elif args.action == "deploy":
        manager.deploy(args.environment)

if __name__ == "__main__":
    main()
