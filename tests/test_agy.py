"""agy subscription engine and transcription backend, driven through a fake runner."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

import agy
from config import get_config, resolve_engine

ROOT = Path(__file__).resolve().parent.parent

FAKE_RUNNER = r'''
import argparse, json, os, sys
from pathlib import Path
ap = argparse.ArgumentParser()
ap.add_argument("--prompt-file"); ap.add_argument("--cwd"); ap.add_argument("--timeout")
ap.add_argument("--print-timeout"); ap.add_argument("--sandbox", action="store_true")
ap.add_argument("--new-project", action="store_true"); ap.add_argument("--response-source")
a = ap.parse_args()
prompt = Path(a.prompt_file).read_text(encoding="utf-8")
log = os.environ.get("FAKE_AGY_LOG")
if log:
    Path(log).write_text(json.dumps({"prompt": prompt, "cwd": a.cwd, "files": sorted(os.listdir(a.cwd)),
                                     "sandbox": a.sandbox}), encoding="utf-8")
mode = os.environ.get("FAKE_AGY_MODE", "answer")
if mode == "fail":
    print("quota exhausted", file=sys.stderr); sys.exit(4)
if "Transcribe" in prompt:
    print('```json\n{"segments": [{"start": 0.5, "end": 2.0, "text": "hello there"}]}\n```')
else:
    print("A blue frame fills the screen at 00:01.")
'''


@pytest.fixture
def fake_runner(tmp_path, monkeypatch):
    runner = tmp_path / "run_pty.py"
    runner.write_text(FAKE_RUNNER, encoding="utf-8")
    log = tmp_path / "agy-call.json"
    monkeypatch.setenv("WATCH_AGY_RUNNER", str(runner))
    monkeypatch.setenv("FAKE_AGY_LOG", str(log))
    return log


def test_ask_runs_sandboxed_in_the_media_directory(fake_runner, static_clip):
    import json
    answer = agy.ask(static_clip, "What color is it?", clip=(1.0, None))
    assert answer == "A blue frame fills the screen at 00:01."
    call = json.loads(fake_runner.read_text(encoding="utf-8"))
    assert call["sandbox"] and Path(call["cwd"]) == static_clip.parent.resolve()
    assert static_clip.name in call["prompt"] and "What color is it?" in call["prompt"]
    assert "from 1s to the end" in call["prompt"]


def test_transcribe_parses_fenced_segment_json(fake_runner, tmp_path):
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"x")
    segments = agy.transcribe_audio(audio)
    assert segments == [{"start": 0.5, "end": 2.0, "text": "hello there"}]


def test_runner_failure_is_reported(fake_runner, monkeypatch, tmp_path):
    monkeypatch.setenv("FAKE_AGY_MODE", "fail")
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"x")
    with pytest.raises(SystemExit, match="agy failed"):
        agy.transcribe_audio(audio)


def test_config_accepts_agy(monkeypatch):
    assert resolve_engine("agy", False) == "agy"
    monkeypatch.setenv("WATCH_WHISPER_BACKEND", "agy")
    monkeypatch.setenv("WATCH_ENGINE", "agy")
    config = get_config()
    assert config["whisper_backend"] == "agy" and config["engine"] == "agy"


def test_watch_agy_engine_never_exposes_the_source_folder(fake_runner, static_clip, tmp_path):
    import json
    result = subprocess.run([sys.executable, str(ROOT / "skills/watch/scripts/watch.py"), str(static_clip),
                             "--engine", "agy", "--question", "What color?", "--out-dir", str(tmp_path / "out")],
                            capture_output=True, encoding="utf-8", env=dict(os.environ))
    assert result.returncode == 0, result.stderr
    assert "## Answer (from agy)" in result.stdout and "blue frame" in result.stdout
    call = json.loads(fake_runner.read_text(encoding="utf-8"))
    assert Path(call["cwd"]) != static_clip.parent.resolve() and call["files"] == ["video.mp4"]
    assert not any((tmp_path / "out").iterdir())  # The run-owned copy is removed.
