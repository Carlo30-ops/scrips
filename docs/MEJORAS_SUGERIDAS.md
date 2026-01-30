# Mejoras sugeridas – Generador de Reportes COTU

Propuestas ordenadas por área y por esfuerzo (rápido / medio / mayor).

---

## 1. Experiencia de usuario (UX)

| Mejora | Descripción | Esfuerzo |
|--------|-------------|----------|
| **Recordar última carpeta en el diálogo** | El diálogo "Examinar" ya usa `initialdir` con la última carpeta; asegurar que siempre se guarde bien y que, al abrir la app por primera vez, no falle si no hay carpeta. | Bajo |
| **Confirmación antes de sobrescribir** | Si el Excel/CSV a generar ya existe, preguntar "El archivo X ya existe. ¿Sobrescribir?" en lugar de sobrescribir directamente. | Bajo |
| **Atajo para Ajustes** | Añadir Ctrl+A (o otro) para ir a Ajustes, documentado en tooltip del botón. | Bajo |
| **Indicador de carpeta válida** | Mostrar un ✓ o indicador sutil junto a la ruta cuando la carpeta existe y tiene estructura reconocible (opcional: escaneo ligero). | Medio |
| **Progreso en extracción larga** | En carpetas muy grandes, ya se actualiza "Escaneando... N carpetas"; opcional: barra de progreso determinada si se puede estimar el total. | Medio |
| **Exportar historial** | Botón "Exportar historial" en la página Historial que guarde la lista actual en CSV para auditoría o respaldo. | Medio |

---

## 2. Interfaz (UI)

| Mejora | Descripción | Esfuerzo |
|--------|-------------|----------|
| **Hover por tarjeta (D2 pendiente)** | Hover solo en la tarjeta bajo el cursor, sin afectar al resto (requiere estilos por instancia o Canvas). | Medio |
| **Tooltip en tema oscuro** | Hacer el tooltip sensible al tema: fondo oscuro y texto claro cuando la app está en modo oscuro. | Bajo |
| **Accesibilidad** | Revisar contraste (WCAG AA) en todos los textos; asegurar que los controles tengan tamaño mínimo táctil/clickeable. | Bajo |
| **Ventana de vista previa redimensionable** | Permitir redimensionar la ventana de vista previa y que la tabla se adapte. | Bajo |
| **Orden de columnas en historial** | Permitir ordenar la tabla de historial por fecha, tipo o facturas (click en cabecera). | Medio |

---

## 3. Código y mantenimiento

| Mejora | Descripción | Esfuerzo |
|--------|-------------|----------|
| **Extraer lógica a módulo** | Mover `extraer_facturas`, `verificar_duplicados`, `calcular_estadisticas`, `filtrar_por_tipo`, `validar_fecha` a un módulo `cotu_logic.py` para facilitar tests y reutilización. | Medio |
| **Constantes en un solo lugar** | Centralizar rutas de archivos (config, historial, log), nombres de estilos y mensajes en constantes o un pequeño módulo `constants.py`. | Bajo |
| **Type hints completos** | Añadir type hints en las firmas que faltan (retornos, variables clave) para mejor IDE y documentación. | Bajo |
| **Logging por niveles** | Usar `_log.debug()` en flujos detallados y mantener `_log.info`/`warning`/`error`; opcional: nivel configurable desde config.json. | Bajo |
| **Tests con tmp_path (6.2)** | Usar `tmp_path` de pytest para el test de extracción en lugar de `tests/tmp_cotu_test`, si el entorno lo permite. | Bajo |

---

## 4. Tests

| Mejora | Descripción | Esfuerzo |
|--------|-------------|----------|
| **Tests de integración** | Un test que ejecute "generar reporte" con una carpeta temporal mínima y compruebe que se crea el Excel esperado. | Medio |
| **Tests de _es_ruta_sistema** | Añadir tests para `_es_ruta_sistema` (Windows: WINDIR, ProgramFiles; no sistema: carpeta usuario). | Bajo |
| **Tests de UI mínimos** | Opcional: test que cree la ventana, cambie de página y cambie tema sin fallar (smoke test). | Medio |
| **Cobertura** | Ejecutar `pytest --cov` y revisar líneas no cubiertas (sobre todo ramas de error y guardado). | Bajo |

---

## 5. Rendimiento y robustez

| Mejora | Descripción | Esfuerzo |
|--------|-------------|----------|
| **Cancelar extracción** | Si la extracción es muy larga, permitir un botón "Cancelar" que detenga el hilo de forma segura (bandera + comprobación periódica). | Medio |
| **Límite de registros en vista previa** | Ya se limita a 100 en la vista previa; documentar en UI "Mostrando hasta 100 de N" si N > 100. | Bajo |
| **Manejo de archivos bloqueados** | Si el Excel/CSV está abierto en otro programa, el guardado falla; mostrar mensaje claro "Cierre el archivo en Excel/editor e intente de nuevo". | Bajo |
| **Reintento en guardado** | En `guardar_historial` y `_guardar_config`, opcional: reintentar 1–2 veces con pequeño delay si falla por acceso. | Bajo |

---

## 6. Documentación y despliegue

| Mejora | Descripción | Esfuerzo |
|--------|-------------|----------|
| **Changelog** | Mantener un `CHANGELOG.md` con versiones 2.0.0, 2.1.0 y cambios (interfaz iOS, tema oscuro, etc.). | Bajo |
| **Versión en la app** | Mostrar la versión (ej. 2.1.0) en Ajustes o en el título de la ventana para que el usuario sepa qué tiene instalado. | Bajo |
| **README: capturas** | Añadir 1–2 capturas de pantalla (tema claro y oscuro) al README. | Bajo |
| **Instalador: desinstalador silencioso** | Opcional: parámetro para desinstalar en modo silencioso (para actualizaciones automáticas o scripts). | Medio |

---

## 7. Seguridad y privacidad

| Mejora | Descripción | Esfuerzo |
|--------|-------------|----------|
| **Rutas en log** | Evitar loguear rutas completas de usuario en producción; usar rutas relativas o ofuscar. | Bajo |
| **Config e historial en AppData** | Ya se usa APPDATA/GeneradorCOTU; documentar en README dónde se guardan config e historial. | Bajo |

---

## 8. Resumen por prioridad

- **Rápido y útil:** Confirmación antes de sobrescribir, tooltip en tema oscuro, versión en la app, CHANGELOG, tests de `_es_ruta_sistema`, documentar ubicación de config/historial.
- **Medio esfuerzo, alto impacto:** Extraer lógica a módulo, tests de integración, cancelar extracción, exportar historial.
- **Opcional / largo plazo:** Hover por tarjeta, ordenar columnas en historial, barra de progreso determinada, desinstalador silencioso.

Si quieres, se puede bajar a tareas concretas (por ejemplo solo "confirmación al sobrescribir" y "versión en la app") y aplicarlas en el código paso a paso.
