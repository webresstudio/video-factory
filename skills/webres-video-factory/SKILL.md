---
name: webres-video-factory
description: >-
  State-of-the-art production manual and technical execution engine for broadcast-quality,
  retention-engineered vertical videos (1080x1920, 60fps). Combines Google Flow @me digital
  avatar voice cloning, whisper word-clock alignment, deterministic headless Chrome CDP rendering,
  procedural audio synthesis, and viral 2026 social copywriting.
---

# Webres Video Factory (WVF) · Production Manual & Agent Runbook

WVF is the official video production standard of **Webres Studio**. It replaces amateur video editing software and screen recording with a **pure mathematical, deterministic code-to-video pipeline**.

---

## 🏛️ The 4 Non-Negotiable Laws of WVF

1. **Deterministic Render (`renderAt(t)` as a Pure Function):**
   Videos are NEVER recorded in real time. Every single frame is evaluated through `window.renderAt(t)`. The exact same timestamp `t` must render the exact same pixels on any machine.
2. **Word-Level Micro-Synchronization:**
   Animation events, counter rolls, icon strikes, and transition cuts do NOT use arbitrary timers. They trigger strictly on the millisecond where the presenter pronounces that specific word, queried through `W("Lxx", "palabra")`.
3. **Zero-Slop Fact-Checking:**
   Never invent statistics, percentages, or pricing tiers. Only facts validated in `facts.md` are permitted in the script.
4. **Broadcast Audio Standards:**
   Final audio must be 48 kHz stereo normalized to **-14 LUFS (±1.0 LUFS)** with True Peak **≤ -1.0 dBTP** under ITU-R BS.1770 / EBU R128. Music must automatically duck under vocals by -8 dB to -10 dB.

---

## 🧭 The 10-Phase Production Workflow

```
[Phase 1: Ingestion & Brief] ──> [Phase 2: Scriptwriting] ──> [Phase 3: Flow @me Voice]
                                                                        │
[Phase 6: Audio Synthesis]  <── [Phase 5: Motion Graphics] <── [Phase 4: Word Clock]
          │
[Phase 7: 60fps CDP Render] ──> [Phase 8: QA & Audit]     ──> [Phase 9: Mobile & WA]
                                                                        │
                                                               [Phase 10: Social Copy]
```

### Phase 1: Ingestion & Asset Cataloging
* When the user provides documents, links, or media files, place them in `inputs/research/` or `inputs/media/`.
* Run:
  ```bash
  wvf ingest
  ```
* Generates `facts.md` and `media_catalog.json`.

### Phase 2: Scriptwriting (`script.json`)
* Structure: 8–10 lines of 8–10 seconds each (18–22 words per line).
* Read skill: `internet-video-2026` (hook in <1.0s, re-hooks at tip numbers, seamless loop ending).
* **Crucial Rule on Pronunciation:**
  Flow @me spells out uppercase acronyms (e.g., "API" becomes "a-pe-i-ai"). Write phonetic equivalents in the script or prompt (`"la ápi"`).
* **USER APPROVAL CHECKPOINT 1:** Present the script table to the user. Do not generate audio until approved.

### Phase 3: Presenter & Voice Generation (Flow `@me`)
* Check avatar likeness chip:
  Must verify that the user's likeness chip is active in the Flow prompt box before submitting.
* Run:
  ```bash
  python tools/make_prompts.py
  python tools/flow_submit.py --dur 8 --res 720p --prompt-file prompts/L01.txt
  ```
* For on-camera scenes (typically 3 scenes: hook/premise, midpoint, warning), upscale to 1080p via `tools/flow_dl1080.py`.
* Extract audio and transcribe word timestamps:
  ```bash
  python tools/inspect_clip.py L01
  ```

### Phase 4: Word Clock & Timeline
* Assemble master vocal track and export timing data:
  ```bash
  wvf timeline
  ```
* Trims pre-speech and post-speech dead zones.
* Compresses quiet pauses on voiceover-only lines.
* Outputs `audio/voice.wav` and `timing.js`.

### Phase 5: Motion Graphics Engine (`engine.js`)
* Read skills:
  - `motion-kinetic-typography`: Unboxed Swiss typography, Lucide SVG icons, zero emojis.
  - `dynamic-text-animations`: Horizon unmask, character cascades, hairline draw-ins.
  - `commercial-video-transitions-2026`: Iris match-cuts, knife-edge shutters, 2.5D spatial pushes (8–18 frames).
  - `impeccable`: Craft-floor adherence, no gradients on text, no generic cards.
* Synchronize elements using:
  ```javascript
  const t_start = W("L05", "mil"); // exact second where presenter says "mil"
  ```
* Preview frames rapidly:
  ```bash
  wvf frames 1.5 7.8 14.2
  ```

### Phase 6: Audio Architecture & Sound Design
* Export animation visual cues:
  ```bash
  wvf cues
  ```
* Synthesize harmonic pads and motion SFX:
  ```bash
  wvf audio
  ```
* Generates `audio/master.wav` (-14 LUFS) and `audio/master.m4a`.

### Phase 7: Deterministic CDP Render (60 fps)
* Starts local server:
  ```bash
  wvf serve &
  ```
* Renders frame-by-frame across parallel workers:
  ```bash
  wvf render --workers 4 --fps 60
  ```
* Muxes video chunks with `audio/master.wav` into `whatsapp_ahorro_master.mp4`.

### Phase 8: Technical & Vocal QA
* Run comprehensive audit:
  ```bash
  wvf qa
  ```
* Confirms 1080x1920, 60.0 fps, -14 LUFS, and transcribes final audio with Whisper to verify 100% pronunciation accuracy.

### Phase 9: Mobile Compression & Distribution
* Compress to lightweight version (<15MB):
  ```bash
  wvf share
  ```
* Optionally send directly to WhatsApp Web self-chat:
  ```bash
  wvf share --send-wa --contact "William Romero"
  ```

### Phase 10: Multi-Channel Social Copy
* Read skill: `social-copy-multichannel-2026`.
* Format captions for:
  - **LinkedIn:** Executive briefing with market context and bottom-line impact.
  - **YouTube Shorts:** Title <55 characters, description, pinned comment.
  - **Instagram Reels:** Hook before 125-character cutoff, save/DM keyword.
  - **TikTok:** Search-query opening line, numbered takeaways, debate prompt.

---

## 🛠️ CLI Quick Reference

```bash
wvf doctor                                    # Verify system tools, Chrome, and skills
wvf new "project-name" [--from <folder>]      # Scaffold project
wvf ingest                                    # Ingest research and media assets
wvf timeline                                  # Align vocal track and generate timing.js
wvf cues                                      # Export window.CUES to audio/cues.json
wvf audio                                     # Procedural sound design & -14 LUFS mix
wvf frames [seconds...]                       # Spot-check animation frames
wvf render [--workers 4] [--fps 60]           # Full deterministic export
wvf qa                                        # Technical compliance & Whisper audit
wvf share [--send-wa]                         # Compress & send to WhatsApp
wvf fix-word <Lxx> <word> <phonetic_phrase>   # Surgical vocal patch
```
