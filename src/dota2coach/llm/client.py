"""DeepSeek（OpenAI 兼容）客户端：只用于离线总结攻略，不参与对局内决策。"""

from __future__ import annotations

import json
import os
from typing import Any

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"


class LlmError(RuntimeError):
    pass


class LlmClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 90.0,
        http: Any = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._http = http

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _client(self):
        if self._http is None:  # pragma: no cover - 真实网络
            import httpx

            self._http = httpx.Client(timeout=self.timeout)
        return self._http

    def ping(self) -> str:
        """轻量自检：只请求 /models，返回一句人话（不打印 key 本身）。"""
        if not self.api_key:
            return "未设置 DEEPSEEK_API_KEY"
        try:
            response = self._client().get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        except Exception as exc:  # noqa: BLE001
            return f"网络失败：{exc}"
        status = getattr(response, "status_code", 0)
        if status == 200:
            return f"OK（HTTP 200，key 可用，长度 {len(self.api_key)}）"
        text = str(getattr(response, "text", ""))[:160]
        return f"HTTP {status}：{text}（key 长度 {len(self.api_key)}）"

    def chat_json(self, system: str, user: str, *, temperature: float = 0.2) -> dict:
        if not self.api_key:
            raise LlmError("缺少 DEEPSEEK_API_KEY")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "max_tokens": 2000,
        }
        try:
            response = self._client().post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        except Exception as exc:  # noqa: BLE001
            raise LlmError(f"请求失败：{exc}") from exc
        status = getattr(response, "status_code", 200)
        if status >= 400:
            raise LlmError(f"HTTP {status}：{getattr(response, 'text', '')[:200]}")
        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            raise LlmError(f"返回结构异常：{exc}") from exc
        return parse_json_content(str(content))


def parse_json_content(content: str) -> dict:
    """容忍 ```json 代码块和前后噪声。"""
    text = (content or "").strip()
    if text.startswith("```"):
        lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise LlmError("模型输出不是 JSON")
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LlmError(f"模型输出不是 JSON：{exc}") from exc
    if not isinstance(data, dict):
        raise LlmError("模型输出不是 JSON 对象")
    return data
