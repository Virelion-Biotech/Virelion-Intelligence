from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class LLMClient:
    base_url: str
    api_key: str
    model: str
    timeout: float = 90.0

    @classmethod
    def from_env(cls) -> "LLMClient | None":
        key = os.getenv("VIRELION_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not key:
            return None
        return cls(
            base_url=os.getenv("VIRELION_LLM_BASE_URL") or "https://api.openai.com/v1",
            api_key=key,
            model=os.getenv("VIRELION_LLM_MODEL") or "gpt-5",
        )

    def chat(self, messages: list[dict[str, str]], *, json_mode: bool = False) -> str:
        payload: dict[str, Any] = {"model": self.model, "messages": messages}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
        return str(body["choices"][0]["message"]["content"])

    def json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        text = self.chat(messages, json_mode=True)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM returned invalid JSON") from exc
