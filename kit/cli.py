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


def cmd_new(args):
    name = args.name
    dest = os.path.abspath(args.path or os.path.join(os.getcwd(), name))
    if os.path.exists(dest):
        sys.exit(f"❌ Error: El directorio destino ya existe: {dest}")

    print(f"🎬 [wvf new] Creando nuevo proyecto de video: '{name}' en {dest}...")
    shutil.copytree(TEMPLATE_DIR, dest)

    # Copiar herramientas
    tools_dest = os.path.join(dest, "tools")
    shutil.copytree(TOOLS_DIR, tools_dest)

    # Crear carpetas operativas
    for d in ("prompts", "flow", "frames", "audio", "check", "render_segments", "share", "scratch"):
        os.makedirs(os.path.join(dest, d), exist_ok=True)

    # Copiar inputs si se especificó --from
    if args.from_dir:
        src_from = os.path.abspath(args.from_dir)
        if os.path.isdir(src_from):
            print(f"📥 Copiando insumos desde: {src_from}...")
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
            # Auto-ingest
            print("📦 Ejecutando auto-ingest preliminar...")
            subprocess.run([sys.executable, os.path.join(dest, "tools", "ingest.py")], cwd=dest)
        else:
            print(f"⚠️ La ruta --from especificada no es un directorio: {src_from}")

    print(f"\n✅ Proyecto creado con éxito en: {dest}")
    print("👉 Siguientes pasos recomendados:")
    print(f"   1. cd '{os.path.relpath(dest)}'")
    print("   2. Revisa o edita inputs/brief.md")
    print("   3. Pide al agente o ejecuta: wvf ingest && wvf script")


def cmd_exec_tool(script_name, extra_args):
    cwd = os.getcwd()
    tool_path = os.path.join(cwd, "tools", script_name)
    if not os.path.isfile(tool_path):
        tool_path = os.path.join(TOOLS_DIR, script_name)
    if not os.path.isfile(tool_path):
        sys.exit(f"❌ Herramienta no encontrada: {script_name}")
    cmd = [sys.executable, tool_path] + extra_args
    return subprocess.run(cmd, cwd=cwd).returncode


def cmd_serve(args):
    port = args.port
    print(f"🌐 [wvf serve] Iniciando servidor local en http://127.0.0.1:{port}...")
    import http.server
    import socketserver
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
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
    subparsers = parser.add_subparsers(dest="command")

    # doctor
    subparsers.add_parser("doctor", help="Verifica el entorno, dependencias y skills")

    # new
    p_new = subparsers.add_parser("new", help="Crea un nuevo proyecto de video")
    p_new.add_argument("name", help="Nombre o slug del proyecto")
    p_new.add_argument("--path", help="Ruta de destino alternativa")
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

    # copy
    subparsers.add_parser("copy", help="Guía para generación de copys multicanal")

    args, unknown = parser.parse_known_args()

    if not args.command:
        print_banner()
        parser.print_help()
        sys.exit(0)

    if args.command == "doctor":
        sys.exit(cmd_doctor(args))
    elif args.command == "new":
        cmd_new(args)
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
        sys.exit(cmd_exec_tool("render.py", unknown))
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
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "copy":
        cmd_copy(args)


if __name__ == "__main__":
    main()
