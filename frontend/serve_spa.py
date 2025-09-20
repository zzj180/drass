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
        path = self.translate_path(self.path)
        if not os.path.exists(path) or os.path.isdir(path):
            self.path = '/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, format, *args):
        if '/assets/' not in args[0]:
            super().log_message(format, *args)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with socketserver.TCPServer(("0.0.0.0", PORT), SPAHandler) as httpd:
    print(f"Frontend server running at http://0.0.0.0:{PORT}/")
    httpd.serve_forever()
