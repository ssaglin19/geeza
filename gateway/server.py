#!/usr/bin/env python3
"""
Boosh Gateway — local HTTP server that bridges text messages to the Boosh stack.

Runs on localhost (or LAN with token auth). Receives POSTs from the iOS
Shortcut, processes messages through System 0/1/2, returns responses.

Usage:
  python gateway/server.py [--port 8080] [--host 127.0.0.1] [--token SECRET]
"""

import argparse
import json
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sys

# Add engine to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

from boosh_flow.intent_router_hybrid import route_intent, IntentAction


class BooshGateway(BaseHTTPRequestHandler):
    """HTTP request handler for the Boosh gateway."""

    # Class-level config (set by run_server)
    config = {
        "token": None,
        "available_flows": ["consumers-energy-pay", "kroger-grocery-order"],
    }

    def log_message(self, format, *args):
        """Suppress default logging; use our own."""
        pass

    def _send_json(self, data, status=200):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_error(self, message, status=400):
        """Send an error response."""
        self._send_json({"error": message}, status)

    def _check_auth(self):
        """Check the X-Boosh-Token header if a token is configured."""
        if self.config["token"] is None:
            return True  # localhost, no auth needed
        token = self.headers.get("X-Boosh-Token")
        return token == self.config["token"]

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self._send_json({"status": "ok", "timestamp": time.time()})
        elif self.path == "/config":
            if not self._check_auth():
                self._send_error("unauthorized", 401)
                return
            self._send_json({
                "available_flows": self.config["available_flows"],
                "version": "0.1.0",
            })
        else:
            self._send_error("not found", 404)

    def do_POST(self):
        """Handle POST requests."""
        if self.path != "/message":
            self._send_error("not found", 404)
            return

        if not self._check_auth():
            self._send_error("unauthorized", 401)
            return

        # Parse request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_error("invalid JSON", 400)
            return

        # Validate required fields
        text = data.get("text", "").strip()
        if not text:
            self._send_error("missing 'text' field", 400)
            return

        sender = data.get("sender", "unknown")
        message_id = data.get("message_id", str(uuid.uuid4()))

        # Process the message
        response = self._process_message(text, sender, message_id)
        self._send_json(response)

    def _process_message(self, text, sender, message_id):
        """Route a message through the Boosh stack."""
        # Emergency bypass
        if any(kw in text.lower() for kw in ["help", "911", "emergency", "fell", "can't get up", "chest pain"]):
            return {
                "response": "Calling 911 now. Stay on the line.",
                "actions": [{"type": "emergency_call", "number": "911"}],
                "confidence": 1.0,
                "message_id": message_id,
            }

        # Scam screen (if we had Laya loaded — placeholder for now)
        # TODO: integrate Laya scam screen when fine-tuned model is available

        # Intent routing
        result = route_intent(
            laya_skill="general_help",  # placeholder until Laya is integrated
            laya_confidence=0.5,
            laya_probs={},
            text=text,
            available_flows=set(self.config["available_flows"]),
        )

        # Build response based on action
        if result.action == IntentAction.EMERGENCY:
            return {
                "response": result.message,
                "actions": [{"type": "emergency_call", "number": "911"}],
                "confidence": 1.0,
                "message_id": message_id,
            }

        if result.action == IntentAction.LAUNCH_FLOW:
            return {
                "response": f"I can help you {result.skill.replace('_', ' ')}. "
                           f"Say 'yes' to start, or ask me something else.",
                "actions": [{
                    "type": "flow_offer",
                    "flow_id": result.flow_id,
                    "skill": result.skill,
                }],
                "confidence": result.confidence,
                "message_id": message_id,
            }

        if result.action == IntentAction.ASK_CLARIFY:
            return {
                "response": result.message,
                "actions": [{
                    "type": "clarify",
                    "skill": result.skill,
                    "alternatives": result.alternatives,
                }],
                "confidence": result.confidence,
                "message_id": message_id,
            }

        # CHAT_FALLBACK — pass to LLM (placeholder)
        return {
            "response": f"I heard: \"{text}\". I'm still learning — "
                       f"for now I can help with bills, family calls, and emergencies.",
            "actions": [],
            "confidence": 0.5,
            "message_id": message_id,
        }


def run_server(host="127.0.0.1", port=8080, token=None):
    """Start the Boosh gateway server."""
    BooshGateway.config["token"] = token
    server = HTTPServer((host, port), BooshGateway)
    print(f"Boosh Gateway running on http://{host}:{port}")
    print(f"  Health check: http://{host}:{port}/health")
    print(f"  Token auth: {'enabled' if token else 'disabled (localhost only)'}")
    print(f"  Available flows: {BooshGateway.config['available_flows']}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--token", default=None, help="Shared secret for LAN auth")
    args = ap.parse_args()
    run_server(args.host, args.port, args.token)
