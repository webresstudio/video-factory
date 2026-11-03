---
name: shotcraft-ui-recipes
description: >-
  Recetario de planos de interfaz auténtica (Product-Token Skinning + Shot Cards) adaptado de
  Vincentwei1021/video-shotcraft (★ 16.2K, Apache-2.0) a WBRS/DEM. Prohíbe pantallas genéricas de IA/neón,
  exige tokens reales del producto y provee 4 recetas probadas para explicar comandos y herramientas en vivo.
---

# Video Shotcraft Authentic UI Recipes (`Vincentwei1021/video-shotcraft` · ★ 16.2K · Apache-2.0)

Adaptación de la filosofía central y cartas de plano de [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) (Apache-2.0) cumpliendo estrictamente [AGENTS.md](../../../AGENTS.md) (cero tarjetas genéricas color hueso por vicio, cero exceso de chips, cero diagramas de flechas innecesarios).

---

## 1. El Lenguaje Visual Nace del Producto Real (`Authentic Token Skinning`)

- **Prohibido inventar «pieles genéricas de anuncio con neón/HUD»:** antes de armar una escena sobre una herramienta (Antigravity, Chrome, SCALAos), usa su **icono oficial, tipografía real y anatomía exacta** (ej. barra `/` de Antigravity con prompt limpio, pestaña real de Chrome con botón de grabación `REC`, logo oficial `scalaos` en Gabarito 800).
- **Una sola técnica protagonista por escena:** si una escena usa *escritura de comando + clic*, la siguiente usa *transformación de botón + sello*, la siguiente *navegador autónomo*, la siguiente *carriles paralelos*. **Jamás repitas la misma entrada mecánica 6 veces seguidas.**

## 2. Las 4 Recetas Probadas para Videos de Comandos y Productos

### Receta A · `slash-interview-card` (Ideal para `/grill-me`)
- **Intención:** Mostrar que la herramienta pregunta antes de ejecutar.
- **Coreografía:** Barra `/` teclea `/grill-me` (`0.28 s`) ▸ despliega **1 sola tarjeta limpia de pregunta** con 2 opciones legibles y la recomendada iluminada ▸ cursor gigante hace clic en `(Recomendada)` en `S.W('sugeridas')`.
- **Fallo común a evitar:** Meter 5 preguntas diminutas de formulario ilegibles en móvil.

### Receta B · `defect-to-rule-stamp` (Ideal para `/learn` / correcciones)
- **Intención:** Contrastar error visual vs. regla permanente.
- **Coreografía:** Muestra el elemento feo/deforme ▸ en `S.W('learn')` se corrige su forma con resorte limpio y cae un sello físico contundente (`PROHIBIDO REPETIRLO` / regla guardada en `.agents/rules`) antes de cortar a la reacción facial de William.

### Receta C · `parallel-lanes-sprint` (Ideal para `/teamwork` / procesos simultáneos)
- **Intención:** Demostrar paralelismo real sin diagramas de flujo aburridos (`AGENTS.md` C4).
- **Coreografía:** 3 pistas horizontales limpias (`Diseño`, `Código`, `Pruebas`) que arrancan **en el mismo milisegundo** (`S.W('equipo')`) y llenan sus barras con check verde al unísono en `S.W('mismo')`.

### Receta D · `collectible-cheat-sheet` (Ideal para cierre `L10` de Guardados)
- **Intención:** Convertir la última toma en una lámina coleccionable que obliga a tomar captura o pulsar *Guardar*.
- **Coreografía:** Las `N` filas limpias (`icono + /comando + 2 palabras de efecto`) aterrizan escalonadas en `0.35 s` totales dentro de `x: 72–910, y: 200–900` y quedan completamente quietas y nítidas durante `2.5 s` mientras William lanza el CTA en la mitad inferior (`PD`).

## 3. Presupuesto Máximo de Golpes de Cámara (`≤ 3 Full Slams`)

- Los golpes fuertes de escala/sacudida a pantalla completa (`S.shake` + `S.flash`) se reservan para **máximo 3 momentos cumbre** en todo el video (ej. el dolor en `L02`, el sello en `L04`, el clímax). El resto de acentos ocurren solo en la capa del elemento para no fatigar la vista.
