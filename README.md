# Mismo Rasero — Sistema Operativo de España (blueprint técnico v2.5)

Plataforma de transparencia administrativa con fuente citada: a gobierno y
oposición se les aplica el mismo rasero. Familia de secciones: **La ley dice**
(verificación competencial), **Los datos dicen** (presupuestos), **El registro
dice** (organigrama), **El artículo dice** (trámites). 8 pilares + radar
DISARM + verificación de vídeo (solo análisis, nunca generación ni
redistribución de clips).

**Capa de usuario**: la web pública es `¿Quién manda?` (packages/web) —
interfaz ciudadana sobre el motor: pregunta en lenguaje llano ("¿puede el
ayuntamiento bajar el IRPF?") y responde con cadena competencial, artículo y
fuente BOE. El verificador funciona hoy con matching determinista de
competencias (endpoint `/api/v1/verificar`); el análisis semántico con LLM
llega en Fase 4 y solo mejorará la extracción, el flujo no cambia.

Este repo implementa las **Fases 0 y 1** del roadmap (§20) más los primeros
incrementos de la 2: infraestructura, esquema completo, seeds y adaptadores de
boletines.

## Estado por fases (§20)

| Fase | Alcance | Estado |
|------|---------|--------|
| -1 | Revisión legal (§21/§22) con especialista | **Pendiente** — antes de publicar al público |
| 0 | Monorepo + docker (postgres+postgis+pgvector, redis, qdrant) + alembic | **Hecha** |
| 1 | DDL completo + seeds boletines (20+43) + DISARM + BoeAdapter + DogvAdapter + DOUE + DIR3 | **Hecha** |
| 2 | Pilar 1 (Mapa de Poder) + Pilar 2 (Competencias) + `/calle` | **Hecha** — geocodificación viva, organigrama real, 5 competencias sembradas |
| 3 | Pilar 3 (Dinero) + Pilar 4 (Normas) + `/fiscalidad` | **Hecha** — `/fiscalidad` con impuestos curados + presupuesto REAL de ~9.000 entidades con comparación interanual 2023→2024 (scraper SGCIEF por lotes, ~297.000 filas, 0 errores); flujo normativo DOUE→BOE con timeline en `/norma/{id}`; pendiente: liquidaciones y nodos DOGV/BOP del flujo |
| 4 | Pilar 5 (Personas) + Pilar 6 (Detector de Mentiras con LLM) + `/verificador` completo | **Motor v1 en producción** — veredicto competencial determinista (FALSO/VERDADERO/SIN SUJETO) con sello en la web y en el MCP; LLM como seam opcional de extracción (LLM_BASE_URL/LLM_API_KEY, compatible OpenAI). Pendiente: extracción semántica real con LLM configurado + Pilar 5 personas |
| 5 | Pilar 7 (Programas) + Pilar 8 (Manual de Acción) | **Iniciada** — manual de acción sembrado y en /reclama |
| 6 | Vídeo — solo verificación (el código ya está en `packages/video`) | Pendiente ejecución (necesita GPU/modelos) |
| 7 | Radar + explorador DISARM completo + export STIX2 + deploy Hetzner | Pendiente |
| 8 | Aviso legal + rectificación + transparencia de financiación | Pendiente |

## Servidor MCP (`packages/mcp`)

Las mismas herramientas que la API web, expuestas vía Model Context Protocol
para clientes LLM (Claude Desktop, opencode, …). SDK `mcp` 2.x
(`MCPServer`, stdio por defecto). 8 herramientas:

| Herramienta | Qué hace |
|-------------|----------|
| `verificar_frase(texto)` | Pilar 6 — cadena competencial + artículo + fuente BOE |
| `buscar_competencias(consulta)` | Índice de competencias por palabra/nombre |
| `listar_boletines(filtro)` | Los 64 boletines con URL y método |
| `buscar_normas(boletin, desde, hasta, limite)` | Normas con hash SHA-256 y PDF |
| `como_reclamar()` | Trámites §08 con artículo que ampara |
| `disarm(tipo, consulta, fase)` | Técnicas RED / contramedidas BLUE |
| `auditoria_sesgo(desde, hasta)` | Panel §11 por partido/rol |
| `estado_sistema()` | Conteos por tabla — para orientarse |

El motor es el mismo módulo que la web (`app.services.verificar`) y el mismo
que usará el paquete de vídeo — un solo criterio, sin ramas por actor (§11).

Config de cliente (Claude Desktop / opencode):

```json
{
  "mcpServers": {
    "quien-manda": {
      "command": "uv",
      "args": ["--directory", "/ruta/a/blueprint", "run", "blueprint-mcp"],
      "env": {
        "DATABASE_URL": "postgresql+psycopg://blueprint:blueprint@localhost:5432/blueprint"
      }
    }
  }
}
```

En `nocilla` la ruta es `/home/cristian/blueprint` (el `DATABASE_URL` por
defecto ya coincide). Modo servicio HTTP local opcional:
`uv run blueprint-mcp --transport streamable-http --port 8620`.

Prueba rápida de que el servidor responde:

```bash
uv run python - <<'EOF'
import asyncio, json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="uv", args=["run", "blueprint-mcp"], cwd=".",
    )
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool("verificar_frase",
                                    {"texto": "El ayuntamiento bajará el IRPF"})
            print(json.loads(res.content[0].text)["matches"][0]["nombre"])

asyncio.run(main())
EOF
```

## Estructura

```
packages/
  api/       FastAPI + SQLAlchemy + Alembic — modelos = DDL §19 exacto, API v1 (§17)
  scrapers/  Adaptadores DB-agnósticos: BOE (API JSON), DOGV (Playwright), DOUE (RSS), DIR3 (CSV)
  disarm/    Importador DISARM → disarm_techniques (RED) + disarm_counters (BLUE)
  video/     Pipeline §12 completo (transcripción, diarización, OCR chyrons, claims, borrado)
  mcp/       Servidor MCP — 8 herramientas sobre el mismo motor que la web
  web/       Next.js 14 + Tailwind — shell con las rutas §18, explorador DISARM vivo
docker/     Dockerfile db (pgvector+postgis), api, web
```

## Arranque (requiere Docker)

```powershell
# 1. Infra
docker compose up -d db redis qdrant

# 2. Esquema
uv sync
uv run --project packages/api alembic upgrade head        # desde la raíz: ver nota abajo

# 3. Seeds + DISARM
uv run python -m app.seeds.runner all
uv run disarm-import          # o --offline-data data/disarm con los ficheros cacheados

# 4. API (puerto 8000, docs en /docs)
uv run uvicorn app.main:app --reload

# 5. Web (puerto 3000)
corepack pnpm install
corepack pnpm --filter @blueprint/web dev
```

Nota alembic: ejecutar desde `packages/api` (`cd packages/api; uv run alembic upgrade head`)
o exportar `DATABASE_URL`. `alembic.ini` usa `app.config` para leer la env var.

### Ingesta de boletines (verificada en vivo)

```powershell
uv run boletines boe --fecha 2024-01-02 --limit 5     # dry-run, sin BD
# con BD arriba, por API:
curl -X POST "http://localhost:8000/api/v1/ingest/boletin/BOE?fecha=2024-01-02&limit=20"
```

## Fuentes — verificadas en vivo (oct. 2026)

| Fuente | Realidad | Acción |
|--------|----------|--------|
| BOE API | `datosabiertos/api/boe/sumario/YYYYMMDD` funciona con `Accept: application/xml`; sin esa cabecera devuelve 400. 48 docs el 02/01/2024 en el smoke test. | Ninguna — operativa |
| DISARM | El repo es `DISARMFoundation/DISARMframeworks` (no `/DISARM` como dice §15) y ya no hay `red/blue_framework.json`: red = `DISARM_STIX/DISARM.json` (391 técnicas T), blue = `DISARM_database.sqlite` (140 counters C). | Importador adaptado a las rutas reales |
| DOGV | Sin RSS operativo; portada y índice diario son SPA Liferay (JS). Patrón de PDFs confirmado vía robots.txt (`/datos/YYYY/MM/DD/pdf/…`). | Adaptador con Playwright (`uv sync --extra scrapers-playwright` + `playwright install chromium`) |
| EUR-Lex (DOUE) | Devuelve 202 con cuerpo vacío a IPs automatizadas (soft-block de ubicación, no de cabeceras). | `EURLEX_PROXY` en `.env`, o carga manual; el adaptador apunta al RSS oficial |
| CartoCiudad | La API REST clásica (`/geocoder/api/geocoder/find`) responde 500 server-side (Tomcat exception) y el callejero REST del Catastro 404 — ambas rotas/movidas (oct. 2026). | Geocodificación con **Nominatim/OSM estructurada** (street+city, sin fuzzy) + provincia resuelta del display_name contra lista estática de 50 provincias. Documentado como fuente no-oficial en /metodologia |
| DIR3 | **Resuelto y fresco (oct. 2026).** El catálogo vive en el CTT (`administracionelectronica.gob.es/ctt/verPestanaDescargas.htm?idIniciativa=dir3`) tras F5 TrafficShield (challenge JS — sin descarga automatizable; los ficheros se bajan a mano del navegador). Datos actuales: 65.350 unidades (26.606 EELL + 18.825 CCAA + 19.919 AGE) con `codigo_dir3`, jerarquía y provincia (migración 0002). Quirk del generador CTT actual: los XLSX traen la hoja de datos HUÉRFANA (no declarada en workbook.xml — openpyxl solo ve hojas vacías) y la cabecera `C_DNM_UD_ORGANICA` repetida en 3 columnas; el parser OOXML directo (`scrapers.dir3._parse_xlsx_xml`) resuelve ambos. | Refrescar cuando toque: bajar los 3 listados del navegador a `data/dir3/` y `POST /api/v1/ingest/dir3-xlsx?path=...` (idempotente por código DIR3). Códigos de 2023 ya no vigentes quedan como filas residuales (no estorban: el organigrama casa por nombre+tipo). La afiliación exacta municipio→mancomunidad sigue pendiente del Censo EELL |

## Huecos documentados (no inventados)

1. **`disarm_techniques.fase`**: las fuentes actuales de DISARM ya no exponen el
   agrupado en Plan/Prepare/Execute/Assess. Se guarda `tactica` (verificada); `fase`
   queda NULL hasta que se confirme el mapeo con el framework oficial.
2. **`/api/v1/auditoria/sesgo`**: el DDL §19 no tiene tabla de veredictos ligada a
   `declaraciones_r0`; el endpoint devuelve conteos por partido/rol y % verificado.
   Los pct FALSO/VERDADERO/PARCIAL se activan en Fase 4 cuando el motor persista
   veredictos (decisión de esquema pendiente — añadir a §22 como punto abierto).
3. **Módulo vídeo**: código completo pero no ejecutado aquí (modelos de
   whisper/pyannote/EasyOCR + GPU + HF_TOKEN para diarización). Deps:
   `uv sync --extra pipeline`.
4. **Redis/Qdrant**: contenedores listos; Celery y pgvector entran en Fases 2+.
5. **Legal**: Fase -1 previa a cualquier publicación pública (§22).
6. **Mancomunidad → municipio**: DIR3 lista las mancomunidades (con provincia)
   pero no su composición; /calle muestra las mancomunidades reales de la
   provincia con la afiliación declarada pendiente del Censo EELL.
7. **Flujo normativo**: solo el nodo DOUE+BOE del ejemplo canónico está
   sembrado (Directiva 2019/904 → Ley 7/2022, con la ley real ingesta del BOE
   por identificador). Los nodos DOGV (requiere índice diario con Playwright)
   y BOP (43 portales distintos) quedan "pendiente" declarado en el timeline;
   la semilla crece con más flujos vía `POST /api/v1/ingest/boe-norma/{id}` +
   `POST /api/v1/flujo/seed-ejemplo` (patrón generalizable).
8. **Presupuestos EELL (verificado, oct. 2026)**: el portal público SGCIEF
   (`serviciostelematicosext.hacienda.gob.es/sgcief/presupuestos/Publico`)
   funciona por scraping con token antiforgery rotatorio — flujo completo en
   `scrapers/hacienda.py`: sesión → ejercicio → CCAA/provincia/tipo →
   entidades → F.1.1.1 → ExportarXMLFormulario. Ingesta:
   `POST /api/v1/ingest/presupuestos?ccaa=17&provincia=12&tipo=A5&ejercicio=2024`.
   **Toda España — COMPLETADO (oct. 2026)**: runner por lotes reanudable
   (`app/services/presupuestos_batch.py`, 19 CCAA × provincias × 8 tipos,
   rate-limited) — ejercicios 2023 y 2024 ingestados en nocilla: **18.219
   administraciones y ~297.000 filas de presupuesto** (8.964 + 9.255
   administraciones respectivamente), 0 errores en ~11 h totales de scrapeo.
   Verificado contra Madrid/Barcelona/Sevilla/Zaragoza y municipios pequeños. Quirk del portal: la exportación XML es de SESIÓN (el
   idFormulario del enlace es cosmético) — el flujo activa la entidad justo
   antes de exportar y valida por eso que cada XML traiga su propio
   codigo_entidad. El matching entidad→administración es por nombre
   normalizado (prioridad "Ayuntamiento de X"); residual: 2 municipios con
   artículo valenciano invertido en el nombre DIR3 ("l'Alcora") crean ficha
   duplicada — los datos son correctos, el enlace es mejorable. Liquidaciones
   (gastos ejecutados vs presupuestados) aún sin scrapear — mismo patrón.
9. **DOGV (actualizado)**: la API interna del portal
   (`dogv-portal/dogv/latest` con Referer del propio portal) sustituye al
   plan Playwright — sin navegador, solo expone el último número; el cron
   diario lo acumula. Playwright instalado en nocilla para usos futuros.
8. **Fiscalidad**: el desglose "de cada 100 €" es el curado del §03 con
   fuente; la personalización por renta/municipio requiere los presupuestos y
   liquidaciones EELL de Hacienda (pendiente de explorar su descarga real).

## Verificación ejecutada en esta máquina

- `uv sync` — 177 paquetes resueltos, workspace completo instalado ✓
- Imports de api/scrapers/disarm/video ✓
- 18 tablas en `Base.metadata` — coincide exacto con el DDL §19 ✓
- Migración `0001` carga y compila ✓
- BOE: smoke test en vivo, 48 documentos parseados ✓
- DISARM: 391 técnicas RED + 140 counters BLUE parseadas de las fuentes reales ✓
- Tests unitarios: 12/12 ✓ (`uv run pytest packages/api/tests -q`)
- `pnpm install` + `next build` — 13 rutas compiladas ✓
- **Pendiente de Docker**: `alembic upgrade head`, seeds, API con BD, ingesta persistente
  *(resuelto — ver sección siguiente)*

## Despliegue en producción (nocilla — 192.168.0.18)

Máquina Ubuntu con Docker; el proyecto vive en `~/blueprint`. La API corre
directa con `uv` en el host (mejor para desarrollo iterativo) y la web en
contenedor. Postgres+PostGIS+pgvector, Redis y Qdrant en contenedores.

```
Accesos:   web http://192.168.0.18:3000 · API http://192.168.0.18:8000/docs
Estado:    Fase 0 + Fase 1 COMPLETAS y verificadas end-to-end en remoto
```

Verificado en remoto (oct. 2026): migración 0001 (18 tablas + extensiones
postgis/vector + índice GIN), 64 boletines, 12 metanarrativas, 391 técnicas
DISARM RED + 140 counters BLUE, ingesta BOE persistida (15 normas con hash
SHA-256 único) e idempotente (2ª pasada: 0 nuevos / 15 duplicados), API y web
sirviendo datos reales.

Operación:

```bash
ssh cristian@192.168.0.18

# infra
cd ~/blueprint && docker compose up -d db redis qdrant

# API en host (survive al cerrar ssh: nohup)
cd ~/blueprint/packages/api && export PATH="$HOME/.local/bin:$PATH"
nohup uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 >/tmp/blueprint-api.log 2>&1 &

# web en contenedor (API_PUBLIC_URL va en ~/blueprint/.env)
cd ~/blueprint && docker compose --profile full up -d --no-deps web

# migraciones / seeds / DISARM (idempotentes)
cd ~/blueprint/packages/api && uv run alembic upgrade head
uv run python -m app.seeds.runner all
cd ~/blueprint && uv run disarm-import --offline-data data/disarm

# ingesta diaria
curl -X POST "http://192.168.0.18:8000/api/v1/ingest/boletin/BOE?fecha=$(date -I)&limit=500"

# consultas directas
docker exec blueprint-db psql -U blueprint -d blueprint
```

Notas de infraestructura:
- El usuario `cristian` pertenece al grupo `docker` (añadido vía sudo, 1 vez).
- `pgvector/pgvector:pg16` como base de la db — `postgis/postgis:16-*` sigue en
  Debian bullseye y el repo PGDG de bullseye fue archivado (apt falla).
- `API_PUBLIC_URL` en `.env` del remoto: la usa el contenedor web para hablar
  con la API del host, tanto en build (bundle del navegador) como en runtime.

