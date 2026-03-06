# 📝 Notas — Japón 2027

**Estado:** En planificación  
**Última actualización:** 2026-03-06

---

## ✅ Estado del Proyecto

- [x] Crear skill de OpenClaw para planificación
- [x] Estructurar archivos MD en workspace
- [ ] **Sincronizar archivos con GitHub** ← PRÓXIMO PASO
- [ ] Configurar bot de vuelos (`.env` con tokens Telegram) — *Otra instancia*
- [ ] Definir duración exacta del viaje
- [ ] Arrancar a armar itinerario con el skill

---

## 🔄 Pendiente Inmediato (después de reiniciar gateway)

### Sincronizar con GitHub

**Comando para ejecutar:**
```bash
cd /data/workspace/skills/japon && bash scripts/sync_all.sh
```

**O archivo por archivo:**
```bash
cd /data/workspace/skills/japon
python3 scripts/github_sync.py itinerario.md --message "[OpenClaw] Sync inicial"
python3 scripts/github_sync.py destinos.md
python3 scripts/github_sync.py gastronomia.md
python3 scripts/github_sync.py experiencias.md
python3 scripts/github_sync.py logistica.md
python3 scripts/github_sync.py presupuesto.md
python3 scripts/github_sync.py notas.md
```

**Archivos a subir:**
- `itinerario.md`
- `destinos.md`
- `gastronomia.md`
- `experiencias.md`
- `logistica.md`
- `presupuesto.md`
- `notas.md`

**Destino:** `smariconde/viaje_japon/openclaw/`

**Requerido:** `GITHUB_TOKEN` en variables de entorno de Railway

---

## 📚 Archivos del Skill

**Skill:** `/data/workspace/skills/japon/`
- `SKILL.md` — Instrucciones principales
- `scripts/github_sync.py` — Script de sincronización
- `scripts/sync_all.sh` — Script para subir todos los archivos
- `references/destinos_curados.md` — Guía de destinos
- `references/logistica_completa.md` — Logística completa

**Workspace:** `/data/workspace/viaje_japon/`
- 7 archivos MD listos para sincronizar

**Canal Discord:** `#viaje-japon` (ID: `1479273629534654575`)

---

## 📅 Fechas Tentativas

- **Período**: Febrero o Marzo 2027 (a definir mes exacto)
- **Duración mínima**: 20 días
- **Mejor mes**: Febrero (precios bajos ~$680-$1.350, menos turistas)

---

## 🎯 Decisiones Tomadas

### Sobre la planificación
- ✅ Usar OpenClaw skill para investigar y armar itinerario
- ✅ Archivos MD en espejo: workspace + GitHub repo
- ✅ Publicar actualizaciones en Discord `#viaje-japon`
- ✅ Bot de vuelos separado (otra instancia, no se toca desde este skill)

### Sobre el viaje
- [ ] Definir duración exacta
- [ ] Confirmar fechas
- [ ] Elegir estilo de viaje (budget/mid-range/comfort)

---

## 💡 Ideas y Links Guardados

_Agregar links de posts de Reddit, recomendaciones de amigos, etc._

### Reddit
- [r/JapanTravel](https://reddit.com/r/JapanTravel) — Comunidad principal
- [r/japanlife](https://reddit.com/r/japanlife) — Expats y residentes

### Guías
- [Japan Guide](https://www.japan-guide.com) — La más completa
- [Tokyo Cheapo](https://tokyocheapo.com) — Consejos económicos
- [Lonely Planet Japan](https://www.lonelyplanet.com/japan) — Guía general

### Vuelos
- [Google Flights](https://flights.google.com) — Monitorear precios
- [Skyscanner](https://www.skyscanner.com) — Comparador

---

## 🤔 Preguntas para Investigar

- ¿Cuántos días son ideales para no apurarse?
- ¿Conviene JR Pass para nuestro itinerario?
- ¿Qué ciudad es mejor base: Tokio o Kioto?
- ¿Vale la pena Hakone para ver el Fuji?
- ¿Hiroshima requiere 1 o 2 días?
- ¿Mejor alquilar kimono en Kioto o Tokio?
- ¿Qué onsens son mejores para primera vez?
- ¿Reservar todos los alojamientos o solo primeros días?

---

## 📌 Pendientes por Decidir

### Alta prioridad
- [ ] Definir duración exacta (¿20, 21, 30 días?)
- [ ] Confirmar mes (¿febrero o marzo?)
- [ ] Presupuesto total máximo
- [ ] Estilo de viaje (budget/mid-range/comfort)

### Media prioridad
- [ ] Ciudades a incluir
- [ ] Experiencias imperdibles
- [ ] Tipo de alojamiento (hostel/hotel/ryokan)

### Baja prioridad
- [ ] Restaurantes específicos para reservar
- [ ] Compras planificadas
- [ ] Fotos/lugares instagrammables

---

## 🎒 Preferencias Personales

### Intereses
- [ ] Cultura y templos
- [ ] Naturaleza y hiking
- [ ] Gastronomía
- [ ] Anime/manga
- [ ] Onsens
- [ ] Compras/tecnología
- [ ] Vida nocturna
- [ ] Fotografía

### Comida
- **Para probar**: Ramen, sushi, kaiseki, takoyaki, okonomiyaki
- **Restricciones**: ___
- **Preferencias**: ___

### Alojamiento
- **Preferido**: ___
- **No negociable**: ___

### Ritmo
- [ ] Relax (pocas cosas por día)
- [ ] Mix (2-3 actividades por día)
- [ ] Intenso (mañana/tarde/noche full)

---

## 📊 Tracking de Investigación

### Semana 1 (2026-03-06)
- [x] Crear skill OpenClaw
- [x] Estructurar archivos MD
- [ ] Investigar vuelos (precios febrero 2027)
- [ ] Investigar alojamientos en Tokio
- [ ] Definir duración del viaje

### Próximas semanas
- [ ] Armar itinerario borrador
- [ ] Cotizar presupuesto total
- [ ] Decidir fechas exactas
- [ ] Comprar vuelos (cuando haya buen precio)

---

## 🔗 Links de Referencia del Repo

- [Recursos completos](https://github.com/smariconde/viaje_japon/blob/main/docs/recursos.md)
- [Skill de Claude Code](https://github.com/smariconde/viaje_japon/tree/main/skills/japon-trip)
- [Bot de vuelos](https://github.com/smariconde/viaje_japon) — *Otra instancia*

---

**Última sync con GitHub:** Por definir
