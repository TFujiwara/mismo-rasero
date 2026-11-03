# Mismo Rasero

> Quién puede hacer qué, con la ley delante.

Plataforma de transparencia administrativa española: **a gobierno y oposición
se les aplica el mismo rasero**, y cada dato lleva la fuente oficial delante.
Contrasta frases de políticos con la cadena competencial real, muestra el
presupuesto de los ayuntamientos de España capítulo a capítulo, resuelve qué
administraciones hay encima de tu dirección, y busca a tus representantes —
con el artículo de la ley y el enlace al boletín en cada respuesta.

No decimos que nadie mienta. Mostramos lo que se dijo y lo que dicen los datos:
el contraste habla solo.

## La familia de secciones

| Sección | Qué responde | Fuente |
|---------|--------------|--------|
| **La ley dice** | "¿Puede el ayuntamiento bajar el IRPF?" → FALSO COMPETENCIAL, con cadena y artículo | competencias verificadas vía ELI |
| **Los datos dicen** | El presupuesto real de tu ayuntamiento, capítulo a capítulo, 2023 vs 2024 | portal SGCIEF de Hacienda |
| **El registro dice** | Qué administraciones hay sobre tu dirección, con qué puede hacer cada una | Nominatim/OSM + registro DIR3 |
| **El artículo dice** | Cómo reclamar: alegaciones, instancias, quejas, reclamaciones | Leyes 39/2015, 40/2015, LBRL… |

## Qué funciona hoy, con números

- **Verificador competencial**: 30 competencias estructuradas (cadena UE →
  Estado → CCAA → Local, niveles decisorios, artículo y fuente BOE verificada
  vía ELI). El veredicto lo decide una regla, nunca un modelo.
- **Presupuestos EELL**: ~9.000 entidades × ejercicios 2023 y 2024
  (~297.000 filas) ingestadas por lotes desde el portal público SGCIEF de
  Hacienda, con comparación interanual.
- **Organigrama nacional**: cualquier dirección de España se resuelve contra
  65.000+ entidades del registro DIR3 (EELL + CCAA + AGE).
- **Diputados**: 5.794 registros históricos y actuales del Congreso (datos
  abiertos), con grupo, circunscripción, alta y biografía.
- **Boletines en ingesta diaria automática**: BOE, BOJA, BOCM, DOE, DOGV, DOG
  (y BOPV en metadatos, pendiente de proxy para los PDF).
- **DISARM**: 391 técnicas RED + 140 contramedidas BLUE cargadas del framework.
- **Legislación vasca**: 25 leyes (2020-2026) vía SPARQL sobre el grafo ELI
  oficial, con fuente en Legegunea.
- **MCP**: 8 herramientas para clientes LLM (Claude Desktop, opencode…).

## Arquitectura

```
packages/
  web/       Next.js 14 + Tailwind — interfaz ciudadana
  api/       FastAPI + SQLAlchemy + Alembic — API v1 y esquema completo
  scrapers/  Adaptadores: BOE, BOJA, BOCM, BOPV, DOE, DOGV, DOUE, DIR3, Hacienda
  disarm/    Importador del framework DISARM (Red/Blue)
  video/     Verificación de vídeo: transcripción, diarización, OCR (§12)
  mcp/       Servidor MCP — las mismas herramientas para clientes LLM
docker/      Postgres 16 + PostGIS + pgvector, imágenes de api y web
scripts/     Cron diario de ingesta de boletines
```

- **Monorepo**: pnpm (web) + uv workspace (python)
- **Base de datos**: PostgreSQL 16 con PostGIS (geocodificación) y pgvector
  (búsqueda semántica, en preparación); Redis y Qdrant para tareas asíncronas

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

# ingesta de fuentes (ejemplos)
uv run boletines boe --fecha 2024-01-02      # sumario diario (dry-run)
uv run disarm-import                          # framework DISARM
curl -X POST "localhost:8000/api/v1/ingest/boletin/BOE?fecha=2024-01-02"
curl -X POST "localhost:8000/api/v1/ingest/legislacion-vasca?desde=2020-01-01"
```

Configuración en `.env` (ver `.env.example`). El motor de verificación funciona
100 % determinista; opcionalmente se puede enchufar un LLM compatible con la
API de OpenAI (`LLM_BASE_URL`, `LLM_API_KEY`) para asistir en la extracción del
sujeto de frases difíciles — **el veredicto lo decide siempre una regla contra
la cadena competencial, nunca un modelo**.

## Fuentes — verificadas en vivo

La lección que estructura este repo: **las URLs oficiales podridas son la
norma, no la excepción**. Cada fuente se prueba contra su portal real antes de
escribir el adaptador, y lo que falla se documenta aquí.

| Fuente | Estado | Notas |
|--------|--------|-------|
| BOE | ✅ operativa | API de datos abiertos (exige `Accept: application/xml`) + normas por identificador + ELI (`boe.es/eli/es/...`) para verificar fuentes |
| DOGV | ✅ operativa | API interna del portal (`dogv-portal/dogv/latest`, con Referer); solo el último número |
| BOJA | ✅ operativa | API tabular pública (`datos.juntadeandalucia.es/api/v0/boja`, spec OpenAPI del CTT) — descubierta vía el buscador de APIs |
| BOCM | ✅ operativa | Feed `ultimo-boletin.xml` + XML espejo por documento (mismo patrón que el BOE) |
| DOE | ✅ operativa | RSS por secciones (`rss.php?seccion=1..4`) con PDF directo |
| DOG | ✅ operativa | RSS de sumario diario (`Sumario_es.rss`, 54 disposiciones/día) + PDF desde la página de cada documento |
| BOPV | 🟡 metadatos | API REST en `api.euskadi.eus` (OpenAPI v0.0.1): los actos fluyen; los PDF de `www.euskadi.eus` dan 406 a toda nuestra red (ban confirmado: portada incluida, API libre). Salida: proxy vía `HTTPS_PROXY` |
| Presupuestos EELL | ✅ toda España | Portal público SGCIEF: scraping con token antiforgery rotatorio; runner por lotes reanudable. Las liquidaciones aún no se publican en consulta pública |
| DIR3 | ✅ ingesta completa | 25.178 EELL + 17.025 CCAA + 19.919 AGE. El CTT está tras F5 TrafficShield: los ficheros se bajan a mano del navegador |
| CartoCiudad | ⚠️ caída | La API REST responde 500 server-side; geocodificación vía Nominatim/OSM estructurada (documentado como fuente no oficial) |
| EUR-Lex (DOUE) | ⚠️ soft-block | Responde 202 a IPs automatizadas; adaptador listo con proxy opcional |
| Congreso | ✅ operativa | Datos abiertos: diputados (JSON diario). Las votaciones de Leg15 solo se publican como planchas PNG — bloqueado hasta cambio de formato |
| Senado | ⛔ | El portal de datos abiertos responde 500; el listado de senadores es JS sin enlaces |

## Huecos documentados (no inventados)

La honestidad sobre lo que falta es parte del método:

1. `disarm_techniques.fase` queda NULL — las fuentes actuales de DISARM ya no
   exponen el agrupado Plan/Prepare/Execute/Assess.
2. El panel de auditoría de sesgo (`/api/v1/auditoria/sesgo`) muestra conteos
   por partido/rol; los porcentajes de veredicto se activan cuando el motor
   persista veredictos ligados a declaraciones.
3. El módulo de vídeo está implementado pero no ejecutado en producción
   (requiere modelos whisper/pyannote y HF_TOKEN para diarización).
4. El índice de competencias: **30 estructuradas** — el alcance del veredicto
   crece con el índice. Las fuentes se verifican contra boe.es/eli/es/...
   antes de sembrar (hay un test que lo obliga).
5. La afiliación exacta municipio→mancomunidad requiere el Censo de Entes
   Locales: /calle muestra las mancomunidades reales de la provincia con la
   afiliación declarada pendiente.
6. Antes de cualquier publicación pública amplia: revisión legal (RGPD,
   honor/rectificación, ToS de las plataformas) — ver §22 del blueprint.
7. **Cabeceras CCAA en cola**: DOGC y BOA resisten el scraping sin navegador
   (DOGC: Liferay con widgets httpFetch cuya URL de datos solo se ve en el
   navegador; BOA: Angular cuya ruta de datos dispara al buscar). Playbook
   conocido: abrir el portal, hacer una búsqueda de fecha y copiar la llamada
   de datos desde DevTools → Network. Los boletines forales (BOTHA, BOB, BOG)
   van como filas BOP en el seed — son los boletines de los Territorios
   Históricos (capacidad legislativa foral), no BOPs municipales.
8. **Votaciones del Congreso (Leg15)**: el opendata solo publica gráficos PNG
   por sesión (la página lista únicamente la última, el XML hermano no existe).
   Volverá cuando el Congreso cambie de formato o tras revertir el portlet.
9. **Matching por nombre**: 2 municipios con artículo valenciano invertido en
   el nombre DIR3 ("l'Alcora") crean ficha duplicada — los datos son correctos,
   el enlace es mejorable.

## Hoja de ruta

| Fase | Alcance | Estado |
|------|---------|--------|
| 0-1 | Infraestructura, esquema completo, seeds, adaptadores BOE/DOGV/DOUE/DIR3 | ✅ |
| 2 | Mapa de poder + competencias + `/calle` con geocodificación | ✅ |
| 3 | Presupuestos EELL de toda España + comparación interanual + flujo normativo | ✅ |
| 4 v1 | Veredicto competencial determinista + seam LLM | ✅ |
| 4 v2 | Extracción semántica con LLM (requiere configurar `LLM_BASE_URL`) | 🔜 |
| 5 v1 | Pilar 5 personas — Congreso de los Diputados | ✅ |
| 5 v2 | Votaciones (bloqueadas por formato PNG), Senado (portal 500), agendas | 🔜 |
| 5 v3 | Verificador de programas electorales + generación de escritos | 🔜 |
| 6 | Verificación de vídeo (solo análisis) | código listo, sin ejecutar |
| 7 | Radar R0R1R2 + export STIX2 | 🔜 |
| 8 | Rectificación 24h + aviso legal + transparencia de financiación | 🔜 |

## Servidor MCP

Las mismas herramientas, expuestas vía Model Context Protocol para clientes
LLM (Claude Desktop, opencode…):

```json
{
  "mcpServers": {
    "mismo-rasero": {
      "command": "uv",
      "args": ["--directory", "/ruta/al/repo", "run", "blueprint-mcp"],
      "env": { "DATABASE_URL": "postgresql+psycopg://blueprint:blueprint@localhost:5432/blueprint" }
    }
  }
}
```

Herramientas: `verificar_frase` (con veredicto competencial),
`buscar_competencias`, `listar_boletines`, `buscar_normas`, `como_reclamar`,
`disarm`, `auditoria_sesgo`, `estado_sistema`.

## Licencia

MIT — el código es auditable por diseño: no hay que fiarse de la palabra de
la plataforma cuando se puede leer la lógica del motor.

## Agradecimientos

El blueprint técnico v2.5 que fundó este proyecto, y las fuentes públicas que
lo hacen posible: BOE, las 19 comunidades y ciudades que publican sus
boletines, el Ministerio de Hacienda (SGCIEF), el registro DIR3, el Congreso
de los Diputados, el framework DISARM (CC-BY-SA-4.0) y OpenStreetMap.
