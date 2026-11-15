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
  - Run `wvf audit-script borrador.json --lang es` (supports `--allow-override`) and verify `PASS` before showing the script.
* Structure every group of related shots as its own micro-story: **problem → hook → solution**. Plan these three beats for each group; do not rely on a single video-level hook and payoff.
* Use the approachable **2-tier phonetic cadence** at `1.0x` (strictly zero `atempo`):
  - **Tier 1 · Pulso Ágil (`10–18` phonetic words → `~3.5–5.8 s`):** `Omni 1.1 Flash · 6 s · 720p` (`10 credits`), 1 camera+position state.
  - **Tier 2 · Pulso Extendido (`19–24` phonetic words → `~6.0–7.8 s`):** `Omni 1.1 Flash · 8 s · 720p` (`12 credits`) + a mid-take visual shift at `~4.0–4.8 s` in `engine.js` so no visual state exceeds `6.2 s`.
* Keep `script.json` as the spoken-script and presenter-direction source. Put shot-level visual decisions in the project's edit plan or production notes so dialogue does not become cluttered with camera and animation instructions.
* Also read `internet-video-2026` and `tiktok-promote-ui-demos` (`2.135B`-view TikTok Promote Creative Center rules: Safe Zone `x: 72–910px`, `y: 200–1320px`; dual subtitle export `1745px` IG/Shorts vs `1380px` TikTok `?tiktok=1`).
* **Crucial Rule on Pronunciation & Phonetic Contagion (`flow_qc lint`):**
  Flow @me spells out uppercase acronyms (`"API"` → `"la ápi"`) AND suffers from **English-to-Spanish phonetic contagion** when mixing English tech terms (`Blender`, `Hydrogen`, `Orchestrator`, `prompt`) with Spanish/Maya cognates (`"gran jaguar"` → `"gran yawar"`). Use explicit accent guides in `spoken_text` (`"gran jáguar"`, `"Haidroyen"`, `"Orquestreitor"`) and verify with `wvf tool flow_qc lint`.
* **USER APPROVAL CHECKPOINT 1:** Present the spoken-script table with its concise shot plan or storyboard. Do not generate Flow narration or commit to expensive visual production until the user approves the content and direction.

### Phase 3: Presenter & Voice Generation (Flow `@me`)
* Check avatar likeness chip:
  Must verify that the user's likeness chip is active in the Flow prompt box before submitting.
* Lint prompts BEFORE spending credits (blocks quotes in English stage block, exaggerated body words, and consecutive camera repeats):
  ```bash
  wvf tool make_prompts
  wvf tool flow_qc lint --line L01 --prompt prompts/L01_r1.txt
  wvf tool flow_submit --dur 6 --res 720p --prompt-file prompts/L01_r1.txt
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

### Phase 5: Motion Graphics, Retention Sweetspot & Unison Engine (`engine.js` / `serie.js` + `unison.js`)
* **Mandatory Retention & Spatial Director Skill:**
  - `wbrs-retention-sweetspot`: Enforces `4.0–6.0 s` visual state pulses (`Cam A/B/C/D × Pos P1..P5` alternation), `#zback` Z-Depth giant typography behind the presenter (`z-index: 14`, `-0.45x` opposite parallax), seamless full-canvas `1080×1920` B-roll with auto-measured RGBA `nativeHairY` (zero `mode: 'half'`, zero `#flash`), `< 0.5 s` Swiss `#FFFFFF` Pie Charts + `84 px` Causal Cursor + collectible `#s9-sheet`, and Story V2 `1255..1415 px` Instagram Sticker corridor. Run `wvf audit-sweetspot` before rendering to emit `check/engineering_manifest.json`.
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

### Phase 6: Audio Architecture & Psychoacoustic Mix (`wbrs-psychoacoustic-mix` + FlowMusic)
* **Mandatory Psychoacoustic & Harmonic Audit (`wbrs-psychoacoustic-mix`):**
  - Before mixing any FlowMusic candidate track, audit it with Constant-Q (`Q=34`) CQT analysis:
    ```bash
    wvf audit-music audio/candidata.m4a --target-dur 48
    ```
  - Enforces Major key (`≥ 80%` CQT diatonic purity, zero minor/chromatic clash under executive voice), melodic energy centered in **Octaves 3–4 (`180–780 Hz`)** avoiding shrill upper octaves (`> 1.6 kHz`), `0` internal splices, consonant root-tuned SFX (`≤ 1` cue per `5 s`), vocal-pocket EQ (`-2.2 dB @ 1.9 kHz`), `-12.0 to -13.5 dB` bed-to-voice delta, and `-14.0 LUFS / -1.5 dBTP` master compliance.
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

### Phase 10: Multi-Channel Social Copy & Professional Presentation Package
* Read skill: `social-copy-multichannel-2026` and obey `WBRS/AGENTS.md` §E.
* Format captions with 4-layer multimodal SEO alignment, flawless natural Spanish, open-loop retention, and zero forced agency brochure pitches:
  - **Instagram Reels:** Searchable meta-title hook `<125` characters before `…más`, open loop to end-card, plus dedicated **Alt Text** (*Configuración avanzada*).
  - **TikTok:** Natural search-query opening sentence `<80` characters + multi-audience bridge + open loop.
  - **LinkedIn:** **H.O.O.P.S. 2026** executive framework (searchable hook `<160` chars, orientation, on-screen bridge, `01/02/03` dwell-time breakdown, substantive operational question).
  - **YouTube Shorts:** Complete idiomatic title `<55` characters, SEO description, and pinned comment.
* **Professional Video Presentation Package (`AGENTS.md` §E):**
  Whenever the user requests the **professional presentation of the video** (*«presentación profesional del video»*), always deliver together in a single unified artifact/response (playable directly in Antigravity, never auto-sent to WhatsApp unless explicitly requested):
  1. **Main Video(s)** (Reels/Shorts/LinkedIn + TikTok Safe Zone edition).
  2. **All Story Videos** (Instagram Stories + TikTok/WhatsApp editions).
  3. **Contact Sheet for Every Video** (one unobstructed final-render contact sheet with footer timestamps for the main video + one for every story video).
  4. **Social Media Prompts / Copy** (`COPYS-REDES.md` updated with IG + Alt Text, TikTok, LinkedIn, Shorts + Story rollout order using **per-brand, per-network empirical optimal windows** where `Facebook ≠ Instagram ≠ TikTok` via `wvf analytics --save-windows`, never a hardcoded hour).
* **Post-Publish Analytics & Quantitative Video Ledger (`social-analytics-audit`):**
  - Audit live retention curves across **TikTok Studio**, **YouTube Studio Shorts** (Polymer Shadow DOM), **Meta Business Suite**, and **Instagram** (with zero tab-focus stealing), recalibrate independent publish windows, and record the fair-weighted `WBRS Score (0–100)`:
    ```bash
    wvf analytics --platform all --yt-video <shortId> --self-subs <n> --save-windows
    wvf ledger record --project . --exclude-self-follows <n>
    wvf ledger compare
    ```

---

## 🛠️ CLI Quick Reference

```bash
wvf doctor                                    # Verify system tools, Chrome, and 17 skills
wvf init [--client <name>]                    # Initialize WVF directly in current directory
wvf start [--port 4391]                       # Launch dashboard and live preview in Chrome
wvf media [add <files...> | list]             # Manage and catalog project media assets
wvf new "project-name" [--from <folder>]      # Scaffold project in a new folder
wvf ingest                                    # Ingest research and media assets
wvf audit-script <draft> [--allow-override]   # Validate 2-tier (6s/8s) listicle/story script
wvf timeline                                  # Align vocal track and generate timing.js
wvf audit-sweetspot [--project <dir>]         # Audit 4-6s visual pulse, Z-Depth, HairY & Story V2
wvf cues                                      # Export window.CUES to audio/cues.json
wvf audit-music <track> [--voice] [--master]  # CQT Major purity, Oct 3-4 & -14 LUFS mix audit
wvf audio                                     # Procedural sound design & -14 LUFS mix
wvf flowmusic [--status | --nav | --import]   # Connect & import FlowMusic project tracks
wvf frames [seconds...]                       # Spot-check animation frames
wvf render [--workers 4] [--fps 60]           # Full deterministic export
wvf qa                                        # Technical compliance & Whisper audit
wvf share [--send-wa]                         # Compress & send to WhatsApp
wvf analytics [--save-windows]                # Multi-studio audit + per-brand FB/IG/TT deploy hours
wvf ledger [compare | score | record]         # WBRS Score (0-100) accounting & history
wvf fix-word <Lxx> <word> <phonetic_phrase>   # Surgical vocal patch
wvf tool <name> [args...]                     # Run any pipeline tool (e.g. flow_qc, make_prompts)
```

## Initialization, updates and repair

The default template is a complete WhatsApp example, not a generic scene generator. Adapt factual content, DOM and word anchors for each new topic. Fresh previews estimate word times and display an example notice. Render mode rejects missing `timing.js`; demo timing must never be used to publish a video.

A project folder holds only what is edited for that video (`engine.js`, `index.html`, `style.css`, scripts, timing, media). Pipeline tools live only in the package, so every package fix reaches every project. To customize a tool for one video, copy just that file into the project's `tools/`: `wvf` runs it, and imports resolve from `tools/` first and then from the package. Always run tools through `wvf` (`wvf tool <name>`), never `python tools/...`, so that layering applies. `wvf start` lists a project's own tools.

`wvf init` preserves existing configuration; `--force` refreshes template files. Neither ever touches `tools/`. The installer preserves existing custom skills. Use `wvf --version` to identify the installed release.

`wvf fix-word` is for voiceover-only lines. It validates the existing word before generation, supports `--patch-file`, `--patch-word`, `--patch-words` and `--occurrence`, backs up the original audio and timestamps, replaces the word within its original interval, and rebuilds the timeline. For on-camera lines regenerate the whole take to preserve lip sync. After patching, rebuild audio, render and QA; the previous master remains unchanged until these commands run.

Do not generate Flow clips or send WhatsApp messages as a software smoke test. Use `tests/test_regressions.py` and `tests/smoke_pipeline.py`; the latter exercises the actual local pipeline with synthetic test narration. External connectors still require a signed-in compatible UI session.
