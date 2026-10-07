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
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from boosh_flow.intent_router_hybrid import route_intent, IntentAction

STATIC = Path(__file__).resolve().parent / "static"


_HITS: dict[str, list] = {}


def _rate_ok(ip: str, limit: int = 60, window: float = 3600.0) -> bool:
    """Demo guard so a public URL cannot burn the Nebius credits. 60 messages/hour per IP."""
    now = time.time()
    hits = [t for t in _HITS.get(ip, []) if now - t < window]
    if len(hits) >= limit:
        _HITS[ip] = hits
        return False
    hits.append(now)
    _HITS[ip] = hits
    return True


class BooshGateway(BaseHTTPRequestHandler):
    """HTTP request handler for the Boosh gateway."""

    # Class-level config (set by run_server)
    config = {
        "token": None,
        "available_flows": ["consumers-energy-pay", "kroger-grocery-order"],
        "assistant": None,  # set by run_server(demo=True): Nemotron-backed System 2 + engine demo
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
        if self.path in ("/", "/index.html") and self.config["assistant"]:
            body = (STATIC / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/status" and self.config["assistant"]:
            c = self.config["assistant"].client
            self._send_json({"nebius_live": c.live, "model": c.model, "project": "Geeza"})
        elif self.path == "/health":
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
        if self.path not in ("/message", "/api/scenario"):
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

        if self.path == "/api/scenario":
            a = self.config["assistant"]
            if not a or data.get("scenario") not in ("normal", "suspicious"):
                self._send_error("bad scenario", 400)
                return
            a.scenario = data["scenario"]
            a.pending.clear()
            self._send_json({"scenario": a.scenario})
            return

        # Validate required fields
        text = data.get("text", "").strip()
        if not text:
            self._send_error("missing 'text' field", 400)
            return

        if self.config["assistant"]:
            if len(text) > 500:
                self._send_error("message too long", 400)
                return
            if not _rate_ok(self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()):
                self._send_error("slow down: demo limit reached, try again later", 429)
                return
        sender = data.get("sender", "unknown")
        message_id = data.get("message_id", str(uuid.uuid4()))

        # Process the message
        response = self._process_message(text, sender, message_id)
        self._send_json(response)

    def _process_message(self, text, sender, message_id):
        """Route a message through the Boosh stack."""
        # Emergency bypass
        from gateway import emergency_sim
        if emergency_sim.is_emergency(text):
            if self.config["assistant"]:
                # Demo: a labelled simulated dispatcher. Nothing is dialed (see gateway/emergency_sim.py).
                out = emergency_sim.respond(text)
                out["message_id"] = message_id
                return out
            return {
                "response": "Calling 911 now. Stay on the line.",
                "actions": [{"type": "emergency_call", "number": "911"}],
                "confidence": 1.0,
                "message_id": message_id,
            }

        # Demo mode: Nemotron-backed assistant answers everything the emergency bypass did not.
        if self.config["assistant"]:
            out = self.config["assistant"].handle(text, sender)
            out["message_id"] = message_id
            return out

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


def run_server(host="127.0.0.1", port=8080, token=None, demo=False):
    """Start the Boosh gateway server. demo=True wires in the Nemotron assistant (key from NEBIUS_API_KEY)."""
    BooshGateway.config["token"] = token
    if demo:
        from boosh_flow.nebius import NebiusClient
        from gateway.assistant import Assistant
        BooshGateway.config["assistant"] = Assistant(NebiusClient())
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
    ap.add_argument("--demo", action="store_true", help="serve the Geeza web demo with the Nemotron assistant")
    args = ap.parse_args()
    run_server(args.host, args.port, args.token, args.demo)
