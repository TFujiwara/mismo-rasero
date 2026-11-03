# PostgreSQL 16 + pgvector + PostGIS — el DDL §19 necesita ambos.
# NOTA: la base postgis/postgis:16-* sigue anclada a Debian bullseye, y el repo
# PGDG de bullseye fue archivado (sin Release file) → apt falla.
# Al revés: pgvector/pgvector:pg16 es el postgres:16 oficial (bookworm, PGDG vivo)
# y PostGIS se instala como paquete normal.
FROM pgvector/pgvector:pg16

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      postgresql-16-postgis-3 \
      postgresql-16-postgis-3-scripts \
 && rm -rf /var/lib/apt/lists/*
