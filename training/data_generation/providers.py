"""Optional synthetic-only text provider clients; never pass real resumes here."""

from __future__ import annotations

import json
import os
import urllib.request
from urllib.parse import urlparse


def generate_synthetic_text(prompt: str, *, synthetic: bool) -> str:
    if not synthetic:
        raise ValueError("external generation is restricted to synthetic taxonomy seeds")
    provider = os.getenv("DATA_GENERATION_PROVIDER", "template").lower()
    if provider == "template":
        return prompt
    if provider == "ollama":
        url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "127.0.0.1",
            "localhost",
            "::1",
        }:
            raise ValueError("OLLAMA_URL must be a loopback HTTP(S) URL")
        payload = {
            "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
            "prompt": prompt,
            "stream": False,
        }
        request = urllib.request.Request(
            url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=120) as response:  # nosec B310
            return str(json.load(response)["response"])
    if provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OPENROUTER_API_KEY is required")
        payload = {
            "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=120) as response:  # nosec B310
            return str(json.load(response)["choices"][0]["message"]["content"])
    raise ValueError("DATA_GENERATION_PROVIDER must be template, ollama, or openrouter")
