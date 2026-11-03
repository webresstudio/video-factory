---
name: lottie-attention-choreography
description: >-
  Jerarquía de atención de un solo protagonista, regla de 1/3 de elementos activos, contramovimiento
  con paralaje y medición real de texto sin recortes, destilada de LottieFiles/motion-design-skill
  (★ 2.7K, MIT) y remotion-dev/skills (★ 6.1K). Evita pantallas caóticas o saturadas y dirige el ojo
  con precisión quirúrgica en cada segundo del video.
---

# LottieFiles Attention Choreography & Real-Font Fit (★ 2.7K + ★ 6.1K · MIT)

Principios de dirección de movimiento de [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill) (`director/choreography.md`) y medición tipográfica de [remotion-dev/skills](https://github.com/remotion-dev/skills) (`measuring-text.md`), adaptados a [AGENTS.md](../../../AGENTS.md) C1–C4 (*«La gente no lee; animaciones hermosas y limpias»*).

---

## 1. Un Solo Protagonista Visual por Instante (`Lead with the Hero`)

El ojo humano solo puede fijar un punto focal en `1.5 s`:
- En cualquier fotograma `t`, define explícitamente **quién manda**:
  - Si manda **la cara y gesto de William (`PC`)**: el titular entra rápido arriba (`y: 90–210 px`), se asienta y deja que el gesto lleve el remate.
  - Si manda **la demostración de interfaz (`PD` / `GRAF`)**: el elemento activo recibe el `100 %` del desplazamiento y contraste; los elementos secundarios se mueven a `20–30 %` de amplitud o permanecen asentados.

## 2. Regla del `1/3` y Origen Espacial Coherente

- **Máximo `1/3` en vuelo simultáneo:** si una tarjeta tiene 3 o 6 filas, escalona sus entradas (`stagger: 0.05–0.07 s`) para que la fila 1 ya esté asentándose cuando arranca la fila 3. Todo moviéndose a la vez se percibe como ruido.
- **Consistencia de origen espacial:** en una misma escena, los elementos hermanos entran desde **un mismo eje coherente** (ej. todos suben `+44 px → 0` con `S.spring`). Mezclar entradas desde arriba, izquierda, derecha y zoom simultáneos produce caos amateur.

## 3. Contramovimiento Sutil de Profundidad (`Parallax 1.0× / 0.5× / 0.2×`)

Para que el lienzo se sienta cinematográfico y vivo sin usar efectos chillones:
- **Primer plano (Hero / Cursor / Sello):** velocidad `1.0×`.
- **Plano medio (Panel UI / Evidencia):** desplazamiento suave `0.4–0.5×` + reacción leve de escala (`0.98 → 1.00`) al recibir un clic.
- **Fondo atmosférico:** deriva orgánica ultra-lenta (`0.15–0.20×`) con alto contraste respecto al primer plano (ni negro muerto ni verde lima chillón a pantalla completa; `AGENTS.md` C2).

## 4. Medición con la Fuente Real Cargada (`Zero Clipped Glyphs`)

- **Nunca estimes el ancho de un título a ojo:** espera siempre a `await document.fonts.ready` antes de medir cajas o trazar subrayados/tachones (`DOC.rect`).
- **Tope de lectura móvil:** máximo **`6 palabras`** en cualquier rótulo principal en pantalla. Verifica tildes mayúsculas (`Á, É, Í, Ó`), signos `¿ ?` y descendentes (`g, j, p, q, y`) para que ningún `clip-path` o borde de tarjeta los mutile.
