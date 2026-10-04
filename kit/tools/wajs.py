#!/usr/bin/env python3
"""Run a JS file (or inline JS) inside the user's Chrome tab on flow.google.com.

usage: flowjs.py file.js            -> prints the JS return value
       flowjs.py -e "document.title"
       flowjs.py --nav URL           -> navigates the Flow tab
"""
import subprocess, sys, tempfile, os

MATCH = "web.whatsapp.com"


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
    os.unlink(path)
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
                return "ok"
            end if
        end repeat
    end repeat
end tell
return "NO_TAB"
'''
    res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return res.stdout.strip() + res.stderr.strip()


if __name__ == "__main__":
    if sys.argv[1] == "-e":
        print(run_js(sys.argv[2]))
    elif sys.argv[1] == "--nav":
        print(nav(sys.argv[2]))
    else:
        print(run_js(open(sys.argv[1], encoding="utf-8").read()))
