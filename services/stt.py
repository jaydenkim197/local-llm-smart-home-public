from __future__ import annotations

import os
import tempfile
from typing import Tuple

from fastapi import UploadFile

from app.config import WHISPER_COMPUTE_TYPE, WHISPER_DEVICE, WHISPER_MODEL

_model = None


async def transcribe_audio(file: UploadFile) -> Tuple[str, str]:
    suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text = _transcribe_with_faster_whisper(tmp_path)
        return text, f"faster-whisper:{WHISPER_MODEL}"
    except Exception as exc:
        return f"[STT unavailable: {exc}]", "unavailable"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _transcribe_with_faster_whisper(path: str) -> str:
    global _model
    from faster_whisper import WhisperModel

    if _model is None:
        _model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)

    segments, _info = _model.transcribe(path, language="en", vad_filter=False)
    return " ".join(segment.text.strip() for segment in segments).strip()
