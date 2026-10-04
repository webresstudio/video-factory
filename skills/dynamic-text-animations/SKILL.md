---
name: dynamic-text-animations
description: >-
  Commercial broadcast motion design system and technical runbook for crafting high-end
  kinetic typography, vector ribbon/flag reveals, and animated brand identity systems.
  Inspired by premier global studios (Ordinary Folk, Studio Dumbar, Buck, Collins, Apple).
  Enforces zero-AI-cliché aesthetics, strict prohibition of chips/badges, unboxed Swiss
  typographic layouts, vector stroke draws, and an automated pipeline for animating custom logos.
---

# Commercial Kinetic Typography & Vector Motion Design Skill

A broadcast-grade design system and runbook for designing, coding, and animating on-screen motion graphics that feel physical, editorial, and commercial. Formulated to eliminate "AI-generated video" stereotypes (neon glow overlays, floating chips, generic dark cards, rubber-band bounces) and replace them with the techniques used by world-class studios (**Ordinary Folk, Studio Dumbar, Buck, Pentagram, DIA Studio**).

---

## 🚫 The Anti-AI Cliché Manifest (Strict Rules)

1. **NO CHIPS / NO FLOATING PILLS (Absolute Prohibition):**
   - Never wrap subtitles, tags, percentages, or categories in pill-shaped badges (`rounded-full bg-emerald-950/40 border border-emerald-500/30`).
   - *Why:* Nothing screams "cheap AI video generator" louder than floating neon chips. 
   - *The Studio Standard:* Use Swiss typographic hierarchy, monospaced micro-labels with wide kerning (`tracking-[0.2em]`), and fine hairline vector guide rules.

2. **NO ELECTRIC NEON OVERGLOW (The "Crypto / Cyber Slop" Trap):**
   - Avoid bathing every word in electric cyan/lime text-shadows (`text-shadow: 0 0 30px #00cea7`). It looks like a 2021 NFT promo.
   - *The Studio Standard:* Pure surgical whites (`#FFFFFF`), architectural warm creams (`#F5F5F0`), deep obsidian blacks (`#0B0F19`), and purposeful solid color blocking (cobalt blue `#1E40AF`, cadmium amber `#F59E0B`, refined studio teal `#00CEA7`).

3. **NO CARD TRAPPING (The Modal Window Anti-pattern):**
   - Never place metrics or text inside translucent rounded boxes (`.pricing-grid`, `.card`) just to separate them from the footage.
   - *The Studio Standard:* If text is illegible, the background footage is too busy. Fix the footage, apply a feathered cinema scrim, or use bold vector backplates.

4. **NO CHEAP VARIABLE WEIGHT KEYFRAME BREAKS:**
   - Animating `font-weight: 300` to `900` across standard CSS keyframes results in jerky stepped jumps.
   - *The Studio Standard:* Use verified variable font axes (`font-variation-settings: 'wght' var(--w)`), or achieve impact through vector scale-punches, geometric tracking shifts, and vector track mattes.

5. **NO AMATEUR RUBBER-BAND BOUNCES:**
   - Eliminate elastic overshoot animations that wobble like gelatin. Use exponential deceleration (`cubic-bezier(0.16, 1, 0.3, 1)` or `easeOutExpo`).

---

## 🏛️ Commercial Studio Motion Archetypes (Ordinary Folk & Studio Dumbar Inspired)

### 1. `Dynamic Vector Ribbon & Flag Slicer` (The Commercial Broadcast Reveal)
* **The Concept:** A bold, graphic SVG polygon ribbon or diagonal geometric flag sweeps across the frame behind the typography. The headline is unmasked in real time via an aligned track matte / clip-path as the ribbon passes.
* **Why It Works:** Creates tactile momentum and integrates graphic shapes directly with letterforms. Frequently seen in Nike, Google, and TED commercials.
* **Web / Motion Implementation:**
  ```html
  <div class="relative overflow-hidden py-4">
    <!-- SVG Vector Ribbon sweeping behind -->
    <svg class="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none" viewBox="0 0 100 100">
      <polygon class="anim-ribbon-sweep" points="0,0 25,0 5,100 -20,100" fill="#00CEA7" />
      <polygon class="anim-ribbon-trail" points="20,0 45,0 25,100 0,100" fill="#1E40AF" opacity="0.6" />
    </svg>
    <!-- Masked Typography revealing in synchronization -->
    <h2 class="anim-flag-text font-black text-4xl text-white tracking-tight">
      INGENIERÍA SIN FRICCIONES
    </h2>
  </div>
  ```
  ```css
  .anim-ribbon-sweep {
    transform: translateX(-120%);
    animation: sweepAcross 0.65s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }
  .anim-flag-text {
    clip-path: polygon(0 0, 0 0, 0 100%, 0% 100%);
    animation: clipReveal 0.65s cubic-bezier(0.16, 1, 0.3, 1) 0.08s forwards;
  }
  @keyframes sweepAcross {
    0% { transform: translateX(-120%) skewX(-15deg); }
    100% { transform: translateX(350%) skewX(-15deg); }
  }
  @keyframes clipReveal {
    0% { clip-path: polygon(0 0, 0 0, 0 100%, 0% 100%); }
    100% { clip-path: polygon(0 0, 100% 0, 100% 100%, 0% 100%); }
  }
  ```

---

### 2. `Swiss Editorial Data Grid` (Bloomberg & Pentagram Authority)
* **The Concept:** Complete replacement for tacky pricing cards. Data is arranged in an open, unboxed architectural grid defined by crisp 1px hairline drafting rules, corner crosshairs (`+`), and bold monolithic numbers.
* **Why It Works:** Communicates multi-million dollar engineering credibility rather than a consumer coupon.
* **Layout Structure:**
  ```
  +-----------------------------------+-----------------------------------+
  | 01 // INPUT INFERENCE             | 02 // OUTPUT GENERATION           |
  | $2.00                             | $10.00                            |
  | / 1,000,000 TOKENS                | / 1,000,000 TOKENS                |
  +-----------------------------------+-----------------------------------+
  // INFRAESTRUCTURA GEMINI 4 ARGON • PROMPT CACHE REDUCTION -95%
  ```
* **Animation Sequence:**
  1. Fine vector horizontal and vertical drafting lines draw in from center (`scaleX(0) -> scaleX(1)`).
  2. Numbers rise from a masked baseline slot with clean vertical deceleration.
  3. Footnote technical telemetry appears with character tracking expansion.

---

### 3. `Masked Horizon Unmask` (Apple Keynote Style)
* **The Concept:** Monolithic typography emerges vertically from an invisible razor-sharp horizon slot.
* **Easing Curve:** `cubic-bezier(0.16, 1, 0.3, 1)` (Zero rebound, pure mass).
* **CSS Implementation:**
  ```css
  .mask-horizon {
    overflow: hidden;
    display: inline-block;
  }
  .anim-horizon-rise {
    transform: translateY(110%);
    opacity: 0;
    filter: blur(8px);
    animation: horizonRise 0.65s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }
  @keyframes horizonRise {
    40% { opacity: 1; }
    100% { transform: translateY(0%); opacity: 1; filter: blur(0); }
  }
  ```

---

### 4. `Kinetic Character Stagger Cascade` (Studio Dumbar Rhythm)
* **The Concept:** Words assemble glyph-by-glyph with a percussive 28ms to 35ms sequential delay, creating an authoritative cadence that synchronizes with audio transients.

---

## 🏷️ Brand Identity & Custom Logo Animation Pipeline

This skill provides a systematic engine for integrating and animating any brand's custom logo.

### Supported Logo Formats
- **Primary:** Clean Vector SVG (`.svg`) with separated groups/paths.
- **Secondary:** High-Resolution Transparent PNG (`.png`, minimum 1000px wide).

### The 4 Commercial Logo Motion Archetypes:

#### Archetype 1: `Geometric Nodal / Petal Blossom` (Ideal for Webres Studio)
* **How It Operates:** Multi-element or symmetrical logos have their constituent petals/nodes animated radially from the center anchor point.
* **Formula:**
  - Define `transform-origin` at the exact geometric center of the emblem.
  - Stagger each node's arrival by `0.025s` to `0.035s`.
  - Apply simultaneous rotation (`-45deg -> 0deg`) and scale (`0.2 -> 1.0`).
  - Follow immediately with the brand wordmark sliding in from a razor-sharp vector clip-path.

#### Archetype 2: `Vector Blueprint Path Draw (Trim Paths)`
* **How It Operates:** Logo contours draw themselves like technical architectural blueprints using SVG `stroke-dasharray` and `stroke-dashoffset`.
* **Formula:**
  ```css
  .brand-path-draw {
    stroke-dasharray: 1000;
    stroke-dashoffset: 1000;
    animation: drawPath 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }
  @keyframes drawPath {
    to { stroke-dashoffset: 0; }
  }
  ```

#### Archetype 3: `Graphic Ribbon Slicer & Brand Wipe`
* **How It Operates:** A vibrant brand-color vector flag slices across the logo bounding box, wiping the logo into view with motion blur.

#### Archetype 4: `Monolithic Stage Spotlight`
* **How It Operates:** The logo hovers over a dark ambient stage with subtle volumetric lighting, zero border boxes, and a synchronized tagline reveal.

---

## 💻 CLI & Workflow Commands for Brand Assets

Use these standardized workflows when processing or updating brand logos:

1. **`brand:inspect-svg <filepath>`**
   - Analyzes SVG viewBox, path count, fill/stroke classes, and geometric center coordinates.
2. **`brand:generate-blossom --logo=<path> --stagger=30ms`**
   - Automatically injects CSS petal animation classes (`.wbrs-petal:nth-child(n)`) with calculated angular offsets.
3. **`brand:apply-closer --brand="Webres Studio" --tagline="SAAS DEVELOPMENT, AUTOMATIZATION & AI"`**
   - Deploys the complete unboxed closer scene with the official vector emblem, high-contrast typography, and audio synchronization.

---

## 🛠️ Verification Checklist for Motion Graphics
- [ ] **Zero Chips:** Did you verify that no floating pill badges exist anywhere on screen?
- [ ] **Zero Glow Clichés:** Is typography rendered with clean, high-contrast solid colors rather than fuzzy neon halos?
- [ ] **Unboxed Data:** Are metrics framed by architectural hairlines or whitespace, rather than modal cards?
- [ ] **Living Motion:** Does the asset have secondary subtle life (continuous micro-drift) during the voiceover?
- [ ] **Audio Sync:** Is every vector sweep, character unmask, or logo blossom paired with a surgical transient sound effect (whoosh, click, or sub-thud)?
