import http.server
import socketserver
import json
import os
from urllib.parse import parse_qs, urlparse
from utils.db import db
from utils.git_handler import git_handler
from datetime import datetime

# Constants
PORT = 8081
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

class ChatRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for the chat application."""
    
    def _send_cors_headers(self):
        """Send headers for CORS support."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _serve_static_file(self, filepath):
        """Serve static files (CSS, JS, etc.)."""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
                self.send_response(200)
                
                # Set content type based on file extension
                if filepath.endswith('.css'):
                    self.send_header('Content-Type', 'text/css')
                elif filepath.endswith('.js'):
                    self.send_header('Content-Type', 'application/javascript')
                elif filepath.endswith('.html'):
                    self.send_header('Content-Type', 'text/html')
                    
                self.send_header('Content-Length', len(content))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, 'File not found')

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Serve index.html for root path
        if path == '/':
            self._serve_static_file(os.path.join(TEMPLATES_DIR, 'index.html'))
            return
            
        # Serve static files
        if path.startswith('/static/'):
            relative_path = path[8:]  # Remove '/static/' prefix
            filepath = os.path.join(STATIC_DIR, relative_path)
            self._serve_static_file(filepath)
            return
            
        # API endpoint to get messages
        if path == '/api/messages':
            try:
                # Parse query parameters
                query = parse_qs(parsed_path.query)
                limit = int(query.get('limit', [50])[0])
                offset = int(query.get('offset', [0])[0])
                
                # Get messages from database
                messages = db.get_messages(limit=limit, offset=offset)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self._send_cors_headers()
                self.end_headers()
                
                response = {
                    'messages': messages,
                    'count': len(messages),
                    'limit': limit,
                    'offset': offset
                }
                
                self.wfile.write(json.dumps(response).encode())
                return
                
            except ValueError as e:
                self.send_error(400, f'Invalid query parameters: {str(e)}')
                return
            except Exception as e:
                print(f"Error retrieving messages: {str(e)}")
                self.send_error(500, f'Server error: {str(e)}')
                return
        
        # If path not recognized, return 404
        self.send_error(404, 'Path not found')

    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/api/messages':
            try:
                # Get content length
                content_length = int(self.headers['Content-Length'])
                
                # Read and parse request body
                body = self.rfile.read(content_length)
                data = json.loads(body)
                
                # Validate request
                if 'content' not in data:
                    self.send_error(400, 'Missing content field')
                    return
                
                # Create message in database
                message_id = db.create_message(data['content'])
                
                # Sync message to GitHub
                commit_hash = git_handler.sync_message(message_id, data['content'])
                
                # Update sync status
                db.update_sync_status(message_id, commit_hash)
                
                # Get updated message
                message = db.get_message(message_id)
                
                # Send response
                self.send_response(201)  # Changed from 200 to 201 for resource creation
                self.send_header('Content-Type', 'application/json')
                self._send_cors_headers()
                self.end_headers()
                
                self.wfile.write(json.dumps(message).encode())
                
            except json.JSONDecodeError:
                self.send_error(400, 'Invalid JSON')
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                self.send_error(500, f'Server error: {str(e)}')
            
        # Handle other POST endpoints here
        self.send_error(404, 'Endpoint not found')

def run_server():
    """Start the HTTP server."""
    class TCPServerReusable(socketserver.TCPServer):
        allow_reuse_address = True
    
    with TCPServerReusable(("", PORT), ChatRequestHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
