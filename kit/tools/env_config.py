#!/usr/bin/env python3
"""Environment and tool path discovery helper.

Dynamically finds ffmpeg, ffprobe, Google Chrome, and active virtual environment
across macOS Apple Silicon (/opt/homebrew) and Intel (/usr/local), as well as local user bins.
Zero hardcoded system paths.
"""
import glob
import os
import re
import shutil
import sys
import unicodedata

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


def find_project_root(path):
    """Project folder (marked by engine.js) that contains `path`, or None."""
    current = os.path.dirname(os.path.abspath(path))
    while True:
        if os.path.isfile(os.path.join(current, "engine.js")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def get_project_root(for_file=None):
    """Tools operate on the current project even when invoked from the installed kit.

    Priority: WVF_PROJECT_ROOT, then the project containing `for_file`, then the cwd.
    """
    if os.environ.get("WVF_PROJECT_ROOT"):
        return os.path.abspath(os.environ["WVF_PROJECT_ROOT"])
    return (for_file and find_project_root(for_file)) or os.path.abspath(os.getcwd())


def kit_tools_dir():
    """The package's tools folder (set by the launcher, so a project override of this module still finds it)."""
    return os.environ.get("WVF_KIT_TOOLS") or os.path.dirname(os.path.abspath(__file__))


def tool_path(name, root=None):
    """Projects keep only what they customize: tools/<name> overrides the package's tool."""
    own = os.path.join(root or get_project_root(), "tools", name)
    return own if os.path.isfile(own) else os.path.join(kit_tools_dir(), name)


def tool_env(root=None, base=None):
    """Imports resolve like tools: the project's tools/ first, then the package.

    PYTHONSAFEPATH (Python 3.11+) stops each script's own folder from jumping ahead of tools/.
    """
    env = dict(os.environ if base is None else base)
    kit = kit_tools_dir()
    paths = [os.path.join(root or get_project_root(), "tools"), kit]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env.update(PYTHONPATH=os.pathsep.join(paths), PYTHONSAFEPATH="1", WVF_KIT_TOOLS=kit, WVF_PYTHON=sys.executable)
    return env


def tool_command(name, args=(), root=None):
    path = tool_path(name, root)
    return (["bash"] if path.endswith(".sh") else [sys.executable]) + [path, *map(str, args)]


def project_slug(root):
    """Stable file-name stem from the project folder name (no accents, lowercase)."""
    name = unicodedata.normalize("NFKD", os.path.basename(os.path.abspath(root)))
    name = "".join(c for c in name if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_") or "video"


def get_master_path(root=None):
    """Where `render` writes this project's master."""
    root = root or get_project_root()
    return os.path.join(root, f"{project_slug(root)}_master.mp4")


def find_master(root=None):
    """This project's master; otherwise the only *_master.mp4. Several candidates are ambiguous."""
    root = root or get_project_root()
    expected = get_master_path(root)
    if os.path.isfile(expected):
        return expected
    candidates = sorted(glob.glob(os.path.join(glob.escape(root), "*_master.mp4")))
    if len(candidates) > 1:
        names = ", ".join(os.path.basename(c) for c in candidates)
        raise RuntimeError(f"Hay varios masters ({names}); indica cuál usar con la ruta del archivo.")
    return candidates[0] if candidates else None


def get_preview_url():
    return os.environ.get("WVF_PREVIEW_URL", "http://127.0.0.1:4391/index.html?render=1")
