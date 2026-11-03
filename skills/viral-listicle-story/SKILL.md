---
name: viral-listicle-story
description: >-
  Metodología y validador automático (ES/EN) para guiones virales de listas en video vertical
  («5 cosas que no sabías sobre…», «6 comandos de…», «N herramientas…», «N errores…», «Top N…»).
  Transforma listas planas en una sola historia continua de causa-efecto con dolor previo (The Stake),
  gancho triple sin duplicación, alto burstiness humano, re-hook espacial a mitad y doble cierre
  (DM Sends + tarjeta mapa coleccionable para Guardados). Úsala SIEMPRE que el usuario pida un video
  enumerado o de «N cosas / herramientas / comandos / secretos / errores».
---

# Viral Listicle-as-Story Runbook (ES / EN)

Sistema de escritura y validación para convertir cualquier video tipo **«N cosas que no sabías sobre…» / «N comandos / herramientas / errores»** en una pieza de alta retención, guardados y compartidos por DM en Reels, TikTok y YouTube Shorts, cumpliendo al 100 % las reglas de [AGENTS.md](../../../AGENTS.md), [CDF](../../../manual_maestro_formato_creativo_completo.md), [DEM](../../../manual_documental_en_movimiento.md) y el catálogo oficial de TikTok Promote.

> **Fuentes integradas:** `coreyhaines31/marketingskills` (`hook-system.md`), `Jakeschincariol/instagram-agent-skill` (`ig-reel` + `ig-human`, MIT), `vyralcontent/content-skills` (`sends-playbook.md` + `tiktok-script-structure.md`), arquitectura narrativa *Pero / Entonces* (Jenny Hoyos / Kallaway) y hallazgos empíricos de [catalogo_tiktok_promote_oficial.md](../../../catalogo_tiktok_promote_oficial.md) (`#031`, `#033`, `#040`, `#072`, `#079`, `#113`).

---

## Las 7 Leyes Obligatorias del Formato «Lista como Historia»

### 1. Prohibido el catálogo plano («Uno… Dos… Tres…»)
* **Nunca** redactes el texto hablado como un glosario numerado (*«Uno: X. Dos: Y. Tres: Z.»*). La numeración va **únicamente en el texto en pantalla** (`1 · ...`, `2 · ...`) para orientar el ojo.
* En la voz, los `N` puntos deben encadenarse como **una sola historia continua de causa y efecto (`Pero → Entonces`)**: resolver los tropiezos reales de una misma persona o proyecto de principio a fin.
* **Nivel de comprensión general:** cada punto debe entenderlo tanto un experto como alguien ajeno al gremio en una sola escucha. Cero siglas o jerga técnica sin traducir a una acción física cotidiana.

### 2. Gancho Triple sin Duplicación (`0–3 s`)
Los tres canales de apertura se complementan; **jamás dicen lo mismo**:
1. **Primera oración hablada (`≤ 8 palabras` / `≤ 2.5 s`):** Imperativo o reto directo al espectador con nombre propio, cifra o contraste desde las primeras 4 palabras. Cero saludos ni preámbulos (*«Hoy te traigo…»*).
2. **Texto en pantalla (`≤ 6 palabras`):** Abre el ángulo amplio para quien mira sin sonido o fuera del nicho (ej. voz reta a usuarios de `Claude Code`, mientras la pantalla promete `CREA APPS SIN SABER CÓDIGO`). Solapamiento léxico con la voz `< 40 %`.
3. **Acción visual (`0–3 s`):** Gesto físico inmediato de William grande (`PC`, `0–1.8 s`) + corte visual antes del segundo `2.0` (`PD` o `GRAF`).

### 3. Bloque `EL DOLOR / THE STAKE` antes del Ítem #1 (`~5–10 s`)
* **Prohibido** saltar del gancho directo al ítem #1 (patrón TikTok Promote `#040` `5.4M` y `#072` `36.5M` vistas).
* La **Toma 2 (`L02`)** debe mostrar y hacer sentir el desastre cotidiano, pérdida de tiempo o frustración de **no** tener esos `N` elementos (incluyendo explícitamente al público no experto cuando aplique).
* Recién en `L03` entra un corte seco de rescate (*«Aquí no.»* / *«Hasta que pruebas esto.»*) seguido del Ítem #1.

### 4. Orden de Impacto (`2.º mejor → Escalada → Mejor al final`)
* **Ítem `#1`:** Pon el **segundo punto más fuerte** para justificar el clic de inmediato.
* **Ítems intermedios (`#2` a `#N-1`):** Escalada causal; cada punto resuelve la fricción que aparece después del anterior (*«¿Hizo un botón horrible?…» → «¿Quién prueba que sirva?…»*).
* **Ítem `#N` (Clímax):** Guarda **el punto más sorprendente, nocturno o contraintuitivo** para el final. Evita el abandono prematuro tras el punto 3.

### 5. Ritmo Humano (`Burstiness ≥ 0.55`) + Regla Flow `1.0x` + Cortes `≤ 3.5 s`
* **Variación radical de longitud de frase (`std / media ≥ 0.55`):** Prohibido escribir `N` tomas con oraciones uniformes de 18–20 palabras. Alterna **micro-remates secos o cómicos de 2 a 4 palabras** (*«Aquí no.»*, *«Ni yo aprendo así.»*, *«¿Tienes prisa?»*) con frases de acción concretas de 10 a 14 palabras.
* **Límite de voz en Google Flow (`AGENTS.md` A5):** Voz estrictamente a `1.0x` (prohibido `atempo`). Cada toma completa (`8 s` máx.) debe tener entre **15 y 20 palabras** (tope máximo: 22).
* **Sub-cortes internos (`A → B ≤ 3.5 s`):** Ningún encuadre permanece estático más de `3.5–4.0 s`. Toda toma alterna dos estados visuales (`PC → PD`, `PV → GRAF`, `GRAF → PC`).
* **Español neutro de Guatemala (`AGENTS.md` B1):** Prohibidos regionalismos marcados (*«ocupas»*, *«ojo con»*, *«chaval»*, *«che»*, *«parce»*) y muletillas de IA (*«en el mundo actual»*, *«sumérgete»*, *«revolucionario»*, guiones largos `—`).

### 6. Re-Hook + CTA Temprano con Precisión Espacial (`~50 %`, `#113` TikTok)
* Justo a la mitad de la lista (ej. tras el punto 3 de 6, o el 2/3 de 5), inserta un cambio de ritmo musical y un **Re-Hook** con humor ligero.
* Si se pide *Like* a mitad del video: señalar **a la derecha** (`x ≈ 900 px`, decir *«aquí al lado»*, **jamás «aquí abajo»**) y atarlo a un bucle abierto (*«porque los últimos tres parecen trampa»*).

### 7. Doble Cierre Viral: `DM Sends` en Voz + `Mapa N/N` en Pantalla + `Loop`
Nunca pidas dos acciones habladas a la vez. Divide el trabajo entre oído y vista:
* **Voz → Dispara compartidos por DM (`3×–5×` peso algorítmico):** Nombra **1 o 2 perfiles hiper-específicos** de amigo o colega (*«Mándaselo a tu amigo con cien ideas y cero código, o al que sigue casado con…»*).
* **Pantalla → Dispara Guardados (`#031` `+45 %` recuerdo y `#079` `10.7M` vistas):** Muestra arriba una **Tarjeta Mapa Coleccionable (`N/N`)** limpia dentro de la Safe Zone (`x: 72–910 px`, `y: 200–1320 px`) para invitar captura/guardado sin saturar de texto (`≤ 6 palabras` por encabezado).
* **Loop verbal exacto:** Termina la última frase con la misma marca o palabra ancla de `L01` para conectar el final con el segundo `0.0`.

---

## Flujo de Trabajo Paso a Paso

1. **Verificar hechos primero (`facts.md`):**
   - Documentar fuentes primarias reales para los `N` puntos antes de redactar una sola línea (`AGENTS.md` A1). Si una función requiere plan de pago o tiene una condición real, anotarla con transparencia en pantalla (`Plan Pro` / `Plan de pago`).
2. **Definir la escalada `Pero / Entonces` y el mapa de `N + 4` tomas:**
   - Para una lista de `N` cosas, la estructura base tiene **`N + 4` tomas** (~`45–55 s`):
     - `L01`: Gancho triple sin duplicación (`0–5 s`).
     - `L02`: `El Dolor / The Stake` cotidiano (`5–10.5 s`).
     - `L03` a `L(2 + mitad)`: Primera mitad de ítems encadenados por fricción real.
     - `L(Re-Hook)`: Quiebre de patrón a mitad + CTA espacial (*«aquí al lado»*) + bucle abierto.
     - Siguientes tomas hasta Ítem `#N`: Segunda mitad escalando hasta el ítem más salvaje al final.
     - Toma final: Mapa coleccionable `N/N` en pantalla + CTA hablado de *DM Send* con perfil concreto + *Loop* verbal hacia `L01`.
3. **Ejecutar el validador automático (`audit_listicle.py`) antes de mostrar el guion:**
   - Corre [scripts/audit_listicle.py](./scripts/audit_listicle.py) sobre el archivo JSON del borrador (español y/o inglés).
   - **Prohibido entregar el guion a William si el validador marca `FAIL` o `REVIEW`.** Corrige longitud de gancho, *burstiness*, palabras por toma o duplicación de texto hasta obtener `PASS`.
4. **Presentar la tabla DEM para aprobación (`AGENTS.md` A10):**
   - Mostrar la tabla completa con columnas: `Toma`, `Cortes (A → B ≤ 3.5 s)`, `Texto en pantalla (≤ 6 pal)`, `Acción visual DEM (Safe Zone)`, `Texto hablado (1.0x)` y `Pal.`.
   - Esperar aprobación explícita de William antes de generar cualquier toma en Google Flow.

---

## Validador Automático (`scripts/audit_listicle.py`)

El script [audit_listicle.py](./scripts/audit_listicle.py) evalúa sin dependencias externas:
- **Hook Score (`≥ 75 STRONG`):** brevedad de la 1.ª oración (`≤ 8 palabras`), especificidad, tensión, *frontload* y apelación directa.
- **No-duplicación `L01`:** solapamiento entre voz y texto en pantalla `< 40 %` y tope de `≤ 6 palabras` por rótulo.
- **Burstiness humano (`CV ≥ 0.55`) y Anti-Slop:** variación de longitud de oraciones (Unicode completo para español e inglés), ausencia de muletillas de IA, ausencia de `—` y ausencia de modismos prohibidos en `AGENTS.md`.
- **Detector Anti-Catálogo:** bloquea enumeraciones planas (*«Uno: … Dos: …»*) en la voz.
- **Ritmo Flow `1.0x` + Cortes + Loop:** verifica `12–22 palabras` por toma, sub-cortes `≤ 4.0 s`, dirección espacial correcta del Like y *loop* léxico entre la primera y la última toma.

### Uso rápido

```bash
python3 /Users/williamromero/MediaProjects/WBRS/.agents/skills/viral-listicle-story/scripts/audit_listicle.py \
  borrador_guion.json --lang es
```

Formato mínimo de `borrador_guion.json`:
```json
{
  "takes": [
    {
      "id": "L01",
      "cuts_sec": [1.8, 3.4],
      "screen_text": "CREA APPS SIN SABER CÓDIGO",
      "spoken": "Suelta Claude Code un minuto. Sé que le haces el feo a Antigravity, pero es mejor de lo que piensas."
    }
  ]
}
```

---

## Ejemplo Canónico Aprobado

Consulta [examples/seis_comandos_antigravity_v3.md](./examples/seis_comandos_antigravity_v3.md) para ver un guion completo aprobado por William (español neutro de Guatemala + espejo en inglés, 10 tomas, `Burstiness = 0.61`, `Hook Score ≥ 80`).

## Dependencias y Skills Complementarias

- [AGENTS.md](../../../AGENTS.md): Reglas maestras de guion, acento neutro de Guatemala, voz `1.0x` y punto de aprobación antes de Flow.
- [manual_documental_en_movimiento.md](../../../manual_documental_en_movimiento.md): Piezas visuales (`PC`, `PD`, `PV`, `GRAF`, `CINE`), escala de William y paleta cromática.
- `viral-video-masterclass-2026` y `webres-video-factory`: Sincronización sub-milisegundo con Whisper, renderizado a `60fps` y diseño sonoro.
- `social-copy-multichannel-2026`: Redacción de descripciones SEO y ganchos de 125 caracteres para IG, TikTok, Shorts y LinkedIn.
