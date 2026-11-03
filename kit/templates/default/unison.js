/* unison.js · Motor determinista de animaciones explicativas al unísono con la voz (renderAt(t) + S.W()).
   Implementa en tiempo real las 5 skills probadas para WVF y DEM (serie.js):
   1. hyperframes-causal-cursor (★ 77.7K): cursor gigante 96px, entrada física off-screen, clic asimétrico 1:2.
   2. manim-progressive-proof (★ 96.0K + ★ 19.7K): morph in-situ Wrong→Right, spotlight dimming 0.24, ValueTracker.
   3. gsap-word-sequencer (★ 17.7K): cero reflujo en bucle, solo transform/opacity/clip-path.
   4. shotcraft-ui-recipes (★ 16.2K): escritura de comando `/` + impacto de estado.
   5. lottie-attention-choreography (★ 2.7K) + tiktok-promote-ui-demos: jerarquía 1/3 + modo ?tiktok=1 (cap top 1380px). */
(() => {
const U = window.U = {};
const S = window.S || {
  clamp: (v, a = 0, b = 1) => Math.min(b, Math.max(a, v)),
  prog: (t, a, b) => Math.min(1, Math.max(0, (t - a) / Math.max(0.0001, b - a))),
  lerp: (a, b, k) => a + (b - a) * k,
  out3: (x) => 1 - Math.pow(1 - x, 3),
  out5: (x) => 1 - Math.pow(1 - x, 5),
  in3: (x) => x * x * x,
  io: (x) => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2,
  spring: (dt, k = 185, d = 16) => {
    if (dt <= 0) return 0;
    const w0 = Math.sqrt(k), z = d / (2 * w0);
    if (z >= 1) return 1 - Math.exp(-w0 * dt) * (1 + w0 * dt);
    const wd = w0 * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w0 * dt) * (Math.cos(wd * dt) + (z * w0 / wd) * Math.sin(wd * dt));
  }
};

/* --- Safe Zone & TikTok Subtitle Mode (?tiktok=1 sube #cap a 1380px) --- */
U.initSafeMode = () => {
  const qs = new URLSearchParams(location.search);
  if (qs.get('tiktok') === '1') {
    document.documentElement.classList.add('tiktok');
    const st = document.createElement('style');
    st.textContent = '.tiktok #cap { top: 1475px !important; }';
    document.head.appendChild(st);
  }
};

/* --- 1. HyperFrames Oversized Cursor (punta en 21% 14%, entrada física fuera de cuadro) --- */
U.createCursor = (parent, { size = 98, dark = false } = {}) => {
  const el = document.createElement('div');
  el.className = 'u-cursor';
  el.style.cssText = `position:absolute;left:0;top:0;width:${size}px;height:${size}px;z-index:60;pointer-events:none;will-change:transform,opacity;transform-origin:${(size * 0.21).toFixed(1)}px ${(size * 0.14).toFixed(1)}px;filter:drop-shadow(0 10px 18px rgba(0,0,0,.42));`;
  const fill = dark ? '#14161A' : '#FFFFFF';
  const stroke = dark ? '#FFFFFF' : '#14161A';
  el.innerHTML = `<svg viewBox="0 0 28 28" width="${size}" height="${size}" fill="none">
    <path d="M5.8 3.6L22.6 15.1C23.5 15.7 23.1 17.1 22.0 17.2L14.8 18.0L18.1 24.4C18.5 25.2 18.1 26.1 17.3 26.5L15.4 27.3C14.6 27.7 13.7 27.3 13.3 26.5L10.1 20.0L5.3 24.1C4.5 24.8 3.2 24.2 3.2 23.1V4.7C3.2 3.6 4.9 3.0 5.8 3.6Z"
      fill="${fill}" stroke="${stroke}" stroke-width="2.2" stroke-linejoin="round"/>
  </svg>`;
  const ring = document.createElement('div');
  ring.style.cssText = `position:absolute;left:${(size * 0.21 - 36).toFixed(1)}px;top:${(size * 0.14 - 36).toFixed(1)}px;width:72px;height:72px;border-radius:50%;border:5px solid #00E6A8;opacity:0;pointer-events:none;will-change:transform,opacity;`;
  el.appendChild(ring);
  parent.appendChild(el);
  const tipX = size * 0.21, tipY = size * 0.14;

  /* waypoints: [{ t, x, y }, ...], clicks: [tClick1, ...] */
  return (t, { from = [560, 2020], enterAt = 0.2, enterDur = 0.52, target = [500, 500], clickAt = null, driftAt = null, driftTo = null, exitAt = null, exitTo = [1180, 900] } = {}) => {
    if (t < enterAt) { el.style.opacity = 0; return 0; }
    el.style.opacity = 1;
    const ke = S.out3(S.prog(t, enterAt, enterAt + enterDur));
    let x = S.lerp(from[0], target[0], ke);
    let y = S.lerp(from[1], target[1], ke);
    if (driftAt != null && driftTo && t > driftAt) {
      const kd = S.out3(S.prog(t, driftAt, driftAt + 0.55));
      x = S.lerp(target[0], driftTo[0], kd);
      y = S.lerp(target[1], driftTo[1], kd);
    }
    if (exitAt != null && t > exitAt) {
      const kx = S.in3(S.prog(t, exitAt, exitAt + 0.42));
      x = S.lerp(x, exitTo[0], kx);
      y = S.lerp(y, exitTo[1], kx);
    }
    let sc = 1;
    let clicked = 0;
    if (clickAt != null && t >= clickAt) {
      clicked = 1;
      if (t < clickAt + 0.09) sc = S.lerp(1, 0.80, S.in3(S.prog(t, clickAt, clickAt + 0.09)));
      else if (t < clickAt + 0.31) sc = S.lerp(0.80, 1.0, S.out3(S.prog(t, clickAt + 0.09, clickAt + 0.31)));
      const rp = S.prog(t, clickAt, clickAt + 0.38);
      ring.style.opacity = rp > 0 && rp < 1 ? ((1 - rp) * 0.92).toFixed(3) : 0;
      ring.style.transform = `scale(${(0.45 + rp * 1.35).toFixed(3)})`;
    } else {
      ring.style.opacity = 0;
    }
    el.style.transform = `translate3d(${(x - tipX).toFixed(1)}px, ${(y - tipY).toFixed(1)}px, 0) scale(${sc.toFixed(3)})`;
    return clicked;
  };
};

/* --- Reacción de botón al clic del cursor (mismo fotograma) --- */
U.pressReaction = (el, t, clickAt, { amp = 0.06 } = {}) => {
  if (!el) return;
  let sc = 1;
  if (clickAt != null && t >= clickAt && t < clickAt + 0.30) {
    sc = t < clickAt + 0.09
      ? S.lerp(1, 1 - amp, S.in3(S.prog(t, clickAt, clickAt + 0.09)))
      : S.lerp(1 - amp, 1, S.out3(S.prog(t, clickAt + 0.09, clickAt + 0.30)));
  }
  return sc;
};

/* --- 2. Shotcraft Terminal / Slash Command Typewriter determinista --- */
U.typeSlash = (el, fullText, t, startAt, { charStep = 0.028, cursorChar = '▋' } = {}) => {
  if (t < startAt) { el.textContent = ''; return false; }
  const count = Math.min(fullText.length, Math.floor((t - startAt) / charStep) + 1);
  const done = count >= fullText.length;
  const blink = !done || (Math.floor((t - startAt) * 4) % 2 === 0 && t < startAt + fullText.length * charStep + 0.9);
  el.textContent = fullText.slice(0, count) + (blink ? cursorChar : '');
  return done;
};

/* --- 3. Manim / Motion Canvas Spotlight Dimming (atenúa a 0.24 el contexto no activo) --- */
U.spotlight = (items, activeIndex, t, at, { dim = 0.24, dur = 0.24 } = {}) => {
  const k = S.out3(S.prog(t, at, at + dur));
  items.forEach((el, idx) => {
    if (!el) return;
    if (t < at || activeIndex < 0) {
      el.style.opacity = 1;
      el.style.transform = 'scale(1)';
    } else if (idx === activeIndex) {
      el.style.opacity = 1;
      el.style.transform = `scale(${(1 + 0.03 * k).toFixed(3)})`;
    } else {
      el.style.opacity = S.lerp(1, dim, k).toFixed(3);
      el.style.transform = `scale(${(1 - 0.02 * k).toFixed(3)})`;
    }
  });
};

/* --- 4. Manim Wrong → Right In-Situ Morph --- */
U.morphPair = (wrongEl, rightEl, t, morphAt, { dur = 0.32 } = {}) => {
  const k = S.io(S.prog(t, morphAt, morphAt + dur));
  if (wrongEl) {
    wrongEl.style.opacity = (1 - k).toFixed(3);
    wrongEl.style.transform = `scale(${(1 - 0.14 * k).toFixed(3)}) rotate(${(-4 * k).toFixed(2)}deg)`;
  }
  if (rightEl) {
    const sp = S.spring(t - morphAt, 220, 16);
    rightEl.style.opacity = t < morphAt ? 0 : S.clamp(sp * 2.4).toFixed(3);
    rightEl.style.transform = `scale(${(0.82 + 0.18 * sp).toFixed(3)})`;
  }
  return k;
};

/* --- 5. Lottie Staggered Waterfall Entry (1/3 active rule, mismo eje coherente) --- */
U.staggerIn = (els, t, startAt, { step = 0.06, dy = 44, exitAt = null } = {}) => {
  els.forEach((el, i) => {
    if (!el) return;
    const a = startAt + i * step;
    const k = S.spring(t - a, 210, 17);
    const out = exitAt == null ? 0 : S.in3(S.prog(t, exitAt - 0.18, exitAt + 0.06));
    el.style.opacity = t < a ? 0 : (S.clamp(k * 2.5) * (1 - out)).toFixed(3);
    el.style.transform = `translate3d(0, ${((1 - k) * dy - out * 60).toFixed(1)}px, 0)`;
  });
};
})();
