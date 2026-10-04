#!/usr/bin/env python3
"""Run a JS file (or inline JS) inside the user's Chrome tab on flow.google.com.

usage: flowjs.py file.js            -> prints the JS return value
       flowjs.py -e "document.title"
       flowjs.py --nav URL           -> navigates the Flow tab
"""
import subprocess, sys, tempfile, os

MATCH = "flow.google.com"


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


def get_default_project_url():
    cfg_file = os.path.join(os.getcwd(), "project_config.json")
    if os.path.isfile(cfg_file):
        try:
            import json
            cfg = json.load(open(cfg_file, encoding="utf-8"))
            return cfg.get("flow", {}).get("project_url")
        except Exception:
            pass
    return None


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
    return res.stdout.strip() + res.stderr.strip()


if __name__ == "__main__":
    if sys.argv[1] == "-e":
        print(run_js(sys.argv[2]))
    elif sys.argv[1] == "--nav":
        print(nav(sys.argv[2]))
    else:
        print(run_js(open(sys.argv[1], encoding="utf-8").read()))
