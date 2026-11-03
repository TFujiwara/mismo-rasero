#!/bin/bash
# Cron diario de ingesta de boletines — Mismo Rasero
# Instalación (nocilla):
#   crontab -e  →  30 9,14 * * * /home/cristian/blueprint/scripts/cron_boletines.sh
# Idempotente: la ingesta deduplica por hash SHA-256, re-ejecutar no duplica.

API="${API:-http://localhost:8000}"
LOG="${LOG:-/home/cristian/blueprint/data/logs/cron_boletines.log}"
HOY=$(date -I)
AYER=$(date -I -d "yesterday")

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

log "=== inicio ingesta diaria ($HOY)"

# BOE: sumario del día (y del día anterior por si la máquina estuvo apagada)
for FECHA in "$HOY" "$AYER"; do
  RESP=$(curl -s -m 600 -X POST "$API/api/v1/ingest/boletin/BOE?fecha=$FECHA&limit=2000")
  log "BOE $FECHA -> ${RESP:-SIN RESPUESTA}"
  sleep 2
done

# BOJA: fecha direccionable (calendario + boletín por número)
for FECHA in "$HOY" "$AYER"; do
  RESP=$(curl -s -m 900 -X POST "$API/api/v1/ingest/boletin/BOJA?fecha=$FECHA")
  log "BOJA $FECHA -> ${RESP:-SIN RESPUESTA}"
  sleep 2
done

# BOCM y DOE: solo el último boletín (como DOGV)
RESP=$(curl -s -m 1500 -X POST "$API/api/v1/ingest/boletin/BOCM?fecha=$HOY")
log "BOCM $HOY -> ${RESP:-SIN RESPUESTA}"
RESP=$(curl -s -m 900 -X POST "$API/api/v1/ingest/boletin/DOE?fecha=$HOY")
log "DOE $HOY -> ${RESP:-SIN RESPUESTA}"

# BOPV: la API va un día por detrás del portal — ingesta con dos días de margen
ANTIER=$(date -I -d "2 days ago")
for FECHA in "$ANTIER" "$AYER"; do
  RESP=$(curl -s -m 900 -X POST "$API/api/v1/ingest/boletin/BOPV?fecha=$FECHA")
  log "BOPV $FECHA -> ${RESP:-SIN RESPUESTA}"
  sleep 2
done

# DOGV: la API solo expone el último número; fecha=hoy
RESP=$(curl -s -m 900 -X POST "$API/api/v1/ingest/boletin/DOGV?fecha=$HOY")
log "DOGV $HOY -> ${RESP:-SIN RESPUESTA}"

log "=== fin ingesta diaria"
