# Plan: Aspecto iOS en el Generador de Reportes COTU

Objetivo: acercar la interfaz al aspecto del iOS más reciente — minimalista, limpio, premium, con sensación de “no estorbo, solo ayudo”.

**Estado:** Plan ejecutado (A1–A4, E1–E2, B1–B3, C1–C3, F1–F3, D1, G1–G2). F4 (Messagebox/Toast) y D2 (hover por tarjeta) quedan como limitaciones de ttkbootstrap/ttk.

---

## 1. Objetivo visual (referencia)

| Aspecto | Descripción objetivo |
|--------|------------------------|
| **Estética general** | Minimalismo elegante; todo ligero, sin ruido visual. Capas y profundidad sutil; sombras suaves, desenfoques tipo frosted glass, transparencias. Animaciones fluidas; nada se mueve de golpe. |
| **Materiales (glass/blur)** | Uso de blur dinámico (efecto vidrio). Fondos translúcidos. Menús y tarjetas que “flotan” sobre el fondo. |
| **Tipografía** | San Francisco / Segoe UI. Textos grandes y claros. Jerarquía muy marcada: títulos grandes y seguros; texto secundario más fino y discreto. Mucho espacio en blanco; sensación premium. |
| **Pantalla principal** | Iconos consistentes, suaves. Widgets protagonistas; información clara y rápida. Paleta que se adapta al fondo (modo claro/oscuro bien trabajado). |
| **Listas y menús** | Notificaciones/listas apiladas, redondeadas, limpias. Animaciones suaves. Tipografía grande y legible, sin saturar. Listas claras, iconografía sutil, separaciones limpias. Interruptores con animaciones suaves y colores balanceados. Todo coherente y predecible. |
| **Modo oscuro** | No negro puro; grises profundos. Reduce cansancio. Contraste sin ser agresivo. |
| **Sensación** | Premium, calmado, intuitivo. “No estorbo, solo te ayudo”. |

---

## 2. Limitaciones de tkinter/ttk

| Objetivo iOS | En tkinter/ttk | Conclusión |
|--------------|-----------------|------------|
| Blur / frosted glass real | No hay API de blur; transparencia limitada en widgets. | **Simular** con color “glass” y separadores sutiles. |
| Bordes redondeados nativos | ttk.Frame/Button no tienen border-radius. | **Simular** con más padding y sensación de “caja suave”; o Canvas con formas (coste alto). |
| Sombras reales | No hay drop-shadow en ttk. | **Simular** con línea de 1 px (separador) o color ligeramente más oscuro en “sombra”. |
| Animaciones fluidas | No hay motor de animación. | **Aproximar** con fade de opacidad (root.attributes("-alpha")) y transiciones cortas (after). |
| Tipografía variable / SF | Segoe UI es la más cercana en Windows. | **Usar** Segoe UI en todos los textos; jerarquía por tamaño y peso. |

Por tanto: el plan se centra en **todo lo que sí se puede controlar** (colores, espaciado, tipografía, jerarquía, consistencia) y en **simulaciones razonables** donde no hay equivalente nativo.

---

## 3. Estado actual (ya implementado)

- **Paleta iOS-like:** `ETH_COLORS` light/dark con bg tipo System Gray 6, surface, glass, text, text_sec, accent, border, card_hover. Modo oscuro con grises profundos (no negro puro).
- **Tipografía:** Segoe UI 28pt títulos, 13pt secciones, 11pt cuerpo, 10pt caption; estilos Title.TLabel, Section.TLabel, Caption.TLabel, CardSection.TLabel, CardCaption.TLabel.
- **Espaciado:** Sidebar 280 px, padding 56/28/24; contenido 56 px; tarjetas 28 px; separaciones 32–36 px entre bloques.
- **Separador lateral:** 1 px entre sidebar y contenido, color `border`, actualizado al cambiar tema.
- **Tarjetas:** Card.TFrame con surface, padding 28, hover con card_hover.
- **Navegación:** Nav.TButton con estados active/selected en accent y card_hover.
- **Transición de página:** Fade out/in con alpha.
- **Ventana:** 1120×820, minsize 1000×700.
- **Barra de progreso:** bootstyle success (sin rayas).
- **Tooltips y diálogos:** Segoe UI, fondos suaves, padding aumentado.

---

## 4. Plan de tareas (para acercar al máximo el aspecto)

### Fase A — Refuerzo de lo ya aplicado (prioridad alta)

| # | Tarea | Acción concreta | Criterio de éxito |
|---|--------|------------------|-------------------|
| A1 | Revisar que ningún widget use Arial/Helvetica/Consolas | Buscar y reemplazar por Segoe UI en ventanas secundarias, Treeview, Messagebox si es configurable. | Una sola familia: Segoe UI (o Segoe UI Emoji solo para emojis). |
| A2 | Unificar padding de tarjetas | Todas las Card.TFrame con padding 28; bloques entre tarjetas 32 px. | Misma “respiración” en Reportes, Historial y Ajustes. |
| A3 | Asegurar que el separador sidebar siga al tema | Ya existe `_sidebar_sep` y actualización en `_apply_theme`. Verificar que en toggle_tema se llame _apply_theme. | Al cambiar tema claro/oscuro el separador cambia de color. |
| A4 | Entry y controles de formulario | Mismo tamaño de fuente (12pt) y, si ttkbootstrap lo permite, color de borde/focus suave (accent). | Campos de texto se sienten parte del mismo sistema. |

### Fase B — Simulación “glass” y capas (prioridad media)

| # | Tarea | Acción concreta | Criterio de éxito |
|---|--------|------------------|-------------------|
| B1 | Separadores internos en listas | En Historial y Ajustes, entre secciones, usar un Frame de 1 px de alto con bg=glass (o border). | Secciones claramente separadas sin cajas pesadas. |
| B2 | Refuerzo visual de “tarjeta flotante” | Opcional: envolver cada Card.TFrame en un Frame con 1 px de padding y bg=border, para simular borde muy sutil. | Tarjetas con límite visual suave, sin bordes duros. |
| B3 | Color de fondo del root | Asegurar que la ventana principal use exactamente ETH_COLORS['bg'] (ttkbootstrap puede pintar el root; verificar o forzar vía root.configure(bg=...)). | Fondo uniforme en toda la ventana. |

### Fase C — Tipografía y jerarquía (prioridad media)

| # | Tarea | Acción concreta | Criterio de éxito |
|---|--------|------------------|-------------------|
| C1 | Treeview (Historial) | Aplicar fuente Segoe UI 11 en el Treeview si la plataforma lo permite (opciones de estilo o font en ttk). | Lista de historial con la misma familia que el resto. |
| C2 | Headers de columnas | Mismo estilo que Section o Caption según jerarquía deseada. | Encabezados de tabla alineados con el sistema tipográfico. |
| C3 | Mensajes de estado | Status bar siempre con Caption.TLabel; mensajes de error/éxito con color danger/success pero misma fuente. | Sin fuentes pequeñas o distintas en esquinas. |

### Fase D — Animaciones y micro-interacciones (prioridad baja)

| # | Tarea | Acción concreta | Criterio de éxito |
|---|--------|------------------|-------------------|
| D1 | Suavizar fade de cambio de página | Ajustar pasos y duración del fade (p. ej. 5 pasos de 0.02 en 15 ms). | Transición perceptible pero rápida y fluida. |
| D2 | Hover en tarjetas de tipo | Ya hay cambio global de Card.TFrame; si se puede, aplicar hover solo a la card bajo el cursor (requiere identificar el widget o usar estilos por instancia). | Hover solo en la tarjeta señalada, sin parpadeos. |
| D3 | Botón “Generar” como primario | Mantener bootstyle success y tamaño destacado; evitar que otros botones compitan visualmente. | Un solo CTA claro: “Generar Reporte”. |

### Fase E — Modo oscuro y contraste (prioridad alta)

| # | Tarea | Acción concreta | Criterio de éxito |
|---|--------|------------------|-------------------|
| E1 | Revisar contraste en oscuro | Comprobar que text sobre surface y text_sec sobre bg cumplan contraste legible (WCAG AA si es posible). | Sin texto ilegible en tema oscuro. |
| E2 | Bordes y separadores en oscuro | border y glass deben verse sutiles pero visibles. Ajustar tonos si algo se pierde. | Capas distinguibles también de noche. |

### Fase F — Ventanas secundarias y diálogos (prioridad media)

| # | Tarea | Acción concreta | Criterio de éxito |
|---|--------|------------------|-------------------|
| F1 | Estructura de carpetas | Ventana con Segoe UI 11, padding 16, fondo y color de texto coherentes con el tema actual (si se puede leer tema desde app). | Misma sensación que la ventana principal. |
| F2 | Vista previa (tabla + estadísticas + duplicados) | Títulos con Section/Caption; textos con Segoe UI 10–11; padding uniforme. | Diálogo alineado con el diseño iOS-like. |
| F3 | Diálogo de éxito (Abrir carpeta) | Ya con Segoe UI y más padding; asegurar que el Toplevel tenga fondo bg si es posible. | Coherencia con el resto de la app. |
| F4 | Messagebox / Toast | ttkbootstrap Messagebox y Toast pueden tener estilo propio; documentar si se pueden personalizar (colores, fuentes). | Si es configurable, usar paleta ETH_COLORS y Segoe UI. |

### Fase G — Documentación y mantenimiento (prioridad baja)

| # | Tarea | Acción concreta | Criterio de éxito |
|---|--------|------------------|-------------------|
| G1 | Documentar paleta y estilos | En código o en este doc: tabla ETH_COLORS y cuándo usar cada estilo (Title, Section, Caption, Card*). | Cualquier cambio futuro respeta el sistema. |
| G2 | Checklist visual antes de release | Lista de comprobación: todas las pantallas en claro y oscuro, todas las ventanas secundarias, tooltips, estado y errores. | No se sube versión con incoherencias obvias. |

---

## 5. Orden sugerido de ejecución

1. **A1, A2, A3, A4** — Consolidar lo ya hecho y fuentes/espaciado.
2. **E1, E2** — Asegurar modo oscuro y contraste.
3. **B1, B2, B3** — Refinar capas y sensación “glass”.
4. **C1, C2, C3** — Pulir tipografía en listas y estado.
5. **F1, F2, F3, F4** — Unificar ventanas secundarias y diálogos.
6. **D1, D2, D3** — Mejorar animaciones y hover si el coste es bajo.
7. **G1, G2** — Documentar y definir checklist.

---

## 6. Resumen

- **Ya conseguido:** Paleta iOS, tipografía Segoe UI con jerarquía, espaciado generoso, separador lateral, tarjetas “flotantes”, transición suave, modo oscuro con grises.
- **Próximos pasos:** Eliminar fuentes residuales, reforzar separadores y bordes sutiles, unificar Treeview y diálogos, revisar contraste en oscuro y, si queda tiempo, suavizar animaciones y hover.
- **Límite técnico:** Blur real y bordes redondeados nativos no son viables en ttk; el aspecto se acerca al máximo con color, tipografía, espaciado y transiciones ligeras.

Este plan sirve como hoja de ruta para ir aplicando tareas en el orden indicado y comprobar cada una con su criterio de éxito.

---

## 7. Uso de paleta y estilos (G1)

| Token | Uso |
|-------|-----|
| `bg` | Fondo principal de la ventana y del contenido. |
| `surface` | Tarjetas (Card.TFrame), Treeview, áreas de contenido secundario. |
| `glass` | Separadores internos (1 px), cabeceras de tabla (Treeview.Heading). |
| `text` | Títulos, cuerpo principal, texto sobre surface. |
| `text_sec` | Captions, estado, texto secundario. |
| `accent` | Botón activo en nav, enlaces, selección de card. |
| `border` | Separador lateral sidebar-contenido. |
| `card_hover` | Hover en tarjetas y botones de navegación. |
| `success` / `danger` | Estado, mensajes de éxito/error. |

**Estilos de etiqueta:** `Title.TLabel` (títulos de página), `Section.TLabel` (secciones en contenido), `Caption.TLabel` (pies, estado), `CardSection.TLabel` / `CardCaption.TLabel` (títulos y pies dentro de tarjetas).

---

## 8. Checklist visual antes de release (G2)

- [ ] **Modo claro:** Ventana principal, Reportes, Historial, Ajustes; fondo uniforme, tarjetas visibles, texto legible.
- [ ] **Modo oscuro:** Misma revisión; contraste suficiente, separadores visibles.
- [ ] **Ventanas secundarias:** Estructura de carpetas, Vista previa, Diálogo de éxito; fondo y texto coherentes con el tema.
- [ ] **Tooltips:** Apariencia suave, Segoe UI.
- [ ] **Estado y errores:** Barra de estado y mensajes con colores success/danger y misma familia tipográfica.
- [ ] **Transición de página:** Fade suave al cambiar de Reportes/Historial/Ajustes.
- [ ] **Treeview:** Fuente Segoe UI 11, encabezados alineados al sistema.
