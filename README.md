# Viaje Japón 2027 🗾

Repositorio para planificar el viaje a Japón desde Buenos Aires.

Dos componentes:
1. **Skill de Claude Code** — asistente especializado en Japón (itinerarios, destinos, tendencias, práctica)
2. **Bot CLI de vuelos** — monitorea precios BUE → TYO y manda alertas a Telegram

---

## Setup

### 1. Instalar dependencias

```bash
uv sync
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus tokens
```

O usar el wizard:

```bash
uv run japon setup
```

Variables requeridas para alertas Telegram:
- `TELEGRAM_BOT_TOKEN` — obtener en [@BotFather](https://t.me/BotFather)
- `TELEGRAM_CHAT_ID` — tu chat ID ([cómo obtenerlo](https://t.me/userinfobot))

Variables opcionales (fallback Amadeus si Google Flights falla):
- `AMADEUS_API_KEY` / `AMADEUS_API_SECRET` — [registro gratuito](https://developers.amadeus.com)

---

## Bot de Vuelos

### Consulta inmediata

```bash
uv run japon flights check
```

```bash
# Mes específico
uv run japon flights check --date 2027-02

# Con umbral personalizado
uv run japon flights check --threshold 1000
```

### Monitoreo periódico

```bash
# Inicia monitor (chequea cada 60 min por defecto)
uv run japon flights monitor

# Configuración personalizada
uv run japon flights monitor --interval 30 --threshold 900

# Para probar rápido (cada 5 min, umbral alto para que siempre alerte)
uv run japon flights monitor --interval 5 --threshold 9999
```

El monitor:
- Chequea precios al iniciar y luego cada N minutos
- Guarda todos los resultados en `data/price_history.json`
- Muestra un panel Rich en terminal cuando hay ofertas bajo el umbral
- Envía mensaje a Telegram si está configurado

`Ctrl+C` para detener.

### Historial de precios

```bash
uv run japon flights history

# Ver más registros
uv run japon flights history --limit 50
```

### Cambiar umbral de alerta

```bash
uv run japon flights alert set 1100
```

---

## Skill de Claude Code — `/japon`

El skill vive en `skills/japon-trip/SKILL.md` y permite usar Claude como asistente
especializado en Japón desde este directorio.

Para activarlo en Claude Code:

```bash
# Dentro de este directorio
claude
/japon armame un itinerario de 3 semanas para japón
```

### Capacidades del skill

| Comando | Qué hace |
|---------|----------|
| `itinerario` | Día a día personalizado según duración e intereses |
| `lugares` | Recomendaciones por categoría (cultura, natura, anime, gastro) |
| `tendencias` | Busca en Reddit/blogs qué está de moda o qué evitar |
| `práctica` | JR Pass, IC cards, visa, apps, dinero |
| `presupuesto` | Rangos orientativos por estilo de viaje |

### Ejemplos

```
/japon armame un itinerario de 2 semanas, me interesan cultura y gastronomía
/japon qué está pasando con el overtourism en Kioto?
/japon vale la pena el JR Pass para 10 días?
/japon cuánto presupuesto necesito para viajar cómodo?
```

---

## Deploy en Railway (bot en la nube)

Para que el bot busque vuelos automáticamente cada 6 horas sin dejar tu máquina prendida.

### 1. Crear proyecto en Railway

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Desde el repo
railway init
railway up
```

O directamente desde [railway.app](https://railway.app) → "New Project" → "Deploy from GitHub repo".

### 2. Configurar variables de entorno

En Railway Dashboard → tu servicio → **Variables**, agregar:

| Variable | Valor | Requerido |
|----------|-------|-----------|
| `TELEGRAM_BOT_TOKEN` | token de BotFather | ✅ |
| `TELEGRAM_CHAT_ID` | tu chat ID | ✅ |
| `FLIGHT_PRICE_THRESHOLD_USD` | ej: `1200` | opcional (default 1200) |
| `TARGET_MONTHS` | `2027-02,2027-03` | opcional |
| `ORIGIN_IATA` | `EZE` | opcional |
| `DESTINATION_IATA` | `NRT,HND` | opcional |
| `AMADEUS_API_KEY` | key de Amadeus | opcional |
| `AMADEUS_API_SECRET` | secret de Amadeus | opcional |

### 3. Configurar volumen para persistir el historial

Railway Dashboard → tu servicio → **Volumes** → Add Volume:
- Mount path: `/app/data`

Sin volumen, el historial se pierde cada vez que el cron corre (el chequeo igual funciona y manda Telegram, pero no acumula historial entre ejecuciones).

### 4. Verificar el cron

El `railway.toml` ya configura el cron a **cada 6 horas**. Para cambiar la frecuencia, editar `railway.toml`:

```toml
cronSchedule = "0 */6 * * *"   # cada 6 horas
cronSchedule = "0 8,20 * * *"  # dos veces al día (8am y 8pm UTC)
cronSchedule = "0 * * * *"     # cada hora (más agresivo)
```

Railway Dashboard → Deployments muestra cada ejecución del cron con sus logs.

---

## Estructura del Repositorio

```
viaje_japon/
├── pyproject.toml              # Dependencias + entry point `japon`
├── Dockerfile                  # Imagen para Railway
├── railway.toml                # Config Railway (cron cada 6h)
├── .env.example                # Template de variables de entorno
├── .env                        # Secrets (gitignored)
│
├── src/
│   └── japon/
│       ├── cli.py              # Typer CLI: `japon` command
│       ├── config.py           # Pydantic Settings (.env)
│       ├── scraper.py          # fast-flights + fallback Amadeus
│       ├── monitor.py          # APScheduler loop
│       ├── alerts.py           # Evaluación umbral + Rich panel
│       ├── telegram_notif.py   # Notificaciones Telegram
│       └── history.py          # data/price_history.json
│
├── data/
│   └── price_history.json      # Generado en runtime (gitignored)
│
├── skills/
│   └── japon-trip/
│       ├── SKILL.md            # Skill Claude Code
│       └── references/
│           ├── destinos.md     # Datos curados de destinos
│           └── practico.md     # JR Pass, visa, apps, etc.
│
└── docs/
    ├── recursos.md             # Links útiles y referencias
    └── notas.md                # Notas personales del viaje
```

---

## Ruta de Vuelo

- **Origen**: EZE (Ezeiza, Buenos Aires)
- **Destinos**: NRT (Narita) o HND (Haneda), Tokio
- **Sin directo** — mínimo 1 escala, 29-57h de viaje
- **Mejor mes de salida**: Febrero (precios bajos, menos turistas)
- **Rango típico**: USD 700 - 1.500 (economy, ida y vuelta)
- **Aerolíneas frecuentes**: LATAM, Korean Air, Air China, JAL, ANA

---

## Stack

| Componente | Herramienta |
|---|---|
| Package manager | uv |
| CLI | Typer + Rich |
| Vuelos scraping | fast-flights (Google Flights) |
| Fallback vuelos | Amadeus API free tier |
| Scheduler | APScheduler |
| Notificaciones | python-telegram-bot + Rich |
| Config | pydantic-settings + .env |
| Datos | JSON en `data/` |
