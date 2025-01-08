import http.server
import socketserver
import json
import os
from urllib.parse import parse_qs, urlparse
from utils.db import db
from utils.git_handler import git_handler
from datetime import datetime

# Constants
PORT = 5002  # Changed port to avoid conflicts
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
        print(f"Attempting to serve file: {filepath}")  # Debug logging
        try:
            with open(filepath, 'r', encoding='utf-8') as f:  
                content = f.read()
                print(f"File content length: {len(content)}")  # Debug logging
                self.send_response(200)
                
                # Set content type based on file extension
                if filepath.endswith('.css'):
                    content_type = 'text/css'
                elif filepath.endswith('.js'):
                    content_type = 'application/javascript'
                elif filepath.endswith('.html'):
                    content_type = 'text/html; charset=utf-8'  
                else:
                    content_type = 'text/plain'
                
                print(f"Serving file with content type: {content_type}")  # Debug logging
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', len(content.encode('utf-8')))  
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))  
                print("File served successfully")  # Debug logging
        except FileNotFoundError:
            print(f"File not found: {filepath}")  # Debug logging
            self.send_error(404, 'File not found')
        except Exception as e:
            print(f"Error serving file: {str(e)}")  # Debug logging
            self.send_error(500, f'Server error: {str(e)}')

    def do_GET(self):
        """Handle GET requests."""
        print(f"\nReceived GET request for path: {self.path}")  # Debug logging
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Serve index.html for root path
        if path == '/':
            print("Serving index.html")  # Debug logging
            filepath = os.path.join(TEMPLATES_DIR, 'index.html')
            print(f"Looking for index.html at: {filepath}")  # Debug logging
            if os.path.exists(filepath):
                print(f"Found index.html at {filepath}")  # Debug logging
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"Content length: {len(content)}")
                        print("First 100 chars:", content[:100])
                    self._serve_static_file(filepath)
                except Exception as e:
                    print(f"Error reading file: {str(e)}")
            else:
                print(f"index.html not found at {filepath}")  # Debug logging
                self.send_error(404, 'File not found')
            return
            
        # Serve static files
        if path.startswith('/static/'):
            print(f"Serving static file: {path}")  # Debug logging
            filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), path[1:])
            print(f"Looking for static file at: {filepath}")  # Debug logging
            if os.path.exists(filepath):
                print(f"Found static file at {filepath}")  # Debug logging
            else:
                print(f"Static file not found at {filepath}")  # Debug logging
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
            return
            
        # Handle other POST endpoints here
        self.send_error(404, 'Endpoint not found')

def run_server():
    """Start the HTTP server."""
    try:
        print(f"Starting server on port {PORT}...")
        server_address = ('localhost', PORT)  
        class TCPServerReusable(http.server.HTTPServer):
            allow_reuse_address = True  
            
        httpd = TCPServerReusable(server_address, ChatRequestHandler)
        print(f"Server running at http://localhost:{PORT}")
        httpd.serve_forever()
    except Exception as e:
        print(f"Failed to start server: {str(e)}")
        raise

if __name__ == "__main__":
    run_server()
