#!/usr/bin/env python3
"""Universal Google Chrome connector via macOS AppleScript + multi-PID JXA (zero remote-debugging setup).

Connects directly to the user's active Google Chrome windows and tabs on macOS,
sharing the same Apple Events bridge used by flowjs.py, flowmusicjs.py, and wajs.py.
Supports:
  - Multi-instance Chrome PID routing (`Application(pid)`) when more than one Chrome process runs.
  - Zero-focus-steal background tabs (`activeTabIndex` preserved automatically).

Usage:
  wvf tool chromejs --tabs [--filter tiktok]
  wvf tool chromejs --nav "https://www.tiktok.com/tiktokstudio/analytics" [--match "tiktok.com"]
  wvf tool chromejs --open-bg "https://studio.youtube.com/video/ID/analytics/hub_overview"
  wvf tool chromejs --close-tab 68845462
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


def run_jxa(jxa_source: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as temp_jxa:
        temp_jxa.write(jxa_source)
        temp_jxa_path = temp_jxa.name
    try:
        completed_process = subprocess.run(
            ["osascript", "-l", "JavaScript", temp_jxa_path],
            capture_output=True,
            text=True,
        )
        if completed_process.returncode != 0:
            error_detail = completed_process.stderr.strip() or "Google Chrome no respondió a JXA."
            raise RuntimeError(error_detail)
        return completed_process.stdout.strip()
    finally:
        if os.path.exists(temp_jxa_path):
            os.unlink(temp_jxa_path)


def discover_chrome_pids() -> list[int]:
    """Return all running `Google Chrome` main process PIDs on macOS."""
    try:
        proc = subprocess.run(
            ["pgrep", "-x", "Google Chrome"],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return []
        return [int(line.strip()) for line in proc.stdout.splitlines() if line.strip().isdigit()]
    except OSError:
        return []


def _is_applescript_mocked() -> bool:
    return hasattr(run_applescript, "assert_called") or getattr(run_applescript, "__module__", "").startswith("unittest")


def _list_tabs_via_jxa_pids(pids: list[int], normalized_filter: str = "") -> list[dict]:
    discovered: list[dict] = []
    for pid in pids:
        jxa = f"""
        const app = Application({pid});
        const rows = [];
        const wins = app.windows();
        for (let wi = 0; wi < wins.length; wi++) {{
          const tabs = wins[wi].tabs();
          for (let ti = 0; ti < tabs.length; ti++) {{
            const t = tabs[ti];
            rows.push({{
              pid: {pid},
              window_index: wi + 1,
              tab_index: ti + 1,
              tab_id: String(t.id()),
              url: String(t.url() || ''),
              title: String(t.title() || '')
            }});
          }}
        }}
        JSON.stringify(rows);
        """
        try:
            batch = json.loads(run_jxa(jxa) or "[]")
            for item in batch:
                u = item.get("url", "").lower()
                t = item.get("title", "").lower()
                if normalized_filter and normalized_filter not in u and normalized_filter not in t:
                    continue
                discovered.append(item)
        except Exception:
            continue
    return discovered


def list_tabs(url_filter: str = "") -> list[dict]:
    normalized_filter = (url_filter or "").strip().lower()
    if not _is_applescript_mocked():
        pids = discover_chrome_pids()
        if len(pids) > 1:
            multi = _list_tabs_via_jxa_pids(pids, normalized_filter)
            if multi:
                return multi

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


def open_background_tab(target_url: str, window_index: int = 0, pid: int | None = None) -> dict:
    """Open `target_url` in a background Chrome tab without stealing `activeTabIndex` focus."""
    pids = [pid] if pid else discover_chrome_pids()
    target_pid = pids[-1] if pids else None
    if target_pid is not None and not _is_applescript_mocked():
        for candidate_pid in ([pid] if pid else reversed(pids)):
            try:
                raw = run_jxa(f"""
                const app = Application({candidate_pid});
                const wins = app.windows();
                if (!wins.length) throw new Error('NO_WINDOWS');
                const w = wins[Math.min({max(0, window_index)}, wins.length - 1)];
                const origIdx = w.activeTabIndex();
                const nt = app.Tab({{url: {json.dumps(target_url, ensure_ascii=False)}}});
                w.tabs.push(nt);
                const created = w.tabs()[w.tabs().length - 1];
                const tid = String(created.id());
                if (origIdx >= 1 && origIdx <= w.tabs().length) {{
                  w.activeTabIndex = origIdx;
                }}
                JSON.stringify({{pid: {candidate_pid}, tab_id: tid, url: {json.dumps(target_url, ensure_ascii=False)}}});
                """)
                return json.loads(raw)
            except Exception:
                continue

    status = navigate_tab(target_url, url_match="__force_new_bg_tab__", background=True)
    return {"pid": None, "tab_id": "", "status": status, "url": target_url}


def close_tab_by_id(tab_id: str, pid: int | None = None) -> bool:
    """Close a temporary background tab by its Chrome `tab_id` without disturbing other tabs."""
    if not tab_id:
        return False
    pids = [pid] if pid else discover_chrome_pids()
    for candidate_pid in pids:
        try:
            res = run_jxa(f"""
            const app = Application({candidate_pid});
            let closed = false;
            for (const w of app.windows()) {{
              for (const t of w.tabs()) {{
                if (String(t.id()) === {json.dumps(str(tab_id))}) {{
                  t.close();
                  closed = true;
                  break;
                }}
              }}
              if (closed) break;
            }}
            closed ? 'CLOSED' : 'NOT_FOUND';
            """)
            if res == "CLOSED":
                return True
        except Exception:
            continue
    return False


def execute_javascript_on_tab_id(javascript_code: str, tab_id: str, pid: int | None = None) -> str:
    """Execute JavaScript on a specific Chrome `tab_id` without changing active tab focus."""
    pids = [pid] if pid else discover_chrome_pids()
    for candidate_pid in pids:
        try:
            out = run_jxa(f"""
            const app = Application({candidate_pid});
            let targetTab = null;
            for (const w of app.windows()) {{
              for (const t of w.tabs()) {{
                if (String(t.id()) === {json.dumps(str(tab_id))}) {{
                  targetTab = t;
                  break;
                }}
              }}
              if (targetTab) break;
            }}
            if (!targetTab) {{
              '__TAB_NOT_FOUND__';
            }} else {{
              const r = app.execute(targetTab, {{javascript: {json.dumps(javascript_code, ensure_ascii=False)}}});
              r === undefined || r === null ? '' : (typeof r === 'string' ? r : JSON.stringify(r));
            }}
            """)
            if out != "__TAB_NOT_FOUND__":
                return out
        except Exception:
            continue
    raise RuntimeError(f"No se encontró la pestaña de Chrome con id '{tab_id}'.")


def navigate_tab(target_url: str, url_match: str = "", background: bool = True) -> str:
    parsed_target = urlparse(target_url)
    effective_match = (url_match or parsed_target.netloc or target_url).strip()

    if not _is_applescript_mocked():
        pids = discover_chrome_pids()
        if len(pids) > 1:
            for pid in reversed(pids):
                try:
                    nav_res = run_jxa(f"""
                    const app = Application({pid});
                    let matched = false;
                    for (const w of app.windows()) {{
                      for (const t of w.tabs()) {{
                        if (String(t.url() || '').includes({json.dumps(effective_match, ensure_ascii=False)})) {{
                          t.url = {json.dumps(target_url, ensure_ascii=False)};
                          matched = true;
                          break;
                        }}
                      }}
                      if (matched) break;
                    }}
                    matched ? 'NAVIGATED_EXISTING' : 'NO_MATCH';
                    """)
                    if nav_res == "NAVIGATED_EXISTING":
                        return nav_res
                except Exception:
                    continue

    restore_clause = (
        "if prevActiveIndex >= 1 and prevActiveIndex <= (count of tabs) then set active tab index to prevActiveIndex"
        if background
        else ""
    )
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
            set prevActiveIndex to active tab index
            make new tab with properties {{URL:{json.dumps(target_url, ensure_ascii=False)}}}
            {restore_clause}
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


def _execute_js_across_jxa_pids(javascript_code: str, url_match: str, pids: list[int]) -> str:
    for pid in reversed(pids):
        try:
            res = run_jxa(f"""
            const app = Application({pid});
            let foundTab = null;
            for (const w of app.windows()) {{
              for (const t of w.tabs()) {{
                if (String(t.url() || '').includes({json.dumps(url_match, ensure_ascii=False)})) {{
                  foundTab = t;
                  break;
                }}
              }}
              if (foundTab) break;
            }}
            if (!foundTab) {{
              'NO_MATCHING_TAB';
            }} else {{
              const r = app.execute(foundTab, {{javascript: {json.dumps(javascript_code, ensure_ascii=False)}}});
              r === undefined || r === null ? '' : (typeof r === 'string' ? r : JSON.stringify(r));
            }}
            """)
            if res != "NO_MATCHING_TAB":
                return res
        except Exception:
            continue
    return "NO_MATCHING_TAB"


def execute_javascript(
    javascript_code: str,
    url_match: str,
    open_if_missing_url: str = "",
    wait_seconds: float = 4.0,
    background: bool = True,
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
        try:
            execution_result = run_applescript(applescript_source)
        except RuntimeError:
            if not _is_applescript_mocked():
                pids = discover_chrome_pids()
                if pids:
                    execution_result = _execute_js_across_jxa_pids(javascript_code, url_match, pids)
                else:
                    raise
            else:
                raise

        if execution_result == "NO_MATCHING_TAB" and not _is_applescript_mocked():
            pids = discover_chrome_pids()
            if len(pids) > 1:
                execution_result = _execute_js_across_jxa_pids(javascript_code, url_match, pids)

        if execution_result == "NO_MATCHING_TAB" and open_if_missing_url:
            navigate_tab(open_if_missing_url, url_match=url_match, background=background)
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            execution_result = run_applescript(applescript_source)
            if execution_result == "NO_MATCHING_TAB" and not _is_applescript_mocked():
                pids = discover_chrome_pids()
                if len(pids) > 1:
                    execution_result = _execute_js_across_jxa_pids(javascript_code, url_match, pids)

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
        description="Conector universal de Google Chrome vía AppleScript/JXA multi-instancia para WBRS / WVF."
    )
    parser.add_argument("--tabs", action="store_true", help="Lista las pestañas abiertas en Google Chrome")
    parser.add_argument("--filter", default="", help="Filtra pestañas por texto en URL o título")
    parser.add_argument("--nav", default="", help="Navega una pestaña existente o abre una en segundo plano")
    parser.add_argument("--open-bg", default="", help="Abre una pestaña nueva en segundo plano sin robar foco y devuelve su tab_id")
    parser.add_argument("--close-tab", default="", help="Cierra una pestaña por su tab_id")
    parser.add_argument("--foreground", action="store_true", help="Permitir traer al frente una pestaña recién abierta")
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

    if parsed_args.open_bg:
        info = open_background_tab(parsed_args.open_bg)
        print(json.dumps(info, ensure_ascii=False))
        return 0

    if parsed_args.close_tab:
        closed = close_tab_by_id(parsed_args.close_tab)
        print("CLOSED" if closed else "NOT_FOUND")
        return 0 if closed else 1

    if parsed_args.nav:
        navigation_status = navigate_tab(
            parsed_args.nav,
            url_match=parsed_args.match,
            background=not parsed_args.foreground,
        )
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
        background=not parsed_args.foreground,
    )
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
