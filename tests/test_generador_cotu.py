"""
Tests unitarios para el Generador de Reportes COTU.
Prueban la lógica de negocio sin depender de la GUI visible.
"""
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pytest



# --- validar_fecha ---
class TestValidarFecha:
    """Tests para validar_fecha (formato DD/MM/YYYY)."""

    def test_fecha_valida(self, app):
        assert app.validar_fecha("15/08/2025") == datetime(2025, 8, 15)
        assert app.validar_fecha("01/01/2024") == datetime(2024, 1, 1)
        assert app.validar_fecha("31/12/2025") == datetime(2025, 12, 31)

    def test_fecha_invalida_formato(self, app):
        assert app.validar_fecha("") is None
        assert app.validar_fecha("15-08-2025") is None
        assert app.validar_fecha("2025/08/15") is None
        assert app.validar_fecha("15/13/2025") is None  # mes 13
        assert app.validar_fecha("32/01/2025") is None  # día 32

    def test_fecha_invalida_texto(self, app):
        assert app.validar_fecha("abc") is None
        assert app.validar_fecha("15/08/abcd") is None


# --- parsear_fecha_carpeta ---
class TestParsearFechaCarpeta:
    """Tests para parsear_fecha_carpeta (día, mes, año desde nombres de carpeta)."""

    def test_formato_estandar(self, app):
        # "23 DE DICIEMBRE", "12-DICIEMBRE", "2025"
        assert app.parsear_fecha_carpeta("23 DE DICIEMBRE", "12-DICIEMBRE", "2025") == datetime(2025, 12, 23)
        assert app.parsear_fecha_carpeta("02 DE AGOSTO", "AGOSTO", "2025") == datetime(2025, 8, 2)
        assert app.parsear_fecha_carpeta("1 DE ENERO", "ENERO", "2024") == datetime(2024, 1, 1)

    def test_mes_nombre_espanol(self, app):
        assert app.parsear_fecha_carpeta("15 DE MARZO", "MARZO", "2025") == datetime(2025, 3, 15)
        assert app.parsear_fecha_carpeta("10 DE JULIO", "JULIO", "2025") == datetime(2025, 7, 10)

    def test_vacios_retorna_none(self, app):
        assert app.parsear_fecha_carpeta("", "DICIEMBRE", "2025") is None
        assert app.parsear_fecha_carpeta("23 DE DICIEMBRE", "", "2025") is None
        assert app.parsear_fecha_carpeta("23 DE DICIEMBRE", "DICIEMBRE", "") is None

    def test_fecha_invalida_retorna_none(self, app):
        # 31 de febrero no existe
        assert app.parsear_fecha_carpeta("31 DE FEBRERO", "FEBRERO", "2025") is None


# --- verificar_duplicados ---
class TestVerificarDuplicados:
    """Tests para verificar_duplicados."""

    def test_sin_duplicados(self, app):
        registros = [
            {app.COL_FACTURA: "COTU001", app.COL_FECHA: "1 ENERO", app.COL_COMPANIA: "SOLIDARIA"},
            {app.COL_FACTURA: "COTU002", app.COL_FECHA: "2 ENERO", app.COL_COMPANIA: "AURORA"},
        ]
        assert app.verificar_duplicados(registros) == []

    def test_con_duplicados(self, app):
        registros = [
            {app.COL_FACTURA: "COTU001", app.COL_FECHA: "1 ENERO", app.COL_COMPANIA: "SOLIDARIA"},
            {app.COL_FACTURA: "COTU001", app.COL_FECHA: "2 ENERO", app.COL_COMPANIA: "AURORA"},
        ]
        dups = app.verificar_duplicados(registros)
        assert len(dups) == 1
        assert "COTU001" in dups[0]
        assert "2 veces" in dups[0]

    def test_lista_vacia(self, app):
        assert app.verificar_duplicados([]) == []

    def test_ignora_cotu_vacio(self, app):
        registros = [
            {app.COL_FACTURA: "COTU", app.COL_FECHA: "1", app.COL_COMPANIA: "X"},
            {app.COL_FACTURA: "", app.COL_FECHA: "2", app.COL_COMPANIA: "Y"},
        ]
        assert app.verificar_duplicados(registros) == []


# --- calcular_estadisticas ---
class TestCalcularEstadisticas:
    """Tests para calcular_estadisticas."""

    def test_resumen_por_aseguradora(self, app):
        registros = [
            {app.COL_COMPANIA: "SOLIDARIA"},
            {app.COL_COMPANIA: "SOLIDARIA"},
            {app.COL_COMPANIA: "AURORA"},
        ]
        texto = app.calcular_estadisticas(registros)
        assert "Total Facturas: 3" in texto
        assert "SOLIDARIA" in texto
        assert "AURORA" in texto
        assert "66.7" in texto or "66,7" in texto  # porcentaje SOLIDARIA

    def test_lista_vacia(self, app):
        assert app.calcular_estadisticas([]) == "No hay registros."

    def test_sin_aseguradora(self, app):
        registros = [{app.COL_COMPANIA: ""}, {app.COL_COMPANIA: None}]
        texto = app.calcular_estadisticas(registros)
        assert "SIN ASEGURADORA" in texto
        assert "Total Facturas: 2" in texto


# --- filtrar_por_tipo ---
class TestFiltrarPorTipo:
    """Tests para filtrar_por_tipo."""

    def test_tipo_anio_devuelve_todo(self, app):
        registros = [
            {app.COL_ANIO: "2025", app.COL_MES: "DICIEMBRE", app.COL_FECHA: "23 DE DICIEMBRE", app.COL_FACTURA: "COTU1", app.COL_COMPANIA: "SOL"},
        ]
        resultado = app.filtrar_por_tipo(registros, app.TIPO_ANIO)
        assert len(resultado) == 1
        assert resultado[0][app.COL_FACTURA] == "COTU1"

    def test_filtro_por_rango_fechas(self, app):
        registros = [
            {app.COL_ANIO: "2025", app.COL_MES: "DICIEMBRE", app.COL_FECHA: "20 DE DICIEMBRE", app.COL_FACTURA: "COTU1", app.COL_COMPANIA: "SOL"},
            {app.COL_ANIO: "2025", app.COL_MES: "DICIEMBRE", app.COL_FECHA: "25 DE DICIEMBRE", app.COL_FACTURA: "COTU2", app.COL_COMPANIA: "SOL"},
            {app.COL_ANIO: "2025", app.COL_MES: "DICIEMBRE", app.COL_FECHA: "30 DE DICIEMBRE", app.COL_FACTURA: "COTU3", app.COL_COMPANIA: "SOL"},
        ]
        # Rango 21/12/2025 - 28/12/2025: solo COTU2
        resultado = app.filtrar_por_tipo(registros, app.TIPO_MES, "21/12/2025", "28/12/2025")
        assert len(resultado) == 1
        assert resultado[0][app.COL_FECHA] == "25 DE DICIEMBRE"

    def test_lista_vacia(self, app):
        assert app.filtrar_por_tipo([], app.TIPO_MES, "01/12/2025", "31/12/2025") == []


# --- extraer_facturas ---
class TestExtraerFacturas:
    """Tests para extraer_facturas con estructura temporal de carpetas."""

    def _crear_estructura_cotu(self, tmp_path):
        """Crea AÑO/MES/DÍA/ASEGURADORA/COTUxxx en tmp_path."""
        base = tmp_path / "2025" / "12-DICIEMBRE" / "23 DE DICIEMBRE" / "SOLIDARIA"
        (base / "COTU001").mkdir(parents=True, exist_ok=True)
        (base / "COTU002").mkdir(parents=True, exist_ok=True)
        otro = tmp_path / "2025" / "12-DICIEMBRE" / "24 DE DICIEMBRE" / "AURORA"
        (otro / "COTU003").mkdir(parents=True, exist_ok=True)
        return str(tmp_path)

    def test_extrae_facturas_estructura_estandar(self, app):
        # Directorio temporal dentro del proyecto para evitar restricciones de sandbox
        tmp_dir = Path(__file__).resolve().parent / "tmp_cotu_test"
        tmp_dir.mkdir(exist_ok=True)
        try:
            ruta_base = self._crear_estructura_cotu(tmp_dir)
            ruta_anio = os.path.join(ruta_base, "2025")
            registros = app.extraer_facturas(ruta_anio)
            assert len(registros) >= 3
            cotus = {r[app.COL_FACTURA] for r in registros}
            assert "COTU001" in cotus
            assert "COTU002" in cotus
            assert "COTU003" in cotus
            aseguradoras = {r[app.COL_COMPANIA] for r in registros}
            assert "SOLIDARIA" in aseguradoras
            assert "AURORA" in aseguradoras
        finally:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_carpeta_inexistente_levanta_error(self, app):
        with pytest.raises(FileNotFoundError) as exc:
            app.extraer_facturas(os.path.join("C:", "ruta", "que", "no", "existe", "2025"))
        assert "no existe" in str(exc.value).lower() or "exist" in str(exc.value).lower()


# --- _es_ruta_sistema ---
class TestEsRutaSistema:
    """Tests para _es_ruta_sistema (evitar escritura en carpetas de sistema)."""

    def test_vacio_o_relativo_retorna_false(self):
        from generador_facturas_cotu import _es_ruta_sistema as _es
        assert _es("") is False
        from generador_facturas_cotu import _es_ruta_sistema as _es
        assert _es("carpeta") is False
        assert _es("relativo/path") is False

    @pytest.mark.skipif(sys.platform != "win32", reason="Solo Windows: WINDIR, ProgramFiles")
    def test_windows_rutas_sistema_true(self):
        from generador_facturas_cotu import _es_ruta_sistema as _es
        windir = os.environ.get("WINDIR")
        if windir:
            assert _es(windir) is True
            assert _es(os.path.join(windir, "System32")) is True
        pf = os.environ.get("ProgramFiles")
        if pf:
            assert _es(pf) is True
            assert _es(os.path.join(pf, "Algo")) is True

    @pytest.mark.skipif(sys.platform != "win32", reason="Solo Windows: carpeta usuario no es sistema")
    def test_windows_carpeta_usuario_false(self):
        from generador_facturas_cotu import _es_ruta_sistema as _es
        user = os.path.expanduser("~")
        if user and os.path.isabs(user):
            assert _es(user) is False
        temp_base = os.environ.get("TEMP", "C:\\Temp")
        assert _es(os.path.join(temp_base, "prueba")) is False

    @pytest.mark.skipif(sys.platform == "win32", reason="Solo Unix: /usr, /etc son sistema")
    def test_unix_rutas_sistema_true(self):
        from generador_facturas_cotu import _es_ruta_sistema as _es
        assert _es("/usr") is True
        assert _es("/usr/bin") is True
        assert _es("/etc") is True

    @pytest.mark.skipif(sys.platform == "win32", reason="Solo Unix: home no es sistema")
    def test_unix_home_false(self):
        from generador_facturas_cotu import _es_ruta_sistema as _es
        user = os.path.expanduser("~")
        if user:
            assert _es(user) is False
        assert _es("/tmp/cotu_test") is False
