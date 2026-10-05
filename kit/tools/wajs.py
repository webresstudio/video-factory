#!/usr/bin/env python3
"""Run a JS file (or inline JS) inside the user's Chrome tab on web.whatsapp.com.

usage: wajs.py file.js            -> prints the JS return value
       wajs.py -e "document.title"
       wajs.py --nav URL           -> navigates the Flow tab
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
    if res.returncode:
        raise RuntimeError(res.stderr.strip() or "Chrome no respondió a AppleScript")
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


def send_file(path, contact, timeout=30):
    """Attach and send only when Chrome's selected chat exactly matches contact.

    Uses Chrome's existing signed-in tab; never opens a different contact implicitly.
    """
    import base64
    import json
    import mimetypes
    import time
    from pathlib import Path
    path = Path(path)
    selected = run_js("""JSON.stringify(Array.from(document.querySelectorAll('#main header span[title], #main header [data-testid="conversation-info-header-chat-title"]')).map(e => e.getAttribute('title') || e.textContent.trim()))""")
    try:
        titles = json.loads(selected)
    except (ValueError, TypeError):
        raise RuntimeError('No se pudo identificar el chat de WhatsApp en Chrome.')
    if contact.strip().casefold() not in [title.strip().casefold() for title in titles]:
        raise RuntimeError(f'El chat seleccionado no coincide con {contact!r}. Selecciona ese chat antes de enviar.')
    # Open the native attachment menu if its file input is not mounted yet.
    run_js("""(() => { const root=document.querySelector('#main'); const b=root?.querySelector('button[aria-label="Adjuntar"], button[aria-label="Attach"], [data-icon="plus-rounded"]'); b?.click(); return 'ok'; })()""")
    encoded = base64.b64encode(path.read_bytes()).decode('ascii')
    code = """(() => {
      const input = Array.from(document.querySelectorAll('input[type=file]')).find(e => /video|image/.test(e.accept));
      if (!input) return 'NO_FILE_INPUT';
      const bytes = Uint8Array.from(atob(%s), c => c.charCodeAt(0));
      const transfer = new DataTransfer();
      transfer.items.add(new File([bytes], %s, {type:%s}));
      input.files=transfer.files; input.dispatchEvent(new Event('change',{bubbles:true}));
      return 'ATTACHED';
    })()""" % (json.dumps(encoded), json.dumps(path.name), json.dumps(mimetypes.guess_type(path.name)[0] or 'video/mp4'))
    if run_js(code) != 'ATTACHED':
        raise RuntimeError('No se encontró la entrada de archivos de WhatsApp.')
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        # The preview dialog's send button is intentionally separate from the chat composer.
        result = run_js("""(() => {
          const expected=%s;
          const titles=Array.from(document.querySelectorAll('#main header span[title], #main header [data-testid="conversation-info-header-chat-title"]')).map(e=>(e.getAttribute('title')||e.textContent.trim()).trim().toLowerCase());
          if (!titles.includes(expected.trim().toLowerCase())) return 'WRONG_CONTACT';
          const dialog=document.querySelector('[role=dialog]');
          const scopes=[dialog, ...document.querySelectorAll('[data-animate-modal-popup]')].filter(Boolean);
          for (const scope of scopes) {
            const b=scope.querySelector('button[aria-label="Enviar"], button[aria-label="Send"], [data-icon="send"]');
            if (b && b.getClientRects().length && !b.disabled) { b.click(); return 'SENT'; }
          }
          return 'WAIT';
        })()""" % json.dumps(contact))
        if result == 'WRONG_CONTACT':
            raise RuntimeError('El chat seleccionado cambió antes de enviar; envío detenido.')
        if result == 'SENT':
            return
        time.sleep(0.5)
    raise RuntimeError('No se pudo confirmar el envío desde la vista previa de WhatsApp.')
