#!/usr/bin/env python3
"""WVF (Webres Video Factory) Main CLI Implementation.

Provides human-friendly and agent-friendly commands to orchestrate
broadcast-quality vertical explainer videos.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
FACTORY_ROOT = os.path.abspath(os.path.join(HERE, ".."))
TOOLS_DIR = os.path.join(FACTORY_ROOT, "kit", "tools")
TEMPLATE_DIR = os.path.join(FACTORY_ROOT, "kit", "templates", "default")
SKILLS_DIR = os.path.join(FACTORY_ROOT, "skills")

sys.path.insert(0, TOOLS_DIR)
import env_config


def print_banner():
    banner = """
  ╔═══════════════════════════════════════════════════════════════════╗
  ║   W V F  ·  W E B R E S   V I D E O   F A C T O R Y               ║
  ║   Engineered 60fps Deterministic Motion Graphics & Voice Pipeline ║
  ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner.strip())


def cmd_doctor(args):
    print("\n🩺 [wvf doctor] Diagnosticando entorno de producción...")
    ok = True

    # 1. ffmpeg
    try:
        ff = env_config.get_ffmpeg()
        out = subprocess.run([ff, "-version"], capture_output=True, text=True).stdout.splitlines()[0]
        print(f"  ✓ FFmpeg:         {ff} ({out[:40]})")
    except Exception as e:
        print(f"  ❌ FFmpeg:        NO ENCONTRADO ({e})")
        ok = False

    # 2. ffprobe
    try:
        fp = env_config.get_ffprobe()
        print(f"  ✓ FFprobe:        {fp}")
    except Exception as e:
        print(f"  ❌ FFprobe:       NO ENCONTRADO ({e})")
        ok = False

    # 3. Google Chrome
    ch = env_config.get_chrome()
    if ch:
        print(f"  ✓ Google Chrome:  {ch}")
    else:
        print("  ⚠️ Google Chrome:  Ruta estándar no encontrada (se usará Chromium Playwright)")

    # 4. Python libraries
    libs = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("soundfile", "soundfile"),
        ("faster_whisper", "faster-whisper"),
        ("playwright", "playwright"),
        ("PIL", "pillow"),
    ]
    for mod, name in libs:
        try:
            __import__(mod)
            print(f"  ✓ Python Lib:     {name}")
        except ImportError:
            print(f"  ❌ Python Lib:     {name} FALTANTE")
            ok = False

    # Check packaged scaffold as well as installed dependencies.
    for required in ("index.html", "engine.js", "style.css", "script.json"):
        if not os.path.isfile(os.path.join(TEMPLATE_DIR, required)):
            print(f"  ❌ Plantilla incompleta: {required}")
            ok = False

    # 5. Skills
    req_skills = [
        "internet-video-2026",
        "motion-kinetic-typography",
        "dynamic-text-animations",
        "commercial-video-transitions-2026",
        "social-copy-multichannel-2026",
        "impeccable",
    ]
    all_skills_ok = True
    for s in req_skills:
        sp = os.path.join(SKILLS_DIR, s, "SKILL.md")
        if os.path.isfile(sp):
            pass
        else:
            print(f"  ❌ Skill:         {s} NO ENCONTRADA en el paquete")
            all_skills_ok = False
            ok = False
    if all_skills_ok:
        print(f"  ✓ Skills:         {len(req_skills)} habilidades de producción empaquetadas OK")

    # 6. Global skills installation check
    glob_skill_dir = os.path.expanduser("~/.gemini/config/skills")
    if os.path.isdir(glob_skill_dir):
        print(f"  ✓ Agente Global:  Directorio de skills activo ({glob_skill_dir})")
    else:
        print("  ℹ️ Agente Global:  Directorio global no existe aún (se configurará con ./install.sh)")

    print()
    if ok:
        print("✨ ¡Todo listo! Tu entorno está 100% preparado para producir videos con WVF.")
    else:
        print("⚠️ Hay dependencias faltantes. Ejecuta: ./install.sh")
    return 0 if ok else 1


def cmd_init(args):
    dest = os.path.abspath(args.path or os.getcwd())
    print_banner()
    print(f"🎬 [wvf init] Inicializando Video Factory en: {dest}")

    if args.from_dir and not os.path.isdir(args.from_dir):
        raise SystemExit(f"❌ No existe el directorio de insumos: {args.from_dir}")
    os.makedirs(dest, exist_ok=True)

    existing_config = os.path.isfile(os.path.join(dest, "project_config.json"))
    # Copiar archivos de plantilla sin sobreescribir si ya existen
    for item in os.listdir(TEMPLATE_DIR):
        s = os.path.join(TEMPLATE_DIR, item)
        d = os.path.join(dest, item)
        if os.path.isdir(s):
            for source_root, _, files in os.walk(s):
                relative = os.path.relpath(source_root, s)
                target_root = os.path.join(d, relative)
                os.makedirs(target_root, exist_ok=True)
                for filename in files:
                    target = os.path.join(target_root, filename)
                    if args.force or not os.path.exists(target):
                        shutil.copy2(os.path.join(source_root, filename), target)
        else:
            if not os.path.exists(d) or args.force:
                shutil.copy2(s, d)

    # Las herramientas no se copian: viven en el paquete. tools/ del proyecto solo guarda las que se personalicen,
    # y init nunca lo modifica (ni con --force).

    # Crear carpetas operativas
    for d in ("prompts", "flow", "frames", "audio", "check", "render_segments", "share", "scratch", "inputs/research", "inputs/media"):
        os.makedirs(os.path.join(dest, d), exist_ok=True)

    # Configuración de cliente
    client_name = args.client or "Webres Studio"
    flow_url = args.flow_url or "https://flow.google.com/"
    flowmusic_url = args.flowmusic_url or "https://www.flowmusic.app/"

    cfg = {
        "client_name": client_name,
        "flow": {
            "project_url": flow_url,
            "likeness_label": "Yo"
        },
        "flowmusic": {
            "project_url": flowmusic_url,
            "preferred_track": "Tech Commercial",
            "ducking_db": -9.5,
            "use_imported_track": True
        }
    }
    cfg_file = os.path.join(dest, "project_config.json")
    if existing_config and not args.force:
        with open(cfg_file, encoding="utf-8") as fh:
            cfg = json.load(fh)
        if args.client:
            cfg["client_name"] = args.client
        if args.flow_url:
            cfg.setdefault("flow", {})["project_url"] = args.flow_url
        if args.flowmusic_url:
            cfg.setdefault("flowmusic", {})["project_url"] = args.flowmusic_url
    with open(cfg_file, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2, ensure_ascii=False)
    client_name = cfg.get("client_name", client_name)

    # Ingestar insumos si se especificó --from
    if args.from_dir:
        src_from = os.path.abspath(args.from_dir)
        if os.path.isdir(src_from):
            print(f"📥 Copiando insumos iniciales desde: {src_from}...")
            inp_res = os.path.join(dest, "inputs", "research")
            inp_med = os.path.join(dest, "inputs", "media")
            for root, _, files in os.walk(src_from):
                for f in files:
                    full = os.path.join(root, f)
                    ext = os.path.splitext(f)[1].lower()
                    if ext in (".md", ".txt", ".pdf", ".docx", ".json"):
                        shutil.copy2(full, os.path.join(inp_res, f))
                    elif ext in (".png", ".jpg", ".jpeg", ".webp", ".svg", ".mp4", ".mov", ".wav", ".mp3"):
                        shutil.copy2(full, os.path.join(inp_med, f))
            if cmd_exec_tool("ingest.py", [], cwd=dest):
                raise SystemExit("❌ La ingesta de insumos falló.")

    print(f"\n✅ Video Factory inicializado exitosamente para: {client_name}")
    print("👉 Puedes lanzar el entorno interactivo de producción con:")
    print("   wvf start")
    return 0


def cmd_start(args):
    cwd = os.getcwd()
    engine_file = os.path.join(cwd, "engine.js")
    if not os.path.isfile(engine_file):
        sys.exit("❌ Error: wvf start debe ejecutarse dentro de un proyecto inicializado.\n   Ejecuta 'wvf init' o 'wvf new <nombre>' primero.")

    print_banner()
    print(f"🚀 [wvf start] Iniciando entorno de producción y vista previa...")

    # Diagnóstico del proyecto
    has_brief = os.path.isfile(os.path.join(cwd, "inputs", "brief.md"))
    has_facts = os.path.isfile(os.path.join(cwd, "facts.md"))
    has_script = os.path.isfile(os.path.join(cwd, "script.json"))
    has_timing = os.path.isfile(os.path.join(cwd, "timing.js"))
    has_master_audio = os.path.isfile(os.path.join(cwd, "audio", "master.wav"))
    cands_video = glob.glob(os.path.join(cwd, "*_master.mp4")) + glob.glob(os.path.join(cwd, "*.mp4"))

    print("\n📊 Estado actual del proyecto:")
    print(f"  {'✓' if has_brief or has_facts else '○'} 1. Ingesta:    {'facts.md disponible' if has_facts else 'Pendiente (wvf ingest)'}")
    print(f"  {'✓' if has_script else '○'} 2. Guion:      {'script.json listo' if has_script else 'Pendiente'}")
    print(f"  {'✓' if has_timing else '○'} 3. Timeline:   {'timing.js sincronizado' if has_timing else 'Pendiente (wvf timeline)'}")
    print(f"  {'✓' if has_master_audio else '○'} 4. Audio:      {'master.wav (-14 LUFS) listo' if has_master_audio else 'Pendiente (wvf audio)'}")
    print(f"  {'✓' if cands_video else '○'} 5. Video:      {os.path.basename(cands_video[0]) if cands_video else 'Pendiente de render (wvf render)'}")
    tools_dir = os.path.join(cwd, "tools")
    own_tools = sorted(f for f in os.listdir(tools_dir) if os.path.isfile(os.path.join(tools_dir, f))) if os.path.isdir(tools_dir) else []
    print(f"  🔧 Herramientas propias: {', '.join(own_tools) if own_tools else 'ninguna (usa todas las del paquete)'}")

    port = args.port
    preview_url = f"http://127.0.0.1:{port}/index.html"
    print(f"\n🌐 Servidor de previsualización en: {preview_url}")

    # Iniciar servidor estático
    import http.server
    import socketserver
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
        print(f"✓ Servidor activo en puerto {port}. Presiona Ctrl+C para detener.")
        if not args.no_open:
            subprocess.run(["open", preview_url], capture_output=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
    return 0


def cmd_media(args):
    cwd = os.getcwd()
    med_dir = os.path.join(cwd, "inputs", "media")
    os.makedirs(med_dir, exist_ok=True)

    action = getattr(args, "media_action", None) or "list"
    files = getattr(args, "files", [])

    if action == "add" or files:
        targets = files if files else []
        if not targets:
            print("⚠️ Debes especificar al menos un archivo para agregar. Ejemplo: wvf media add logo.png clip.mp4")
            return 1

        print(f"📥 [wvf media add] Agregando {len(targets)} archivo(s) a inputs/media/...")
        for t in targets:
            if os.path.isfile(t):
                dest = os.path.join(med_dir, os.path.basename(t))
                shutil.copy2(t, dest)
                print(f"  ✓ Copiado: {os.path.basename(t)}")
            else:
                print(f"  ❌ Archivo no encontrado: {t}")

        # Ejecutar auto-ingest
        print("\n⚙️ Catalogando activos multimedia...")
        cmd_exec_tool("ingest.py", [], cwd=cwd)

    # List / Inspect
    cat_file = os.path.join(cwd, "media_catalog.json")
    if not os.path.isfile(cat_file):
        cmd_exec_tool("ingest.py", [], cwd=cwd)

    if os.path.isfile(cat_file):
        items = json.load(open(cat_file, encoding="utf-8"))
        print(f"\n📂 [wvf media] Catálogo de Activos Multimedia ({len(items)} activos en inputs/media/):")
        if not items:
            print("  (No hay archivos en inputs/media/ todavía. Usa: wvf media add <archivos...>)")
            return 0
        print(f"  {'NOMBRE':<28} {'TIPO':<8} {'DIMENSIONES':<12} {'DURACIÓN':<10} {'ENFOQUE / AJUSTE'}")
        print("  " + "-" * 78)
        for it in items:
            name = it.get("name", "")[:26]
            mtype = it.get("type", "")
            dims = f"{it.get('width','?')}x{it.get('height','?')}" if it.get('width') else "-"
            dur = f"{it.get('duration')}s" if it.get("duration") else "-"
            note = it.get("fit_note", "")
            print(f"  {name:<28} {mtype:<8} {dims:<12} {dur:<10} {note}")
        print()
    return 0


def cmd_new(args):
    name = args.name
    dest = os.path.abspath(args.path or os.path.join(os.getcwd(), name))
    if os.path.exists(dest):
        sys.exit(f"❌ Error: El directorio destino ya existe: {dest}")

    args.path = dest
    args.force = False
    return cmd_init(args)


def cmd_exec_tool(script_name, extra_args, cwd=None):
    """Única forma de lanzar herramientas: tools/ del proyecto primero, luego el paquete (también al importar)."""
    if sys.version_info < (3, 11):
        sys.exit("❌ WVF requiere Python 3.11 o superior para dar prioridad a tools/ del proyecto. Ejecuta ./install.sh.")
    cwd = cwd or os.getcwd()
    cmd = env_config.tool_command(script_name, extra_args, root=cwd)
    if not os.path.isfile(cmd[1]):
        sys.exit(f"❌ Herramienta no encontrada: {script_name}")
    return subprocess.run(cmd, cwd=cwd, env=env_config.tool_env(cwd)).returncode


def cmd_tool(args):
    name = args.name
    if not os.path.splitext(name)[1]:
        name = next((name + ext for ext in (".py", ".sh") if os.path.isfile(env_config.tool_path(name + ext, os.getcwd()))), name + ".py")
    return cmd_exec_tool(name, args.args)


def cmd_serve(args):
    port = args.port
    print(f"🌐 [wvf serve] Iniciando servidor local en http://127.0.0.1:{port}...")
    import http.server
    import socketserver
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
        print(f"✓ Servidor activo en puerto {port}. Presiona Ctrl+C para detener.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor cerrado.")


def cmd_copy(args):
    print("📝 [wvf copy] Generando textos optimizados para redes (LinkedIn, Shorts, Reels, TikTok)...")
    cwd = os.getcwd()
    facts_file = os.path.join(cwd, "facts.md")
    script_file = os.path.join(cwd, "script.json")
    if not os.path.isfile(script_file):
        sys.exit("❌ script.json no encontrado en el directorio actual.")
    print("💡 Consulta la skill social-copy-multichannel-2026 para estructurar los ganchos y el embudo de conversión.")


def main():
    parser = argparse.ArgumentParser(
        description="WVF — Webres Video Factory CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    with open(os.path.join(FACTORY_ROOT, "VERSION"), encoding="utf-8") as version_file:
        version = version_file.read().strip()
    parser.add_argument("--version", action="version", version=f"wvf {version}")
    subparsers = parser.add_subparsers(dest="command")

    # doctor
    subparsers.add_parser("doctor", help="Verifica el entorno, dependencias y skills")

    # init
    p_init = subparsers.add_parser("init", help="Inicializa Video Factory directamente en el directorio actual")
    p_init.add_argument("--path", help="Ruta de destino alternativa (default: actual)")
    p_init.add_argument("--client", help="Nombre del cliente o marca (default: Webres Studio)")
    p_init.add_argument("--flow-url", help="URL del proyecto en Google Flow")
    p_init.add_argument("--flowmusic-url", help="URL del proyecto en FlowMusic")
    p_init.add_argument("--from", dest="from_dir", help="Directorio con archivos de investigación o medios para auto-importar")
    p_init.add_argument("--force", action="store_true", help="Sobreescribe archivos de plantilla existentes")

    # start
    p_start = subparsers.add_parser("start", help="Lanza el entorno de producción, dashboard de estado y vista previa en Chrome")
    p_start.add_argument("--port", type=int, default=4391, help="Puerto del servidor local (default: 4391)")
    p_start.add_argument("--no-open", action="store_true", help="No abrir automáticamente el navegador")

    # media
    p_media = subparsers.add_parser("media", help="Gestiona, inspecciona y agrega insumos multimedia (fotos, videos, logos)")
    p_media.add_argument("media_action", nargs="?", default="list", choices=["list", "add", "inspect"], help="Acción: list, add, inspect")
    p_media.add_argument("files", nargs="*", help="Archivos a agregar (ej: wvf media add logo.png)")

    # new
    p_new = subparsers.add_parser("new", help="Crea un nuevo proyecto de video")
    p_new.add_argument("name", help="Nombre o slug del proyecto")
    p_new.add_argument("--path", help="Ruta de destino alternativa")
    p_new.add_argument("--client", help="Nombre del cliente")
    p_new.add_argument("--flow-url", help="URL del proyecto Flow")
    p_new.add_argument("--flowmusic-url", help="URL del proyecto FlowMusic")
    p_new.add_argument("--from", dest="from_dir", help="Directorio con archivos de investigación o medios para auto-importar")

    # ingest
    subparsers.add_parser("ingest", help="Escanea inputs/research y inputs/media, genera facts.md y media_catalog.json")

    # timeline
    subparsers.add_parser("timeline", help="Sincroniza audio vocal por palabra y genera timing.js")

    # cues
    subparsers.add_parser("cues", help="Extrae eventos de animación window.CUES a audio/cues.json")

    # audio
    subparsers.add_parser("audio", help="Genera síntesis armónica procedural, SFX por cues y mezcla a -14 LUFS")

    # frames
    p_frames = subparsers.add_parser("frames", help="Captura frames para inspección rápida")
    p_frames.add_argument("times", nargs="*", help="Segundos específicos para capturar")

    # render
    p_render = subparsers.add_parser("render", help="Render determinista 60fps frame a frame con Chrome CDP")
    p_render.add_argument("--workers", type=int, default=4, help="Número de workers en paralelo")
    p_render.add_argument("--fps", type=int, default=60, help="Frames por segundo")
    p_render.add_argument("--test", action="store_true", help="Render de prueba de 2 segundos")

    # qa
    p_qa = subparsers.add_parser("qa", help="Auditoría integral técnica y vocal del master MP4")
    p_qa.add_argument("file", nargs="?", help="Ruta al video master")

    # share
    p_share = subparsers.add_parser("share", help="Comprime versión ligera (<15MB) y opcionalmente envía a WhatsApp")
    p_share.add_argument("--master", help="Ruta al archivo master")
    p_share.add_argument("--send-wa", action="store_true", help="Envía a chat de WhatsApp Web")
    p_share.add_argument("--contact", default="William Romero", help="Nombre del contacto en WhatsApp")

    # fix-word
    p_fix = subparsers.add_parser("fix-word", help="Corrige quirúrgicamente la pronunciación de una palabra")
    p_fix.add_argument("line_id", help="ID de la línea (e.g. L09)")
    p_fix.add_argument("target_word", help="Palabra a reemplazar")
    p_fix.add_argument("phonetic_phrase", help="Frase fonética para el clip corto")

    # serve
    p_serve = subparsers.add_parser("serve", help="Servidor estático local para el motor HTML")
    p_serve.add_argument("--port", type=int, default=4391, help="Puerto local (default: 4391)")

    # flowmusic
    p_fm = subparsers.add_parser("flowmusic", help="Gestiona y conecta con el proyecto FlowMusic del cliente")
    p_fm.add_argument("--status", action="store_true", help="Inspecciona pistas y estado del proyecto en Chrome")
    p_fm.add_argument("--nav", nargs="?", const="", help="Abre o navega Chrome al proyecto FlowMusic")
    p_fm.add_argument("--import", dest="import_file", help="Importa pista de audio descargada hacia audio/music_flowmusic.wav")

    # copy
    subparsers.add_parser("copy", help="Guía para generación de copys multicanal")

    # tool
    p_tool = subparsers.add_parser("tool", help="Ejecuta una herramienta del paquete (o la versión propia del proyecto en tools/)")
    p_tool.add_argument("name", help="Nombre de la herramienta, p. ej. make_prompts o flow_submit")
    p_tool.add_argument("args", nargs=argparse.REMAINDER, help="Argumentos para la herramienta")

    args, unknown = parser.parse_known_args()

    if not args.command:
        print_banner()
        parser.print_help()
        sys.exit(0)

    if args.command == "doctor":
        sys.exit(cmd_doctor(args))
    elif args.command == "init":
        sys.exit(cmd_init(args))
    elif args.command == "start":
        sys.exit(cmd_start(args))
    elif args.command == "media":
        sys.exit(cmd_media(args))
    elif args.command == "new":
        sys.exit(cmd_new(args))
    elif args.command == "ingest":
        sys.exit(cmd_exec_tool("ingest.py", unknown))
    elif args.command == "timeline":
        sys.exit(cmd_exec_tool("build_timeline.py", unknown))
    elif args.command == "cues":
        sys.exit(cmd_exec_tool("export_cues.py", unknown))
    elif args.command == "audio":
        sys.exit(cmd_exec_tool("build_audio.py", unknown))
    elif args.command == "frames":
        sys.exit(cmd_exec_tool("frames.py", args.times + unknown))
    elif args.command == "render":
        extra = ["--workers", str(args.workers), "--fps", str(args.fps)]
        if args.test:
            extra.append("--test")
        sys.exit(cmd_exec_tool("render.py", extra + unknown))
    elif args.command == "qa":
        extra = [args.file] if args.file else []
        sys.exit(cmd_exec_tool("qa.py", extra + unknown))
    elif args.command == "share":
        extra = []
        if args.master: extra += ["--master", args.master]
        if args.send_wa: extra += ["--send-wa"]
        if args.contact: extra += ["--contact", args.contact]
        sys.exit(cmd_exec_tool("share.py", extra + unknown))
    elif args.command == "fix-word":
        sys.exit(cmd_exec_tool("fix_word.py", [args.line_id, args.target_word, args.phonetic_phrase] + unknown))
    elif args.command == "flowmusic":
        extra = []
        if args.status: extra.append("--status")
        if args.nav is not None: extra += ["--nav", args.nav] if args.nav else ["--nav"]
        if args.import_file: extra += ["--import", args.import_file]
        sys.exit(cmd_exec_tool("flowmusic.py", extra + unknown))
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "copy":
        cmd_copy(args)
    elif args.command == "tool":
        sys.exit(cmd_tool(args))


if __name__ == "__main__":
    main()
