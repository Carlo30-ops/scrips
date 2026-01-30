# Changelog

Todos los cambios notables del proyecto se documentan aquí.

## [2.1.0] – 2025-01

### Añadido
- Interfaz con aspecto tipo iOS: paleta de grises suaves, tipografía Segoe UI, espaciado amplio, tarjetas y separadores coherentes con el tema.
- Modo oscuro: tema "darkly" con grises profundos (no negro puro), tooltips y ventanas secundarias adaptadas al tema.
- Versión visible en el título de la ventana (ej. "Generador COTU 2.1.0").
- Confirmación antes de sobrescribir: si el Excel o CSV de salida ya existe, se pregunta "¿Deseas sobrescribirlo?" antes de continuar.
- Atajo de teclado Ctrl+A para ir a Ajustes; tooltip del botón Ajustes indica Ctrl+A y se adapta al tema (fondo y texto según modo claro/oscuro).
- Vista previa de facturas: texto "Mostrando hasta 100 de N facturas" cuando hay más de 100; ventana redimensionable.
- Bloqueo de carpetas de sistema: no se permite generar reportes en WINDIR, ProgramFiles, etc.; mensaje claro al usuario.
- Logging configurado al importar el módulo; guardado de historial y configuración con locks y mensajes de advertencia si falla el guardado.
- CHANGELOG y sección en README sobre ubicación de config e historial.

### Cambiado
- Paleta de colores unificada (`ETH_COLORS`) para fondo, superficies, texto y bordes en tema claro y oscuro.
- Transición de cambio de página más suave (fade por pasos).
- Barra de progreso con estilo success (sin rayas).

### Documentación
- Plan de aspecto iOS en `docs/PLAN_ASPECTO_IOS.md`.
- Guía del instalador en `docs/INSTALADOR.md`.
- README actualizado con estructura del proyecto, tests y ubicación de configuración e historial.

---

## [2.0.0]

### Añadido
- Aplicación unificada para reportes diarios, semanales, mensuales y anuales.
- Navegación por páginas: Reportes, Historial, Ajustes (ttkbootstrap).
- Exportación a Excel (openpyxl/xlsxwriter) y CSV.
- Vista previa de facturas antes de generar.
- Historial de reportes guardado en disco.
- Configuración persistente: última carpeta, tema claro/oscuro, formato resumido.
- Atajos: Ctrl+O (carpeta), Ctrl+G (generar), Ctrl+P (vista previa), Ctrl+H (historial).

---

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).
