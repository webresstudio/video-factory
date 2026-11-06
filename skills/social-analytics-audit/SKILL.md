---
name: social-analytics-audit
description: >-
  Auditoría automática de métricas reales en TikTok Studio, Meta Business Suite e Instagram
  usando el conector AppleScript nativo de WVF (`wvf analytics` y `wvf tool chromejs`) sin
  pedir `chrome://inspect/#remote-debugging`. Calibra diagnósticos de retención, duración,
  audiencia y conversión para múltiples clientes y 5 modelos de negocio (B2B Alto Ticket,
  SaaS, E-commerce B2C, Noticias/Editorial y Educación). Úsala SIEMPRE que el usuario pida
  revisar vistas, retención, caídas de segundos, estadísticas de Reels/TikToks o rendimiento
  de anuncios/videos de cualquier marca en WBRS.
---

# Social Analytics Audit & Multi-Business-Model Retention Runbook (WBRS / WVF)

Protocolo oficial para conectarse de forma **100 % automática** al Google Chrome activo del usuario en macOS y diagnosticar por qué los videos retienen o pierden audiencia en **TikTok Studio**, **Meta Business Suite** e **Instagram**, adaptando los umbrales al modelo de negocio real de cada cliente en `WBRS/ads/`.

---

## 1. Regla de Conexión Automática (Prohibido pedir `remote-debugging`)

1. **Nunca bloquees al usuario pidiendo `chrome://inspect/#remote-debugging` ni `DevToolsActivePort`.**
2. En macOS, `WVF` se conecta directo a las pestañas autenticadas del Google Chrome abierto mediante AppleScript (`osascript`), exactamente igual que `flowjs.py` y `wajs.py`:
   - **Auditoría completa de los 3 paneles (TikTok Studio + Meta Business Suite + Instagram):**
     ```bash
     wvf analytics --limit 6
     ```
   - **Auditoría filtrada o para un cliente/modelo específico:**
     ```bash
     wvf analytics --model b2b_high_ticket --ig avalocorp --tiktok avalocorp --meta-asset 123456789
     wvf analytics --platform meta --model ecommerce_b2c
     ```
   - **Inspección puntual de cualquier pestaña abierta en Chrome:**
     ```bash
     wvf tool chromejs --tabs
     wvf tool chromejs --nav "https://business.facebook.com/latest/insights/content"
     wvf tool chromejs --match "tiktok.com/tiktokstudio" -e "document.body.innerText.slice(0, 2000)"
     ```

---

## 2. Configuración Multi-Cliente en `project_config.json`

Cada carpeta de cliente dentro de `WBRS/ads/<Proyecto>/project_config.json` puede declarar su bloque `"social"` para no mezclar cuentas ni portafolios de Meta Business Suite:

```json
{
  "client_name": "AVALO CORP",
  "social": {
    "business_model": "b2b_high_ticket",
    "instagram_handle": "avalocorp",
    "tiktok_handle": "avalocorp",
    "meta_asset_id": "1027787490574070",
    "meta_business_id": "1318499984852481"
  }
}
```

> **Verificación de seguridad multi-cuenta:** Si `tiktok_handle` está definido en `project_config.json` y la sesión abierta de TikTok Studio pertenece a otra marca, `wvf analytics` emite una alerta explícita (`account_mismatch_warning`) para nunca atribuir métricas de un cliente a otro.

---

## 3. Siempre Consultar AMBOS Studios (Nunca solo la vista pública de Instagram)

- **Instagram Web (`instagram.com/<handle>/reel/...` → `Ver estadísticas`)** muestra vistas, `%` no seguidores, guardados, compartidos y si Meta colocó la etiqueta **`Contenido de IA`**, pero **NO muestra el tiempo promedio de reproducción**.
- **Meta Business Suite (`business.facebook.com/latest/insights/content`)** es el Studio donde viven **Watch time**, **Video average play time**, **3-second views**, clics en **Stories** y la separación entre Reels **Nativos de IG** vs. **Crossposted (IG+FB)**.
- **TikTok Studio (`tiktok.com/tiktokstudio/analytics/<videoId>` y general)** entrega **Tiempo promedio de vista**, **`%` que vio el video completo**, el **minuto exacto de mayor abandono (`0:01` / `0:02`)**, tráfico por **Búsqueda**, demografía (**Edad / País**), **horario pico de espectadores** y **qué otros videos ve esa misma audiencia**.

---

## 4. Matriz de Diagnóstico según Modelo de Negocio (`--model`)

Nunca evalúes todos los negocios como si fueran canales de entretenimiento masivo:

| `--model` | Giro / Ejemplos | Duración Ideal | Qué exigir en `0.0–5.0 s` | KPIs que deciden éxito real |
| :--- | :--- | :---: | :--- | :--- |
| `b2b_high_ticket` | `AVALO CORP`, `INGENIEROS_PANAMA`, software a medida, inmobiliaria, salud | `30–45 s` | Riesgo económico/operativo real desde `0.5 s`, cero cortina de marca al inicio | Edad `25–54` (`>70 %`), `>=14 s` prom., Envíos DM a socios, Guardados y Clics a WhatsApp/link |
| `saas_product` | `SCALAos`, apps, herramientas digitales | `25–40 s` | Dolor humano (`0–4 s`) → interfaz real a `2.5×` antes del `5.0 s` | Promedio `>=15 s`, `>=15 %` completos, Guardados de tarjeta resumen, Búsqueda `>5 %` |
| `ecommerce_b2c` | Tiendas online, retail, comida, gadgets | `12–25 s` | Producto físico en uso en `0.3 s` + beneficio/oferta clara | Completos `>=28 %`, Clics directos a catálogo/tienda y comentarios de compra |
| `editorial_news` | `Las Noticias Tech`, marca personal | `25–38 s` *(1 noticia/video)* | Evidencia noticiosa en `0.5 s` (cortina solo al final) | No seguidores `>=70 %`, Completos `>=18 %`, Compartidos y Seguidores nuevos |
| `education_creator` | Tutoriales, listas de comandos, cursos | `35–55 s` | Asomar tarjeta mapa `N/N` en `3 s` + punto `#1` antes del `5.0 s` | `Saves / Reach >= 3 %`, Promedio `>=16 s`, Búsqueda SEO `>5 %` |

---

## 5. Cruce Quirúrgico contra Guion y Hojas de Contacto

Después de correr `wvf analytics`:
1. Lee `check/social_analytics.json` y ubica los segundos de abandono (`0:01`, `0:02` o el promedio en segundos).
2. Abre `GUION.md` / `script.json` y la hoja de contactos en `check/` (`contacto_*.jpg`) del proyecto correspondiente.
3. Señala exactamente **qué fotograma** provocó la fuga (ej. cortinilla verde en `0–2.8 s`, ausencia de titular en `1.2 s`, exceso de logos abstractos antes del segundo `14`, lista destripada completa en el copy, o pauta abierta que metió `>40 %` de público `18–24` en un producto B2B).
