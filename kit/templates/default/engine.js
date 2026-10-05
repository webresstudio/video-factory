/* WhatsApp: 5 formas de pagar menos — engine
   renderAt(t) is a pure function of time → frame-perfect 60 fps export.
   Voice: William's own voice (Flow @me) on every line; on camera only in L02, L06, L09.
   Skills: dynamic-text-animations (horizon unmask, char cascade, petal blossom, hairline draws),
   motion-kinetic-typography (unboxed type, Lucide-only icons, scene physics), commercial-video-transitions-2026
   (iris match-cut, knife-edge, scale-punch, ribbon sweep, 2.5D push, luminance flash, louvers, laser streak,
   Swiss horizon split — all 6–18 frames), internet-video-2026 (cold open mid-action, re-hooks, loop ending),
   impeccable craft floor (no cards, no eyebrows, no gradient text, tabular numerals). */
(async () => {
"use strict";
await window.WVF_TIMING_READY;
const DEMO = !window.TIMING;
if (DEMO) {
  if (new URLSearchParams(location.search).has("render")) {
    throw new Error("Timeline pendiente: ejecutar wvf timeline antes de exportar.");
  }
  const response = await fetch("script.json");
  if (!response.ok) throw new Error("No se pudo cargar script.json");
  const script = await response.json();
  let cursor = 0;
  const lines = [], words = [];
  for (const line of script) {
    const duration = Number(line.dur);
    const text = line.text.split(/\s+/);
    lines.push({id: line.id, t0: cursor, t1: cursor + duration, clipIn: 0, cam: false});
    text.forEach((w, i) => words.push({l: line.id, w, t: cursor + i * duration / text.length, e: cursor + (i+1) * duration / text.length}));
    cursor += duration;
  }
  window.TIMING = {duration: cursor, lines, words};
  window.CAM_FRAMES = {};
  const notice = document.createElement("p");
  notice.textContent = "Plantilla de ejemplo · tiempos estimados · validar hechos y generar la voz antes de publicar";
  notice.style.cssText = "position:fixed;top:0;left:0;right:0;margin:0;padding:10px;background:#0e1114;color:#f3eee6;text-align:center;font:13px sans-serif;z-index:20";
  document.body.appendChild(notice);
}
const TM = window.TIMING;
const DURATION = TM.duration;
const FPS_CAM = 24;
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

/* ───────── math ───────── */
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const p = (t, a, d) => clamp((t - a) / d);
const lerp = (a, b, k) => a + (b - a) * k;
const eo = (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));                 // easeOutExpo ≈ cubic-bezier(.16,1,.3,1)
const eio = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const ei = (x) => x * x * x * x;                                             // ≈ cubic-bezier(.7,0,.84,0)
const knifeEase = (x) => 1 - Math.pow(1 - x, 4.2);                           // ≈ cubic-bezier(.05,.9,.2,1)
const blur = (b) => (b > 0.05 ? `blur(${b.toFixed(2)}px)` : "none");

/* ───────── word clock (whisper word timestamps on the Flow takes) ───────── */
const LN = {}; TM.lines.forEach((l) => (LN[l.id] = l));
const norm = (s) => s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]/g, "").replace(/^click$/, "clic");
function W(line, word, n = 1) {
  let c = 0;
  for (const w of TM.words) if (w.l === line && norm(w.w) === norm(word) && ++c === n) return w.t;
  if (DEMO && LN[line]) return LN[line].t0 + 0.25;
  throw new Error(`word not found: ${line}/${word}#${n}`);
}
function WE(line, word, n = 1) {
  let c = 0;
  for (const w of TM.words) if (w.l === line && norm(w.w) === norm(word) && ++c === n) return w.e;
  if (DEMO && LN[line]) return LN[line].t0 + 0.25;
  throw new Error(`word not found: ${line}/${word}#${n}`);
}

/* ───────── style writer (skips redundant writes) ───────── */
function css(el, o) {
  const c = el._c || (el._c = {});
  for (const k in o) { const v = String(o[k]); if (c[k] !== v) { c[k] = v; el.style[k] = v; } }
}
function vis(el, on) { css(el, { visibility: on ? "visible" : "hidden" }); }
function attr(el, k, v) { const s = String(v); if (el.getAttribute(k) !== s) el.setAttribute(k, s); }
function txt(el, s) { if (el.textContent !== s) el.textContent = s; }

/* ───────── text splitting → masked slots ───────── */
function splitAll() {
  for (const el of $$("[data-split]")) {
    const mode = el.dataset.split;
    const units = [];
    const frag = document.createDocumentFragment();
    const addWord = (word, cls) => {
      const m = document.createElement("span"); m.className = "m";
      const i = document.createElement("span"); i.className = "mi" + (cls ? " " + cls : ""); i.textContent = word;
      m.appendChild(i); frag.appendChild(m); units.push(i);
    };
    if (mode === "words") {
      Array.from(el.childNodes).forEach((n) => {
        const cls = n.nodeType === 1 ? n.className : "";
        for (const w of n.textContent.split(/(\s+)/)) { if (!w) continue; if (/^\s+$/.test(w)) frag.appendChild(document.createTextNode(" ")); else addWord(w, cls); }
      });
    } else {
      const m = document.createElement("span"); m.className = "m";
      for (const ch of el.textContent) { const s = document.createElement("span"); s.className = "ch"; s.textContent = ch; m.appendChild(s); units.push(s); }
      frag.appendChild(m);
    }
    el.textContent = ""; el.appendChild(frag); el._u = units;
  }
}
/* Masked horizon rise (Apple-keynote unmask), optional exit upward */
function rise(el, t, o) {
  const units = el._u || [el];
  const st = o.st ?? 0.05, din = o.din ?? 0.7, dout = o.dout ?? 0.34, sto = o.sto ?? 0.016;
  for (let i = 0; i < units.length; i++) {
    const ti = o.times ? o.times[Math.min(i, o.times.length - 1)] : o.t0 + i * st;
    const k1 = eo(p(t, ti, din));
    let y = (1 - k1) * 108, op = clamp(k1 * 2.4), b = (1 - k1) * 6;
    if (o.tout != null) { const k2 = eio(p(t, o.tout + i * sto, dout)); y -= k2 * 108; op *= 1 - clamp(k2 * 1.3); b += k2 * 5; }
    css(units[i], { transform: `translateY(${y.toFixed(2)}%)`, opacity: op.toFixed(3), filter: blur(b) });
  }
}
/* Monumental numeral: rises from its baseline slot with a slight skew, holds with micro-drift */
function numeral(el, t, t0, tout) {
  const k = eo(p(t, t0, 0.8));
  let y = (1 - k) * 160, op = clamp(k * 2), sk = (1 - k) * -8;
  if (tout != null) { const k2 = ei(p(t, tout, 0.25)); op *= 1 - k2; }
  css(el, { transform: `translateY(${(y - (t - t0) * 6).toFixed(2)}px) skewX(${sk.toFixed(2)}deg)`, opacity: op.toFixed(3), filter: blur((1 - k) * 14) });
}

/* ───────── WhatsApp UI builders ───────── */
const TICK = '<svg class="tick" viewBox="0 0 26 18"><path class="t1" d="M1.5 9.5 6 14 15 3.5"/><path class="t2" d="M9.6 12.2 11.5 14 20.5 3.5"/></svg>';
function bubble(parent, o) {
  const b = document.createElement("div");
  b.className = `bub ${o.side}`;
  if (o.side === "out") b.style.right = (o.right ?? 70) + "px"; else b.style.left = (o.left ?? 70) + "px";
  b.style.top = o.top + "px";
  if (o.width) b.style.width = o.width + "px";
  const lab = o.lab ? `<span class="lab ${o.labCls || ""}">${o.lab}</span>` : "";
  const tick = o.side === "out" ? `<span class="tk">${TICK}</span>` : "";
  b.innerHTML = `<div class="body">${o.html}</div><div class="meta">${lab}<span>${o.time || "10:42"}</span>${tick}</div>`;
  parent.appendChild(b);
  b._lab = $(".lab", b); b._tk = $(".tk", b); b._t2 = $(".t2", b);
  return b;
}
/* pop-in physics for a chat bubble (fast, no rubber band) */
function pop(b, t, t0, extra = "") {
  const k = eo(p(t, t0, 0.42));
  css(b, { transform: `translateY(${((1 - k) * 34).toFixed(2)}px) scale(${lerp(0.86, 1, k).toFixed(4)}) ${extra}`, opacity: clamp(k * 2.2).toFixed(3), filter: blur((1 - k) * 6) });
  return k;
}
/* delivery ticks: ✓ → ✓✓ (gray) → coral when the delivery becomes a charge */
function ticks(b, t, tDeliver, tCharge) {
  if (!b._tk) return;
  css(b._t2, { opacity: t >= tDeliver ? "1" : "0" });
  const kc = tCharge != null ? eo(p(t, tCharge, 0.35)) : 0;
  const c0 = [233, 237, 239, 0.62], c1 = [255, 106, 77, 1];
  const c = c0.map((v, i) => lerp(v, c1[i], kc));
  css(b._tk, { color: `rgba(${c[0].toFixed(0)},${c[1].toFixed(0)},${c[2].toFixed(0)},${c[3].toFixed(3)})`, transform: `scale(${(1 + Math.sin(Math.PI * clamp(kc * 1.4)) * 0.35).toFixed(3)})` });
  if (b._lab) css(b._lab, { opacity: kc.toFixed(3), transform: `translateX(${((1 - kc) * -14).toFixed(2)}px)` });
}
function labIn(b, t, t0) { if (!b._lab) return; const k = eo(p(t, t0, 0.45)); css(b._lab, { opacity: k.toFixed(3), transform: `translateX(${((1 - k) * -14).toFixed(2)}px)` }); }

/* ───────── WebGL: low-frequency volumetric light field (studio backdrop) ───────── */
const FRAG = `
precision highp float;
uniform vec2 uRes; uniform float uTime; uniform float uFlare;
uniform vec3 uA[8]; uniform vec3 uB[8]; uniform float uMix;
float h(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
float n2(vec2 p){ vec2 i=floor(p), f=fract(p); vec2 u=f*f*(3.-2.*f);
  return mix(mix(h(i),h(i+vec2(1,0)),u.x), mix(h(i+vec2(0,1)),h(i+vec2(1,1)),u.x), u.y); }
float fbm(vec2 p){ float s=0., a=.5; for(int i=0;i<4;i++){ s+=a*n2(p); p=p*2.03+vec2(1.7,9.2); a*=.5; } return s; }
vec3 scene(vec2 p, vec3 P[8], float t){
  vec3 base=P[0], c1=P[1], c2=P[3], rc=P[5];
  vec2 l1=P[2].xy + .02*vec2(sin(t*.21), cos(t*.17)); float f1=P[2].z;
  vec2 l2=P[4].xy + .03*vec2(cos(t*.13), sin(t*.19)); float f2=P[4].z;
  float ribY=P[6].x, ribI=P[6].y, rayI=P[6].z, vig=P[7].y;
  vec2 d1=p-l1; float r1=length(d1*vec2(1.,.92)); float a1=atan(d1.y,d1.x);
  float n=fbm(p*1.4+vec2(t*.03,-t*.024));
  vec3 col=base + c1*exp(-r1*r1*f1)*(1.+uFlare);
  vec2 d2=p-l2; col+=c2*exp(-dot(d2,d2)*f2);
  float rays=pow(.5+.5*sin(a1*7.+n*3.2+t*.09),6.)*exp(-r1*2.2);
  col+=c1*rays*rayI*(1.+uFlare*.5);
  float w=p.y-ribY-.14*sin(p.x*2.1+t*.19)-.3*(n-.5);
  col+=rc*exp(-w*w*30.)*ribI*(.55+.45*n);
  col+=(n-.5)*.02;
  vec2 q=(p-vec2(.5,.889))/vec2(.8,1.2);
  col*=mix(1.,1.-dot(q,q)*.85,vig);
  return col;
}
void main(){
  vec2 px=gl_FragCoord.xy/uRes*vec2(1080.,1920.); px.y=1920.-px.y;
  vec2 p=px/1080.;
  vec3 col = uMix<=0. ? scene(p,uA,uTime) : (uMix>=1. ? scene(p,uB,uTime) : mix(scene(p,uA,uTime),scene(p,uB,uTime),uMix));
  col+=(h(px+fract(uTime*7.31)*91.)-.5)*(2.2/255.);
  gl_FragColor=vec4(clamp(col,0.,1.),1.);
}`;
const VERT = "attribute vec2 a; void main(){ gl_Position=vec4(a,0.,1.); }";
let gl, U = {};
function initGL() {
  const cv = $("#bg");
  gl = cv.getContext("webgl", { preserveDrawingBuffer: true, antialias: false, alpha: false });
  const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
  const prog = gl.createProgram();
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, VERT)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FRAG));
  gl.linkProgram(prog); gl.useProgram(prog);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, "a"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  for (const n of ["uRes", "uTime", "uFlare", "uA", "uB", "uMix"]) U[n] = gl.getUniformLocation(prog, n);
  gl.viewport(0, 0, cv.width, cv.height);
  gl.uniform2f(U.uRes, cv.width, cv.height);
}
/* 0 base · 1 key light color · 2 key pos.xy, falloff · 3 fill color · 4 fill pos.xy, falloff · 5 ribbon color · 6 ribY, ribI, rays · 7 -, vignette, - */
const pal = (a) => new Float32Array(a.flat());
const PAL = {
  ink:   pal([[.039, .047, .059], [0, 0, 0], [.5, .5, 3], [0, 0, 0], [.5, 1.6, 1], [0, 0, 0], [1.3, 0, 0], [0, .7, 0]]),
  studio:pal([[.030, .038, .042], [.012, .135, .118], [.5, .42, 2.3], [.012, .03, .034], [.5, 1.6, 1.1], [0, .05, .044], [1.34, .3, .1], [0, .86, 0]]),
  cost:  pal([[.040, .031, .030], [.19, .066, .044], [.80, .30, 2.5], [.0, .05, .046], [.15, 1.55, 1.3], [.11, .036, .026], [1.36, .36, .12], [0, .86, 0]]),
  free:  pal([[.020, .040, .038], [0, .21, .17], [.36, .66, 2.0], [.02, .04, .045], [.9, 1.5, 1.4], [0, .09, .075], [1.30, .42, .14], [0, .86, 0]]),
  web:   pal([[.010, .022, .021], [0, .34, .27], [.5, .52, 3.2], [0, .085, .075], [.5, 1.72, 1.3], [0, .16, .135], [1.36, .38, .2], [0, .86, 0]]),
};
const lerpPal = (A, B, k) => { const o = new Float32Array(24); for (let i = 0; i < 24; i++) o[i] = A[i] + (B[i] - A[i]) * k; return o; };

/* ───────── timeline anchors (derived from the voice) ───────── */
let S;
function anchors() {
  const s = {};
  s.T1 = LN.L02.t0 - 0.22; s.T1d = 14 / 60;   // iris match-cut  (L01 → L02)
  s.T2 = LN.L03.t0 - 0.20; s.T2d = 10 / 60;   // knife-edge      (L02 → L03)
  s.T3 = LN.L04.t0 - 0.16; s.T3d = 10 / 60;   // scale-punch     (L03 → L04)
  s.T4 = LN.L05.t0 - 0.24; s.T4d = 16 / 60;   // ribbon sweep    (L04 → L05)
  s.T5 = LN.L06.t0 - 0.26; s.T5d = 18 / 60;   // 2.5D push       (L05 → L06)
  s.T6 = LN.L07.t0 - 0.12; s.T6d = 6 / 60;    // luminance flash (L06 → L07)
  s.T7 = LN.L08.t0 - 0.24; s.T7d = 16 / 60;   // louver shutter  (L07 → L08)
  s.T8 = LN.L09.t0 - 0.26; s.T8d = 14 / 60;   // laser streak    (L08 → L09)
  s.T9 = LN.L10.t0 - 0.22; s.T9d = 12 / 60;   // horizon split   (L09 → L10)
  return s;
}
const R = {};
function refs() { for (const el of $$("[id]")) R[el.id.replace(/-/g, "_")] = el; }

/* ═════════ build dynamic DOM ═════════ */
function build() {
  // L01 — the cold open is mid-conversation
  const c1 = R.s1_chat;
  R.s1b = [
    bubble(c1, { side: "in", top: 290, html: "¿Tienen envío hoy?", time: "10:41" }),
    bubble(c1, { side: "out", top: 438, html: "¡Hola!", lab: "se cobra", labCls: "cost" }),
    bubble(c1, { side: "out", top: 576, html: "Sí, hoy mismo", lab: "se cobra", labCls: "cost" }),
    bubble(c1, { side: "out", top: 714, html: "¿A qué zona?", lab: "se cobra", labCls: "cost" }),
    bubble(c1, { side: "out", top: 852, html: "Te paso el enlace", lab: "se cobra", labCls: "cost" }),
  ];
  // L03 — free in, charged out
  const c3 = R.s3_chat;
  R.s3b = [
    bubble(c3, { side: "in", top: 560, html: "¿Tienen la talla M?", lab: "gratis", labCls: "free", time: "11:02" }),
    bubble(c3, { side: "in", top: 698, html: "¿Y en negro?", lab: "gratis", labCls: "free", time: "11:02" }),
    bubble(c3, { side: "out", top: 864, html: "Sí, en M y en negro", lab: "se cobra", labCls: "cost", time: "11:03" }),
    bubble(c3, { side: "out", top: 1002, html: "¿Te la aparto?", lab: "se cobra", labCls: "cost", time: "11:03" }),
    bubble(c3, { side: "out", top: 1140, html: "Envío hoy mismo", lab: "se cobra", labCls: "cost", time: "11:03" }),
  ];
  // L04 — five bubbles collapse into one
  const c4 = R.s4_chat;
  const five = ["¡Hola!", "Sí tenemos talla M", "Envío hoy mismo", "¿A qué zona?", "Te paso el enlace"];
  R.s4b = five.map((h, i) => bubble(c4, { side: "out", top: 640 + i * 132, html: h, lab: "se cobra", labCls: "cost" }));
  R.s4one = bubble(c4, { side: "out", top: 760, width: 820, html: "¡Hola! Sí tenemos talla M y el envío sale hoy mismo. ¿A qué zona te lo mando? Aquí tienes el enlace.", lab: "1 cobro", labCls: "cost" });
  // L07 — interactive message + WhatsApp Flow (customer view)
  const c7 = R.s7_chat;
  R.s7msg = bubble(c7, { side: "in", top: 640, width: 760, html: "<b>Tienda Lino</b><br>¿Qué necesitas hoy?<div class='btns'><div>Ver catálogo</div><div>Hacer pedido</div><div>Hablar con alguien</div></div>", time: "12:10" });
  R.s7done = bubble(c7, { side: "out", top: 1290, html: "Pedido enviado: Camisa lino · M", time: "12:11" });
  R.s7in = $$(".in", R.s7_sheet); R.s7seg = $$(".seg span", R.s7_sheet);
  const rnd = mulberry(5);
  R.s7g = [];
  for (let i = 0; i < 12; i++) {
    const g = document.createElement("i"); const right = i % 3 !== 0;
    const w = 240 + rnd() * 380; g._w = w; g._right = right; g._y = 600 + i * 66;
    g.style.width = w + "px"; g.style.top = g._y + "px"; g.style[right ? "right" : "left"] = "70px";
    R.s7_ghost.appendChild(g); R.s7g.push(g);
  }
  // L08 — two utility templates → one
  const c8 = R.s8_chat;
  R.s8a = bubble(c8, { side: "out", top: 640, width: 800, html: "<div class='tpl-h'>Pedido confirmado</div>Tu pedido #4821 está confirmado.<div class='tpl-f'>Tienda Lino</div>", lab: "se cobra", labCls: "cost", time: "09:15" });
  R.s8b = bubble(c8, { side: "out", top: 1000, width: 800, html: "<div class='tpl-h'>Va en camino</div>Número de guía: 7731 0045 1290<div class='tpl-f'>Tienda Lino</div>", lab: "se cobra", labCls: "cost", time: "09:15" });
  R.s8c = bubble(c8, { side: "out", top: 760, width: 800, html: "<div class='tpl-h'>Pedido confirmado · #4821</div>Va en camino. Número de guía: 7731 0045 1290<div class='tpl-f'>Tienda Lino</div><div class='btns'><div>Rastrear envío</div></div>", lab: "1 cobro", labCls: "cost", time: "09:15" });
  // L06 — 72 hour ring ticks
  let tk = "";
  for (let i = 0; i < 72; i++) {
    const a = (i / 72) * Math.PI * 2 - Math.PI / 2, major = i % 24 === 0, r1 = 236, r2 = major ? 262 : 248;
    tk += `<line x1="${(260 + Math.cos(a) * r1).toFixed(1)}" y1="${(260 + Math.sin(a) * r1).toFixed(1)}" x2="${(260 + Math.cos(a) * r2).toFixed(1)}" y2="${(260 + Math.sin(a) * r2).toFixed(1)}" stroke="rgba(243,238,230,${major ? 0.9 : 0.35})" stroke-width="${major ? 3 : 2}" data-i="${i}"/>`;
  }
  R.s6_ticks.innerHTML = tk; R.s6tk = $$("line", R.s6_ticks);
  css(R.s6_ring, { left: "280px", top: "1000px" });
  css(R.s6_72, { left: "280px" }); css(R.s6_free, { left: "280px" });
  // L05 dot matrix context
  R.dctx = R.s5_dots.getContext("2d");
  R.s5_dots.height = 620;
}
function mulberry(a) { return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

async function loadEmblem() {
  const t = await (await fetch("wbrs-emblem.svg")).text();
  R.s10_emblem.innerHTML = t.replace(/<\?xml[^>]*\?>/, "");
  const svg = $("svg", R.s10_emblem);
  const cx = 78.19, cy = 52.07;
  R.emCircle = []; R.emPetal = []; R.emText = [];
  for (const path of $$("path", svg)) {
    const b = path.getBBox();
    path.style.transformOrigin = `${cx}px ${cy}px`;
    if (b.y > 97) R.emText.push(path);
    else if (b.width > 40) R.emCircle.push(path);
    else { path._a = Math.atan2(b.y + b.height / 2 - cy, b.x + b.width / 2 - cx); R.emPetal.push(path); }
  }
  R.emPetal.sort((a, b) => a._a - b._a);
  R.emText.sort((a, b) => a.getBBox().x - b.getBBox().x + (a.getBBox().y - b.getBBox().y) * 10);
}

/* ═════════ presenter (Flow @me) ═════════ */
const CAMS = [];  // {line, a, b}
let camCtx, camImg = null, camKey = "";
const imgCache = new Map();
function camWindow(t) { for (const c of CAMS) if (t >= c.a && t < c.b) return c; return null; }
function camFrame(c, t) {
  const L = LN[c.line];
  const ct = Math.max(0, t - L.t0 + L.clipIn);
  return Math.min(c.n, Math.floor(ct * FPS_CAM) + 1);
}
function frameURL(line, i) { return `frames/${line}/${String(i).padStart(4, "0")}.jpg`; }
async function prepare(t) {
  const c = camWindow(clamp(t, 0, DURATION));
  if (!c) return;
  const url = frameURL(c.line, camFrame(c, t));
  let im = imgCache.get(url);
  if (!im) {
    im = new Image(); im.src = url; await im.decode(); imgCache.set(url, im);
    if (imgCache.size > 40) imgCache.delete(imgCache.keys().next().value);
  }
  camImg = im; camKey = url;
}
function drawCam(t, split = 0) {
  const src = RENDER ? camImg : R.camv;
  if (!src) return;
  if (!RENDER && R.camv.readyState < 2) return;
  const ctx = camCtx;
  if (split <= 0) { ctx.drawImage(src, 0, 0, 1080, 1920); return; }
  // Swiss asymmetric horizon split: top 55% slides left, bottom 45% slides right
  const sw = RENDER ? src.naturalWidth : src.videoWidth, shh = RENDER ? src.naturalHeight : src.videoHeight;
  const cut = 1056, dx = split * 1180;
  ctx.clearRect(0, 0, 1080, 1920);
  ctx.drawImage(src, 0, 0, sw, shh * cut / 1920, -dx, 0, 1080, cut);
  ctx.drawImage(src, 0, shh * cut / 1920, sw, shh * (1920 - cut) / 1920, dx, cut, 1080, 1920 - cut);
}

/* ═════════ L01 · Hook ═════════ */
function s1(t) {
  const on = t < S.T1 + S.T1d + 0.02;
  vis(R.s1, on); if (!on) return;
  const L = "L01";
  const outT = [0.30, 0.66, 1.02, 1.38];
  const tOct = W(L, "octubre"), tTus = W(L, "tus"), tCue = W(L, "cuestan");
  // chat recedes when the headline arrives
  const kr = eio(p(t, tTus - 0.15, 0.6));
  css(R.s1_chat, { transform: `translateY(${(-kr * 40).toFixed(2)}px) scale(${lerp(1, 0.94, kr).toFixed(4)})`, transformOrigin: "540px 300px" });
  // incoming bubble is already arriving on frame 0 (pattern interrupt)
  pop(R.s1b[0], t, -0.12);
  R.s1b.slice(1).forEach((b, i) => {
    pop(b, t, outT[i]);
    ticks(b, t, outT[i] + 0.24, tOct + i * 0.09);
  });
  rise(R.s1_h1, t, { times: [tTus - 0.04, W(L, "respuestas") - 0.04] });
  rise(R.s1_h2, t, { times: [W(L, "ya") - 0.04, tCue - 0.04] });
  css(R.s1_hair, { transform: `scaleX(${eo(p(t, tCue + 0.12, 0.7)).toFixed(4)})` });
  rise(R.s1_foot, t, { t0: tCue + 0.28, st: 0.035, din: 0.6 });
  // exit: the scene leans into the lens while the iris opens on the presenter
  const ke = eio(p(t, S.T1, S.T1d));
  css(R.s1, { transform: `scale(${(1 + ke * 0.08).toFixed(4)})`, filter: blur(ke * 8) });
}

/* iris origin = the last coral double-tick */
let IRIS = [960, 960];
function irisClip(t) {
  if (t < S.T1) return "circle(0px at 50% 50%)";
  const k = eo(p(t, S.T1, S.T1d));
  return k >= 1 ? "none" : `circle(${(k * 2250).toFixed(1)}px at ${IRIS[0].toFixed(1)}px ${IRIS[1].toFixed(1)}px)`;
}

/* ═════════ L02 · Presenter ═════════ */
function s2(t) {
  const on = t >= S.T1 && t < S.T2 + S.T2d + 0.02;
  vis(R.s2, on); if (!on) return;
  const L = "L02";
  const tPero = W(L, "pero");
  rise(R.s2_a, t, { times: [W(L, "cada") - 0.04, W(L, "mensaje") - 0.04], tout: tPero - 0.1 });
  rise(R.s2_b, t, { times: [W(L, "de", 1) - 0.04, W(L, "servicio") - 0.04], tout: tPero - 0.08 });
  rise(R.s2_c, t, { t0: W(L, "ventana") - 0.05, st: 0.04, din: 0.6, tout: tPero - 0.06, dout: 0.3 });
  const t5 = W(L, "cinco");
  const k5 = eo(p(t, t5 - 0.06, 0.75));
  css(R.s2_5, { transform: `translateY(${((1 - k5) * 220).toFixed(2)}px) skewX(${((1 - k5) * -8).toFixed(2)}deg)`, opacity: clamp(k5 * 2).toFixed(3), filter: blur((1 - k5) * 16), clipPath: `inset(0 0 ${((1 - k5) * 40).toFixed(2)}% 0)` });
  rise(R.s2_d, t, { times: [W(L, "formas") - 0.04, W(L, "formas") + 0.14] });
  rise(R.s2_e, t, { times: [W(L, "pagar") - 0.04, W(L, "menos") - 0.04] });
  css(R.s2, { clipPath: knifeClip(t, "left", S.T2, S.T2d) || irisClip(t) });
}

/* knife-edge −24° geometry */
const TAN24 = Math.tan((24 * Math.PI) / 180);
function knifeE(t, T, d) { return lerp(1080 + 960 * TAN24 + 8, -960 * TAN24 - 8, knifeEase(p(t, T, d))); }
function knifeClip(t, side, T, d) {
  if (t < T) return side === "left" ? null : "inset(0 0 0 100%)";
  if (t > T + d) return side === "left" ? "inset(0 0 0 100%)" : "none";
  const e = knifeE(t, T, d), top = e + 960 * TAN24, bot = e - 960 * TAN24;
  return side === "left"
    ? `polygon(-2000px 0, ${top.toFixed(1)}px 0, ${bot.toFixed(1)}px 1920px, -2000px 1920px)`
    : `polygon(${top.toFixed(1)}px 0, 3000px 0, 3000px 1920px, ${bot.toFixed(1)}px 1920px)`;
}

/* ═════════ L03 · What is charged ═════════ */
function s3(t) {
  const on = t >= S.T2 && t < S.T3 + 0.1;
  vis(R.s3, on); if (!on) return;
  const L = "L03";
  rise(R.s3_h1, t, { times: [W(L, "te") - 0.04, W(L, "escriben") - 0.04] });
  rise(R.s3_h1b, t, { times: [W(L, "gratis") - 0.04] });
  const tg = W(L, "gratis");
  pop(R.s3b[0], t, W(L, "clientes") - 0.08); labIn(R.s3b[0], t, tg);
  pop(R.s3b[1], t, W(L, "escriben") - 0.05); labIn(R.s3b[1], t, tg + 0.08);
  const outs = [W(L, "cobra"), W(L, "mensaje"), W(L, "envias")];
  R.s3b.slice(2).forEach((b, i) => { pop(b, t, outs[i] - 0.1); ticks(b, t, outs[i] + 0.12, outs[i] + 0.2); });
  rise(R.s3_h2, t, { times: [W(L, "lo", 2) - 0.04, W(L, "que", 2) - 0.04] });
  rise(R.s3_h2b, t, { times: [W(L, "se") - 0.04, W(L, "cobra") - 0.04] });
  // in: right side of the knife · out: inertial scale-punch (1 → 2.4, ease-in, cut at frame 6)
  const ko = ei(p(t, S.T3, 0.1));
  css(R.s3, { clipPath: knifeClip(t, "right", S.T2, S.T2d), transform: `scale(${(1 + ko * 1.4).toFixed(4)})`, filter: blur(ko * 10), opacity: (t >= S.T3 + 0.1 ? 0 : 1).toString() });
}

/* ═════════ L04 · 1 — one message, not five ═════════ */
function s4(t) {
  const on = t >= S.T3 + 0.1 && t < S.T4 + S.T4d + 0.02;
  vis(R.s4, on); if (!on) return;
  const L = "L04";
  const kin = eo(p(t, S.T3 + 0.1, S.T3d));
  css(R.s4, { transform: `scale(${lerp(0.85, 1, kin).toFixed(4)})`, clipPath: ribbonClip(t, "out") });
  numeral(R.s4_n, t, S.T3 + 0.1);
  rise(R.s4_h1, t, { times: [W(L, "no") - 0.04, W(L, "mandes") - 0.04] });
  rise(R.s4_h2, t, { times: [W(L, "mandes") + 0.1, W(L, "cinco") - 0.04] });
  const tb = W(L, "burbujas"), tEnt = W(L, "entregado"), tUno = W(L, "uno"), tSolo = W(L, "solo");
  const km = eio(p(t, tUno - 0.05, 0.5));
  R.s4b.forEach((b, i) => {
    const t0 = tb - 0.25 + i * 0.09;
    const k = eo(p(t, t0, 0.42));
    const y0 = 640 + i * 132, yc = 760;
    const dy = (yc - y0) * km;
    css(b, { transform: `translateY(${((1 - k) * 34 + dy).toFixed(2)}px) scale(${(lerp(0.86, 1, k) * lerp(1, 0.9, km)).toFixed(4)})`, opacity: (clamp(k * 2.2) * (1 - clamp(km * 1.6))).toFixed(3), filter: blur((1 - k) * 6 + km * 6) });
    ticks(b, t, t0 + 0.2, tEnt - 0.1 + i * 0.07);
  });
  const k1 = eo(p(t, tUno + 0.1, 0.55));
  css(R.s4one, { transform: `scale(${lerp(0.9, 1, k1).toFixed(4)})`, opacity: k1.toFixed(3), filter: blur((1 - k1) * 8) });
  ticks(R.s4one, t, tUno + 0.3, tSolo + 0.1);
  const kc = eo(p(t, W(L, "cuenta") - 0.05, 0.6));
  css(R.s4_ct, { opacity: kc.toFixed(3), transform: `translateY(${((1 - kc) * 30).toFixed(2)}px)` });
  const one = t >= tSolo;
  txt(R.s4_ctn, one ? "1" : "5"); txt(R.s4_ctl, one ? "mensaje cobrado" : "mensajes cobrados");
  const kn = eo(p(t, tSolo, 0.4));
  css(R.s4_ctn, { color: one ? "var(--teal)" : "var(--coral)", display: "inline-block", transform: `translateY(${(one ? (1 - kn) * 24 : 0).toFixed(2)}px)` });
}

/* kinetic ribbon sweep (L04 → L05): diagonal ribbons cross; B unmasks along the trailing edge */
function ribbonX(t) { return lerp(-1500, 1900, eio(p(t, S.T4, S.T4d))); }   // trailing edge x at y=0
const RIB_SK = 0.42; // horizontal shift per px of y
function ribbonClip(t, side) {
  if (t < S.T4) return side === "out" ? "none" : "inset(0 0 0 100%)";
  if (t > S.T4 + S.T4d) return side === "out" ? "inset(0 0 0 100%)" : "none";
  const x0 = ribbonX(t), x1 = x0 - 1920 * RIB_SK;
  return side === "in"
    ? `polygon(-3000px 0, ${x0.toFixed(1)}px 0, ${x1.toFixed(1)}px 1920px, -3000px 1920px)`
    : `polygon(${x0.toFixed(1)}px 0, 4000px 0, 4000px 1920px, ${x1.toFixed(1)}px 1920px)`;
}

/* ═════════ L05 · 2 — 1,000 free ═════════ */
const COLS = 40, ROWS = 25, GAP = 23;
let dotKey = "";
function s5(t) {
  const on = t >= S.T4 && t < S.T5 + S.T5d + 0.02;
  vis(R.s5, on); if (!on) return;
  const L = "L05";
  const kp = ei(p(t, S.T5, S.T5d));
  css(R.s5, { clipPath: ribbonClip(t, "in"), transform: `scale(${lerp(1, 0.8, kp).toFixed(4)})`, filter: blur(kp * 12), opacity: (1 - kp).toFixed(3) });
  numeral(R.s5_n, t, S.T4 + 0.08);
  rise(R.s5_h1, t, { times: [W(L, "mil") - 0.05] });
  rise(R.s5_h2, t, { times: [W(L, "gratis") - 0.04] });
  rise(R.s5_sub, t, { times: [W(L, "cada") - 0.04, W(L, "mes") - 0.04, W(L, "mes") + 0.08, W(L, "por") - 0.04, W(L, "numero") - 0.04] });
  // dot matrix: every dot is one service message
  const fa = W(L, "primeros") - 0.05, fb = W(L, "gratis") + 0.1;
  const kf = eio(p(t, fa, fb - fa));
  const filled = Math.round(kf * 1000);
  const kIn = eo(p(t, S.T4 + 0.1, 0.6));
  const tMid = W(L, "midelos");
  const scan = p(t, tMid - 0.05, 0.9);
  const kOver = eo(p(t, tMid + 0.35, 0.4));
  const key = `${filled}|${kIn.toFixed(2)}|${scan.toFixed(3)}|${kOver.toFixed(2)}`;
  if (key !== dotKey) {
    dotKey = key;
    const ctx = R.dctx; ctx.clearRect(0, 0, 920, 620);
    for (let i = 0; i < 1000; i++) {
      const c = i % COLS, r = Math.floor(i / COLS);
      const x = 12 + c * GAP, y = 12 + r * GAP;
      // column-major wave so the fill reads as a sweep
      const order = c * ROWS + r;
      const isOn = order < filled;
      const appear = clamp(kIn * 1.6 - (r / ROWS) * 0.6);
      if (appear <= 0) continue;
      const sc = Math.abs(x - 12 - scan * 900) < 14 && scan > 0 && scan < 1;
      ctx.globalAlpha = appear;
      ctx.fillStyle = isOn ? (sc ? "#b9fff0" : "#00cea7") : "rgba(243,238,230,0.13)";
      ctx.beginPath(); ctx.arc(x, y, isOn ? 6.6 : 5.2, 0, Math.PI * 2); ctx.fill();
    }
    // the 1,001st message
    if (kOver > 0) {
      ctx.globalAlpha = kOver; ctx.fillStyle = "#ff6a4d";
      ctx.beginPath(); ctx.arc(12, 12 + ROWS * GAP + 10, 6.6 + (1 - kOver) * 8, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
    if (scan > 0 && scan < 1) { ctx.fillStyle = "rgba(185,255,240,0.55)"; ctx.fillRect(12 + scan * 900, 0, 1.5, ROWS * GAP + 2); }
  }
  txt(R.s5_cntn, String(filled).padStart(4, "0"));
  const kc = eo(p(t, fa - 0.2, 0.5));
  css(R.s5_cnt, { opacity: kc.toFixed(3) });
  rise(R.s5_over, t, { t0: tMid + 0.35, st: 0.04, din: 0.55 });
}

/* ═════════ L06 · 3 — 72 h free (presenter) ═════════ */
function s6(t) {
  const on = t >= S.T5 && t < S.T6 + 0.05;
  vis(R.s6, on); if (!on) return;
  const L = "L06";
  numeral(R.s6_n, t, LN.L06.t0 - 0.02);
  const tAb = W(L, "abren");
  rise(R.s6_a, t, { times: [W(L, "llega") - 0.04, W(L, "desde") - 0.04, W(L, "un") - 0.04, W(L, "anuncio") - 0.04], tout: tAb - 0.12 });
  rise(R.s6_b, t, { times: [W(L, "click") - 0.04], tout: tAb - 0.1 });
  rise(R.s6_c, t, { t0: W(L, "whatsapp") + 0.05, st: 0.035, din: 0.55, tout: tAb - 0.08, dout: 0.3 });
  // ring: three laps of 24 h, one per beat, landing on "horas"
  const t72 = W(L, "72"), tH = W(L, "horas");
  const kRing = eo(p(t, tAb - 0.05, 0.5));
  css(R.s6_ring, { opacity: kRing.toFixed(3), transform: `scale(${lerp(0.82, 1, kRing).toFixed(4)})` });
  const lap = eio(p(t, tAb + 0.05, Math.max(0.5, tH - tAb + 0.1)));
  const laps = lap * 3;
  const C = 2 * Math.PI * 214;
  const frac = laps >= 3 ? 1 : laps % 1;
  attr(R.s6_arc, "stroke-dasharray", `${(C * (laps >= 3 ? 1 : frac)).toFixed(1)} 2000`);
  const lapN = Math.min(3, Math.floor(laps) + (laps > 0 ? 1 : 0));
  txt(R.s6_72n, String(Math.max(24, Math.min(72, lapN * 24))));
  R.s6tk.forEach((l, i) => attr(l, "opacity", (i / 72 <= lap ? 1 : 0.35).toFixed(2)));
  const kN = eo(p(t, t72 - 0.3, 0.5));
  css(R.s6_72, { opacity: (kRing * kN).toFixed(3), transform: `translateY(${((1 - kN) * 30).toFixed(2)}px)` });
  rise(R.s6_free, t, { times: [W(L, "gratis") - 0.04] });
}

/* ═════════ L07 · 4 — buttons, lists, forms ═════════ */
function typed(el, t, t0, d) {
  const v = el.dataset.v, n = Math.floor(v.length * p(t, t0, d));
  txt(el, v.slice(0, n));
  el.classList.toggle("focus", t >= t0 && t < t0 + d + 0.2);
}
function s7(t) {
  const on = t >= S.T6 && t < S.T7 + S.T7d * 0.5;
  vis(R.s7, on); if (!on) { vis(R.s7_sheet, false); vis(R.s7_tap, false); return; }
  const L = "L07";
  numeral(R.s7_n, t, S.T6 + 0.02);
  const tBot = W(L, "botones"), tForm = W(L, "formularios"), tToque = W(L, "toque"), tConv = W(L, "conversacion");
  // ghost of the long back-and-forth, collapsing into one interactive message
  const kg = eio(p(t, tBot - 0.2, 0.45));
  R.s7g.forEach((g, i) => {
    const ka = eo(p(t, S.T6 + 0.05 + i * 0.05, 0.35));
    css(g, { opacity: (ka * (1 - kg)).toFixed(3), transform: `translateY(${((1 - ka) * 20 + (900 - g._y) * kg * 0.6).toFixed(1)}px) scaleY(${lerp(1, 0.2, kg).toFixed(3)})` });
  });
  pop(R.s7msg, t, tBot - 0.08);
  const btns = $$(".btns div", R.s7msg);
  const tPick = W(L, "listas") - 0.05;
  btns.forEach((b, i) => css(b, { background: i === 1 && t >= tPick && t < tPick + 0.35 ? "rgba(83,189,235,0.14)" : "transparent" }));
  // WhatsApp Flow sheet
  const kS = eo(p(t, tForm - 0.12, 0.5)), kD = eio(p(t, tToque + 0.28, 0.35));
  vis(R.s7_sheet, kS > 0 && kD < 1);
  css(R.s7_sheet, { transform: `translateY(${((1 - kS) * 1100 + kD * 1100).toFixed(1)}px)` });
  css(R.s7msg, { opacity: (1 - 0.55 * kS * (1 - kD)).toFixed(3) });
  typed(R.s7in[0], t, W(L, "dentro") - 0.05, 0.45);
  R.s7seg.forEach((s, i) => s.classList.toggle("on", i === 1 && t >= W(L, "chat") - 0.05));
  typed(R.s7in[1], t, W(L, "resuelves") - 0.1, 0.55);
  // the one tap
  const ctaY = 820 + 22 + 8 + 26 + 44 * 1.2 + 28 + 3 * (36 + 84 + 26) + 34 + 48;
  const kT = eo(p(t, tToque - 0.35, 0.3)), press = Math.sin(Math.PI * p(t, tToque - 0.04, 0.16));
  vis(R.s7_tap, kT > 0 && t < tToque + 0.35);
  css(R.s7_tap, { transform: `translate(${(780 - 60 + (1 - kT) * 120).toFixed(1)}px, ${(ctaY - 60 + (1 - kT) * 160).toFixed(1)}px) scale(${(1 - press * 0.18).toFixed(3)})`, opacity: (kT * (1 - p(t, tToque + 0.2, 0.15))).toFixed(3) });
  const kr = p(t, tToque, 0.4);
  css($(".rip", R.s7_cta), { transform: `scale(${(kr * 26).toFixed(2)})`, opacity: (kr > 0 && kr < 1 ? 1 - kr : 0).toFixed(3) });
  pop(R.s7done, t, tToque + 0.45);
  ticks(R.s7done, t, tToque + 0.65, null);
  rise(R.s7_h1, t, { times: [W(L, "un", 1) - 0.04, tToque - 0.04] });
  rise(R.s7_h2, t, { times: [W(L, "una") - 0.12, W(L, "una") - 0.04, tConv - 0.04] });
}

/* louver shutter (L07 → L08): 3 slats flip closed (A) then open (B) with 30 ms domino */
function louvers(t) {
  const T = S.T7, d = S.T7d, on = t >= T && t < T + d + 0.1;
  vis(R.louvers, on); if (!on) return;
  $$("i", R.louvers).forEach((el, i) => {
    const k = p(t, T + i * 0.03, d - 0.06);
    const a = k < 0.5 ? lerp(90, 0, knifeEase(k * 2)) : lerp(0, -90, ei((k - 0.5) * 2));
    css(el, { transform: `rotateY(${a.toFixed(2)}deg)`, opacity: (Math.abs(a) > 89 ? 0 : 1).toString() });
  });
}

/* ═════════ L08 · 5 — merge templates ═════════ */
function s8(t) {
  const on = t >= S.T7 + S.T7d * 0.5 && t < S.T8 + S.T8d + 0.02;
  vis(R.s8, on); if (!on) return;
  const L = "L08";
  css(R.s8, { clipPath: laserClip(t, "below") });
  numeral(R.s8_n, t, S.T7 + S.T7d * 0.5);
  rise(R.s8_h1, t, { times: [W(L, "junta") - 0.02, W(L, "plantillas") - 0.04] });
  rise(R.s8_h2, t, { times: [W(L, "un") - 0.04, W(L, "mensaje") - 0.04] });
  const tJ = W(L, "junta"), tSolo = W(L, "solo"), tC = W(L, "confirmacion"), tG = W(L, "guia");
  const km = eio(p(t, tSolo - 0.1, 0.5));
  [[R.s8a, tJ - 0.1, 640], [R.s8b, tJ + 0.12, 1000]].forEach(([b, t0, y0], i) => {
    const k = eo(p(t, t0, 0.42));
    const dy = (760 - y0) * km;
    css(b, { transform: `translateY(${((1 - k) * 34 + dy).toFixed(2)}px) scale(${(lerp(0.86, 1, k) * lerp(1, 0.94, km)).toFixed(4)})`, opacity: (clamp(k * 2.2) * (1 - clamp(km * 1.5))).toFixed(3), filter: blur((1 - k) * 6 + km * 5) });
    ticks(b, t, t0 + 0.22, W(L, "plantillas") + 0.05 + i * 0.1);
  });
  // emphasis follows the voice: header of A on "Confirmación", guide number of B on "guía"
  css($(".tpl-h", R.s8a), { color: t >= tC - 0.05 && t < tSolo ? "#ffffff" : "" , textDecoration: t >= tC - 0.05 && t < tSolo ? "underline 3px #00cea7" : "none", textUnderlineOffset: "8px" });
  css($(".body", R.s8b), { color: t >= tG - 0.05 && t < tSolo ? "#ffffff" : "" });
  const kc = eo(p(t, tSolo + 0.05, 0.55));
  css(R.s8c, { transform: `scale(${lerp(0.9, 1, kc).toFixed(4)})`, opacity: kc.toFixed(3), filter: blur((1 - kc) * 8) });
  ticks(R.s8c, t, tSolo + 0.3, W(L, "dos") - 0.05);
  const kt = eo(p(t, W(L, "plantillas") + 0.15, 0.5));
  css(R.s8_ct, { opacity: kt.toFixed(3), transform: `translateY(${((1 - kt) * 30).toFixed(2)}px)` });
  const one = t >= tSolo + 0.1;
  txt(R.s8_ctn, one ? "1" : "2"); txt(R.s8_ctl, one ? "plantilla cobrada" : "plantillas cobradas");
  css(R.s8_ctn, { color: one ? "var(--teal)" : "var(--coral)" });
}

/* anamorphic laser streak (L08 → L09): the line sweeps down, the presenter is etched in above it */
function laserY(t) { return lerp(-10, 1930, p(t, S.T8, S.T8d)); }
function laserClip(t, part) {
  if (t < S.T8) return part === "below" ? "none" : "inset(0 0 100% 0)";
  if (t > S.T8 + S.T8d) return part === "below" ? "inset(100% 0 0 0)" : "none";
  const y = laserY(t);
  return part === "below" ? `inset(${y.toFixed(1)}px 0 0 0)` : `inset(0 0 ${(1920 - y).toFixed(1)}px 0)`;
}

/* ═════════ L09 · App vs API (presenter) ═════════ */
function s9(t) {
  const on = t >= S.T8 && t < S.T9 + S.T9d + 0.02;
  vis(R.s9, on); if (!on) return;
  const L = "L09";
  const tApp = W(L, "app"), tApi = W(L, "api");
  css(R.s9_r0, { transform: `scaleX(${eo(p(t, tApp - 0.2, 0.7)).toFixed(4)})` });
  const ki1 = eo(p(t, tApp - 0.1, 0.55));
  css(R.s9_i1, { opacity: ki1.toFixed(3), transform: `translateY(${((1 - ki1) * 24).toFixed(2)}px)` });
  rise(R.s9_a, t, { times: [tApp - 0.04, W(L, "whatsapp") - 0.04, W(L, "business") - 0.04] });
  rise(R.s9_a2, t, { times: [W(L, "nada") - 0.04, W(L, "cambia") - 0.04] });
  css(R.s9_r1, { transform: `scaleX(${eo(p(t, tApi - 0.25, 0.7)).toFixed(4)})` });
  const ki2 = eo(p(t, tApi - 0.1, 0.55));
  css(R.s9_i2, { opacity: ki2.toFixed(3), transform: `translateY(${((1 - ki2) * 24).toFixed(2)}px)` });
  rise(R.s9_b, t, { times: [tApi - 0.04, tApi + 0.06, tApi + 0.14] });
  rise(R.s9_b2, t, { times: [W(L, "registra") - 0.04, W(L, "un") - 0.04, W(L, "metodo") - 0.04, W(L, "de", 2) - 0.04, W(L, "pago") - 0.04] });
  // horizon split: everything below the line rides right with the bottom half of the frame
  const ks = splitK(t);
  css(R.s9, { transform: `translateX(${(ks * 1180).toFixed(1)}px)`, clipPath: laserClip(t, "above") });
}
function splitK(t) { return knifeEase(p(t, S.T9, S.T9d)); }

/* ═════════ L10 · Webres Studio ═════════ */
function s10(t) {
  const on = t >= S.T9;
  vis(R.s10, on); if (!on) return;
  const L = "L10";
  const ks = splitK(t);
  // revealed through the widening gap between the two halves
  const gap = ks * 1920;
  css(R.s10, { clipPath: ks >= 1 ? "none" : `inset(${Math.max(0, 1056 - gap * 0.55).toFixed(1)}px 0 ${Math.max(0, 864 - gap * 0.45).toFixed(1)}px 0)` });
  const tw = W(L, "webres") - 0.1;
  R.emCircle.forEach((c, i) => {
    const kc = eo(p(t, S.T9 + 0.1 + i * 0.08, 0.8));
    css(c, { transform: `scale(${lerp(0.4, 1, kc).toFixed(4)})`, opacity: clamp(kc * 2).toFixed(3) });
  });
  R.emPetal.forEach((pt, i) => {
    const kp = eo(p(t, tw + i * 0.03, 0.75));
    css(pt, { transform: `rotate(${((1 - kp) * -45).toFixed(2)}deg) scale(${lerp(0.2, 1, kp).toFixed(4)})`, opacity: clamp(kp * 2).toFixed(3) });
  });
  const tsd = W(L, "studio") - 0.05;
  R.emText.forEach((pt, i) => {
    const kt = eo(p(t, tsd + i * 0.012, 0.6));
    css(pt, { transform: `translateY(${((1 - kt) * 6).toFixed(2)}px)`, opacity: kt.toFixed(3) });
  });
  rise(R.s10_a, t, { times: [W(L, "automatizamos") - 0.04, W(L, "tu") - 0.04, W(L, "whatsapp") - 0.04] });
  rise(R.s10_b, t, { times: [W(L, "cada") - 0.04, W(L, "respuesta") - 0.04] });
  rise(R.s10_c, t, { times: [W(L, "cuenta") - 0.04] });
  const te = WE(L, "cuenta");
  css(R.s10_hair, { transform: `scaleX(${eo(p(t, te + 0.05, 0.7)).toFixed(4)})` });
  rise(R.s10_handle, t, { t0: te + 0.2, st: 0.028, din: 0.7 });
}

/* ═════════ background, presenter layer, overlays ═════════ */
function flare(t) { let f = 0; for (const [tt, a] of S.flares) if (t >= tt) f += a * Math.exp(-(t - tt) * 3.2); return f; }
function background(t) {
  // [start, palette]
  const seq = [[0, PAL.cost], [S.T2, PAL.studio], [S.T3 + 0.1, PAL.cost], [S.T4 + S.T4d * 0.5, PAL.free], [S.T6, PAL.studio], [S.T7 + S.T7d * 0.5, PAL.studio], [S.T9, PAL.web]];
  let A = PAL.ink, B = PAL.ink, mix = 0;
  for (let i = 0; i < seq.length; i++) {
    const [ts, P] = seq[i];
    if (t >= ts) { A = P; const nx = seq[i + 1]; if (nx && t >= nx[0] - 0.0001) continue; break; }
  }
  // soft bleed into each new palette (0.5 s) so the light never pops
  for (let i = 1; i < seq.length; i++) {
    const [ts, P] = seq[i];
    if (t >= ts && t < ts + 0.5) { A = seq[i - 1][1]; B = P; mix = eio(p(t, ts, 0.5)); }
  }
  const coldOpen = eo(p(t, 0, 0.6));
  if (t < 0.6) { B = A; A = PAL.ink; mix = coldOpen; }
  gl.uniform1f(U.uTime, t); gl.uniform1f(U.uFlare, flare(t));
  gl.uniform3fv(U.uA, A); gl.uniform3fv(U.uB, B); gl.uniform1f(U.uMix, mix);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
}
function camLayer(t) {
  const c = camWindow(t);
  vis(R.cam, !!c);
  if (!c) return;
  let clip = "none", tr = "none", filt = "none", op = 1, split = 0;
  if (c.line === "L02") {
    clip = knifeClip(t, "left", S.T2, S.T2d) || irisClip(t);
  } else if (c.line === "L06") {
    const k = eo(p(t, S.T5, S.T5d));      // 2.5D push: B arrives from translateZ(+) to rest
    tr = `scale(${lerp(1.22, 1, k).toFixed(4)})`; filt = blur((1 - k) * 10); op = clamp(k * 1.5);
  } else if (c.line === "L09") {
    clip = laserClip(t, "above");
    split = splitK(t);
  }
  css(R.cam, { clipPath: clip, transform: tr, filter: filt, opacity: op.toFixed(3) });
  drawCam(t, split);
}
function overlays(t) {
  // knife hairline
  const kOn = t >= S.T2 && t <= S.T2 + S.T2d;
  vis(R.knifeLine, kOn);
  if (kOn) css(R.knifeLine, { transform: `translateX(${(knifeE(t, S.T2, S.T2d) - 1.5).toFixed(1)}px) rotate(24deg)` });
  // ribbons
  const rOn = t >= S.T4 - 0.05 && t <= S.T4 + S.T4d + 0.05;
  vis(R.ribbon, rOn);
  if (rOn) {
    const x = ribbonX(t);
    css($(".r1", R.ribbon), { transform: `translateX(${(x - 10).toFixed(1)}px) skewX(${(-Math.atan(RIB_SK) * 180 / Math.PI).toFixed(2)}deg)`, width: "300px" });
    css($(".r2", R.ribbon), { transform: `translateX(${(x - 330).toFixed(1)}px) skewX(${(-Math.atan(RIB_SK) * 180 / Math.PI).toFixed(2)}deg)`, width: "320px" });
  }
  // laser
  const lOn = t >= S.T8 && t <= S.T8 + S.T8d + 0.12;
  vis(R.laser, lOn);
  if (lOn) css(R.laser, { transform: `translateY(${laserY(t).toFixed(1)}px)`, opacity: (1 - p(t, S.T8 + S.T8d, 0.12)).toFixed(3) });
  // horizon split drafting line
  const sOn = t >= S.T9 - 0.03 && t <= S.T9 + S.T9d + 0.05;
  vis(R.splitLine, sOn);
  if (sOn) css(R.splitLine, { top: "1056px", opacity: (1 - p(t, S.T9 + S.T9d - 0.05, 0.1)).toFixed(3) });
  louvers(t);
  // clinical luminance flash: 1-frame attack, 2-frame hold, exponential bleed
  const F = S.T6 + 0.05;
  let f = 0;
  if (t >= F - 0.017 && t < F) f = p(t, F - 0.017, 0.017);
  else if (t >= F && t < F + 0.034) f = 1;
  else if (t >= F + 0.034) f = Math.exp(-(t - F - 0.034) * 22);
  css(R.flash, { opacity: f.toFixed(3) });
  css(R.fade, { opacity: p(t, DURATION - 0.5, 0.5).toFixed(3) });
  css(R.sync, { background: t < 0.0001 ? "#fff" : "#000" });
}

function renderAt(t) {
  t = clamp(t, 0, DURATION);
  background(t);
  camLayer(t);
  s1(t); s2(t); s3(t); s4(t); s5(t); s6(t); s7(t); s8(t); s9(t); s10(t);
  overlays(t);
}

/* ═════════ audio cue sheet (single source of truth for the SFX mix) ═════════ */
function cues() {
  const c = [];
  const add = (t, type, gain = 1) => c.push([+t.toFixed(3), type, gain]);
  // L01
  add(0.0, "pop_in", 0.55);
  [0.30, 0.66, 1.02, 1.38].forEach((tt) => { add(tt, "pop", 0.6); add(tt + 0.24, "tick_soft", 0.3); });
  for (let i = 0; i < 4; i++) add(W("L01", "octubre") + i * 0.09, "coin", 0.5);
  add(W("L01", "tus") - 0.04, "whoosh_s", 0.4); add(W("L01", "cuestan") - 0.04, "hit", 0.7);
  add(W("L01", "cuestan") + 0.12, "hairline", 0.4);
  add(S.T1 - 0.3, "riser", 0.5); add(S.T1, "iris", 0.8); add(S.T1 + S.T1d, "sub", 0.7);
  // L02
  add(W("L02", "cada") - 0.04, "whoosh_s", 0.3); add(W("L02", "ventana") - 0.05, "tick", 0.35);
  add(W("L02", "pero") - 0.1, "whoosh_rev", 0.3); add(W("L02", "cinco") - 0.06, "hit", 0.7);
  add(W("L02", "pagar") - 0.04, "whoosh_s", 0.3);
  // L03
  add(S.T2 - 0.02, "whoosh_fast", 0.55); add(S.T2 + S.T2d * 0.5, "snap", 0.85);
  add(W("L03", "clientes") - 0.08, "pop_in", 0.5); add(W("L03", "escriben") - 0.05, "pop_in", 0.5);
  add(W("L03", "gratis") - 0.04, "chime", 0.45);
  [W("L03", "cobra"), W("L03", "mensaje"), W("L03", "envias")].forEach((tt) => { add(tt - 0.1, "pop", 0.55); add(tt + 0.2, "coin", 0.45); });
  // L04
  add(S.T3, "dive", 0.75); add(S.T3 + 0.1, "snap", 0.7);
  add(S.T3 + 0.1, "hit", 0.55);
  for (let i = 0; i < 5; i++) add(W("L04", "burbujas") - 0.25 + i * 0.09, "pop", 0.5);
  for (let i = 0; i < 5; i++) add(W("L04", "entregado") - 0.1 + i * 0.07, "coin", 0.4);
  add(W("L04", "uno") - 0.05, "whoosh_rev", 0.45); add(W("L04", "uno") + 0.12, "pop", 0.7);
  add(W("L04", "solo"), "chime", 0.45);
  // L05
  add(S.T4 - 0.04, "whoosh", 0.7); add(S.T4 + 0.08, "hit", 0.5);
  add(W("L05", "mil") - 0.05, "hit", 0.55);
  const fa = W("L05", "primeros") - 0.05, fb = W("L05", "gratis") + 0.1;
  for (let k = 0; k < 14; k++) add(fa + (fb - fa) * eio(k / 13), "tick_soft", 0.22);
  add(W("L05", "gratis") - 0.04, "shimmer", 0.5);
  add(W("L05", "midelos") - 0.05, "scan", 0.45); add(W("L05", "midelos") + 0.35, "coin", 0.55);
  // L06
  add(S.T5 - 0.3, "riser", 0.45); add(S.T5, "whoosh_deep", 0.7); add(S.T5 + S.T5d, "sub", 0.75);
  add(W("L06", "llega") - 0.04, "whoosh_s", 0.3); add(W("L06", "click") - 0.04, "tick", 0.4);
  add(W("L06", "abren") - 0.05, "whoosh_rev", 0.35);
  const tAb = W("L06", "abren"), tH = W("L06", "horas");
  const dl = Math.max(0.5, tH - tAb + 0.1);
  for (let k = 1; k <= 3; k++) add(tAb + 0.05 + dl * (k / 3) * 0.9, "tick", 0.5);
  add(W("L06", "gratis") - 0.04, "chime", 0.5);
  // L07
  add(S.T6 - 0.25, "riser", 0.4); add(S.T6 + 0.05, "flash", 1.0);
  for (let i = 0; i < 12; i++) add(S.T6 + 0.05 + i * 0.05, "key", 0.16);
  add(W("L07", "botones") - 0.2, "whoosh_rev", 0.4); add(W("L07", "botones") - 0.08, "pop_in", 0.6);
  add(W("L07", "listas") - 0.05, "click", 0.4);
  add(W("L07", "formularios") - 0.12, "ui_up", 0.55);
  for (let i = 0; i < 10; i++) add(W("L07", "dentro") - 0.05 + i * 0.045, "key", 0.25);
  add(W("L07", "chat") - 0.05, "click", 0.45);
  for (let i = 0; i < 12; i++) add(W("L07", "resuelves") - 0.1 + i * 0.045, "key", 0.25);
  add(W("L07", "toque") - 0.04, "click", 0.85); add(W("L07", "toque") + 0.28, "whoosh_s", 0.4);
  add(W("L07", "toque") + 0.45, "pop", 0.6);
  add(W("L07", "conversacion") - 0.04, "hit", 0.45);
  // L08
  for (let i = 0; i < 3; i++) add(S.T7 + i * 0.03 + 0.02, "clack", 0.6);
  for (let i = 0; i < 3; i++) add(S.T7 + S.T7d * 0.5 + i * 0.03 + 0.02, "clack", 0.45);
  add(W("L08", "junta") - 0.1, "pop", 0.55); add(W("L08", "junta") + 0.12, "pop", 0.55);
  add(W("L08", "plantillas") + 0.05, "coin", 0.45); add(W("L08", "plantillas") + 0.15, "coin", 0.45);
  add(W("L08", "solo") - 0.1, "whoosh_rev", 0.45); add(W("L08", "solo") + 0.05, "pop", 0.7);
  add(W("L08", "dos") - 0.05, "chime", 0.4);
  // L09
  add(S.T8, "laser", 0.65); add(S.T8 + S.T8d, "sub", 0.6);
  add(W("L09", "app") - 0.2, "hairline", 0.35); add(W("L09", "nada") - 0.04, "chime", 0.35);
  add(W("L09", "api") - 0.25, "hairline", 0.35); add(W("L09", "registra") - 0.04, "tick", 0.4);
  // L10
  add(S.T9 - 0.25, "riser", 0.5); add(S.T9, "shutter", 0.8); add(S.T9 + S.T9d, "sub", 0.85);
  add(W("L10", "webres") - 0.1, "bloom", 0.6);
  add(W("L10", "automatizamos") - 0.04, "whoosh_s", 0.35);
  add(W("L10", "cuenta") - 0.04, "hit", 0.6); add(WE("L10", "cuenta") + 0.2, "chime", 0.45);
  add(DURATION - 0.5, "sub_soft", 0.55);
  return c.sort((a, b) => a[0] - b[0]);
}

/* ═════════ boot ═════════ */
const params = new URLSearchParams(location.search);
const RENDER = params.has("render");
async function boot() {
  if (RENDER) document.body.classList.add("render");
  refs(); splitAll(); build(); initGL();
  camCtx = R.camc.getContext("2d");
  await loadEmblem();
  await document.fonts.ready;
  S = anchors();
  if (!DEMO && LN.L02.cam) CAMS.push({ line: "L02", a: S.T1, b: S.T2 + S.T2d + 0.02, n: window.CAM_FRAMES.L02 });
  if (!DEMO && LN.L06.cam) CAMS.push({ line: "L06", a: S.T5, b: S.T6 + 0.05, n: window.CAM_FRAMES.L06 });
  if (!DEMO && LN.L09.cam) CAMS.push({ line: "L09", a: S.T8, b: S.T9 + S.T9d + 0.02, n: window.CAM_FRAMES.L09 });
  // iris origin: the last coral double-tick of the hook
  const last = R.s1b[4]._tk, st = R.stage.getBoundingClientRect(), r = last.getBoundingClientRect();
  IRIS = [r.left - st.left + r.width / 2, r.top - st.top + r.height / 2];
  S.flares = [[W("L01", "cuestan"), 0.35], [S.T3 + 0.1, 0.4], [W("L05", "gratis"), 0.45], [S.T6 + 0.05, 0.6], [W("L10", "webres"), 0.5], [W("L10", "cuenta"), 0.3]];
  window.renderAt = renderAt;
  window.prepare = prepare;
  window.CUES = cues();
  window.DURATION = DURATION;
  const t0 = params.has("t") ? parseFloat(params.get("t")) : 0;
  if (RENDER) await prepare(t0);
  renderAt(t0);
  window.READY = true;
  if (RENDER) return;
  preview(t0);
}

/* preview player — the HTML is a deliverable too */
function preview(t0) {
  const stage = $("#stage"), audio = $("#audio"), btn = $("#play"), scrub = $("#scrub"), clock = $("#clock"), v = R.camv;
  scrub.max = DURATION.toFixed(2);
  const fit = () => { const s = Math.min(innerWidth / 1080, (innerHeight - 80) / 1920); stage.style.transform = `scale(${s})`; stage.style.margin = `${(1920 * s - 1920) / 2}px ${(1080 * s - 1080) / 2}px`; };
  fit(); addEventListener("resize", fit);
  let playing = false, start = 0, base = t0, curLine = "";
  const now = () => (playing ? (audio.readyState >= 2 && !audio.paused ? audio.currentTime : base + (performance.now() - start) / 1000) : base);
  const setT = (t) => { base = t; audio.currentTime = t; start = performance.now(); };
  btn.onclick = () => {
    if (playing) { base = now(); playing = false; audio.pause(); v.pause(); btn.textContent = "Reproducir"; return; }
    if (base >= DURATION - 0.05) base = 0;
    setT(base); playing = true; audio.play().catch(() => {}); btn.textContent = "Pausa";
  };
  scrub.oninput = () => setT(parseFloat(scrub.value));
  addEventListener("keydown", (e) => { if (e.code === "Space" && e.target === document.body) { e.preventDefault(); btn.click(); } });
  const syncCam = (t) => {
    const c = camWindow(t);
    if (!c) { if (!v.paused) v.pause(); return; }
    if (DEMO) return;
    if (curLine !== c.line) { curLine = c.line; v.src = window.CAM_SOURCES?.[c.line] || `flow/${c.line}_1080.mp4`; }
    const L = LN[c.line], ct = Math.max(0, t - L.t0 + L.clipIn);
    if (Math.abs(v.currentTime - ct) > (playing ? 0.12 : 0.02)) v.currentTime = ct;
    if (playing && v.paused) v.play().catch(() => {});
    if (!playing && !v.paused) v.pause();
  };
  const loop = () => {
    let t = now();
    if (playing && t >= DURATION) { playing = false; audio.pause(); base = DURATION; btn.textContent = "Reproducir"; t = DURATION; }
    syncCam(t);
    renderAt(t);
    if (document.activeElement !== scrub) scrub.value = t.toFixed(2);
    clock.textContent = t.toFixed(2).padStart(5, "0");
    requestAnimationFrame(loop);
  };
  loop();
}
boot().catch((e) => { console.error(e); window.BOOT_ERROR = String(e && e.stack || e); });
})().catch((e) => {
  console.error(e);
  window.BOOT_ERROR = String(e && e.stack || e);
  const message = document.createElement("p");
  message.textContent = "No se pudo iniciar la vista previa: " + e.message;
  message.style.cssText = "position:fixed;top:0;color:#ff6a4d;background:#0e1114;padding:18px;z-index:100";
  document.body.appendChild(message);
});
