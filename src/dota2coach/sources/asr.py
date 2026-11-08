"""可选：把 B 站视频的音频转成文字（faster-whisper，CPU）。

只有脚本会用到；局内程序不 import 这个模块，所以装不装 faster-whisper
都不影响教练本身运行。
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path


def asr_available() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def _patch_av_open() -> None:
    """PyAV 14+ 删掉了 av.open(metadata_errors=...)，而 faster-whisper 仍在传。

    这里做一次兼容包装，避免用户被迫降级 av（降级还会连带别的包）。
    """
    try:
        import av

        if getattr(av, "_dota2coach_compat", False):
            return
        original = av.open

        def compat_open(*args, **kwargs):
            kwargs.pop("metadata_errors", None)
            return original(*args, **kwargs)

        av.open = compat_open
        av._dota2coach_compat = True  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 - 兼容失败就让原库自己报错
        pass


class Transcriber:
    def __init__(
        self,
        model: str = "base",
        *,
        compute_type: str = "int8",
        language: str = "zh",
        model_dir: Path | None = None,
        hf_endpoint: str = "https://hf-mirror.com",
        num_workers: int = 4,
    ) -> None:
        self.model_name = model
        self.compute_type = compute_type
        self.language = language
        self.model_dir = Path(model_dir) if model_dir else Path("logs/models")
        self.hf_endpoint = hf_endpoint
        self.num_workers = num_workers
        self.last_error: str = ""
        self._model = None

    @property
    def ready(self) -> bool:
        return asr_available()

    def _local_model(self) -> str:
        """已下载过就直接用快照目录，避免 huggingface_hub 再走一次下载/临时文件。"""
        snapshots = self.model_dir / f"models--Systran--faster-whisper-{self.model_name}" / "snapshots"
        if snapshots.is_dir():
            for snap in sorted(snapshots.iterdir(), reverse=True):
                if (snap / "model.bin").exists():
                    return str(snap)
        return self.model_name

    def _load(self):
        if self._model is not None:
            return self._model
        if not asr_available():
            raise RuntimeError(
                "未安装 faster-whisper：先运行 scripts\\setup_asr.ps1 或 "
                "pip install faster-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple"
            )
        # 国内直连 huggingface.co 常常超时，默认走镜像
        os.environ.setdefault("HF_ENDPOINT", self.hf_endpoint)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        _patch_av_open()
        from faster_whisper import WhisperModel  # 延迟导入

        self._model = WhisperModel(
            self._local_model(),
            device="cpu",
            compute_type=self.compute_type,
            download_root=str(self.model_dir),
            num_workers=self.num_workers,
        )
        return self._model

    def transcribe(self, audio_path: Path, initial_prompt: str = "") -> str:
        """返回整段转写文本；失败抛异常并把原因记到 last_error。"""
        try:
            model = self._load()
            segments, _info = model.transcribe(
                str(audio_path),
                language=self.language,
                beam_size=5,
                vad_filter=True,
                initial_prompt=initial_prompt or None,
                condition_on_previous_text=False,
            )
            pieces = [segment.text.strip() for segment in segments if segment.text.strip()]
            return "".join(pieces)
        except Exception as exc:  # noqa: BLE001
            self.last_error = str(exc)
            raise

    def hotwords_prompt(self, heroes: list[str], items: list[str], limit: int = 40) -> str:
        """把常见中文名塞进 initial_prompt，降低专有名词的识别错误。"""
        words = [word for word in heroes + items if word]
        unique: list[str] = []
        for word in words:
            if word not in unique:
                unique.append(word)
            if len(unique) >= limit:
                break
        return "、".join(unique)
