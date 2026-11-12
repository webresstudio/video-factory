---
name: viral-listicle-story
description: >-
  Metodología y validador automático v2 (ES/EN) para guiones virales de listas y casos
  causales en video vertical («5 cosas que no sabías sobre…», «6 comandos de…», «3 pasos
  para…», «N herramientas / errores»). Transforma listas planas en una historia continua
  de causa-efecto con apertura directa sin condicionales (<1.2s), bloques estadísticos
  comprimidos sin puentes vacíos (<=6s), cadencia abordable en 2 niveles (Pulso Ágil 6s:
  10-18 pal. / Pulso Extendido 8s: 19-24 pal. con sub-corte visual), re-hook por
  contradicción real a mitad y cierre disociado (clic visual en Guardar guía + 1 pregunta
  hablada, cero fuga a agencias terceras).
---

# Viral Listicle-as-Story Runbook v2 (ES / EN)

Sistema de escritura y validación para convertir cualquier video tipo **«N cosas que no sabías sobre…» / «N comandos / pasos / herramientas / errores»** en una pieza de alta retención, guardados y comentarios calificados en Reels, TikTok, Facebook y YouTube Shorts, cumpliendo al 100 % las reglas de [AGENTS.md](../../../AGENTS.md), [CDF](../../../manual_maestro_formato_creativo_completo.md), [DEM](../../../manual_documental_en_movimiento.md) y el [Manual de Ingeniería de Retención y Punto Dulce](../../../manual_ingenieria_retencion_punto_dulce.md).

---

## Las 8 Leyes Obligatorias del Formato «Lista como Historia» (Calibración v2)

### 1. Prohibido el catálogo plano («Uno… Dos… Tres…»)
* **Nunca** redactes el texto hablado como un glosario numerado (*«Uno: X. Dos: Y. Tres: Z.»*). La numeración va **únicamente en el texto en pantalla** (`01 / 02 / 03` o `1 · ...`) para orientar el ojo.
* En la voz, los `N` puntos se encadenan como **una sola historia continua de causa y efecto (`Pero → Entonces`)**.

### 2. Apertura Directa sin Condicionales (`< 1.2 s`) + Gancho Triple sin Duplicación (`0–3 s`)
* **Prohibidos los condicionales suaves en las primeras 4 palabras de `L01`** (*«Puede que ChatGPT…»*, *«Tal vez tu web…»*, *«¿Sabías que…?»*): retrasan el sustantivo de amenaza/recompensa más allá de `2.0 s` y pierden al `56 %` del tráfico frío. Abre con hecho directo (*«ChatGPT ya recomienda a tu competencia…»* o imperativo seco *«Suelta Claude Code un minuto.»*).
* **No-duplicación (`< 40 %` de solape léxico):** El texto en pantalla (`≤ 6 palabras`) abre el ángulo amplio o muestra `Z-Depth` monumental (`404 px` detrás de William) sin repetir literalmente la voz.

### 3. Compresión Estadística sin Puentes Retóricos (`≤ 6.0 s` Reloj, `0.0 s` de Relleno)
* Dos estudios o estadísticas consecutivas **aplanan la curva de retención** siempre que vayan pegadas (*Magnitud → Causa*).
* **Prohibidas las frases puente vacías** entre datos o antes del Paso 1 (*«Te dejo tres pasos para entrar en esa lista»*, *«¿Por qué tan pocos? Una pista:»*, *«Esta semana salió un estudio…»*). Ese puente sin datos restó `-7 pts` (`41 %` de fuga en `9.5–15.2 s`). Pon el nombre del estudio y muestra (`SOCi · 350,000 ubicaciones`) en el subtítulo visual de `22 px` de la tarjeta blanca.

### 4. Cadena de Evidencia Primaria Especializada (`facts.md`)
* Nunca estires un único artículo para inventar pasos que no midió (`AGENTS.md` A1). Respalda cada pulso con su fuente primaria específica en `facts.md` (Magnitud → Mecanismo → Paso 1/2 → Caso real de contradicción → Factor decisivo).

### 5. Cadencia Abordable de Palabras en 2 Niveles (`1.000x`, Cero `atempo`)
Para que el español suene `100 %` natural y ejecutivo sin asfixiar las frases ni exceder el pulso visual de `4–6 s`:
* **Nivel 1 · Pulso Ágil (`10 a 18 palabras fonéticas`, ideal `12–17`):** Dura `3.5–5.8 s` reales y entra limpio en **un clip `Omni 1.1 Flash · 6 s · 720p` (`10 créditos`)** con un único estado de Cámara + Posición.
* **Nivel 2 · Pulso Extendido (`19 a 24 palabras fonéticas`):** Totalmente permitido cuando una idea o caso real lo pide; se genera en **clip `8 s · 720p` (`12 créditos`)** y **`engine.js` aplica un sub-corte visual a mitad de toma (`t_local ≈ 4.0–4.8 s`)** para que ningún encuadre supere `6.0 s` estáticos.
* **Desborde (`≥ 25 palabras fonéticas`):** Dividir en dos pulsos causales (o usar `--allow-override` solo en casos justificados).

### 6. Ritmo Humano (`Burstiness CV ≥ 0.55`) y Español Neutro de Guatemala
* Alterna **micro-reacciones de 2 a 4 palabras** (*«Aquí no.»*, *«Puro desastre.»*, *«¡Pero atento!»*) con oraciones de `10 a 15` palabras.
* Prohibidos regionalismos marcados (*«ocupas»*, *«ojo con»*, *«chaval»*, *«che»*, *«parce»*) y muletillas de IA (`—`, *«en el mundo actual»*, *«revolucionario»*).

### 7. Re-Hook por Contradicción Real a Mitad (`40 %–50 %` del Metraje)
* Tras enseñar el Paso 1, inyecta un **caso real verificado que cumplió lo básico e igual falló** por omitir el siguiente factor (*«¡Pero atento! Un restaurante con mil cinco reseñas y 4.8 estrellas quedó fuera en la mitad de búsquedas»*) acompañado de cambio a Contrapicado `Cam B` o Pantalla Completa (`0 %` de pérdida en telemetría real).
* Si se señala el botón *Like*, indicar **a la derecha** (*«aquí al lado»*, jamás *«aquí abajo»*).

### 8. Cierre Comercial Disociado: `Guardar` Visual + `1 Acción` Hablada + Cero Fuga a Terceros
* **Prohibición comercial absoluta:** Jamás digas *«envíaselo a quien maneja tu página web / tu marketing»* en videos B2B de marca propia (empuja al cliente hacia otra agencia en vez de contratarte a ti).
* **Prohibida la disyuntiva hablada *«Guarda esta guía O comenta…»*:** El cerebro elige el esfuerzo mínimo (`Guardar`) y deja `0` comentarios.
  - **Canal Visual Silencioso → Guardados:** Muestra la Hoja Editorial Suiza (`#s9-sheet`) y haz que el Cursor Causal (`84 px`) haga clic en `Guardar guía` con sonido `click`.
  - **Canal Vocal → Comentarios / DMs:** Pide en voz **una sola acción concreta** (ej. una pregunta abierta de rubro/diagnóstico o un envío por DM a un socio/amigo específico) cerrando con *loop* léxico hacia `L01`.

---

## Uso del Validador Automático (`scripts/audit_listicle.py`)

```bash
# Mediante el CLI global de WVF:
wvf audit-script borrador_guion.json --lang es

# O directamente (soporta JSON o tabla Markdown GUION.md, y --allow-override):
python3 /Users/williamromero/MediaProjects/WBRS/video-factory/skills/viral-listicle-story/scripts/audit_listicle.py \
  borrador_guion.json --lang es
```
