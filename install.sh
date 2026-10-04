#!/usr/bin/env bash
# ==============================================================================
# Webres Video Factory (WVF) · Universal macOS Installer
# Prepares any Mac (Apple Silicon or Intel) for deterministic video production.
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "================================================================="
echo "  🎬 Instalador Universal: Webres Video Factory (WVF)"
echo "================================================================="

# 1. Comprobar macOS
OS="$(uname -s)"
if [ "$OS" != "Darwin" ]; then
  echo "⚠️ Advertencia: WVF está optimizado para macOS (control de Chrome/WhatsApp por AppleScript)."
fi
ARCH="$(uname -m)"
echo "✓ Arquitectura detectada: macOS ($ARCH)"

# 2. Comprobar / Instalar Homebrew & FFmpeg
if ! command -v brew >/dev/null 2>&1; then
  echo "⚠️ Homebrew no detectado. Si no tienes ffmpeg, instálalo desde https://brew.sh"
else
  if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "📦 Instalando ffmpeg vía Homebrew..."
    brew install ffmpeg
  else
    echo "✓ FFmpeg instalado: $(command -v ffmpeg)"
  fi
fi

# 3. Comprobar / Instalar uv (gestor ultrarrápido de Python)
if ! command -v uv >/dev/null 2>&1 && [ ! -f "$HOME/.local/bin/uv" ]; then
  echo "📦 Instalando uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
UV_BIN="$(command -v uv 2>/dev/null || echo "$HOME/.local/bin/uv")"
echo "✓ uv disponible: $UV_BIN"

# 4. Configurar Entorno Virtual de Python (.venv)
if [ ! -d "$DIR/.venv" ]; then
  echo "📦 Creando entorno virtual Python en $DIR/.venv..."
  "$UV_BIN" venv "$DIR/.venv"
fi
VENV_PY="$DIR/.venv/bin/python"

echo "📦 Instalando librerías científicas y de síntesis..."
"$UV_BIN" pip install --python "$VENV_PY" \
  numpy scipy soundfile faster-whisper playwright pillow edge-tts

# 5. Instalar navegador Chromium para Playwright
echo "🌐 Verificando binario Chromium para Playwright..."
"$DIR/.venv/bin/playwright" install chromium

# 6. Registrar Skills Globalmente para Agentes de IA
echo "🧠 Registrando skills de producción en el sistema de agentes..."
GLOBAL_SKILLS_DIR="$HOME/.gemini/config/skills"
USER_AGENTS_DIR="$HOME/.agents/skills"
mkdir -p "$GLOBAL_SKILLS_DIR"
mkdir -p "$USER_AGENTS_DIR"

for skill_path in "$DIR/skills/"*; do
  if [ -d "$skill_path" ]; then
    s_name="$(basename "$skill_path")"
    # Link a global Gemini / Antigravity
    rm -rf "$GLOBAL_SKILLS_DIR/$s_name"
    ln -s "$skill_path" "$GLOBAL_SKILLS_DIR/$s_name" 2>/dev/null || cp -R "$skill_path" "$GLOBAL_SKILLS_DIR/$s_name"
    # Link a user universal agents
    rm -rf "$USER_AGENTS_DIR/$s_name"
    ln -s "$skill_path" "$USER_AGENTS_DIR/$s_name" 2>/dev/null || cp -R "$skill_path" "$USER_AGENTS_DIR/$s_name"
  fi
done
echo "✓ 7 Skills de diseño y retención registradas globalmente."

# 7. Crear enlace simbólico de wvf en PATH
echo "⚡ Configurando comando global 'wvf'..."
BIN_TARGET="$HOME/.local/bin"
mkdir -p "$BIN_TARGET"
rm -f "$BIN_TARGET/wvf"
ln -s "$DIR/bin/wvf" "$BIN_TARGET/wvf"

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  echo ""
  echo "💡 TIP: Agrega ~/.local/bin a tu PATH en ~/.zshrc:"
  echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# 8. Verificación final
echo ""
echo "🩺 Ejecutando diagnóstico..."
"$DIR/bin/wvf" doctor

echo ""
echo "================================================================="
echo "  🎉 Instalación de Webres Video Factory completada."
echo "  Pruébalo con: wvf new \"mi-primer-video\""
echo "================================================================="
