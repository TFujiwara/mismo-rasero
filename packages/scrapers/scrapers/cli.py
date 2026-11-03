"""CLI de verificación de adaptadores — sin base de datos (dry-run).

Uso:
  uv run boletines boe --fecha 2024-01-02 --limit 5
  uv run boletines dogv --fecha 2026-10-23          (requiere playwright)
  uv run boletines doue --fecha 2026-10-23
  uv run boletines dir3 --url https://.../unidades.csv --limit 5
"""

from __future__ import annotations

import logging
from datetime import date, datetime

import click

from scrapers.base import registrar_adapters
from scrapers.dir3 import Dir3Adapter

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def _parse_fecha(ctx, param, value: str | None) -> date | None:
    if value is None:
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


@click.group()
def main() -> None:
    """Boletines oficiales — adaptadores del blueprint §13/§14."""


@main.command("boe")
@click.option("--fecha", "-f", callback=_parse_fecha, default=None,
              help="YYYY-MM-DD (por defecto hoy)")
@click.option("--limit", "-l", default=10, show_default=True)
def cmd_boe(fecha: date, limit: int):
    """Sumario diario del BOE vía API de datos abiertos."""
    adapter = registrar_adapters()["BOE"]()
    docs = adapter.fetch_day(fecha)
    click.echo(f"BOE {fecha}: {len(docs)} documentos")
    for d in docs[:limit]:
        click.echo(f"  {d.identificador}  [{d.seccion}]  {d.titulo[:90]}")


@main.command("dogv")
@click.option("--fecha", "-f", callback=_parse_fecha, default=None)
@click.option("--limit", "-l", default=10, show_default=True)
def cmd_dogv(fecha: date, limit: int):
    """Índice diario del DOGV vía Playwright (SPA Liferay)."""
    adapter = registrar_adapters()["DOGV"]()
    docs = adapter.fetch_day(fecha)
    click.echo(f"DOGV {fecha}: {len(docs)} documentos")
    for d in docs[:limit]:
        click.echo(f"  {d.identificador}  {d.titulo[:90]}")


@main.command("doue")
@click.option("--fecha", "-f", callback=_parse_fecha, default=None)
@click.option("--limit", "-l", default=10, show_default=True)
def cmd_doue(fecha: date, limit: int):
    """JO de la UE vía RSS de EUR-Lex (puede requerir EURLEX_PROXY)."""
    import os

    adapter = registrar_adapters()["DOUE"](proxy=os.environ.get("EURLEX_PROXY") or None)
    docs = adapter.fetch_day(fecha)
    click.echo(f"DOUE {fecha}: {len(docs)} documentos")
    for d in docs[:limit]:
        click.echo(f"  {d.identificador}  {d.titulo[:90]}")


@main.command("dir3")
@click.option("--url", "-u", required=True, help="URL del CSV de unidades DIR3")
@click.option("--limit", "-l", default=10, show_default=True)
def cmd_dir3(url: str, limit: int):
    """Descarga masiva de unidades DIR3 (URL configurable — ver docstring)."""
    unidades = Dir3Adapter(url).fetch()
    click.echo(f"DIR3: {len(unidades)} unidades")
    for u in unidades[:limit]:
        click.echo(f"  {u.codigo}  n={u.nivel}  {u.nombre[:80]}")


if __name__ == "__main__":
    main()
