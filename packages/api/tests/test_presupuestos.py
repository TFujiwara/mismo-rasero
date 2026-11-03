from decimal import Decimal

from scrapers.hacienda import parse_xml_f111

XML_VILA_REAL = b"""<presupuestos xmlns="presupuestos/salida/PrincipalNoCesion/2024/2024-01-01">
  <version>1.0</version>
  <ambito>EELL</ambito>
  <codigo_entidad>17-12-135-AA-000</codigo_entidad>
  <nombre_entidad>Vila-real</nombre_entidad>
  <periodo><ejercicio>2024</ejercicio></periodo>
  <tipo_contabilidad>L</tipo_contabilidad>
  <formularios>
    <f_1_1_1>
      <resumen_clasificacion_economica_ingresos>
        <n_1><previsiones_iniciales>30899100</previsiones_iniciales></n_1>
        <n_4><previsiones_iniciales>20015145.83</previsiones_iniciales></n_4>
        <total_ingresos><previsiones_iniciales>58319050.58</previsiones_iniciales></total_ingresos>
      </resumen_clasificacion_economica_ingresos>
      <resumen_clasificacion_economica_gastos>
        <n_1><creditos_iniciales>23257262.55</creditos_iniciales></n_1>
        <n_6><creditos_iniciales>1828715.87</creditos_iniciales></n_6>
        <total_gastos><creditos_iniciales>58319050.58</creditos_iniciales></total_gastos>
      </resumen_clasificacion_economica_gastos>
    </f_1_1_1>
  </formularios>
</presupuestos>
"""


def test_parse_xml_f111():
    r = parse_xml_f111(XML_VILA_REAL)
    assert r.codigo_entidad == "17-12-135-AA-000"
    assert r.nombre_entidad == "Vila-real"
    assert r.ejercicio == 2024
    assert r.tipo_contabilidad == "L"
    assert r.ingresos["1"] == Decimal("30899100")
    assert r.ingresos["total"] == Decimal("58319050.58")
    assert r.gastos["1"] == Decimal("23257262.55")
    assert r.gastos["6"] == Decimal("1828715.87")
    assert r.gastos["total"] == Decimal("58319050.58")


def test_capitulos_claves_limpias():
    """Las claves de capítulo son '1'..'9'/'total', no 'n_1' ni 'total_ingresos'."""
    r = parse_xml_f111(XML_VILA_REAL)
    assert set(r.gastos) == {"1", "6", "total"}
    assert all(k.isdigit() or k == "total" for k in r.ingresos)
