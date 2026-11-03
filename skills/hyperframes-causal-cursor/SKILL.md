---
name: hyperframes-causal-cursor
description: >-
  Doctrina de movimiento causal, cursor gigante protagonista (oversized-cursor) y cortes en curva de velocidad
  (cut-the-curve) adaptada de heygen-com/hyperframes (★ 77.7K, Apache-2.0) al motor determinista renderAt(t)
  y S.W('palabra') de WBRS/DEM. Úsala SIEMPRE que una escena explique software, comandos o interfaces al
  unísono con la voz: cada cambio visual debe ser CAUSADO por un clic o trazo en el milisegundo exacto de la palabra.
---

# HyperFrames Causal Motion & Oversized Cursor (`heygen-com/hyperframes` · ★ 77.7K)

Adaptación directa de `motion-doctrine`, `oversized-cursor`, `cut-the-curve`, `visualization-registry` y `review.md` de [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) (Apache-2.0) a las leyes visuales de [AGENTS.md](../../../AGENTS.md) y `window.renderAt(t)`.

---

## 1. Prohibido que las cosas «aparezcan solas» (Causal Motion Law)

Ningún panel, comando o resultado puede encenderse por arte de magia ni quedar flotando con oscilación vacía (*idle sine wobble* prohibido):
- **Cadena causal en el mismo cuadro (`same-frame ignition`):**
  `voz pronuncia palabra clave S.W('palabra')` ▸ `cursor aterriza punta y comprime (clic)` ▸ `botón/barra reacciona (scale 0.95)` ▸ `resultado explota o se transforma en ese exacto instante`.
- **Pausa dramática antes del clímax (`0.25–0.45 s`):** tras teclear un comando o pulsar ejecutar, sostén `0.3 s` de tensión limpia antes de desplegar la prueba visual grande.

## 2. El Cursor Gigante Protagonista (`Oversized Cursor`)

Un cursor real de `16 px` es invisible en un teléfono. En demos explicativos, el puntero es un **actor físico visible**:
- **Tamaño obligatorio:** **`86 px` a `124 px`** en lienzo `1080×1920` (`~8–11 %` del ancho), cuerpo blanco con borde negro nítido (`#14161A`, `2.5 px`) o negro con borde blanco según contraste, y sombra corta `drop-shadow(0 8px 14px rgba(0,0,0,.38))`.
- **Ley de entrada física:** **jamás** aparece con `opacity: 0 → 1` en el sitio. Entra siempre desde fuera de cuadro (`y = 1980` o lateral) en **un solo vector desacelerado** (`S.out3`, `0.42–0.68 s`).
- **Punta exacta (`Tip-Targeting`):** el punto caliente es la **punta de la flecha** (`transform-origin: 21% 14%`), no el centro de la caja.
- **Física asimétrica del clic (`1 : 2`):**
  - Compresión rápida: `scale(0.82)` en `0.09 s` (`S.in3`).
  - Rebote elástico: `scale(1.00)` en `0.20 s` (`S.out3`) + onda/reacción simultánea en el botón tocado.
- **Apartarse cuando no actúa:** mientras el espectador lee el resultado (`> 0.8 s`), el cursor se desliza suavemente a un costado (`+110 px, +70 px`) o sale físicamente del cuadro; nunca queda congelado tapando el texto.

## 3. Ley del Vector en los Cortes (`Cut-the-Curve Seam Law`)

Para que 10 escenas se sientan como **una sola película continua** y no diapositivas sueltas:
1. **Mismo eje y signo:** si el elemento de `A` sale empujando hacia la izquierda o acercándose (`scale` creciendo), `B` entra en esa misma dirección, jamás rebotando en espejo sin causa.
2. **Corte a mitad de velocidad:** evita que todo quede muerto `1.0 s` antes del corte; lanza un sub-corte interno (`PC → PD` o `GRAF → PC` en `t_cut = S.W('palabra') - 0.06`) cuando la acción verbal cambia de pregunta a remate.

## 4. Registro Visual («Show, Don't Tell»)

Orden de prioridad para explicar cualquier comando o función:
1. **`ui-recreate`:** recreación fiel con tokens reales del producto (barra de `/comando` real de Antigravity, ventana real de Chrome, panel real de subagentes).
2. **`ui-analog`:** medidor físico honesto del comportamiento (reloj nocturno corriendo solo, 3 carriles paralelos avanzando a la vez, sello rojo `PROHIBIDO REPETIRLO`).
3. **`terminal`:** escritura rápida del comando (`0.025 s` por carácter) + golpe de `Enter` + resultado inmediato.

## 5. Revisión de 3 Vistas antes de Entregar (`HyperFrames Review Gate`)

Además de la hoja de contactos por escena (`AGENTS.md` D2), verifica:
1. **Momentos clave:** cada escena en el instante exacto de `S.W('palabra') + 0.25 s`.
2. **Tira de costuras (`±0.10 s` alrededor de cada sub-corte):** cero pantallas vacías, cero textos a medio borrar tapando la cara de William.
3. **Escala teléfono (`360 px` de ancho):** si un rótulo no se lee al instante a `360 px`, tiene demasiadas palabras o letra pequeña; recórtalo.
