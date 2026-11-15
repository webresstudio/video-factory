---
name: wbrs-retention-sweetspot
description: >-
  Master visual retention engineering runbook for Webres Studio (WVF) vertical videos
  (1080x1920 @ 60fps) and 10.00s V2 Launch Stories. Enforces the 4-6s camera+position
  pulse (with approachable 2-tier 6s/8s word cadence), monumental Z-Depth typography
  behind the RGBA presenter (#zback + opposite -0.45x parallax), seamless full-canvas
  nativeHairY anchoring, sub-0.5s Swiss pie-chart cards, 84px causal cursor choreography,
  and Instagram Link Sticker corridor geometry (y: 1255-1415px). Use before designing or
  auditing index.html, engine.js, style.css, or story_nuevo_video.html.
---

# WBRS Retention Sweetspot & Z-Depth Visual Engineering (`wbrs-retention-sweetspot`)

Empirical engineering specification distilled from second-by-second retention curves (`React Fiber` vectors in TikTok Studio, Meta Business Suite, and Instagram Insights) and governed by `/Users/williamromero/MediaProjects/WBRS/AGENTS.md` and `/Users/williamromero/MediaProjects/WBRS/manual_ingenieria_retencion_punto_dulce.md`.

---

## 1. The `4–6 s` Visual State Law & Approachable 2-Tier Word Timing

Human visual habituation on vertical feeds triggers thumb-scroll after **`~6.2 seconds`** in an unchanged framing, while hyperactive cuts (`< 2.8 s`) destroy executive authority. Never force unnatural Spanish phrasing to hit a rigid word count—decouple natural spoken sentence length from the `4–6 s` visual refresh using two complementary tiers:

| Tier | Phonetic Word Budget | Spoken Duration (`1.000x`) | Flow Generation (`Omni 1.1 Flash · 720p`) | How `engine.js` Satisfies the `4–6 s` Visual Pulse |
| :--- | :---: | :---: | :---: | :--- |
| **Tier 1 · Pulso Ágil (Default)** | **`10 – 18 words`** *(sweetspot `12–17`)* | `3.5 – 5.8 s` | **`6 s · 720p`** (`10 credits`) | Entire take is one crisp visual beat; switch **both Camera Angle and Spatial Position** on the next take. |
| **Tier 2 · Pulso Extendido (Full Idea / Case)** | **`19 – 24 words`** | `6.0 – 7.8 s` | **`8 s · 720p`** (`12 credits`) | Voice flows naturally in one unbroken take, while **`engine.js` triggers a clean mid-take spatial shift at `t_local ≈ 4.0–4.8 s`** (e.g., `Pos P2 → P4` cutting to 100% Fullscreen on the punchline, or Card A → Card B with `zoom 1.06 → 1.16`). |

### Mandatory Cold-Open Visual Proof (`0.0–1.4 s`) & Duration/End-Card Law
Validated across TikTok Studio (`0:01` primary drop-off) and YouTube Studio (`7.0 %` *Se quedaron viendo* vs `93.0 %` *Saltaron el contenido*, while viewers who stay watch **`24.0 s`** on average):
- **Never open `0.0–3.5 s` with presenter-only talking-head when the video has visual demos:** Show a **`0.0–1.4 s` fullscreen or split-canvas visual flash** of the strongest visual proof (e.g., 3D wireframe → monument or live 60fps UI) BEFORE or behind the opening hook sentence (`first_visual_proof_sec <= 8.5 s`).
- **Ban Pure Narrative Setup Bridges (*Show-While-Telling*):** Never spend `6–7 s` on camera merely announcing *"Pusimos a los dos a..."* or *"Pero atento a la segunda prueba, les pedimos..."*. Cut directly into the live visual proof at `0.0 s` of the sentence while William narrates over or below it.
- **Duration Band (`44–62 s`) & Collectible Sheet Entry (`<= 56.0 s`):** Keep total runtime `<= 64 s` so the final collectible summary sheet (`#s9-sheet`) enters at **`<= 56.0 s`**—placing it at `75 s+` starves Instagram/TikTok Saves because `< 5 %` of cold viewers remain that late.

### Mandatory `4 Cameras × 5 Spatial Positions` Alternation Matrix
Consecutive visual states **must change both optical camera angle (`Cam A..D`) and canvas layout (`Pos P1..P5`)**:
- **`Cam A` (Frontal Executive):** Eye-level chest-up frontal shot (`nativeHairY ≈ 280–346 px`). Best for UI walkthroughs and closing CTA.
- **`Cam B` (25° Low-Angle Authority):** Subtle upward tilt (`nativeHairY ≈ 415–425 px`). Pattern interrupt for mid-video contradiction Re-hooks (*«¡Pero atento!»*).
- **`Cam C` (35° Editorial Three-Quarter):** Torso angled `35°` left or right, eyes locked on lens (`nativeHairY ≈ 308–356 px`). Best for statistical contrasts.
- **`Cam D` (Intimate Close-Up `1.18x–1.26x`):** Tight head-and-shoulders leaning slightly in (`nativeHairY ≈ 240–265 px`). Best for urgent secrets and the human Moral.
- **`Pos P1` (Monumental Z-Depth):** RGBA presenter (`headTop: 568`, `zoom: 1.13`) in front of `404px RamaC` headline (`#zback`, `z-index: 14`). Zero white cards allowed.
- **`Pos P2` (Compact Floating Twin Pie Cards):** White `#FFFFFF` twin cards (`y: 56..740 px`) + large presenter emerging below (`headTop: 775 px`).
- **`Pos P3` (Authentic Product UI `668 px`):** Real product interface (`y: 48..718 px`) + `84 px` Causal Cursor + presenter at `headTop: 885 px`.
- **`Pos P4` (100% Pure Fullscreen):** Presenter fills `1080 × 1920 px` (`zoom: 1.05–1.12`), zero white cards.
- **`Pos P5` (Collectible Swiss End-Sheet `#s9-sheet`):** Summary guide (`y: 54..770 px`) + silent Causal Cursor click on `Guardar guía` + presenter at `headTop: 795 px` with `#cap` subtitles hidden.

---

## 2. Monumental Z-Depth Typography Behind Presenter (`#zback`)

Validated in production (`3.85%` Story CTR record). To make giant text behind William look like broadcast 3D compositing rather than an accidental overlap, obey all **5 optical rules**:

1. **5-Plane Z-Index Stack (`1080 × 1920 px`):**
   - `#cv-bg` (`z-index: 2`): Continuous Emerald Aurora gradient (`#074235 → #052E24 → #021711`) + B-roll (`alpha: 0.72, bright: 0.42`) + bottom scrim.
   - `#zback` (`z-index: 14`): Giant condensed uppercase word (`1–2` short words max, `<= 9` chars/line).
   - `#cv-will` (`z-index: 26`): 2D Canvas rendering macOS Vision RGBA presenter matte (`matte/L0X/%04d.png`).
   - `#front` (`z-index: 34–42`): Unboxed chest-level caption (`top: 1118 px`) + SVG strokes.
2. **Bouma's `<= 25%` Bottom-Overlap Geometry:**
   - Set `#zback` headline in `RamaGothicRoundedC-Heavy` at `font-size: 404px; line-height: 0.78; top: 332px` (cap-height spans `y = 332..648 px`, `316 px` tall).
   - Anchor presenter crown at **`targetHeadTop = 568 px`**: William's hair/head overlaps only `y = 568..648 px` (`80 px` = `25.3%` bottom of glyphs), keeping the top `74.7%` (where uppercase crossbars live) `100%` unobstructed.
3. **Hard Vector Step-Shadow (Never Blurry Neon Glow):**
   ```css
   .zback-giant {
     font: 900 404px/0.78 "RamaC", sans-serif;
     letter-spacing: 0.008em;
     text-transform: uppercase;
     color: #C8FF2E; /* Lime for entity; #FF5E54 coral for threat */
     text-shadow:
       6px 6px 0 #007A56,               /* Step 1 solid mid-tone (#881B14 for coral) */
       14px 16px 0 #021510,             /* Step 2 deep ink */
       0 28px 56px rgba(0, 0, 0, 0.70); /* Atmospheric depth */
   }
   ```
4. **Opposite Horizontal Parallax (`-0.45x` vs `+0.35x`):**
   - Given virtual camera drift `dx = Math.sin(t * 0.85 + 0.4) * 12`:
     - `#zback` moves **`paraX = -dx * 0.45`**
     - `#cv-will` moves **`px = (1080 - 1080 * zoom) / 2 + dx * 0.35`**
5. **Contact Shadow & `destination-out` Torso Fade:**
   - Paint `#cv-will` with `shadowColor = 'rgba(1, 10, 8, 0.82)', shadowBlur = 46, shadowOffsetY = 14`.
   - Never hard-crop torso above `y = 1920`: apply `globalCompositeOperation = 'destination-out'` alpha gradient over `y = 1430..1730 px`.

---

## 3. Seamless Full-Canvas Background & Automatic `nativeHairY`

- **Zero `mode: 'half'` Rectangular Clips:** Always paint `drawFullBrollBg(ctxBg, t)` continuously from `y = 0` to `y = 1920` in one unclipped pass so a semi-transparent seam never crosses William's forehead.
- **Exact Crown Anchor Formula:** Different Flow angles place the top of the hair at different native Y coordinates (`245 px` in Close-Up vs `420 px` in Low-Angle). Always scan `matte/L0X/0001.png` via `wvf audit-sweetspot` and position William with:
  ```js
  const py = targetHeadTop - nativeHairY * zoom + dy * 0.35;
  ```
  where `targetHeadTop = cardBottomY + 30` (typically `24–36 px` below the upper card).

---

## 4. `< 0.5 s` Swiss Information Cards (`#FFFFFF`) & VFX Rules

1. **Ban Multi-Row Text Tables:** Replace tables with **Twin Pie / Donut Cards (`180 px` rings on `#FFFFFF`)** featuring an explicit platform eyebrow (`EN GOOGLE MAPS` `#10B981` vs `EN CHATGPT` `#EF4444`), `48–56 px InterTight 900` center number, and `<= 4` word label (`0–1%` retention drop in live telemetry). Put study attribution (`SOCi · 350,000 ubicaciones`) in a subtle `22 px` subtitle instead of wasting `5 s` of voiceover.
2. **Ban `#flash` & Restrict `#ribbon`:**
   - **Zero `#flash` elements or white strobes** anywhere in the video.
   - **Zero `#ribbon` wipes at the end of the hook (`t ≈ 4–6 s`)**, where diagonal wipes act as an "end-of-intro" exit cue (`-5 pts` drop). Use spring cuts (`k = 215, d = 18`) synced to camera changes; at most `1` editorial wipe entering the final Swiss guide.
3. **84px Causal Cursor (`createCausalCursor`) & Split Dual-Channel CTA:**
   - Every UI state change is caused by an `84 px` white cursor (`#0F172A` stroke + `#10B981` click ring) traveling `0.32 s` ahead of `S.W('palabra')` and compressing to `scale(0.84)` for `90 ms`.
   - **Final Pulse (`Pos P5`):** Hide `#cap` subtitles automatically, click `Guardar guía` **visually** with the cursor + `click` SFX (no spoken *"Guarda o comenta"* disjunction), and dedicate the spoken audio to **one specific comment question** (never telling business owners to *"send this to whoever runs your website"*).

---

## 5. `10.00 s @ 60 fps` Launch Story V2 (`story_nuevo_video.html`)

- **3-Act Minimal Structure:**
  - **Act I (`0.00–2.48 s`):** 3D Brand Emblem (`y = 312 px`) + Poster Headline (`264–312 px RamaC`) + SVG red underline (`#E3261F`). Zero white cards.
  - **Act II (`2.48–7.64 s`):** Elastic RGBA Presenter (`headTop = 568 px`) in front of `404 px` Z-Depth keyword (`#C8FF2E` mutating to `#FF5E54` on the spoken threat word).
  - **Act III (`7.64–10.00 s`):** Conversion Poster (`MIRA EL / VIDEO / COMPLETO.`) + curved lime SVG arrow (`#arw`) landing at `(786, 1346)`.
- **Sacred Instagram Link Sticker Corridor (`?net=ig`):**
  - Keep **`y = 1255 px` to `y = 1415 px` (`160 px` vertical band) `100%` empty** (`#story-cap` stays above at `top: 1118 px`; `#igRow` stays below at `top: 1456 px`).
- **TikTok / WhatsApp Variant (`?net=tt`):** Hides `#arw` and `#igCta`, showing `#ttCta` at `top: 1370 px` (*«Nuevo video · Míralo completo en el perfil»*).
- **Mandatory 2-Story Launch Pair (`has_dual_story_pair`):**
  - **Story 1 (`story_nuevo_video.html` — T+15 min):** Presenter Z-Depth authority hook + Link Sticker (`1255..1415 px`).
  - **Story 2 (`story_<demo>.html` — T+4 to 6 hours):** `100 %` visual proof split/showcase of the video's strongest demo (e.g. 3D + interactive web) with clean `1255..1415 px` Link Sticker corridor to capture visual-first scrollers.

---

## 6. Automated Audit & Manifest Generation

Run before and after rendering to measure `nativeHairY`, verify `4–6 s` visual pulses, check `#flash` / sticker corridor rules, and generate `check/engineering_manifest.json`:

```bash
wvf audit-sweetspot
# Or explicitly on a project path:
python3 /Users/williamromero/MediaProjects/WBRS/video-factory/kit/tools/audit_sweetspot.py --project .
```
