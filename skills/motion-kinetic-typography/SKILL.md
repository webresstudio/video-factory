---
name: motion-kinetic-typography
description: >-
  Standardized system and runbook for designing high-end Motion Graphics (After Effects style),
  2D kinetic typography, and video explainers. Enforces strict typographical hierarchy,
  zero emojis (strictly Lucide / Yesicon SVGs), unboxed/borderless cinematic text overlays,
  justified-only chips, and scene-specific animation physics. Use whenever creating, styling,
  or animating on-screen text overlays, kinetic captions, or video motion graphics.
---

# Motion Graphics & Kinetic Typography Skill

A production-grade design system and runbook for implementing 2D/3D kinetic typography and on-screen motion graphics inspired by 2025/2026 high-end After Effects motion design (Apple Keynotes, Vox, CashApp, Linear, Kurzgesagt).

---

## 🏛️ The Three Golden Rules

### 1. Zero Emoticons — Lucide / Yesicon SVGs Only
* **Strictly Prohibited:** Never use Unicode emojis (`⚠️`, `🚨`, `💥`, `⚡`, `🔴`, `📊`, etc.) anywhere in video text overlays, titles, or subtitles. Unicode emojis look amateur, informal, and like generic AI output.
* **Strictly Required:** When an iconography element is genuinely required, use crisp, monoline vector SVGs from **Lucide** (`lucide.dev`) or **Yesicon** (`yesicon.app`):
  * Vector inline `<svg>` with `width="14"` to `18`, `height="14"` to `18`.
  * `fill="none"`, `stroke="currentColor"`, `stroke-width="2"` (or `1.75` for ultra-clean editorial lines).
  * Color-matched to the semantic tone (Emerald `#25D366`, Danger `#FF3B30`, Gold `#FFB300`, Ice `#38BDF8`).

### 2. Unboxed Typography — No Unnecessary Rectangular Containers
* **Never trap text in generic card boxes:** Do not put text inside dark rounded rectangles, modals, or card containers (`div.card`, `border: 1px solid rgba(...)`) across the video viewport unless it represents an explicit in-video UI mock (like a real WhatsApp message bubble or a physical credit card).
* **Cinematic Floating Overlay:**
  * Kinetic text should float freely integrated over the background imagery or video.
  * Guarantee legibility using deep multi-layer text shadows:
    ```css
    text-shadow: 
      0 2px 4px rgba(0, 0, 0, 0.8),
      0 6px 20px rgba(0, 0, 0, 0.95),
      0 0 40px rgba(0, 0, 0, 0.7);
    ```
  * Contrast support: Use a subtle, soft bottom scrim gradient on the video frame (`linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 35%, transparent 100%)`) without sharp borders or visible box edges.

### 3. Justified Chips Only — No Gratuitous Tags
* **Do not place tags/chips by default:** Avoid automatic eyebrow chips or badge tags (`[ALERTA]`, `[ESCENA 01]`) on every piece of text. Decorative tags clutter the screen.
* **When is a chip justified?**
  * Only when communicating an urgent, actionable constraint that needs visual separation (e.g., a critical countdown deadline `30 DE SEPTIEMBRE` or a hard operational status).
  * If the hero punch line and supporting phrase already explain the concept, omit the chip entirely.

---

## 📐 Typographic Hierarchy & Contrast

Motion graphics relies on extreme visual scale contrast:

Layer | Font Size | Weight & Font Family | Purpose & Styling
:--- | :--- | :--- | :---
**Hero Punch Line** | `26px – 34px` | `900` Outfit / Syne / Inter Display | The main psychological hook. High contrast, tight line-height (`1.05`), optional colored glow or keyword accent.
**Supporting Body** | `13px – 15px` | `600` Inter / Plus Jakarta Sans | Clear explanatory sentence. High legibility (`#E2E8F0` or `#F8FAFC`), line-height `1.35`.
**Data / Code Snippet**| `11px – 12px` | `700` JetBrains Mono | Used for quotes, URLs (`scalaos.com`), prices (`+$0.0113`), or parameters.
**Metric Callout** | `28px – 40px` | `900` Outfit (Mono tabular) | Numerical data points (`+38%`, `-80%`, `1.000`).

---

## ⚡ The 5 Motion Physics Archetypes (After Effects Presets)

Each scene must have an entrance animation tailored to its emotional narrative:

### 1. `Elastic Slam` (Shock / Breaking Changes)
* **Feel:** Heavy physical impact with spring bounce.
* **Best For:** Announcements of broken status quo, price hikes, policy changes.
* **Physics:**
  ```css
  .anim-elastic-slam {
    animation: elasticSlam 0.55s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  }
  @keyframes elasticSlam {
    0% { transform: scale(0.7) translateY(24px); opacity: 0; filter: blur(6px); }
    70% { transform: scale(1.05) translateY(-3px); opacity: 1; filter: blur(0); }
    100% { transform: scale(1) translateY(0); opacity: 1; }
  }
  ```

### 2. `Swipe Reveal` (Rules / Numbers / Limits)
* **Feel:** Sleek horizontal slide with synchronized expanding underline or mask.
* **Best For:** Quotas, time windows (24h), feature rules.
* **Physics:**
  ```css
  .anim-swipe-reveal {
    animation: swipeReveal 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }
  @keyframes swipeReveal {
    0% { transform: translateX(-30px); opacity: 0; filter: blur(4px); }
    100% { transform: translateX(0); opacity: 1; filter: blur(0); }
  }
  ```

### 3. `Haptic Rumble` (Alarms / Mistakes / Pitfalls)
* **Feel:** Mechanical vibration / angular jitter shaking the viewer awake.
* **Best For:** Mistakes, hidden costs, bad practices.
* **Physics:**
  ```css
  .anim-haptic-rumble {
    animation: hapticRumble 0.55s ease-out forwards;
  }
  @keyframes hapticRumble {
    0% { transform: scale(0.88); opacity: 0; }
    30% { transform: scale(1.05) rotate(1.8deg); opacity: 1; }
    50% { transform: scale(0.98) rotate(-1.8deg); }
    70% { transform: scale(1.02) rotate(1deg); }
    100% { transform: scale(1) rotate(0); opacity: 1; }
  }
  ```

### 4. `Liquid Float` (Solutions / Relief / Modern Tech)
* **Feel:** Smooth upward flotation with blur dissipation (`filter: blur(10px) -> blur(0)`).
* **Best For:** Solutions, native workflows, automation, savings.
* **Physics:**
  ```css
  .anim-liquid-float {
    animation: liquidFloat 0.55s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }
  @keyframes liquidFloat {
    0% { transform: translateY(28px) scale(0.92); opacity: 0; filter: blur(10px); }
    100% { transform: translateY(0) scale(1); opacity: 1; filter: blur(0); }
  }
  ```

### 5. `Digital Strobe` (Deadlines / Urgency / HUD)
* **Feel:** High-tech digital stutter/flicker like an illuminated LED display.
* **Best For:** Final countdowns, calls to action, urgent deadlines.
* **Physics:**
  ```css
  .anim-digital-strobe {
    animation: digitalStrobe 0.45s ease-out forwards;
  }
  @keyframes digitalStrobe {
    0% { opacity: 0; transform: scale(0.94); filter: brightness(2); }
    20% { opacity: 0.9; }
    40% { opacity: 0.2; }
    60% { opacity: 1; }
    80% { opacity: 0.6; }
    100% { opacity: 1; transform: scale(1); filter: brightness(1); }
  }
  ```

---

## 🛠️ Lucide SVG Integration Reference

Use these clean Lucide SVG icons instead of emojis:

* **Alert / Warning:**
  ```html
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
    <line x1="12" y1="9" x2="12" y2="13"/>
    <line x1="12" y1="17" x2="12.01" y2="17"/>
  </svg>
  ```
* **Clock / 24h Window:**
  ```html
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <polyline points="12 6 12 12 16 14"/>
  </svg>
  ```
* **Zap / Flows / Optimization:**
  ```html
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
  </svg>
  ```
* **Trending Down / Cost Reduction:**
  ```html
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/>
    <polyline points="17 18 23 18 23 12"/>
  </svg>
  ```
* **Shield / Security / Compliance:**
  ```html
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
  ```

---

## 📋 Quality Verification Checklist

Before finalizing any motion graphics text overlay, verify:
- [ ] **No Unicode emoticons** anywhere in the code or copy.
- [ ] All icons are valid **Lucide or Yesicon SVGs** with `stroke="currentColor"`.
- [ ] Text is **unboxed** (floats without unnecessary container borders or card backgrounds).
- [ ] High contrast is achieved via multi-layer `text-shadow` and soft scrim, not boxing.
- [ ] Any chip/tag present **strictly justifies its existence** by communicating a vital status.
- [ ] Each scene uses its designated **motion physics** curve.
