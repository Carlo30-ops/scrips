@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo.
echo ============================================
echo   Preparar y crear instalador .iss
echo ============================================
echo.

set ERR=0

:: 1) Script Inno Setup
if not exist "instalador.iss" (
    echo [ERROR] No se encuentra instalador.iss
    set ERR=1
) else (
    echo [OK] instalador.iss
)

:: 2) Ejecutable (generado por crear_instalador.bat)
if not exist "dist\GeneradorCOTU.exe" (
    echo [FALTA] dist\GeneradorCOTU.exe
    echo         Ejecuta antes: crear_instalador.bat
    set ERR=1
) else (
    echo [OK] dist\GeneradorCOTU.exe
)

:: 3) Recursos del instalador
if not exist "ICO.ico" (
    echo [FALTA] ICO.ico
    set ERR=1
) else (
    echo [OK] ICO.ico
)
if not exist "installer_wizard_side.bmp" (
    echo [FALTA] installer_wizard_side.bmp
    set ERR=1
) else (
    echo [OK] installer_wizard_side.bmp
)
if not exist "installer_wizard_logo.bmp" (
    echo [FALTA] installer_wizard_logo.bmp
    set ERR=1
) else (
    echo [OK] installer_wizard_logo.bmp
)
if not exist "LICENSE" (
    echo [FALTA] LICENSE
    set ERR=1
) else (
    echo [OK] LICENSE
)
if not exist "README.md" (
    echo [FALTA] README.md
    set ERR=1
) else (
    echo [OK] README.md
)

echo.

if %ERR% neq 0 (
    echo Corrige los archivos faltantes y vuelve a ejecutar este script.
    echo Ver: docs\INSTALADOR.md
    pause
    exit /b 1
)

:: Inno Setup en PATH
where iscc >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Inno Setup no esta en el PATH.
    echo         Instala desde https://jrsoftware.org/isinfo.php
    echo         y marca "Add Inno Setup to PATH".
    pause
    exit /b 1
)

echo Compilando instalador con Inno Setup...
echo.
iscc instalador.iss
if errorlevel 1 (
    echo [ERROR] Fallo la compilacion del instalador.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Listo. Instalador generado en:
echo   dist_installer\Setup_GeneradorCOTU_*.exe
echo ============================================
echo.
start "" "dist_installer"
pause
