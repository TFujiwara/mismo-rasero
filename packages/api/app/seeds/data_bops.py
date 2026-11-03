"""Los 43 BOPs provinciales del blueprint §14.

No existe BOP en uniprovinciales (Asturias, Cantabria, Madrid, Murcia, Navarra,
La Rioja, Baleares) — su boletín autonómico ya está en data_boletines.
Ceuta y Melilla tienen boletín propio (BOCCE/BOME), no BOP.
"""

# (provincia, url_base)
BOPS: list[tuple[str, str]] = [
    ("A Coruña", "http://www.dicoruna.es/bop/"),
    ("Albacete", "http://www.dipualba.es/bop/"),
    ("Alicante", "http://ov.dip-alicante.es/"),
    ("Almería", "http://www.bop.almeria.es/"),
    ("Araba/Álava", "http://web.alava.net/botha/"),
    ("Ávila", "http://www.diputacionavila.net/bop/"),
    ("Badajoz", "http://www.dip-badajoz.es/bop/"),
    ("Barcelona", "https://bop.diba.cat"),
    ("Bizkaia", "http://aplijava.bizkaia.net/BT00/BAO_BOB"),
    ("Burgos", "http://www.burgos.es/boletin-oficial-provincial"),
    ("Cáceres", "http://www.dip-caceres.es/"),
    ("Cádiz", "http://www.bopcadiz.org/"),
    ("Castellón", "https://bop.dipcas.es/"),
    ("Ciudad Real", "http://www.dipucr.com/"),
    ("Córdoba", "http://www.dipucordoba.es/bop/"),
    ("Cuenca", "http://www.dipucuenca.es/bop/"),
    ("Girona", "http://www.ddgi.org/bop"),
    ("Granada", "https://www.dipgra.es/BOP/bop.asp"),
    ("Guadalajara", "http://www.ceyde.com/bop_guadalajara/"),
    ("Gipuzkoa", "https://ssl4.gipuzkoa.net/boletin/asp/index.asp"),
    ("Huelva", "http://www.diphuelva.es/"),
    ("Huesca", "http://www.dphuesca.es/boph/"),
    ("Jaén", "https://bop.dipujaen.es/"),
    ("Las Palmas", "http://www.boplaspalmas.com/"),
    ("León", "http://www.dipuleon.es/"),
    ("Lleida", "http://malo.diputaciolleida.es/bop_c/"),
    ("Lugo", "http://www.deputacionlugo.org/"),
    ("Málaga", "http://www.bopmalaga.org/"),
    ("Ourense", "http://www.dpou.es/bop1/bop.php"),
    ("Palencia", "http://www.dip-palencia.es/"),
    ("Pontevedra", "http://bop.depontevedra.es/"),
    ("Salamanca", "http://www.dipsanet.es/"),
    ("Segovia", "http://www.dipsegovia.es/"),
    ("Sevilla", "http://www.dipusevilla.es/bop/"),
    ("Soria", "http://www.dipsoria.es/"),
    ("Tarragona", "https://www.dipta.cat/bop/"),
    ("Tenerife", "http://www.bopsantacruzdetenerife.org/"),
    ("Teruel", "http://bop.dpteruel.es/"),
    ("Toledo", "http://bop2.diputoledo.es/"),
    ("Valencia", "https://bop.dival.es/bop/"),
    ("Valladolid", "https://bop.sede.diputaciondevalladolid.es/"),
    ("Zamora", "http://www.diputaciondezamora.es/"),
    ("Zaragoza", "http://bop.dpz.es/"),
]


def sigla_bop(provincia: str) -> str:
    slug = (
        provincia.upper()
        .replace("Á", "A").replace("É", "E").replace("Í", "I")
        .replace("Ó", "O").replace("Ú", "U").replace("Ü", "U").replace("Ñ", "N")
        .replace("/", "-").replace(" ", "-")
    )
    return f"BOP-{slug}"
