"""
Fixture de pytest para el Generador COTU.
Mockea ttkbootstrap antes de importar el módulo para que los tests puedan
ejecutarse sin instalar ttkbootstrap (p. ej. en Python 3.14 donde no hay wheel).
Crea una instancia mínima (sin GUI) para probar la lógica de negocio.
"""
import os
import sys
from unittest.mock import MagicMock

import pytest

# Raíz del proyecto en el path
_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)

# Mock de ttkbootstrap para poder importar generador_facturas_cotu sin tenerlo instalado
# (útil en entornos donde ttkbootstrap no está disponible, p. ej. Python 3.14)
if "ttkbootstrap" not in sys.modules:
    _ttk_mock = MagicMock()
    _ttk_mock.constants = MagicMock()
    _ttk_mock.dialogs = MagicMock()
    _ttk_mock.dialogs.Messagebox = MagicMock()
    _ttk_mock.widgets = MagicMock()
    _ttk_mock.widgets.ToastNotification = MagicMock()
    sys.modules["ttkbootstrap"] = _ttk_mock
    sys.modules["ttkbootstrap.constants"] = _ttk_mock.constants
    sys.modules["ttkbootstrap.dialogs"] = _ttk_mock.dialogs
    sys.modules["ttkbootstrap.widgets"] = _ttk_mock.widgets


@pytest.fixture(scope="function")
def app():
    """
    Crea una instancia de GeneradorFacturasCOTU sin ventana real.
    Usa object.__new__ y mocks para root y solo_carpetas_cotu.
    """
    from generador_facturas_cotu import GeneradorFacturasCOTU

    gen = object.__new__(GeneradorFacturasCOTU)
    root_mock = MagicMock()
    root_mock.after = lambda ms, func=None: None
    gen.root = root_mock

    cotu_mock = MagicMock()
    cotu_mock.get.return_value = True
    gen.solo_carpetas_cotu = cotu_mock

    # Locks (añadidos en auditoría): mock para tests
    gen._lock_config = MagicMock()
    gen._lock_historial = MagicMock()

    yield gen
