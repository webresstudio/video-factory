---
name: gsap-word-sequencer
description: >-
  Secuenciación semántica por etiquetas de voz y rendimiento determinista a 60fps sin reflujo de DOM,
  destilada de greensock/gsap-skills (★ 17.7K, MIT: gsap-timeline + gsap-performance). Úsala al programar
  escenas HTML/Canvas en engine.js o serie.js para encadenar entradas, golpes y salidas limpiamente sobre S.W().
---

# GSAP Semantic Word-Sequencing & 60fps Performance (`greensock/gsap-skills` · ★ 17.7K · MIT)

Reglas técnicas de `gsap-timeline` y `gsap-performance` de [greensock/gsap-skills](https://github.com/greensock/gsap-skills) traducidas a la arquitectura determinista `window.renderAt(t)` de WVF y DEM (`serie.js`).

---

## 1. Etiquetas Semánticas de Voz en vez de Segundos Mágicos

Prohibido llenar una escena de números fijos (`1.4`, `2.8`, `4.1`) que se rompen si cambia una pausa de voz:
- Declara al inicio de `renderAt(t)` un **bloque único de etiquetas semánticas** ancladas a Whisper (`S.W`) con respaldos seguros:
  ```javascript
  const T = {
    intro:   0.0,
    trigger: S.W('pones')    || 1.1,
    cmd:     S.W('browser')  || 1.6,
    action:  S.W('abre')     || 2.3,
    proof:   S.W('aprieta')  || 3.1,
    payoff:  S.W('graba')    || 4.0,
  };
  ```
- Define todas las micro-coreografías con **desplazamientos relativos a esas etiquetas** (patrón GSAP Position Parameter `<`, `+=`, `-=`):
  - Cursor inicia viaje: `T.cmd - 0.38`
  - Clic de ignición: `T.cmd + 0.06`
  - Apertura de ventana: `T.action - 0.05` (`<` simultáneo con el eco del clic)
  - Golpe de prueba: `T.proof`

## 2. Separación Estricta: Lectura de Geometría vs. Escritura de Fotograma (`Zero Layout Thrashing`)

En un render determinista a `60 fps` (`3,000+` cuadros por video), medir el DOM dentro del bucle mata el rendimiento y desalinea trazos SVG:
- **Una sola medición tras `document.fonts.ready`:** calcula `getBoundingClientRect()`, `getTotalLength()` (`DOC.path`) y partición de caracteres (`DOC.split`) **una única vez** en la inicialización (`if (!init)`), nunca en cada llamada a `renderAt(t)`.
- **Solo propiedades del compositor en `renderAt(t)`:** anima exclusivamente `transform` (`translate3d`, `scale`, `rotate`), `opacity`, `clip-path` y dibujo en `<canvas>`. Prohibido animar `top`, `left`, `width`, `height`, `padding` o `font-size` cuadro a cuadro.

## 3. Herencia de Curvas por Familia (`Timeline Defaults`)

- No mezcles 6 curvas distintas en la misma escena. Usa una **familia coherente por rol físico**:
  - **Entradas de tarjetas / paneles:** resorte amortiguado `S.spring(dt, 185, 16)`.
  - **Deslizamientos de cámara / cursor / barras:** desaceleración limpia `S.out3` o `S.out5`.
  - **Salidas y cortes en curva:** aceleración `S.in3` (`~75 %` de la duración de entrada).
  - **Prohibido:** rebotes gomosos tipo caricatura (`bounce.out` / `elastic.out` exagerados).
