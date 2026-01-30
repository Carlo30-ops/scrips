# Análisis: Cómo combinar lo mejor del proyecto actual y scrips-main

Este documento resume las fortalezas de cada versión del **Generador de Reportes COTU** y propone una estrategia para fusionarlas en un único proyecto unificado.

---

## 1. Resumen por proyecto

### Proyecto actual (raíz del workspace)

| Aspecto | Descripción |
|--------|-------------|
| **UI** | tkinter estándar (`tk` + `ttk`), sin dependencias extra de interfaz |
| **Tamaño** | Más ligero: solo `pandas` y `openpyxl` |
| **Instalador** | Inno Setup básico pero funcional |
| **Build** | PyInstaller sin ttkbootstrap → .exe más pequeño |
| **Portabilidad** | Menor superficie de fallos: menos librerías, menos incompatibilidades |

**Puntos fuertes:**
- Cero dependencias de UI adicionales → **ideal para entornos restrictivos o PCs lentos**
- Calendario propio (sin `DateEntry`) → funciona en cualquier Python con tkinter
- Mensajes con `messagebox` estándar → sin depender de ttkbootstrap
- Diálogo de éxito con botón "Abrir carpeta" bien integrado
- Atajos de teclado (Ctrl+O, Ctrl+G, Ctrl+P, Ctrl+H) documentados en tooltips
- Historial como ventana emergente (simple y claro)
- `crear_instalador.bat` / `generar_setup.bat` y `instalador.iss` listos para generar .exe e instalador

---

### Proyecto scrips-main

| Aspecto | Descripción |
|--------|-------------|
| **UI** | ttkbootstrap (temas modernos, estilo "Ethereal") |
| **Tamaño** | Incluye `ttkbootstrap` → más pesado |
| **Instalador** | Inno Setup avanzado (iconos, README, LICENSE, imágenes del asistente) |
| **Build** | PyInstaller con hooks de ttkbootstrap |

**Puntos fuertes:**
- Interfaz moderna: sidebar, páginas (Reportes / Historial / Configuración), cards para tipo de reporte
- `DateEntry` de ttkbootstrap para elegir fechas con calendario integrado
- Vista previa en segundo plano (thread) + estadísticas por aseguradora y detección de duplicados
- Constantes de columnas (`COL_ANIO`, `COL_MES`, etc.) y tipos (`TIPO_ANIO`, etc.) → código más mantenible
- Optimización en `extraer_facturas`: límite de profundidad, filtrar `dirs` antes de recorrer, feedback de progreso
- Toast notifications y `Messagebox` de ttkbootstrap para mejor UX
- Historial integrado en una página (no ventana emergente) y botón "Actualizar lista"
- Página de configuración dedicada (formato resumido, solo COTU, tema, estructura de carpetas)
- Recursos de instalador: `ICO.ico`, `installer_wizard_side.bmp`, `installer_wizard_logo.bmp`
- Detección de duplicados en vista previa y aviso al generar reporte

---

## 2. Qué tomar de cada uno

### Del proyecto actual (mantener o recuperar)

1. **Opcional: modo "clásico" sin ttkbootstrap**  
   - Si se prioriza un solo .exe ligero y compatible con todo, se puede mantener una variante que use solo `tk`/`ttk` (como el proyecto actual) y otra "full" con ttkbootstrap.

2. **Calendario manual**  
   - Si se usa ttkbootstrap, seguir usando `DateEntry`; si se hace versión sin ttkbootstrap, reutilizar el calendario del proyecto actual (`abrir_calendario`, `dibujar_calendario`, etc.).

3. **Comportamiento de mensajes y éxito**  
   - Mantener el diálogo de éxito con "Abrir carpeta" (ya está en ambos; en scrips-main se complementa con Toast).

4. **Atajos y tooltips**  
   - Asegurar que Ctrl+O, Ctrl+G, Ctrl+P, Ctrl+H y los tooltips del proyecto actual sigan presentes en la versión unificada.

5. **Build e instalador base**  
   - Mantener `crear_instalador.bat`, `generar_setup.bat` y un `instalador.iss` que funcionen con el .exe generado (como en el proyecto actual).

### De scrips-main (incorporar en la versión unificada)

1. **Constantes y tipos**  
   - `TIPO_ANIO`, `TIPO_MES`, `TIPO_SEMANA`, `TIPO_DIA` y `COL_ANIO`, `COL_MES`, `COL_FECHA`, `COL_FACTURA`, `COL_DETALLE`, `COL_COMPANIA` en un solo lugar (clase o módulo).

2. **Lógica de negocio mejorada**  
   - `extraer_facturas` con límite de profundidad, filtrado de `dirs` y actualización de estado "Escaneando...".
   - `verificar_duplicados` y `calcular_estadisticas` para vista previa y aviso post-generación.

3. **Vista previa en segundo plano**  
   - Ejecutar la extracción en un thread y mostrar resultados cuando termine (evitar bloquear la UI en carpetas grandes).

4. **Vista previa enriquecida**  
   - Panel de "Resumen por Aseguradora" y panel de "Posibles Duplicados" en la ventana de vista previa.

5. **Estructura de UI moderna (si se usa ttkbootstrap)**  
   - Sidebar + páginas (Reportes, Historial, Configuración), cards para tipo de reporte, página de configuración con toggles y tema.

6. **Instalador enriquecido**  
   - Uso de `ICO.ico`, imágenes del asistente (`installer_wizard_side.bmp`, `installer_wizard_logo.bmp`), `LicenseFile=LICENSE`, `InfoBeforeFile=README.md`, y opciones de compresión/versión como en scrips-main.

7. **Notificaciones**  
   - Toast al exportar CSV y al generar reporte (manteniendo también el diálogo de éxito con "Abrir carpeta").

8. **Historial integrado**  
   - Opción de tener historial como página (como en scrips-main) además de, o en lugar de, ventana emergente, y botón "Actualizar lista".

---

## 3. Estrategia de fusión recomendada

### Opción A: Un solo código con ttkbootstrap (recomendada si no importa el tamaño del .exe)

- **Base:** código de **scrips-main** (UI moderna, constantes, optimizaciones, duplicados, estadísticas).
- **Añadir o revisar:**
  - Tooltips en todos los botones principales (como en el proyecto actual).
  - Atajos Ctrl+O, Ctrl+G, Ctrl+P, Ctrl+H bien documentados y consistentes.
  - Diálogo de éxito con "Abrir carpeta" (ya está; asegurar que no se pierda).
- **Build e instalador:**
  - Usar `generador_facturas_cotu.spec` y `instalador.iss` de scrips-main (con ttkbootstrap e iconos/imágenes).
  - Copiar al proyecto unificado: `ICO.ico`, `installer_wizard_side.bmp`, `installer_wizard_logo.bmp`.
  - Mantener `crear_instalador.bat` y `generar_setup.bat` del proyecto actual, ajustando rutas si hace falta (por ejemplo que apunten a `dist\GeneradorCOTU.exe`).

Resultado: una sola aplicación "full" con mejor UX y mejor lógica, y un instalador profesional.

### Opción B: Dos variantes (ligera + full)

- **Variante "clásica" (sin ttkbootstrap):**  
  - Base: proyecto actual.  
  - Incorporar solo mejoras de lógica y datos de scrips-main: constantes, `extraer_facturas` optimizada, `verificar_duplicados`, `calcular_estadisticas`, vista previa en thread y paneles de estadísticas/duplicados (usando tk/ttk para los widgets extra).  
  - Calendario: mantener el del proyecto actual.  
  - Build: `generador_facturas_cotu.spec` del proyecto actual (sin ttkbootstrap).

- **Variante "Ethereal" (con ttkbootstrap):**  
  - Como en Opción A, con UI moderna, DateEntry, Toast, etc.

Se mantendrían dos puntos de entrada (por ejemplo `generador_facturas_cotu.py` y `generador_facturas_cotu_ethereal.py`) o un único script que detecte si ttkbootstrap está instalado y elija UI.

---

## 4. Checklist de fusión (Opción A)

- [ ] Partir del `generador_facturas_cotu.py` de **scrips-main** como base.
- [ ] Añadir/verificar tooltips en botones principales (Vista Previa, Generar, Historial, Tema/Config).
- [ ] Verificar atajos Ctrl+O, Ctrl+G, Ctrl+P, Ctrl+H y que el atajo de historial abra la página correcta.
- [ ] Unificar `requirements.txt`: `pandas`, `openpyxl`, `ttkbootstrap`.
- [ ] Usar `generador_facturas_cotu.spec` de scrips-main (con `collect_all('ttkbootstrap')`) y comprobar que el .exe arranca.
- [ ] Copiar al proyecto unificado: `ICO.ico`, `installer_wizard_side.bmp`, `installer_wizard_logo.bmp`.
- [ ] Usar `instalador.iss` de scrips-main; ajustar si hace falta la ruta de `dist\GeneradorCOTU.exe` para que coincida con lo que genera `crear_instalador.bat`.
- [ ] Dejar un único `README.md` que indique requisitos (Python 3.11+, pandas, openpyxl, ttkbootstrap) y los pasos para ejecutable e instalador (como en el proyecto actual).
- [ ] Probar: ejecución con `python generador_facturas_cotu.py`, generación de .exe, instalador y desinstalación.

---

## 5. Conclusión

- **Proyecto actual** aporta simplicidad, pocas dependencias, build ligero y flujo de instalador probado.
- **scrips-main** aporta UI moderna, mejor estructura de código, optimizaciones, detección de duplicados y estadísticas, e instalador más completo.

La fusión recomendada es **tomar scrips-main como base** (Opción A), asegurando que no se pierdan los detalles del proyecto actual (tooltips, atajos, diálogo de éxito) y usando los recursos e instalador de scrips-main. Si se necesita una variante mínima sin ttkbootstrap, se puede seguir la Opción B y extraer la lógica común a un módulo compartido para no duplicar código de extracción, filtros y duplicados.
