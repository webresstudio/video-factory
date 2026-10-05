#!/usr/bin/env python3
"""Environment and tool path discovery helper.

Dynamically finds ffmpeg, ffprobe, Google Chrome, and active virtual environment
across macOS Apple Silicon (/opt/homebrew) and Intel (/usr/local), as well as local user bins.
Zero hardcoded system paths.
"""
import os
import shutil
import sys

def get_ffmpeg():
    p = shutil.which("ffmpeg")
    if p:
        return p
    for cand in [
        "/opt/homebrew/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        os.path.expanduser("~/.local/bin/ffmpeg"),
    ]:
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    raise RuntimeError("ffmpeg no fue encontrado en PATH ni en las rutas estándar de Homebrew.")

def get_ffprobe():
    p = shutil.which("ffprobe")
    if p:
        return p
    for cand in [
        "/opt/homebrew/bin/ffprobe",
        "/usr/local/bin/ffprobe",
        os.path.expanduser("~/.local/bin/ffprobe"),
    ]:
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    raise RuntimeError("ffprobe no fue encontrado en PATH ni en las rutas estándar.")

def get_chrome():
    cands = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    ]
    for cand in cands:
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    # Fallback to None: Playwright will use its default browser executable if installed
    return None

def get_python():
    # If running inside a venv, sys.executable is already the right python
    return sys.executable


def get_project_root():
    """Tools operate on the current project even when invoked from the installed kit."""
    return os.path.abspath(os.environ.get("WVF_PROJECT_ROOT", os.getcwd()))


def get_preview_url():
    return os.environ.get("WVF_PREVIEW_URL", "http://127.0.0.1:4391/index.html?render=1")
