---
name: manim-progressive-proof
description: >-
  Técnicas de demostración visual progresiva al unísono con la voz, destiladas de 3b1b/manim (★ 96.0K, MIT),
  adithya-s-k/manim_skill (★ 1.2K, MIT) y motion-canvas/motion-canvas (★ 19.7K, MIT). Transforma conceptos
  técnicos en pruebas visuales que mutan en vivo sobre S.W('palabra'): estado roto → estado resuelto (Transform),
  atenuación de foco (Spotlight Dimming) y medidores físicos (ValueTracker).
---

# Manim & Motion Canvas Progressive Visual Proof (★ 96K + ★ 19.7K · MIT)

Síntesis práctica de **3Blue1Brown (`3b1b/manim`)**, **`manim-composer`** (`adithya-s-k/manim_skill`) y **`motion-canvas`** (`waitUntil` voice-sync) adaptada a videos cortos verticales en `window.renderAt(t)` + `S.W('palabra')` cumpliendo `AGENTS.md` C7 (*«Cada animación explica algo: un mapa mental de lo que se dice»*).

---

## 1. Transformar en vez de Reemplazar (`Wrong → Right State Morph`)

El cerebro entiende el doble de rápido cuando **ve el mismo objeto corregirse** que cuando cambia de lámina:
- **Patrón `Wrong → Right`:**
  1. En la pregunta/dolor (`S.W('horrible')` / `S.W('fallo')`), muestra el objeto defectuoso concreto (ej. botón deforme / código en rojo).
  2. En el comando (`S.W('learn')` / `S.W('boost')`), aplica el pulso del comando sobre ese mismo objeto.
  3. En el remate (`S.W('prohibido')` / `S.W('arreglo')`), **muta su geometría/estado in-situ** (`border-radius`, alineación, color de estado rojo `#E3261F` → esmeralda `#00C48C` + sello físico) conservando su posición para que el ojo perciba causa y efecto instantáneo.

## 2. Atenuación de Foco (`Spotlight Dimming` + `Circumscribe`)

Cuando muestras una interfaz real con varios elementos, el espectador no sabe a dónde mirar en `1.5 s`:
- **Regla `0.22` de Motion Canvas:** en el milisegundo `S.W('palabra_clave')`, atenúa el resto del panel a `opacity: 0.22–0.30` e ilumina al `100 %` **únicamente la fila, pregunta o botón que la voz está nombrando**, acompañado de un trazo orgánico (`DOC.ellipse` o borde luminoso limpio) sincronizado con la palabra.

## 3. Variables Abstractas como Medidores Físicos (`ValueTracker`)

Nunca expliques velocidad, autonomía o ahorro con adjetivos vacíos:
- Convierte la promesa en un **indicador físico cuantificable** que corre con `S.odometer` o barra de progreso determinista sobre `S.prog(t, a, b)`:
  - `/teamwork`: `3 / 3 FRENTES ACTIVOS` avanzando en paralelo (`Diseño`, `Código`, `Pruebas`) al mismo tiempo.
  - `/goal`: reloj pasando `23:00 → 03:15 → 06:00` mientras el progreso de tareas sube solo hasta `100 % VERIFICADO`.

## 4. Revelación Progresiva Sincronizada (`waitUntil` → `S.W()`)

- **Cero pantallas pre-llenadas:** jamás abras una escena con 4 elementos ya puestos esperando a que el locutor los lea.
- Cada bloque nace exactamente `-0.08 s` antes de la sílaba tónica de su palabra ancla (`S.W('entrevista') - 0.08`), de modo que **ojo y oído reciben el impacto como un solo estímulo cognitivo**.
- Tras el *Aha moment* visual de la escena, deja **`0.30–0.45 s` de reposo limpio** antes del corte para que el cerebro fije la idea.
