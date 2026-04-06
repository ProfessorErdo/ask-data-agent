# Vercel Python API Handler
# This file handles API requests for Vercel deployment

import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Import the backend logic
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Note: For full Vercel deployment, you need to ensure all dependencies
# are available. Consider using a separate hosting for the backend.

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/models':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "models": [
                    {"name": "gemma3:4b"},
                    {"name": "gemma3:12b"},
                    {"name": "qwen3:8b"}
                ]
            }).encode())
        elif self.path == '/api/brd-template':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"content": "# BRD Template\n\nProject Overview..."}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "response": "This is a placeholder. For full functionality, deploy the backend separately."
            }).encode())
        elif self.path == '/api/export-brd':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"filename": "placeholder.md"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()