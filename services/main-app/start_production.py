#!/usr/bin/env python3
"""
Production startup script for Drass API
This ensures the API starts correctly without import issues
"""

import sys
import os
import time

print("=== Starting Drass API (Production Mode) ===")
print(f"Python: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Ensure we're in the right directory
expected_dir = "/home/qwkj/drass/services/main-app"
if os.getcwd() != expected_dir:
    print(f"Changing directory to {expected_dir}")
    os.chdir(expected_dir)

# Set environment variables
os.environ["PORT"] = "8888"
os.environ["HOST"] = "0.0.0.0"

# Import uvicorn only after setup
try:
    import uvicorn
    print(f"Uvicorn version: {uvicorn.__version__}")
except ImportError:
    print("ERROR: uvicorn not installed!")
    sys.exit(1)

# Start the server
print("Starting server on 0.0.0.0:8888...")
try:
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8888,
        workers=1,
        loop="asyncio",
        log_level="info"
    )
except Exception as e:
    print(f"ERROR: Failed to start server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)