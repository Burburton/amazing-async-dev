"""Local webhook test server for Resend inbound emails."""

import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

from http.server import HTTPServer, BaseHTTPRequestHandler
from runtime.resend_provider import ResendWebhookHandler


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/webhooks/resend':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                payload = json.loads(body.decode('utf-8'))
                handler = ResendWebhookHandler()
                result = handler.handle_event(payload)
                
                print(f"\nReceived webhook: {payload.get('type')}")
                print(f"Result: {json.dumps(result, indent=2)}")
                
                if payload.get('type') == 'email.received':
                    reply = handler.parse_reply_from_payload(payload)
                    print(f"\nParsed Reply:")
                    print(f"  Decision Request ID: {reply.get('decision_request_id')}")
                    print(f"  Reply Text: {reply.get('reply_text')}")
                    print(f"  From: {reply.get('from')}")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok'}).encode())
                
            except Exception as e:
                print(f"Error: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    print("Starting webhook test server on http://localhost:8080")
    print("Endpoint: http://localhost:8080/webhooks/resend")
    print("Press Ctrl+C to stop")
    print()
    
    server = HTTPServer(('localhost', 8080), WebhookHandler)
    server.serve_forever()