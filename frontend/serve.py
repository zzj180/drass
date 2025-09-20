#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys
from pathlib import Path

PORT = 5173
DIRECTORY = "dist"

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Get the requested path
        path = self.translate_path(self.path)

        # If path doesn't exist or is a directory, serve index.html
        if not os.path.exists(path) or os.path.isdir(path):
            self.path = '/index.html'

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, format, *args):
        # Reduce verbosity
        if '/assets/' not in args[0]:
            super().log_message(format, *args)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

Handler = SPAHandler

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Server running at http://0.0.0.0:{PORT}/")
    print(f"Local URL: http://localhost:{PORT}/")
    print("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
