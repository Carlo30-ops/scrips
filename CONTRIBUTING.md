# Cómo contribuir al Generador de Reportes COTU

Gracias por tu interés en contribuir. Estas son unas pautas sencillas para mantener el proyecto ordenado.

## Antes de enviar cambios

1. **Clona el repositorio** y crea una rama para tu cambio:
   ```bash
   git checkout -b mi-mejora
   ```

2. **Instala dependencias** y ejecuta los tests:
   ```bash
   pip install -r requirements.txt
   pip install pytest
   python -m pytest tests/ -v
   ```

3. **Mantén el estilo** del código existente (PEP 8, type hints donde aplique, docstrings en funciones públicas).

## Qué puedes hacer

- **Correcciones de errores:** abre un *issue* describiendo el fallo y, si puedes, envía un *pull request* con la corrección.
- **Mejoras o nuevas funciones:** comenta primero en un *issue* o en una *discussion* para alinear la idea con el proyecto.
- **Documentación:** mejoras en README, docs o comentarios en el código son bienvenidas.

## Pull requests

- Describe qué cambia y por qué.
- Asegúrate de que los tests pasen (`python -m pytest tests/ -v`).
- Si añades lógica nueva, incluye tests en `tests/` cuando sea posible.

## Estructura del proyecto

- **`generador_facturas_cotu.py`** — Aplicación principal (GUI y lógica).
- **`tests/`** — Tests unitarios (pytest).
- **`docs/`** — Documentación técnica y planes.

## Dudas

Si tienes dudas, abre un *issue* con la etiqueta que corresponda (bug, mejora, documentación, etc.).

Licencia: MIT. Al contribuir, aceptas que tus aportaciones se distribuyan bajo la misma licencia.
