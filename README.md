![](https://cdn.fbsbx.com/v/t65.102178-21/889178353_1095341016831854_1113539293528550145_n.jpg/mr_horizontal_navy.png?_nc_ht=cdn.fbsbx.com&_nc_ohc=lcozYgPNFnUQ7kNvwHCbD9N&sdl=0&ccb=14-4&oh=00_AQQf2wL4rft5A5BzUsts4Cw7WvDkmHvI8AemFCiITE_YUg&oe=6B1128A0&_nc_sid=4ee932)

Plataforma de transparencia administrativa española: **a gobierno y oposición
se les aplica el mismo rasero**, y cada dato lleva la fuente oficial delante.
Contrasta frases de políticos con la cadena competencial real, muestra el
presupuesto de los ayuntamientos de España capítulo a capítulo, y resuelve qué
administraciones hay encima de tu dirección — con el artículo de la ley y el
enlace al boletín en cada respuesta.

No decimos que nadie mienta. Mostramos lo que se dijo y lo que dicen los datos:
el contraste habla solo.

## Qué funciona hoy

**La ley dice** — verificación competencial:
> *"El Ayuntamiento de Vila-real bajará el IRPF"* → **FALSO COMPETENCIAL**
> tu ayuntamiento NO decide esto — lo deciden el Estado y tu comunidad autónoma.
> Fuente: Ley 35/2006 + Ley 22/2009.

**Los datos dicen** — presupuestos reales de ~9.000 entidades locales (2023 y
2024, Ministerio de Hacienda): Vila-real, ejercicio 2024 — 58,3 M€, personal
39,9 %, bienes y servicios 42,0 %, con comparación interanual.

**El registro dice** — tu dirección contra el registro oficial: UE → Estado →
Generalitat/Diputación/Ayuntamiento → mancomunidades, cada nivel con qué puede
hacer, qué no y su fuente legal.

**El artículo dice** — los trámites que funcionan: alegaciones, instancias,
queja al Síndic, reclamación patrimonial, con el artículo que te ampara.

## Arquitectura

```
packages/
  web/       Next.js 14 + Tailwind — interfaz ciudadana
  api/       FastAPI + SQLAlchemy + Alembic — API v1 y esquema completo
  scrapers/  Adaptadores de fuentes: BOE, DOGV, DOUE, DIR3, Hacienda (SGCIEF)
  disarm/    Importador del framework DISARM (Red/Blue)
  video/     Verificación de vídeo: transcripción, diarización, OCR (§12)
  mcp/       Servidor MCP — las mismas herramientas para clientes LLM
docker/      Postgres 16 + PostGIS + pgvector, imágenes de api y web
```

- **Monorepo**: pnpm (web) + uv workspace (python)
- **Base de datos**: PostgreSQL 16 con PostGIS (geocodificación) y pgvector
  (búsqueda semántica, en preparación); Redis y Qdrant para tareas asíncronas
- **Datos reales ingestados**: 65.000+ entidades del registro DIR3, ~18.200
  administraciones con presupuesto (297.000 filas, ejercicios 2023-2024),
  391 técnicas DISARM RED + 140 contramedidas BLUE, boletines BOE/DOGV por API

## Arranque rápido

```bash
# infraestructura
docker compose up -d db redis qdrant

# API
uv sync
cd packages/api && uv run alembic upgrade head
uv run python -m app.seeds.runner all
uv run uvicorn app.main:app --port 8000      # docs en /docs

# web
corepack pnpm install
corepack pnpm --filter @blueprint/web dev    # http://localhost:3000

# ingesta de fuentes
uv run boletines boe --fecha 2024-01-02      # sumario diario (dry-run)
uv run disarm-import                          # framework DISARM
curl -X POST "localhost:8000/api/v1/ingest/boletin/BOE?fecha=2024-01-02"
curl -X POST "localhost:8000/api/v1/ingest/presupuestos?ccaa=17&provincia=12&tipo=A5&ejercicio=2024"
```

Configuración en `.env` (ver `.env.example`). El motor de verificación funciona
100 % determinista; opcionalmente se puede enchufar un LLM compatible con la
API de OpenAI (`LLM_BASE_URL`, `LLM_API_KEY`) para asistir en la extracción del
sujeto de frases difíciles — **el veredicto lo decide siempre una regla contra
la cadena competencial, nunca un modelo**.

## Fuentes — verificadas en vivo

| Fuente | Estado | Notas |
|--------|--------|-------|
| BOE | ✅ operativa | API de datos abiertos (requiere `Accept: application/xml`) + ingesta de normas por identificador |
| DOGV | ✅ operativa | API interna del portal (`dogv-portal/dogv/latest`, con Referer); solo el último número — el cron diario lo acumula |
| DIR3 | ✅ ingesta completa | 25.178 EELL + 17.025 CCAA + 19.919 AGE. El CTT está tras F5 TrafficShield: los ficheros se bajan a mano del navegador |
| Presupuestos EELL | ✅ toda España | Portal público SGCIEF, scraping con token antiforgery rotatorio; runner por lotes reanudable (~9.000 entidades/ejercicio) |
| CartoCiudad | ⚠️ caída | La API REST responde 500 server-side; geocodificación vía Nominatim/OSM estructurada (documentado como fuente no oficial) |
| EUR-Lex (DOUE) | ⚠️ soft-block | Responde 202 a IPs automatizadas; adaptador listo con proxy opcional |
| Liquidaciones EELL | ⏳ pendiente | El portal aún no publica 2024 en consulta pública; mismo patrón de scraper |

## Huecos documentados (no inventados)

La honestidad sobre lo que falta es parte del método:

1. `disarm_techniques.fase` queda NULL — las fuentes actuales de DISARM ya no
   exponen el agrupado Plan/Prepare/Execute/Assess.
2. El panel de auditoría de sesgo (`/api/v1/auditoria/sesgo`) muestra conteos
   por partido/rol; los porcentajes de veredicto se activan cuando el motor
   persista veredictos ligados a declaraciones (Fase 4 v2).
3. El módulo de vídeo está implementado pero no ejecutado en producción
   (requiere modelos whisper/pyannote y HF_TOKEN para diarización).
4. El índice de competencias: **18 competencias estructuradas** (con cadena
   competencial, niveles decisorios y fuente BOE verificada vía ELI) — el
   alcance del veredicto crece con el índice. Fuentes siempre verificadas
   contra boe.es/eli/es/... antes de sembrar.
5. La afiliación exacta municipio→mancomunidad requiere el Censo de Entes
   Locales: /calle muestra las mancomunidades reales de la provincia con la
   afiliación declarada pendiente.
6. Antes de cualquier publicación pública amplia: revisión legal (RGPD,
   honor/rectificación, ToS de las plataformas) — ver §22 del blueprint.

## Hoja de ruta

| Fase | Alcance | Estado |
|------|---------|--------|
| 0-1 | Infraestructura, esquema completo, seeds, adaptadores BOE/DOGV/DOUE/DIR3 | ✅ |
| 2 | Mapa de poder + competencias + `/calle` con geocodificación | ✅ |
| 3 | Presupuestos EELL de toda España + comparación interanual + flujo normativo | ✅ |
| 4 v1 | Veredicto competencial determinista + seam LLM | ✅ |
| 4 v2 | Extracción semántica con LLM + pilar de personas (sueldos, patrimonio, agendas) | 🔜 |
| 5 | Verificador de programas electorales + generación de escritos | 🔜 |
| 6 | Verificación de vídeo (solo análisis) | código listo, sin ejecutar |
| 7 | Radar R0R1R2 + export STIX2 + cron de ingesta | 🔜 |
| 8 | Rectificación 24h + aviso legal + transparencia de financiación | 🔜 |

## Servidor MCP

Las mismas herramientas, expuestas vía Model Context Protocol para clientes
LLM (Claude Desktop, opencode…):

```json
{
  "mcpServers": {
    "mismo-rasero": {
      "command": "uv",
      "args": ["--directory", "/ruta/a/mismo-rasero", "run", "blueprint-mcp"],
      "env": { "DATABASE_URL": "postgresql+psycopg://blueprint:blueprint@localhost:5432/blueprint" }
    }
  }
}
```

Herramientas: `verificar_frase`, `buscar_competencias`, `listar_boletines`,
`buscar_normas`, `como_reclamar`, `disarm`, `auditoria_sesgo`, `estado_sistema`.

## Licencia

MIT — el código es auditable por diseño: no hay que fiarse de la palabra de
la plataforma cuando se puede leer la lógica del motor.
