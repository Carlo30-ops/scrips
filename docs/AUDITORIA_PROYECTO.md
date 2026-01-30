# Auditoría del proyecto Generador de Reportes COTU

Resumen de **posibles** problemas, mejoras y buenas prácticas detectados.

---

## 1. Bugs / Comportamiento incorrecto

### 1.1 Tema oscuro: colores no se actualizan al cambiar (Prioridad: media)
- **Dónde:** `toggle_tema()` cambia `self.tema_oscuro` y el tema de ttk (`theme_use`), pero **no actualiza** `self.colors`.
- **Efecto:** Tras cambiar de tema, widgets que usan `self.colors` (labels, cards, estado) pueden seguir con colores del tema anterior hasta reiniciar la app.
- **Sugerencia:** En `toggle_tema()`, asignar de nuevo `self.colors = self.ETH_COLORS["dark"] if self.tema_oscuro else self.ETH_COLORS["light"]` y, si hace falta, refrescar los widgets que dependen de `self.colors`.

### 1.2 Color de estado "text" no mapeado (Prioridad: baja)
- **Dónde:** `actualizar_status(mensaje, color="text")` — en el mapeo de colores no existe la clave `"text"`.
- **Efecto:** Se usa `foreground="text"`, que en Tk puede no ser un color válido en algunos entornos.
- **Sugerencia:** Incluir en el mapeo algo como `"text": self.colors.get('text', '#000000')` para el mensaje de estado por defecto.

### 1.3 `ETH_COLORS` sin clave `danger` (Prioridad: baja)
- **Dónde:** `actualizar_status(..., color="red")` usa `self.colors.get('danger', '#FF3B30')`, pero `ETH_COLORS` no define `"danger"`.
- **Efecto:** Funciona por el fallback `#FF3B30`, pero el diseño de colores no es consistente.
- **Sugerencia:** Añadir `"danger": "#FF3B30"` (y si aplica `"text"`) en `ETH_COLORS` para light/dark.

---

## 2. Código y mantenibilidad

### 2.1 Import con comodín
- **Dónde:** `from ttkbootstrap.constants import *`
- **Problema:** No se ve qué constantes se usan; puede haber conflictos de nombres.
- **Sugerencia:** Importar solo lo necesario, por ejemplo `from ttkbootstrap.constants import PRIMARY, SECONDARY` (o las que realmente se usen).

### 2.2 Tipos no usados
- **Dónde:** `from typing import List, Dict, Optional, Any, Tuple, Union`
- **Problema:** `Any`, `Tuple`, `Union` no parecen usarse en el módulo.
- **Sugerencia:** Eliminar los que no se usen para dejar el código más claro.

### 2.3 `timedelta` importado y no usado
- **Dónde:** `from datetime import datetime, timedelta`
- **Sugerencia:** Quitar `timedelta` si no se usa.

### 2.4 Método vacío
- **Dónde:** `_configure_ethereal_styles(self): pass`
- **Sugerencia:** Eliminarlo o darle contenido; si es un recordatorio, dejarlo como comentario.

---

## 3. Concurrencia y recursos

### 3.1 Historial y config: posible condición de carrera (Prioridad: baja)
- **Dónde:** `guardar_historial` / `cargar_historial` y `_guardar_config` / `_cargar_config` leen y escriben los mismos archivos.
- **Efecto:** Si dos operaciones en segundo plano terminan casi a la vez (p. ej. generar reporte y exportar CSV), dos hilos podrían escribir al mismo tiempo.
- **Sugerencia:** Usar un candado (`threading.Lock`) para acceso a historial y a config, o serializar las escrituras en el hilo principal.

### 3.2 Logging no configurado al importar
- **Dónde:** `_configurar_logging()` solo se llama en `main()`.
- **Efecto:** Si se importa el módulo (p. ej. en tests) sin llamar a `main()`, los handlers de `_log` no se añaden.
- **Sugerencia:** Opcional: llamar a `_configurar_logging()` a nivel de módulo al importar, o documentar que el logging solo está activo cuando se ejecuta la aplicación completa.
- **Estado:** Hecho — se llama a `_configurar_logging()` al importar el módulo (idempotente para no duplicar handlers); se eliminó la llamada duplicada en `main()`.

---

## 4. Rutas y seguridad

### 4.1 Rutas de salida (Prioridad: baja)
- **Dónde:** Los reportes/CSV se escriben en `ruta_base` elegida por el usuario.
- **Observación:** El nombre de archivo se construye en código (`nombre_archivo`, `nombre_anio` con `os.path.basename`), no viene de entrada libre, por lo que no se detecta path traversal en el nombre de fichero.
- **Riesgo:** Si el usuario elige una carpeta sensible (p. ej. sistema), la app puede escribir ahí. Es responsabilidad del usuario; en una app de escritorio suele ser aceptable.
- **Sugerencia opcional:** Avisar o bloquear si `ruta_base` es una ruta de sistema conocida (p. ej. `C:\Windows`, `Program Files`).
- **Estado:** Hecho — se añadió `_es_ruta_sistema(ruta)` que detecta Windows (WINDIR, ProgramFiles, ProgramData, raíz de unidad) y Linux/mac (/usr, /etc, etc.); en vista previa, exportar CSV y generar reporte se bloquea la operación y se muestra aviso si la carpeta es de sistema.

### 4.2 Cálculo de profundidad con `ruta_base` con barra final
- **Dónde:** `extraer_facturas`: `depth = root[len(ruta_base):].count(os.sep)`.
- **Observación:** Si `ruta_base` tiene barra final (p. ej. `C:\A\`), la longitud cambia y el cálculo de profundidad puede dar un nivel menos.
- **Sugerencia:** Normalizar: `ruta_base = os.path.normpath(ruta_base.rstrip(os.sep))` al inicio del método (o usar `Path`) y usar esa variable para el `os.walk` y el cálculo de `depth`.

---

## 5. Robustez

### 5.1 `extraer_facturas`: `ValueError` si el base name no está en la ruta
- **Dónde:** Fallback con `idx_base = partes_ruta.index(os.path.basename(ruta_base))`.
- **Observación:** Si por symlinks o rutas raras el base name no está en `partes_ruta`, `index()` lanza `ValueError`. Ya está capturado en `except (IndexError, ValueError)` y se usa un registro con datos por defecto. Correcto.

### 5.2 Escritura de config/historial
- **Dónde:** `_guardar_config` y `guardar_historial` hacen `pass` en el `except` si falla la escritura.
- **Efecto:** El usuario no sabe que la preferencia o el historial no se guardó.
- **Sugerencia:** Al menos registrar el error con `_log.warning(...)` o mostrar un mensaje breve (por ejemplo en la barra de estado) cuando falle el guardado.

---

## 6. Tests

### 6.1 Mock de ttkbootstrap en `conftest.py`
- **Observación:** Si `ttkbootstrap` está instalado, el mock en `sys.modules` no se aplica porque la comprobación es `if "ttkbootstrap" not in sys.modules`. Correcto.
- **Riesgo:** Si algún test importa el módulo principal antes de que se ejecute el conftest, el orden de importación podría afectar. En pytest el conftest se carga antes; no se detecta problema.

### 6.2 Limpieza de `tests/tmp_cotu_test`
- **Dónde:** Test de extracción crea `tests/tmp_cotu_test` y lo borra en un `finally` con `shutil.rmtree(..., ignore_errors=True)`.
- **Observación:** Si el test falla antes del `finally` o hay excepción en el `finally`, la carpeta puede quedar. Está en `.gitignore`; aceptable. Opcional: usar `tmp_path` de pytest cuando el entorno permita escritura en ese directorio.

---

## 7. Resumen de prioridades (plan ejecutado)

| Prioridad | Tema                               | Acción sugerida                          | Estado   |
|----------|-------------------------------------|------------------------------------------|----------|
| Media    | Colores al cambiar tema             | Actualizar `self.colors` en `toggle_tema` | Hecho    |
| Baja     | Color "text" en estado              | Añadir "text" al mapeo en `actualizar_status` | Hecho    |
| Baja     | Clave "danger" en ETH_COLORS        | Definir "danger" (y "text" si aplica)   | Hecho    |
| Baja     | Condición de carrera historial/config | Lock o escrituras en main thread       | Hecho (Lock/RLock) |
| Baja     | Normalizar ruta en extraer_facturas | `normpath` / `rstrip` al inicio          | Hecho    |
| Baja     | Fallos al guardar config/historial  | Log o mensaje al usuario                 | Hecho (_log.warning) |
| Mantenimiento | Imports ( *, typing, timedelta) | Limpiar y ser explícito                  | Hecho    |
| Mantenimiento | Método vacío _configure_ethereal_styles | Eliminar                              | Hecho    |

---

## 8. Aspectos positivos

- Uso de `encoding="utf-8"` en archivos de texto y JSON.
- Manejo de excepciones en carga/guardado de config e historial (evita caídas).
- `extraer_facturas` limitada en profundidad (`max_depth`) y con filtro de `dirs` para reducir trabajo en redes.
- Rutas de salida construidas con `os.path.join` y nombres controlados por el código (sin path traversal en el nombre de fichero).
- Tests unitarios para la lógica de negocio (fechas, duplicados, estadísticas, filtros, extracción).
- Historial acotado a 50 entradas para no crecer sin límite.
