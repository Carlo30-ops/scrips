; ============================================================================
; Inno Setup - Generador de Reportes COTU
; ============================================================================
; Instalador con iconos, documentación y opción de limpieza de datos.
; v2.1.0: Interfaz tipo iOS, tema claro/oscuro, confirmación al sobrescribir
;         Excel/CSV, atajo Ctrl+A (Ajustes), vista previa "100 de N", mensajes
;         de archivo bloqueado para config/historial.
;
; Requisitos (todos en la raíz del proyecto):
;   - dist\GeneradorCOTU.exe  (generar con: crear_instalador.bat)
;   - ICO.ico                 (icono del programa)
;   - installer_wizard_side.bmp  (imagen lateral asistente, ej. 164x314)
;   - installer_wizard_logo.bmp  (logo pequeño asistente, ej. 55x58)
;   - LICENSE, README.md, CHANGELOG.md (opcional)
;
; Preparar y compilar:  preparar_instalador.bat
; Solo compilar:        iscc instalador.iss   o   generar_setup.bat
; Documentación:       docs\INSTALADOR.md
; ============================================================================

#define MyAppName "Generador de Reportes COTU"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "Generador COTU"
#define MyAppExeName "GeneradorCOTU.exe"
#define MyAppURL "https://github.com"
#define MyAppYear "2026"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) {#MyAppYear}
WizardStyle=modern
WizardImageFile=installer_wizard_side.bmp
WizardSmallImageFile=installer_wizard_logo.bmp

DefaultDirName={autopf}\GeneradorCOTU
DefaultGroupName=Generador COTU
DisableProgramGroupPage=yes

OutputDir=dist_installer
OutputBaseFilename=Setup_GeneradorCOTU_{#MyAppVersion}
SetupIconFile=ICO.ico

LicenseFile=LICENSE
InfoBeforeFile=README.md

Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4
WizardSizePercent=100
DisableWelcomePage=no

PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763

UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallFilesDir={app}\uninst

VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Instalador de {#MyAppName} v{#MyAppVersion} - Reportes Excel/CSV, tema claro/oscuro, confirmación al sobrescribir, atajos Ctrl+A/G/H/P
VersionInfoCopyright=Copyright (C) {#MyAppYear}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
spanish.WelcomeLabel1=Bienvenido al Asistente de Instalación de [name]
spanish.WelcomeLabel2=Este programa instalará [name/ver] en su equipo.%n%nGenera reportes Excel y CSV de facturas COTU a partir de carpetas organizadas. Incluye tema claro/oscuro, confirmación al sobrescribir archivos, atajos (Ctrl+A Ajustes, Ctrl+G generar) y vista previa mejorada.%n%nSe recomienda cerrar otras aplicaciones antes de continuar.
spanish.FinishedLabel=La instalación de [name] se ha completado correctamente.%n%nPuede ejecutar la aplicación desde el Menú Inicio o el acceso directo del escritorio.

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "ICO.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\ICO.ico"; Comment: "Generar reportes Excel/CSV de facturas COTU"; WorkingDir: "{app}"
Name: "{group}\Léeme"; Filename: "{app}\README.md"; Comment: "Documentación"
Name: "{group}\Novedades (CHANGELOG)"; Filename: "{app}\CHANGELOG.md"; Comment: "Cambios por versión"
Name: "{group}\Licencia"; Filename: "{app}\LICENSE"; Comment: "Licencia MIT"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"; Comment: "Quitar la aplicación del equipo"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\ICO.ico"; Tasks: desktopicon; Comment: "Generar reportes COTU"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName} ahora"; Flags: nowait postinstall skipifsilent

[Code]
procedure CreateAppDataFolder();
var
  AppDataPath: String;
begin
  AppDataPath := ExpandConstant('{userappdata}\GeneradorCOTU');
  if not DirExists(AppDataPath) then
  begin
    CreateDir(AppDataPath);
    Log('Carpeta de datos creada: ' + AppDataPath);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    CreateAppDataFolder();
end;

function InitializeUninstall(): Boolean;
var
  AppDataPath: String;
  ResultCode: Integer;
begin
  Result := True;
  AppDataPath := ExpandConstant('{userappdata}\GeneradorCOTU');
  if DirExists(AppDataPath) then
  begin
    ResultCode := MsgBox(
      'Se encontraron datos de la aplicación (configuración, historial).'+#13#10+#13#10+
      '¿Desea eliminar también estos datos?'+#13#10+'Carpeta: ' + AppDataPath+#13#10+#13#10+
      'Sí = eliminar todo. No = conservar datos.',
      mbConfirmation, MB_YESNO
    );
    if ResultCode = IDYES then
      DelTree(AppDataPath, True, True, True);
  end;
end;

[UninstallDelete]
Type: dirifempty; Name: "{app}"
