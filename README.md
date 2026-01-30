# Generador de Reportes COTU

Aplicación de escritorio para generar reportes Excel o CSV de facturas COTU por día, semana, mes o año, a partir de una estructura de carpetas. Incluye interfaz tipo iOS (tema claro/oscuro), confirmación al sobrescribir, atajos de teclado y vista previa mejorada.

**Versión:** 2.1.0 — Ver [CHANGELOG.md](CHANGELOG.md) para novedades.

---

## Clonar y ejecutar (GitHub)

```bash
git clone https://github.com/TU_USUARIO/scrips.git
cd scrips
pip install -r requirements.txt
python generador_facturas_cotu.py
```

Sustituye `TU_USUARIO/scrips` por la URL real de tu repositorio (ej. `tu-org/generador-cotu`).

---

## Estructura del proyecto

```
scrips/
├── generador_facturas_cotu.py   # Aplicación principal
├── requirements.txt
├── README.md
├── CHANGELOG.md                 # Historial de cambios por versión
├── LICENSE
├── CONTRIBUTING.md              # Cómo contribuir al proyecto
├── .gitignore
├── .github/                     # Plantillas GitHub (issues, pull requests)
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
│       ├── config.yml
│       ├── bug_report.md
│       └── feature_request.md
├── docs/                        # Documentación
│   ├── ANALISIS_FUSION_PROYECTOS.md
│   ├── AUDITORIA_PROYECTO.md
│   ├── INSTALADOR.md
│   ├── MEJORAS_SUGERIDAS.md
│   └── PLAN_ASPECTO_IOS.md
├── tests/
│   ├── conftest.py
│   ├── test_generador_cotu.py
│   └── __init__.py
├── crear_instalador.bat         # Genera .exe (PyInstaller)
├── preparar_instalador.bat      # Comprueba requisitos y compila instalador
├── generar_setup.bat            # Solo instalador (requiere dist\GeneradorCOTU.exe)
├── generador_facturas_cotu.spec
├── instalador.iss               # Inno Setup
├── ICO.ico
├── installer_wizard_logo.bmp
└── installer_wizard_side.bmp
```

## Requisitos

- Python 3.11 o 3.12
- `pandas`, `openpyxl`, `ttkbootstrap` → `pip install -r requirements.txt`

## Uso

```bash
pip install -r requirements.txt
python generador_facturas_cotu.py
```

## Tests

Los tests no requieren instalar `ttkbootstrap` (se usa un mock si no está disponible). Ejecutar:

```bash
pip install pytest
python -m pytest tests/ -v
```

## Estructura de carpetas esperada

```
AÑO / MES / DÍA / ASEGURADORA / COTUxxxxx
```

Ejemplo: `FACTURACION\2025\12-DICIEMBRE\23 DE DICIEMBRE\SOLIDARIA\COTU74335`

El botón **"Ver estructura de carpetas esperada"** dentro de la app muestra el esquema completo.

## Configuración e historial

- **Configuración** (última carpeta, tema claro/oscuro, formato resumido): se guarda en `config.json` en la misma carpeta que el ejecutable o el script.
- **Historial de reportes**: en Windows se guarda en `%APPDATA%\GeneradorCOTU\historial_reportes.json`. En otros sistemas, en `~/GeneradorCOTU/`. El log de la aplicación está en la misma carpeta: `generador_cotu.log`.

## Crear ejecutable e instalador (Windows)

1. **Ejecutable portable:** ejecutar `crear_instalador.bat` → genera `dist\GeneradorCOTU.exe`. Copiar ese .exe al otro PC.
2. **Instalador (Setup con desinstalador):**
   - **Recomendado:** ejecutar `preparar_instalador.bat` — comprueba que existan todos los archivos necesarios (exe, ICO.ico, imágenes del asistente, LICENSE, README.md) y compila el instalador.
   - **Alternativa:** instalar [Inno Setup](https://jrsoftware.org/isinfo.php) y ejecutar `generar_setup.bat` (requiere tener ya `dist\GeneradorCOTU.exe`).
   - Resultado: `dist_installer\Setup_GeneradorCOTU_2.1.0.exe`.

Recomendación: ejecutar los .bat desde CMD (no desde la terminal del IDE) y, si la carpeta está en OneDrive, pausar la sincronización durante el build. Ver [docs/INSTALADOR.md](docs/INSTALADOR.md) para la guía completa del instalador .iss.

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [CHANGELOG.md](CHANGELOG.md) | Cambios por versión (2.0.0, 2.1.0) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Cómo contribuir al proyecto |
| [docs/INSTALADOR.md](docs/INSTALADOR.md) | Preparar y crear el instalador (.iss) |
| [docs/PLAN_ASPECTO_IOS.md](docs/PLAN_ASPECTO_IOS.md) | Plan para el aspecto tipo iOS |
| [docs/MEJORAS_SUGERIDAS.md](docs/MEJORAS_SUGERIDAS.md) | Mejoras sugeridas |
| [docs/ANALISIS_FUSION_PROYECTOS.md](docs/ANALISIS_FUSION_PROYECTOS.md) | Análisis de fusión de proyectos |
| [docs/AUDITORIA_PROYECTO.md](docs/AUDITORIA_PROYECTO.md) | Auditoría del proyecto |



## Licencia

MIT. Ver [LICENSE](LICENSE).
