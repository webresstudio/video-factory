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
   Videos are NEVER recorded in real time. Every single frame is evaluated through `window.renderAt(t)`. Repeated timestamps must reproduce the same frame in the tested browser/runtime. Pin the runtime and assets when reproducibility across machines is required.
2. **Word-Level Micro-Synchronization:**
   Animation events, counter rolls, icon strikes, and transition cuts do NOT use arbitrary timers. They trigger strictly on the millisecond where the presenter pronounces that specific word, queried through `W("Lxx", "palabra")`. Whisper timestamps are estimates, stored with three decimals; validate speech alignment by listening.
3. **Zero-Slop Fact-Checking:**
   Never invent statistics, percentages, or pricing tiers. Only facts validated in `facts.md` are permitted in the script.
4. **Streaming Audio Delivery:**
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
* Generates `facts_candidates.md` and `media_catalog.json`; preserves `facts.md`. Extracted bullets are unverified candidates. Confirm sources and dates before adding facts to `facts.md`. PDF/DOCX extraction is not built into ingest; extract these documents with appropriate document tools first.

### Phase 2: Scriptwriting (`script.json` / `GUION.md`)
* Read [`references/story-led-scriptwriting.md`](references/story-led-scriptwriting.md) to plan the narrative and shot language together, including camera coverage, cut rhythm, text/image composition, purposeful motion, retention beats, and CTA.
* **For Listicle / "N Things / N Commands / N Tools" Videos (`viral-listicle-story`):**
  - Activate `viral-listicle-story` mandatory laws: NEVER enumerate as a flat spoken dictionary (`"Uno… Dos… Tres…"`). Chain all `N` items into ONE continuous `Pero / Entonces` story with `L01` 3-Channel Non-Duplication (`< 40%` overlap between spoken hook and `≤ 6-word` screen headline), `L02` Human Pain/Stake (`#040/#072` TikTok Promote) before item `#1`, high sentence-length burstiness (`CV ≥ 0.55`), spatial mid-roll CTA (`"aquí al lado"` pointing right `x ≈ 900px`, `#113` TikTok), and Dual-Engine Closing (Named-Persona DM Send in voice + Collectible `N/N` Map Card on screen for Saves `#031/#079` + verbal loop).
  - Run `wvf audit-script borrador.json --lang es` (or `audit_listicle.py`) and verify `PASS` before showing the script.
* Structure every group of related shots as its own micro-story: **problem → hook → solution**. Plan these three beats for each group; do not rely on a single video-level hook and payoff.
* Treat the template structure of 8–10 lines, 6–8 seconds (`R3`), and 15–20 words per line (max 22 at `1.0x`, strictly zero `atempo`) as the Flow `1.0x` vocal budget. Fit the spoken script to the topic, evidence, platform, target duration, and natural neutral Guatemalan Spanish delivery.
* Keep `script.json` as the spoken-script and presenter-direction source. Put shot-level visual decisions in the project's edit plan or production notes so dialogue does not become cluttered with camera and animation instructions.
* Also read `internet-video-2026` and `tiktok-promote-ui-demos` (`2.135B`-view TikTok Promote Creative Center rules: Safe Zone `x: 72–910px`, `y: 200–1320px`; dual subtitle export `1745px` IG/Shorts vs `1380px` TikTok `?tiktok=1`).
* **Crucial Rule on Pronunciation:**
  Flow @me spells out uppercase acronyms (e.g., "API" becomes "a-pe-i-ai"). Write phonetic equivalents in the script or prompt (`"la ápi"`).
* **USER APPROVAL CHECKPOINT 1:** Present the spoken-script table with its concise shot plan or storyboard. Do not generate Flow narration or commit to expensive visual production until the user approves the content and direction.

### Phase 3: Presenter & Voice Generation (Flow `@me`)
* Check avatar likeness chip:
  Must verify that the user's likeness chip is active in the Flow prompt box before submitting.
* Run:
  ```bash
  wvf tool make_prompts
  wvf tool flow_submit --dur 8 --res 720p --prompt-file prompts/L01.txt
  ```
* For on-camera scenes (typically 3 scenes: hook/premise, midpoint, warning), upscale to 1080p via `wvf tool flow_dl1080 L01`.
* Extract audio and transcribe word timestamps:
  ```bash
  wvf tool inspect_clip L01
  ```

### Phase 4: Word Clock & Timeline
* Assemble master vocal track and export timing data:
  ```bash
  wvf timeline
  ```
* Trims pre-speech and post-speech dead zones. Extracts 24 fps camera frames from the 1080p clip when available, otherwise from the downloaded clip.
* Compresses quiet pauses on voiceover-only lines.
* Outputs `audio/voice.wav` and `timing.js`.

### Phase 5: Motion Graphics & Unison Explanatory Engine (`engine.js` / `serie.js` + `unison.js`)
* Read foundational design & transition skills:
  - `motion-kinetic-typography`: Unboxed Swiss typography, Lucide SVG icons, zero emojis.
  - `dynamic-text-animations`: Horizon unmask, character cascades, hairline draw-ins.
  - `commercial-video-transitions-2026`: Iris match-cuts, knife-edge shutters, 2.5D spatial pushes (8–18 frames).
  - `impeccable`: Craft-floor adherence, no gradients on text, no generic cards.
  - `tiktok-promote-ui-demos`: Safe Zone `x: 72–910px, y: 200–1320px`, `2.5x` single-control UI magnification, `?tiktok=1` subtitle shift (`top: 1380px`).
* Read the **5 Unison Explanatory Animation Skills** (for visual proof locked to spoken words):
  - `hyperframes-causal-cursor` (`heygen-com/hyperframes` ★ 77.7K): Oversized `90–124px` physical cursor (`U.createCursor`), same-frame click ignition on `W()` / `S.W()`, cut-the-curve vector seams, zero idle wobble, and 3-view seam/mobile (`360px`) QA.
  - `manim-progressive-proof` (`3b1b/manim` ★ 96.0K + `motion-canvas` ★ 19.7K): `Wrong → Right` in-situ state morphing (`U.morphPair`), spotlight dimming (`opacity: 0.24` via `U.spotlight`), and `ValueTracker` physical meters.
  - `gsap-word-sequencer` (`greensock/gsap-skills` ★ 17.7K): Semantic word-clock label blocks, relative offsets, zero DOM reflow inside `renderAt(t)` (`transform`, `opacity`, `clip-path` only).
  - `shotcraft-ui-recipes` (`Vincentwei1021/video-shotcraft` ★ 16.2K): Real product-token UI surfaces (`slash-interview-card`, `defect-to-rule-stamp`, `parallel-lanes-sprint`, `collectible-cheat-sheet`) and `≤ 3` full-camera slams.
  - `lottie-attention-choreography` (`LottieFiles/motion-design-skill` ★ 2.7K + `remotion-dev/skills` ★ 6.1K): Single visual protagonist per instant, `1/3` simultaneous active elements rule (`U.staggerIn`), `20–30%` counter-motion parallax, real-font glyph measurement.
* Synchronize elements using:
  ```javascript
  const t_start = W("L05", "mil"); // or S.W("mil") in DEM scenes
  ```
* Preview frames rapidly:
  ```bash
  wvf frames 1.5 7.8 14.2
  ```

### Phase 6: Audio Architecture & Sound Design (Synthesis & FlowMusic)
* **Client Project URL Configuration:**  
  Each project can configure client-specific Google Flow and FlowMusic project URLs in `project_config.json`:
  ```json
  {
    "client_name": "Webres Studio",
    "flow": { "project_url": "https://flow.google.com/..." },
    "flowmusic": { "project_url": "https://www.flowmusic.app/project/..." }
  }
  ```
* **FlowMusic Integration:**
  - Check tracks in the client's FlowMusic project: `wvf flowmusic --status`
  - Navigate/Open the project in Chrome: `wvf flowmusic --nav`
  - Import a downloaded track directly into the audio pipeline: `wvf flowmusic --import track.mp3`
* Export animation visual cues:
  ```bash
  wvf cues
  ```
* Synthesize harmonic pads (or mix FlowMusic stem) with motion SFX & -10 dB voice ducking:
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
* Muxes video chunks with `audio/master.wav` into `nombre_del_proyecto_master.mp4`, named after the project folder (e.g. `SCALA OS Broma Ad` → `scala_os_broma_ad_master.mp4`). `wvf qa` and `wvf share` pick that file; if it is missing and several `*_master.mp4` exist, they stop and ask for the path.

### Phase 8: Technical & Vocal QA
* Run comprehensive audit:
  ```bash
  wvf qa
  ```
* Rejects technical noncompliance and compares the final Whisper transcription against `script.json` (or `spoken_text` when provided), with a default maximum word error rate of 5%. A missing transcription fails full QA. `--technical-only` explicitly limits the audit to technical measurements. Inspect `check/qa_report.json`, review the contact sheet and listen before publishing; transcription does not prove pronunciation accuracy.

### Phase 9: Mobile Compression & Distribution
* Compress to lightweight version (<15 MiB), using duration-based two-pass bitrate and an enforced output-size check:
  ```bash
  wvf share
  ```
* Only when the user explicitly authorizes sending, send to the WhatsApp Web chat already selected in Chrome. Its title must match the requested contact:
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
wvf init [--client <name>]                    # Initialize WVF directly in current directory
wvf start [--port 4391]                       # Launch dashboard and live preview in Chrome
wvf media [add <files...> | list]             # Manage and catalog project media assets
wvf new "project-name" [--from <folder>]      # Scaffold project in a new folder
wvf ingest                                    # Ingest research and media assets
wvf timeline                                  # Align vocal track and generate timing.js
wvf cues                                      # Export window.CUES to audio/cues.json
wvf audio                                     # Procedural sound design & -14 LUFS mix
wvf flowmusic [--status | --nav | --import]   # Connect & import FlowMusic project tracks
wvf frames [seconds...]                       # Spot-check animation frames
wvf render [--workers 4] [--fps 60]           # Full deterministic export
wvf qa                                        # Technical compliance & Whisper audit
wvf share [--send-wa]                         # Compress & send to WhatsApp
wvf fix-word <Lxx> <word> <phonetic_phrase>   # Surgical vocal patch
wvf tool <name> [args...]                     # Run any pipeline tool (e.g. make_prompts, flow_submit)
```

## Initialization, updates and repair

The default template is a complete WhatsApp example, not a generic scene generator. Adapt factual content, DOM and word anchors for each new topic. Fresh previews estimate word times and display an example notice. Render mode rejects missing `timing.js`; demo timing must never be used to publish a video.

A project folder holds only what is edited for that video (`engine.js`, `index.html`, `style.css`, scripts, timing, media). Pipeline tools live only in the package, so every package fix reaches every project. To customize a tool for one video, copy just that file into the project's `tools/`: `wvf` runs it, and imports resolve from `tools/` first and then from the package. Always run tools through `wvf` (`wvf tool <name>`), never `python tools/...`, so that layering applies. `wvf start` lists a project's own tools.

`wvf init` preserves existing configuration; `--force` refreshes template files. Neither ever touches `tools/`. The installer preserves existing custom skills. Use `wvf --version` to identify the installed release.

`wvf fix-word` is for voiceover-only lines. It validates the existing word before generation, supports `--patch-file`, `--patch-word`, `--patch-words` and `--occurrence`, backs up the original audio and timestamps, replaces the word within its original interval, and rebuilds the timeline. For on-camera lines regenerate the whole take to preserve lip sync. After patching, rebuild audio, render and QA; the previous master remains unchanged until these commands run.

Do not generate Flow clips or send WhatsApp messages as a software smoke test. Use `tests/test_regressions.py` and `tests/smoke_pipeline.py`; the latter exercises the actual local pipeline with synthetic test narration. External connectors still require a signed-in compatible UI session.
