---
name: tiktok-promote-ui-demos
description: >-
  Reglas empíricas de producción para demos de software, UI y productos digitales en video vertical
  (1080x1920 @ 60fps), destiladas de 493 anuncios oficiales de TikTok Promote Creative Center
  (2.135B vistas) y manual_demos_producto_y_ui.md. Cubre Safe Zones exactas, doble export de subtítulos
  (IG/Shorts vs TikTok), regla del Dolor antes de la Interfaz (#040/#072), magnificación 2.5x de un solo
  control, CTA espacial a mitad (#113) y tarjeta mapa coleccionable (#031/#079).
---

# TikTok Promote UI Demos & Safe-Zone Engineering (2.135B Views Benchmark)

Manual operativo para mostrar interfaces reales, comandos y flujos de producto sin perder retención en teléfonos reales, integrando [manual_demos_producto_y_ui.md](../../../manual_demos_producto_y_ui.md) y [catalogo_tiktok_promote_oficial.md](../../../catalogo_tiktok_promote_oficial.md).

---

## 1. Safe Zone Estricta de Interfaz (`#033` · 2.2M vistas)

Las botoneras derechas y descripciones inferiores de TikTok, Reels y Shorts tapan cualquier elemento fuera de la caja segura:
- **Caja Segura Obligatoria para tarjetas, paneles UI y titulares:**
  - `x`: **`72 px` a `910 px`** (deja libre la columna derecha `910–1080 px` donde viven Like, Comentarios, Guardados y Compartir).
  - `y`: **`200 px` a `1320 px`** (deja libre el cabezal superior de búsqueda y el tercio inferior de descripción/audio).
- **Doble Export de Subtítulos cuando se publica en TikTok e IG/Shorts:**
  - **Master IG Reels / YouTube Shorts:** `#cap { top: 1745px; }` (estándar DEM limpio sobre William).
  - **Variante TikTok (`?tiktok=1`):** `#cap { top: 1380px; }` para no chocar con el usuario, copy y barra de música de TikTok.

## 2. Regla «Primero el Dolor Humano, Después el Botón» (`#040` 5.4M · `#072` 36.5M vistas)

- **Prohibido** abrir un demo mostrando menús fríos o capturas completas de escritorio.
- Los segundos `0–10` establecen:
  1. **Gancho directo (`0–5 s`):** contraste inmediato con William grande (`PC` → `PD`).
  2. **El Dolor (`5–10.5 s`):** mostrar visualmente el desastre cotidiano (errores, retrabajo, pérdida de tiempo) antes de enseñar el primer comando o botón.

## 3. Magnificación Quirúrgica `2.5×` (1 Control por Toma)

- Una captura completa de laptop a `1080 px` de ancho vuelve ilegible cualquier texto de `13 px`.
- **Regla de recorte y escala:** muestra únicamente el **control activo + 1 línea de contexto**, escalado a **`2.2×–3.0×`** (`font-size ≥ 34 px` real en el lienzo de `1080×1920`).
- Elimina barras laterales, pestañas irrelevantes, pies de ventana y decoraciones que no participen en la frase hablada (`AGENTS.md` C3–C4).

## 4. Re-Hook + CTA Espacial a Mitad (`#113` · 6.5M vistas)

- En videos de `45–60 s`, inserta un quiebre de ritmo al `~50 %` del metraje.
- Cuando se pide *Like* en formato vertical, el ícono de corazón vive **a la derecha (`x ≈ 980 px, y ≈ 1080 px`)**:
  - Voz y flecha gráfica apuntan **«aquí al lado»** (`x → 930 px`), **jamás «aquí abajo»**.
  - Acompaña siempre con un bucle abierto hacia la segunda mitad (*«porque los últimos tres parecen trampa»*).

## 5. Tarjeta Mapa Coleccionable para Guardados (`#031` +45% recuerdo · `#079` 10.7M vistas)

- En la toma final (`L10`), mientras la voz pide un **envío por DM a una persona específica**, muestra arriba una **Tarjeta Resumen / Mapa `N/N`** limpia dentro de `x: 72–910, y: 200–920`.
- Cada fila del mapa tiene máximo **2–4 palabras** (`comando → beneficio`), diseñada para que el espectador tome captura o pulse **Guardar** en menos de `2.5 s`.
