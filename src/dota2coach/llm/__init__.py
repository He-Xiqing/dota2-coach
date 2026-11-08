"""可选的大模型客户端（默认关闭，仅攻略/复盘等非实时场景使用）。"""

from .client import LlmClient, parse_json_content

__all__ = ["LlmClient", "parse_json_content"]
