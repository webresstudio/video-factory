#!/usr/bin/env python3
"""Run a JS snippet (or inline JS) inside the user's Chrome tab on flowmusic.app.

Usage:
  python flowmusicjs.py file.js
  python flowmusicjs.py -e "document.title"
  python flowmusicjs.py --nav URL
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

MATCH = "flowmusic.app"

def run_js(code: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(code)
        path = f.name
    script = f'''
set jsCode to (read POSIX file "{path}" as «class utf8»)
tell application "Google Chrome"
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "{MATCH}" then
                return execute t javascript jsCode
            end if
        end repeat
    end repeat
end tell
return "NO_TAB"
'''
    res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    try:
        os.unlink(path)
    except Exception:
        pass
    if res.stderr.strip():
        sys.stderr.write(res.stderr)
    return res.stdout.strip()

def nav(url: str) -> str:
    script = f'''
tell application "Google Chrome"
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "{MATCH}" then
                set URL of t to "{url}"
                return "NAVIGATED_EXISTING"
            end if
        end repeat
    end repeat
    -- Si no existe la pestaña, abrir una nueva
    if (count of windows) > 0 then
        tell window 1
            make new tab with properties {{URL:"{url}"}}
            return "OPENED_NEW_TAB"
        end tell
    end if
end tell
return "NO_WINDOW"
'''
    res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return res.stdout.strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="JS file to execute")
    ap.add_argument("-e", dest="inline", help="Inline JS snippet")
    ap.add_argument("--nav", help="Navigate or open FlowMusic project URL")
    args = ap.parse_args()

    if args.nav:
        print(nav(args.nav))
        return

    code = args.inline
    if not code and args.file:
        code = open(args.file, encoding="utf-8").read()
    if not code:
        ap.print_help()
        sys.exit(1)

    print(run_js(code))

if __name__ == "__main__":
    main()
