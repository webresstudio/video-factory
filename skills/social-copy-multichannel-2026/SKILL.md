---
name: social-copy-multichannel-2026
description: >-
  State-of-the-art production manual and technical copywriting runbook for multi-platform
  social video in 2026: LinkedIn, YouTube Shorts, Instagram (Reels), and TikTok.
  Enforces 4-layer Multimodal Social SEO alignment (Google/Meta/TikTok indexing + Alt Text),
  LinkedIn H.O.O.P.S. dwell-time architecture, multi-persona search bridges, open-loop retention,
  flawless idiomatic Spanish, zero agency brochure filler, and the 2026 anti-slop emoji standard.
---

# State of the Art: Multi-Platform Video Copywriting & Social SEO (2026 Edition)
### Instagram Reels • TikTok • LinkedIn • YouTube Shorts

A rigorous copy engineering and Social SEO runbook for editorial tech videos, AI product explainers, and software brand storytelling. Governed by `WBRS/AGENTS.md` (§A, §E): every claim comes from `facts.md`, Spanish syntax must be 100% idiomatic and complete, open loops protect video completion, and forced corporate brochure pitches are strictly prohibited.

---

## 1. The 2026 Multimodal Social SEO Law (4-Layer Alignment)

Public Instagram Reels, TikToks, LinkedIn videos, and YouTube Shorts are indexed both inside each platform's semantic search engine and directly on **Google SERPs**. Algorithms cross-check **4 layers simultaneously**:

1. **Spoken Hook (`0–3s`):** The primary topic/entity spoken aloud in the opening sentence.
2. **On-Screen Text (`0–3s`):** Large, clean headline text read via OCR on the opening frames.
3. **Caption Line 1 (The Meta-Title):** Acts as `<title>` on Google & Instagram/TikTok Search. Must contain **both** a broad user-intent search query (so non-technical founders, business owners, and curious viewers find it) **and** the core product/topic entity, written as **one complete, natural, grammatically impeccable sentence** (zero telegraphic tag-soup, zero broken comparatives).
4. **Metadata & Alt Text (Instagram Advanced Settings):** Every Instagram Reel delivery must include a dedicated **Texto alternativo (`Alt Text`)** packing secondary semantic entities (`LSI keywords`) for crawlers without cluttering the visible caption.

---

## 2. Three Strict Prohibitions (`AGENTS.md` §A & §E)

1. **Zero Forced Agency Brochure Filler ("Anti-Advenedizo Rule"):**
   - **Prohibited** on editorial, news, or tool-breakdown videos: tacking on generic commercial paragraphs at the end (*"En Webres Studio diseñamos e implementamos infraestructura de software..."*, *"Construye soluciones hoy con Webres Studio"*). Authority comes from sharp technical/commercial judgment and the video's visual end-card—only mention a product (e.g., SCALAos) when the video itself is an explicit product ad.
2. **Zero Premature Climax (Protect Watch-Time & Saves):**
   - **Prohibited** on Instagram & TikTok listicles or multi-block videos: transcribing all `N` items as a flat dictionary in the caption. Reveal the first 2–3 concretely to prove value, and **keep the remaining items open** so viewers watch to the final visual summary card and hit **Save**.
3. **Zero Emoji Slop & Zero Cheap Guru Clickbait:**
   - **Prohibited:** Emoji chains (`🚀🔥🤯✨`), 2022 CM clichés (*"etiquétalo sin contexto"*), and cheap course-seller phrasing (*"hazte rico sin programar en 5 minutos"*).
   - **Permitted:** `0` to `2` clean typographic symbols (`•`, `→`).
4. **Zero Hardcoded Publish Hours (`FB ≠ IG ≠ TikTok ≠ YouTube` per Brand):**
   - **Prohibited:** Burning a universal deploy hour (such as `12:30 p.m.`) across different brands or assuming Facebook, Instagram, TikTok, and YouTube Shorts share the same optimal window inside `COPYS-REDES.md` or the Story calendar.
   - **Mandatory:** Read `social.optimal_publish_windows` from `project_config.json` or `check/social_analytics.json` (generated via `wvf analytics --save-windows`), specifying the **empirical window separately for `Instagram`, `Facebook`, `TikTok`, and `YouTube Shorts`** for that specific client/account.
5. **Zero Post-Publish Caption/Tag Edits During First 48h on Instagram & Full 4-Channel Rollout:**
   - **Prohibited:** Editing an Instagram Reel's caption, hashtags, or tagged accounts after publishing during the first `48 hours` (empirically shown to reset Meta's cold-exploration classifier, cutting non-follower reach from `76.9 %` down to `36.4 %`). Double-check `@mentions` and `Alt Text` *before* tapping Share.
   - **Mandatory 4-Channel Deployment:** Never leave `YouTube Shorts` or `LinkedIn` unpublished on trending tech/B2B topics (`YouTube Shorts` delivered `716` views + `3.5 %` search traffic + `24.0 s` avg watch duration + `24 %` Desktop audience in just `4 hours` on *Gemini 4 Suite*).

---

## 3. The 4 Platform Blueprints

---

### 1. INSTAGRAM REELS: Google-Indexed Meta-Title + Multi-Persona Bridge + `Alt Text`

* **Cutoff Rule:** First sentence **under 125 characters** so it sits completely intact before `…más` and serves as Google's meta-title.
* **Audience Bridge:** Explicitly connect why the topic matters both to a **business owner / founder** and to a **builder / specialist** so one sends it via DM to the other (*Sends per Reach*).
* **Hashtags:** `4` to `5` clean topical tags.
* **Mandatory Deliverable:** Always output the **Texto alternativo (`Alt Text`)** right underneath the caption.

```markdown
[Oración completa y natural en <125 caracteres con consulta abierta de búsqueda + entidad principal]

[Puente Multi-Audiencia en 2 líneas: por qué importa tanto a quien dirige un negocio como a quien ejecuta técnicamente]

• [Punto 1 concreto y verificable]
• [Punto 2 concreto y verificable]
• [Punto 3 concreto y verificable]

[Bucle abierto hacia la segunda mitad / cierre del video para empujar retención completa y Guardados]

[Llamado a guardar + envío por DM entre roles complementarios + pregunta abierta en tono positivo]

#Keyword1 #Keyword2 #Keyword3 #Keyword4 #Keyword5
```
**Texto alternativo (*Configuración avanzada → Escribir texto alternativo*):**
`[1 oración descriptiva de 30–45 palabras integrando las consultas de búsqueda principales, entidades comparadas y contexto práctico en español natural]`

---

### 2. TIKTOK: Direct Search Query (`<80` chars) + Open-Loop Retention

* **Line 1 Rule:** One clean, complete Spanish sentence **under 80 characters** matching how real users search (`Cómo...`, `Qué cambia con...`, `Por qué...` + core entity). Never smash disconnected fragments together.
* **Body:** Crisp context + first half of the proof + open loop pointing to the video's visual end-card.
* **Hashtags:** `4` to `5` lowercase search tags.

```markdown
[Oración completa de búsqueda natural en <80 caracteres]

[Diagnóstico directo en 2 líneas conectando el dolor real sin jerga vacía]

• [Evidencia / Comando / Dato 1]
• [Evidencia / Comando / Dato 2]
• [Evidencia / Comando / Dato 3]

[Bucle abierto sobre el desenlace del video + invitación a guardar la tarjeta final]

[Pregunta abierta y positiva que invite a comentar experiencias reales]

#keyword1 #keyword2 #keyword3 #keyword4 #keyword5
```

---

### 3. LINKEDIN: The **H.O.O.P.S. 2026** Dwell-Time & B2B Search Framework

* **H — Hook (`<160` chars before `…ver más`):** Sharp business/operational tension that **includes core searchable entities** in the first sentence (never an unsearchable riddle).
* **O — Orientation:** Why decision-makers (founders, directors) and technical leads care right now.
* **O — On-Screen Bridge:** Point directly to what the 60-second video above demonstrates.
* **P — Pedagogical Synthesis (`01 / 02 / 03`):** Translate features or news into 3 executive/operational pillars (doubles active dwell time while the video plays, instead of looking like console documentation).
* **S — Substantive CTA:** Genuine operational debate question (zero *"Comenta PDF"* engagement bait, zero brochure sales pitch).

```markdown
[H · Gancho de <160 caracteres con tensión ejecutiva + entidades buscables clave]

[O · Orientación: qué está fallando o cambiando realmente en la operación de las empresas]

[O · Puente al video: qué demuestra en un minuto el video de arriba]

01 / [Pilar Operativo o Estratégico 1]: [Traducción concreta con dato verificado]
02 / [Pilar Operativo o Estratégico 2]: [Traducción concreta con dato verificado]
03 / [Pilar Operativo o Estratégico 3]: [Traducción concreta con dato verificado]

[Tesis de cierre de 1 línea con criterio propio, sin folleto comercial]

[S · Pregunta consultiva real sobre la operación del lector]

#Keyword1 #Keyword2 #Keyword3 #Keyword4 #Keyword5
```

---

### 4. YOUTUBE SHORTS: Idiomatic Title (`<55` chars) + SERP Description + Pinned Comment

* **Title:** Must be **under 55 characters** AND a **complete, idiomatic Spanish phrase** (never a comma-list of nouns or broken telegraphic fragments).
* **Description:** First 120 characters weave broad Google/YouTube search intent + exact entities; concise verified bullets below; `#Shorts` + 2 topical tags.
* **Pinned Comment:** Welcomes both business/beginner viewers and technical peers into the comments.

---

## 4. Rejected vs. Approved Line-1 Examples (Real Calibration Cases)

* **Rechazado (Broken / Telegraphic Grammar):**
  `¿Google Antigravity es malo frente a Claude Code? 6 comandos que nadie usa`
  *(Why it fails: unnatural comparative «es malo frente a» + two disconnected fragments smashed together).*
* **Rechazado (Literary Riddle — Zero Searchability):**
  `Si alguien en tu equipo entrega sin preguntar o repite el mismo error, le falta método.`
  *(Why it fails: zero searchable keywords; nobody types this in Google, Instagram, or TikTok).*
* **Rechazado (Cheap Course-Seller Clickbait):**
  `Cómo crear una página web sin programar en minutos`
  *(Why it fails: generic «vende-humo» phrasing that cheapens brand authority).*
* **Aprobado (Idiomatic Spanish + Open Search + Core Entity in `<125` chars):**
  `¿Quieres crear una página web o app con inteligencia artificial? Mira estos 6 comandos de Google Antigravity.`
  *(Why it works: natural spoken Spanish, captures broad search from non-coders and founders + exact tool entity, matches `0–3s` of the video).*

---

## 5. Measuring Copy Impact (2026 KPIs)

Evaluate copy changes by the 4 signals each section controls—never by vanity likes alone:
1. **Search Traffic % (`% de vistas por Búsqueda` in TikTok Studio / IG Insights / YouTube Analytics):** Directly measures **Line 1 + `Alt Text` + Title**.
2. **Sends per Reach (`Compartidos por DM / Alcance`) & Saves (`Guardados`):** Measures whether the **Multi-Persona Bridge + Open Loop** made viewers save the visual end-card or send it to a teammate/founder.
3. **Completion Rate & Average Watch Time:** Confirms the caption **did not spoil** the second half of the video.
4. **Substantive Comments (LinkedIn & Shorts):** Real operational replies instead of single-word engagement bait.

---

## 6. Pre-Delivery Audit Checklist

* [ ] **Grammar & Voice Check:** Read every title and Line 1 out loud. Is it 100% natural, educated Spanish with zero telegraphic fragments, anglicisms, or broken comparatives?
* [ ] **Universal Search Check:** Would someone who does *not* know the specific tool/news name yet still find Line 1 via broad topic search on Google, Instagram, TikTok, or LinkedIn?
* [ ] **Retention Check:** Did IG & TikTok avoid spoiling 100% of the video's ending so the viewer still needs to watch and save the video?
* [ ] **Anti-Advenedizo Check:** Zero forced agency sales paragraphs on editorial/news videos; zero emoji chains (`📸`, `🚀`, `🔥` prohibited even in headers).
* [ ] **Alt Text Check:** Included ready-to-paste Instagram `Alt Text`?
* [ ] **Per-Brand, Per-Network Deployment Window Check (`FB ≠ IG ≠ TikTok`):** Did `COPYS-REDES.md` and the Story calendar pull the independent empirical deployment windows for `Instagram`, `Facebook`, and `TikTok` of this specific brand from `wvf analytics` (never hardcoding `12:30 p.m.`)?
