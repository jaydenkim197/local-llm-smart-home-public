#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

try:
    from .stt_eval_core import DEFAULT_AUDIO_DIR, audio_path, expanded_cases, load_stt_dataset
except ImportError:  # Direct script execution.
    from stt_eval_core import DEFAULT_AUDIO_DIR, audio_path, expanded_cases, load_stt_dataset


app = FastAPI(title="KICS STT Recording Tool")
dataset = load_stt_dataset()
cases = expanded_cases(dataset)
case_ids = {case["id"] for case in cases}
audio_dir = DEFAULT_AUDIO_DIR


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return _HTML


@app.get("/api/manifest")
async def manifest() -> dict:
    return {
        "dataset_id": dataset["dataset_id"],
        "takes_per_case": dataset["takes_per_case"],
        "protocol": dataset["recording_protocol"],
        "cases": [
            {
                "id": case["id"],
                "source_case_id": case["source_case_id"],
                "utterance": case["source"]["utterance"],
            }
            for case in cases
        ],
    }


@app.post("/api/recordings/{speaker_id}/{case_id}/{take}")
async def save_recording(
    speaker_id: str,
    case_id: str,
    take: int,
    file: UploadFile = File(...),
) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", speaker_id):
        raise HTTPException(400, "Speaker id may contain only letters, digits, underscore, and hyphen")
    if case_id not in case_ids:
        raise HTTPException(404, "Unknown STT case")
    if take < 1 or take > dataset["takes_per_case"]:
        raise HTTPException(400, "Invalid take number")
    content = await file.read()
    if not content or len(content) > 20 * 1024 * 1024:
        raise HTTPException(400, "Recording must be between 1 byte and 20 MB")
    path = audio_path(audio_dir, speaker_id, case_id, take)
    if path.exists():
        raise HTTPException(
            409,
            "This take already exists. Use a new speaker/session ID instead of overwriting it.",
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {"saved": str(path.relative_to(audio_dir)), "bytes": len(content)}


def main() -> None:
    global audio_dir
    parser = argparse.ArgumentParser(description="Run the local fixed-set STT recorder")
    parser.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO_DIR)
    parser.add_argument("--port", type=int, default=8010)
    args = parser.parse_args()
    audio_dir = args.audio_dir
    uvicorn.run(app, host="127.0.0.1", port=args.port)


_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>KICS STT Recording</title>
  <style>
    body { margin: 0; font-family: system-ui, sans-serif; color: #17202a; background: #f4f6f8; }
    header, main { max-width: 880px; margin: 0 auto; padding: 24px; }
    header { border-bottom: 1px solid #ccd4dc; }
    h1 { margin: 0 0 8px; font-size: 24px; }
    .toolbar { display: flex; gap: 12px; align-items: end; margin: 24px 0; }
    label { display: grid; gap: 6px; font-size: 14px; }
    input { padding: 9px 10px; border: 1px solid #9eabb7; border-radius: 6px; }
    .prompt { min-height: 96px; padding: 20px 0; font-size: 28px; line-height: 1.35; border-block: 1px solid #ccd4dc; }
    .controls { display: flex; gap: 10px; margin: 20px 0; }
    button { border: 0; border-radius: 6px; padding: 10px 16px; font-weight: 650; cursor: pointer; }
    #record { background: #b42318; color: white; }
    #stop { background: #344054; color: white; }
    #next { background: #087e8b; color: white; }
    button:disabled { opacity: .4; cursor: default; }
    #status { min-height: 24px; font-family: ui-monospace, monospace; }
  </style>
</head>
<body>
  <header><h1>Fixed STT Recording Set</h1><div id="progress">Loading...</div></header>
  <main>
    <div class="toolbar"><label>Speaker ID<input id="speaker" value="speaker01" maxlength="32"></label></div>
    <div class="prompt" id="prompt"></div>
    <div class="controls">
      <button id="record">Record</button>
      <button id="stop" disabled>Stop and save</button>
      <button id="next" disabled>Next</button>
    </div>
    <div id="status"></div>
  </main>
  <script>
    let manifest, index = 0, take = 1, recorder, chunks = [];
    const $ = id => document.getElementById(id);
    fetch('/api/manifest').then(r => r.json()).then(data => { manifest = data; render(); });
    function render() {
      const item = manifest.cases[index];
      $('progress').textContent = `Case ${index + 1}/${manifest.cases.length}, take ${take}/${manifest.takes_per_case}`;
      $('prompt').textContent = item.utterance;
      $('status').textContent = 'Ready. Leave a short pause before and after speaking.';
      $('record').disabled = false; $('stop').disabled = true; $('next').disabled = true;
    }
    $('record').onclick = async () => {
      const stream = await navigator.mediaDevices.getUserMedia({audio: true});
      chunks = []; recorder = new MediaRecorder(stream);
      recorder.ondataavailable = e => chunks.push(e.data);
      recorder.start(); $('status').textContent = 'Recording...';
      $('record').disabled = true; $('stop').disabled = false;
    };
    $('stop').onclick = () => {
      recorder.onstop = async () => {
        recorder.stream.getTracks().forEach(track => track.stop());
        const blob = new Blob(chunks, {type: 'audio/webm'});
        const form = new FormData(); form.append('file', blob, 'recording.webm');
        const item = manifest.cases[index];
        const speaker = $('speaker').value.trim();
        const response = await fetch(`/api/recordings/${encodeURIComponent(speaker)}/${item.id}/${take}`, {method: 'POST', body: form});
        const body = await response.json();
        if (!response.ok) { $('status').textContent = body.detail || 'Save failed'; $('record').disabled = false; return; }
        $('status').textContent = `Saved ${body.saved}`; $('next').disabled = false;
      };
      recorder.stop(); $('stop').disabled = true; $('status').textContent = 'Saving...';
    };
    $('next').onclick = () => {
      if (take < manifest.takes_per_case) take += 1;
      else { take = 1; index += 1; }
      if (index >= manifest.cases.length) {
        $('progress').textContent = 'Complete'; $('prompt').textContent = 'All recordings saved.';
        $('record').disabled = true; $('next').disabled = true; return;
      }
      render();
    };
  </script>
</body>
</html>"""


if __name__ == "__main__":
    main()
