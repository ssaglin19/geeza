"""Nebius Token Factory client (OpenAI-compatible) with a deterministic mock fallback.

The key is read from the environment (NEBIUS_API_KEY) and never stored in the repo.
With no key, or when a call fails, the client answers from MockClient and sets
`used_fallback` so callers and the UI can say so honestly. Stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
MODELS = {
    "fast": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    "balanced": "nvidia/nemotron-3-super-120b-a12b",
    "deep": "nvidia/Nemotron-3-Ultra-550b-a55b",
    "lightning": "nvidia/Nemotron-3_5-Lightning",
}
DEFAULT_MODEL = MODELS["fast"]


def _unfence(text: str) -> str:
    """Accept only a single complete JSON/text fence, never extract embedded prose."""
    match = re.fullmatch(r"```(?:json|text)?[ \t]*\r?\n(.*?)\r?\n```", text.strip(), re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()


def _completion_text(payload: str) -> str:
    """Validate the response envelope before accepting nonempty assistant text."""
    data = json.loads(_unfence(payload))
    if not isinstance(data, dict):
        raise ValueError("invalid completion envelope")
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ValueError("invalid completion choices")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ValueError("invalid completion message")
    text = message.get("content")
    if not isinstance(text, str) or not _unfence(text):
        raise ValueError("empty completion")
    return _unfence(text)


class MockClient:
    """Offline stand-in. Canned, clearly labeled output so tests and demos run without a key."""

    name = "mock"

    def complete(self, messages, model=None, **kw) -> str:
        last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        if "JSON" in system and "scam" in system.lower():
            low = last.lower()
            bad = any(w in low for w in ("gift card", "wire", "verify your account", "password", "act now", "suspended"))
            return json.dumps({"is_scam": bad, "confidence": 0.9 if bad else 0.2,
                               "reasons": ["asks for money or credentials under pressure"] if bad else []})
        if "read email aloud" in system:
            body = last.split("\n\n", 1)[-1]
            return "(offline mock) " + body.split(". ")[0].strip(".") + "."
        return "(offline mock reply) I can help with that, one step at a time."


class NebiusClient:
    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL,
                 model: str = DEFAULT_MODEL, timeout: float = 30.0, opener=None, fallback=None):
        self.api_key = api_key if api_key is not None else os.environ.get("NEBIUS_API_KEY", "")
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"
        self.model = model
        self.timeout = timeout
        self._open = opener or urllib.request.urlopen
        self.fallback = fallback or MockClient()
        self.used_fallback = False
        self.last_error: str | None = None
        self.last_model: str | None = None
        self.last_error_class: str | None = None
        self.attempted = False

    @property
    def live(self) -> bool:
        return bool(self.api_key)

    def status(self) -> dict:
        """Read-only status, never an inference or a credential/error-body disclosure."""
        state = ("fallback" if self.used_fallback else "ok") if self.attempted else "not_attempted"
        return {"configured": self.live, "state": state, "exception_class": self.last_error_class}

    def complete(self, messages, model: str | None = None, temperature: float = 0.2,
                 max_tokens: int = 512) -> str:
        """Return the assistant text. Falls back to the mock on missing key or any failure."""
        model = model or self.model
        self.used_fallback, self.last_error = False, None
        self.last_error_class = None
        self.attempted = True
        if not self.api_key:
            return self._fall("no API key configured", messages, model)
        body = json.dumps({"model": model, "messages": messages,
                           "temperature": temperature, "max_tokens": max_tokens}).encode()
        req = urllib.request.Request(
            self.base_url + "chat/completions", data=body, method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        try:
            with self._open(req, timeout=self.timeout) as resp:
                text = _completion_text(resp.read().decode())
            self.last_model = model
            return text.strip()
        except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError) as e:
            # Never put the key or request headers in the error text.
            # Fixed allowlist prevents an arbitrary custom exception name becoming output.
            if isinstance(e, urllib.error.HTTPError): cls = "HTTPError"
            elif isinstance(e, urllib.error.URLError): cls = "URLError"
            elif isinstance(e, TimeoutError): cls = "TimeoutError"
            elif isinstance(e, OSError): cls = "OSError"
            elif isinstance(e, KeyError): cls = "KeyError"
            elif isinstance(e, IndexError): cls = "IndexError"
            else: cls = "ValueError"
            self.last_error_class = cls
            print("Geeza model fallback exception_class=" + cls, file=sys.stderr, flush=True)
            return self._fall(cls, messages, model)

    def _fall(self, why: str, messages, model) -> str:
        self.used_fallback, self.last_error, self.last_model = True, why, "mock"
        return self.fallback.complete(messages, model)
