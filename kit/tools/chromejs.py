#!/usr/bin/env python3
"""Universal Google Chrome connector via macOS AppleScript (zero remote-debugging setup).

Connects directly to the user's active Google Chrome windows and tabs on macOS,
sharing the same Apple Events bridge used by flowjs.py, flowmusicjs.py, and wajs.py.

Usage:
  wvf tool chromejs --tabs [--filter tiktok]
  wvf tool chromejs --nav "https://www.tiktok.com/tiktokstudio/analytics" [--match "tiktok.com"]
  wvf tool chromejs --match "tiktok.com" -e "document.title"
  wvf tool chromejs --match "business.facebook.com" script_file.js
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlparse


def run_applescript(applescript_source: str) -> str:
    completed_process = subprocess.run(
        ["osascript", "-e", applescript_source],
        capture_output=True,
        text=True,
    )
    if completed_process.returncode != 0:
        error_detail = completed_process.stderr.strip() or "Google Chrome no respondió a AppleScript."
        raise RuntimeError(error_detail)
    return completed_process.stdout.strip()


def list_tabs(url_filter: str = "") -> list[dict]:
    applescript_source = '''
tell application "Google Chrome"
    set outputLines to ""
    set windowIndex to 0
    repeat with browserWindow in windows
        set windowIndex to windowIndex + 1
        set tabIndex to 0
        repeat with browserTab in tabs of browserWindow
            set tabIndex to tabIndex + 1
            set tabUrl to URL of browserTab
            set tabTitle to title of browserTab
            set outputLines to outputLines & windowIndex & "\t" & tabIndex & "\t" & tabUrl & "\t" & tabTitle & linefeed
        end repeat
    end repeat
    return outputLines
end tell
'''
    raw_output = run_applescript(applescript_source)
    normalized_filter = (url_filter or "").strip().lower()
    discovered_tabs = []
    for raw_line in raw_output.splitlines():
        if not raw_line.strip():
            continue
        parts = raw_line.split("\t", 3)
        if len(parts) < 4:
            continue
        window_number, tab_number, tab_url, tab_title = parts
        if normalized_filter and normalized_filter not in tab_url.lower() and normalized_filter not in tab_title.lower():
            continue
        discovered_tabs.append(
            {
                "window_index": int(window_number),
                "tab_index": int(tab_number),
                "url": tab_url,
                "title": tab_title,
            }
        )
    return discovered_tabs


def navigate_tab(target_url: str, url_match: str = "") -> str:
    parsed_target = urlparse(target_url)
    effective_match = (url_match or parsed_target.netloc or target_url).strip()
    applescript_source = f'''
tell application "Google Chrome"
    repeat with browserWindow in windows
        repeat with browserTab in tabs of browserWindow
            if URL of browserTab contains {json.dumps(effective_match, ensure_ascii=False)} then
                set URL of browserTab to {json.dumps(target_url, ensure_ascii=False)}
                return "NAVIGATED_EXISTING"
            end if
        end repeat
    end repeat
    if (count of windows) > 0 then
        tell window 1
            make new tab with properties {{URL:{json.dumps(target_url, ensure_ascii=False)}}}
            return "OPENED_NEW_TAB"
        end tell
    else
        make new window
        set URL of active tab of window 1 to {json.dumps(target_url, ensure_ascii=False)}
        return "OPENED_NEW_WINDOW"
    end if
end tell
'''
    return run_applescript(applescript_source)


def execute_javascript(
    javascript_code: str,
    url_match: str,
    open_if_missing_url: str = "",
    wait_seconds: float = 4.0,
) -> str:
    if not url_match:
        raise ValueError("Se requiere url_match para identificar la pestaña de destino en Google Chrome.")

    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as temp_script:
        temp_script.write(javascript_code)
        temp_script_path = temp_script.name

    applescript_source = f'''
set javascriptSource to (read POSIX file "{temp_script_path}" as «class utf8»)
tell application "Google Chrome"
    repeat with browserWindow in windows
        repeat with browserTab in tabs of browserWindow
            if URL of browserTab contains {json.dumps(url_match, ensure_ascii=False)} then
                return execute browserTab javascript javascriptSource
            end if
        end repeat
    end repeat
end tell
return "NO_MATCHING_TAB"
'''
    try:
        execution_result = run_applescript(applescript_source)
        if execution_result == "NO_MATCHING_TAB" and open_if_missing_url:
            navigate_tab(open_if_missing_url, url_match=url_match)
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            execution_result = run_applescript(applescript_source)
        if execution_result == "NO_MATCHING_TAB":
            raise RuntimeError(
                f"No se encontró ninguna pestaña de Google Chrome cuya URL contenga '{url_match}'."
            )
        return execution_result
    finally:
        if os.path.exists(temp_script_path):
            os.unlink(temp_script_path)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Conector universal de Google Chrome vía AppleScript para WBRS / WVF."
    )
    parser.add_argument("--tabs", action="store_true", help="Lista las pestañas abiertas en Google Chrome")
    parser.add_argument("--filter", default="", help="Filtra pestañas por texto en URL o título")
    parser.add_argument("--nav", default="", help="Navega una pestaña existente o abre una nueva en la URL indicada")
    parser.add_argument("--match", default="", help="Subcadena de URL para seleccionar la pestaña objetivo")
    parser.add_argument("-e", "--eval", dest="inline_code", default="", help="Código JavaScript en línea a ejecutar")
    parser.add_argument("--open-if-missing", default="", help="Abre esta URL si no existe pestaña que coincida con --match")
    parser.add_argument("--wait", type=float, default=4.0, help="Segundos de espera tras abrir o navegar pestaña")
    parser.add_argument("script_file", nargs="?", default="", help="Ruta a archivo .js para ejecutar en la pestaña")
    return parser


def main(argv=None) -> int:
    parser = build_argument_parser()
    parsed_args = parser.parse_args(argv)

    if parsed_args.tabs:
        tabs = list_tabs(parsed_args.filter)
        print(json.dumps(tabs, ensure_ascii=False, indent=2))
        return 0

    if parsed_args.nav:
        navigation_status = navigate_tab(parsed_args.nav, url_match=parsed_args.match)
        print(navigation_status)
        return 0

    javascript_payload = parsed_args.inline_code
    if not javascript_payload and parsed_args.script_file:
        with open(parsed_args.script_file, encoding="utf-8") as script_handle:
            javascript_payload = script_handle.read()

    if not javascript_payload:
        parser.print_help()
        return 1

    output = execute_javascript(
        javascript_code=javascript_payload,
        url_match=parsed_args.match,
        open_if_missing_url=parsed_args.open_if_missing,
        wait_seconds=parsed_args.wait,
    )
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
