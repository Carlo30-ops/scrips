# Preparar y crear el instalador (.iss)

Guía para generar el instalador de **Generador de Reportes COTU** con Inno Setup.

---

## Requisitos previos

1. **Python 3.11 o 3.12** en el PATH.
2. **Inno Setup 6** instalado y añadido al PATH:  
   [https://jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php)  
   Durante la instalación, marcar **"Add Inno Setup to PATH"**.

---

## Archivos que debe tener el proyecto (en la raíz)

| Archivo | Uso en el instalador |
|---------|----------------------|
| `instalador.iss` | Script de Inno Setup (compilar con `iscc`) |
| `ICO.ico` | Icono del programa y del instalador |
| `installer_wizard_side.bmp` | Imagen lateral del asistente (164×314 px recomendado) |
| `installer_wizard_logo.bmp` | Logo pequeño del asistente (55×58 px recomendado) |
| `LICENSE` | Licencia mostrada durante la instalación |
| `README.md` | Texto "Antes de instalar" en el asistente |
| `dist\GeneradorCOTU.exe` | Ejecutable (se genera con `crear_instalador.bat`) |

Si falta `ICO.ico` o los `.bmp`, el instalador puede compilar pero sin iconos/imágenes en el asistente.

---

## Pasos para crear el instalador

### 1. Generar el ejecutable

Desde la raíz del proyecto (donde está `instalador.iss`):

```batch
crear_instalador.bat
```

Esto instala dependencias, PyInstaller y genera `dist\GeneradorCOTU.exe`.  
Si ya tienes el .exe, puedes saltar al paso 2.

### 2. Compilar el instalador con Inno Setup

Opción A — Script recomendado (comprueba que todo exista y luego compila):

```batch
preparar_instalador.bat
```

Opción B — Solo compilar (si ya sabes que `dist\GeneradorCOTU.exe` existe):

```batch
generar_setup.bat
```

Opción C — Línea de comandos directa:

```batch
iscc instalador.iss
```

### 3. Resultado

El instalador se genera en:

```
dist_installer\Setup_GeneradorCOTU_2.1.0.exe
```

(La versión en el nombre viene de `MyAppVersion` en `instalador.iss`.)

---

## Resumen rápido

1. Ejecutar `crear_instalador.bat` → genera `dist\GeneradorCOTU.exe`.
2. Tener en la raíz: `ICO.ico`, `installer_wizard_side.bmp`, `installer_wizard_logo.bmp`, `LICENSE`, `README.md`.
3. Ejecutar `preparar_instalador.bat` o `generar_setup.bat` → genera `dist_installer\Setup_GeneradorCOTU_2.1.0.exe`.

---

## Cambiar la versión del instalador

Editar `instalador.iss` y modificar:

```iss
#define MyAppVersion "2.1.0"
```

Luego volver a compilar con `iscc instalador.iss` o `preparar_instalador.bat`.
