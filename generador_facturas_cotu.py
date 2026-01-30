"""
Generador de Reportes de Facturas COTU
Aplicación unificada para generar reportes diarios, semanales, mensuales y anuales
"""

__version__ = "2.1.0"

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as tk_messagebox
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets import ToastNotification
import os
import sys
import subprocess
import threading
import pandas as pd
from datetime import datetime
from pathlib import Path
import re
import json
import logging
from typing import List, Dict, Optional, Any

_log = logging.getLogger("GeneradorCOTU")


def _configurar_logging():
    """Configura logging a consola y, si es posible, a archivo en APPDATA/GeneradorCOTU."""
    if any(isinstance(h, logging.FileHandler) for h in _log.handlers):
        return
    _log.setLevel(logging.INFO)
    try:
        log_dir = os.path.join(
            os.environ.get("APPDATA") or os.environ.get("HOME") or os.path.dirname(os.path.abspath(__file__)),
            "GeneradorCOTU",
        )
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "generador_cotu.log")
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        _log.addHandler(fh)
    except OSError:
        pass


def _es_ruta_sistema(ruta: str) -> bool:
    """Devuelve True si la ruta es o está dentro de una carpeta de sistema (evitar escritura ahí)."""
    if not ruta or not os.path.isabs(ruta):
        return False
    ruta_norm = os.path.normpath(os.path.abspath(ruta))
    if sys.platform == "win32":
        carpetas_sistema = []
        for env in ("WINDIR", "ProgramFiles", "ProgramFiles(x86)", "ProgramData"):
            v = os.environ.get(env)
            if v:
                carpetas_sistema.append(os.path.normpath(v))
        for c in carpetas_sistema:
            if ruta_norm == c or ruta_norm.startswith(c + os.sep):
                return True
        # Raíz de unidad (C:\, D:\, etc.)
        if len(ruta_norm) <= 3 and ruta_norm[1:2] == ":":
            return True
    else:
        carpetas_sistema = ["/", "/usr", "/etc", "/bin", "/sbin", "/sys", "/proc", "/var"]
        for c in carpetas_sistema:
            if ruta_norm == c or ruta_norm.startswith(c + "/"):
                return True
    return False


_configurar_logging()


def _tooltip(widget, texto, get_colors=None):
    """Tooltip minimalista. Si get_colors es un callable que devuelve dict con 'bg' y 'text', el tooltip usa esos colores (tema oscuro/claro)."""
    tip = [None]
    def _show(_e):
        if tip[0]:
            return
        x = widget.winfo_rootx() + 12
        y = widget.winfo_rooty() + widget.winfo_height() + 4
        tip[0] = tw = tk.Toplevel(widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        bg, fg = "#F5F5F7", "#1C1C1E"
        if get_colors:
            try:
                c = get_colors()
                if isinstance(c, dict):
                    bg = c.get("bg", bg)
                    fg = c.get("text", fg)
            except Exception:
                pass
        tk.Label(
            tw, text=texto, justify=tk.LEFT,
            background=bg, foreground=fg,
            relief=tk.FLAT, padx=10, pady=6,
            font=("Segoe UI", 10)
        ).pack()
    def _hide(_e):
        if tip[0]:
            tip[0].destroy()
            tip[0] = None
    widget.bind("<Enter>", _show)
    widget.bind("<Leave>", _hide)



class GeneradorFacturasCOTU:
    # --- iOS-inspired Design System ---
    # Minimalismo elegante, capas sutiles, tipografía clara, modo oscuro con grises profundos (no negro puro)
    ETH_COLORS = {
        "light": {
            "bg": "#F2F2F7",           # System Gray 6 - fondo suave
            "surface": "#FFFFFF",      # Tarjetas que "flotan"
            "glass": "#E5E5EA",         # Separadores / bordes muy suaves
            "text": "#1C1C1E",          # Títulos - grande y seguro
            "text_sec": "#8E8E93",      # Secundario - fino y discreto
            "accent": "#007AFF",        # Azul sistema iOS
            "border": "#C6C6C8",        # Bordes limpios
            "success": "#34C759",
            "danger": "#FF3B30",
            "card_hover": "#F5F5F7",    # Hover sutil
        },
        "dark": {
            "bg": "#1C1C1E",            # Gris profundo (no negro puro) - reduce cansancio
            "surface": "#2C2C2E",       # Tarjetas
            "glass": "#3A3A3C",         # Separadores
            "text": "#F5F5F7",
            "text_sec": "#98989D",
            "accent": "#0A84FF",
            "border": "#38383A",
            "success": "#30D158",
            "danger": "#FF453A",
            "card_hover": "#3A3A3C",
        }
    }

    # Constantes Lógicas
    TIPO_ANIO = "Año"
    TIPO_MES = "Mes"
    TIPO_SEMANA = "Semana"
    TIPO_DIA = "Día"
    
    COL_ANIO = "AÑO"
    COL_MES = "MES"
    COL_FECHA = "FECHA DE LA FACTURA"
    COL_FACTURA = "N° FACTURA"
    COL_DETALLE = "DETALLE COMPLETO"
    COL_COMPANIA = "COMPAÑÍA"

    def __init__(self, root: ttk.Window):
        self.root = root
        self.root.title(f"Generador COTU {__version__}")
        self.root.geometry("1120x820")
        self.root.minsize(1000, 700)
        self.root.place_window_center()
        
        # -- Config Básica --
        self.tema_oscuro = False
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(script_dir, "config.json")
        appdata = os.environ.get("APPDATA") or os.environ.get("HOME") or script_dir
        self._historial_dir = os.path.join(appdata, "GeneradorCOTU")
        os.makedirs(self._historial_dir, exist_ok=True)
        self.historial_file = os.path.join(self._historial_dir, "historial_reportes.json")
        self._lock_config = threading.Lock()
        self._lock_historial = threading.RLock()  # RLock: guardar_historial llama a cargar_historial con lock ya tomado
        
        self._cargar_config()
        
        # -- Estilo Ethereal --
        self.colors = self.ETH_COLORS["dark"] if self.tema_oscuro else self.ETH_COLORS["light"]
        
        # Estilo - ttkbootstrap ya maneja el tema en el main()
        # self.setup_styles() # Eliminado, usaremos bootstyle

        
        # Variables
        self.ruta_base = tk.StringVar(value=getattr(self, "_ultima_carpeta", "") or "")
        self.tipo_reporte = tk.StringVar(value=self.TIPO_ANIO)
        self.fecha_inicio = tk.StringVar()
        self.fecha_fin = tk.StringVar()
        self.formato_resumido = tk.BooleanVar(value=getattr(self, "_formato_resumido", False))
        self.solo_carpetas_cotu = tk.BooleanVar(value=getattr(self, "_solo_carpetas_cotu", True))
        
        # Variables para vista previa
        self.registros_preview = []
        
        # Atributos del calendario (se usan al abrir el selector de fecha)
        self.cal_anio = datetime.now().year
        self.cal_mes = datetime.now().month
        self.mes_label = None
        self.dias_frame = None
        

        
        # Diccionario para guardar las páginas (frames)
        self.pages = {}
        self.nav_buttons = {}
        
        # Inicializar UI
        self.setup_main_layout()
        self.show_page("reportes")
        
        # Aplicar Tema Global
        self._apply_theme()

    def _apply_theme(self):
        """Aplica tema iOS-inspired: tipografía clara, jerarquía marcada, mucho espacio en blanco"""
        theme = 'darkly' if self.tema_oscuro else 'flatly'
        self.style.theme_use(theme)
        c = self.colors
        # Base - cuerpo 11pt, sensación premium
        self.style.configure('.', background=c['bg'], foreground=c['text'], font=("Segoe UI", 11))
        self.style.configure('TFrame', background=c['bg'])
        self.style.configure('TLabel', background=c['bg'], foreground=c['text'], font=("Segoe UI", 11))
        self.style.configure('TButton', font=("Segoe UI", 11))
        self.style.configure('TRadiobutton', background=c['bg'], foreground=c['text'], font=("Segoe UI", 11))
        self.style.configure('TCheckbutton', background=c['bg'], foreground=c['text'], font=("Segoe UI", 11))
        # Tarjetas tipo "flotantes" - superficie clara, separación visual
        self.style.configure('Card.TFrame', background=c['surface'], relief="flat")
        self.style.configure('Sidebar.TFrame', background=c['surface'])
        # Sidebar: título grande y seguro
        self.style.configure('Sidebar.TLabel', background=c['surface'], foreground=c['text'], font=("Segoe UI", 18, "bold"))
        # Títulos de página - grandes, jerarquía muy marcada
        self.style.configure('Title.TLabel', font=("Segoe UI", 28, "bold"), foreground=c['text'])
        self.style.configure('Section.TLabel', font=("Segoe UI", 13, "bold"), foreground=c['text'])
        self.style.configure('Caption.TLabel', font=("Segoe UI", 10), foreground=c['text_sec'])
        # Etiquetas sobre tarjetas (fondo surface para que no se parchee)
        self.style.configure('CardSection.TLabel', background=c['surface'], foreground=c['text'], font=("Segoe UI", 13, "bold"))
        self.style.configure('CardCaption.TLabel', background=c['surface'], foreground=c['text_sec'], font=("Segoe UI", 10))
        # Navegación - en tema oscuro texto más claro para que iconos y logos se vean bien
        nav_fg = c['text'] if self.tema_oscuro else c['text_sec']
        self.style.configure('Nav.TButton', background=c['surface'], foreground=nav_fg, font=("Segoe UI", 12), borderwidth=0, focuscolor=c['bg'])
        self.style.map('Nav.TButton',
            foreground=[('active', c['accent']), ('selected', c['accent'])],
            background=[('active', c['card_hover']), ('selected', c['card_hover'])]
        )
        # Separador sidebar y separadores internos: actualizar color al cambiar tema
        if hasattr(self, '_sidebar_sep') and self._sidebar_sep.winfo_exists():
            self._sidebar_sep.configure(bg=c['border'])
        for attr in ('_historial_sep', '_config_sep'):
            try:
                sep = getattr(self, attr, None)
                if sep is not None and sep.winfo_exists():
                    sep.configure(bg=c['glass'])
            except (tk.TclError, AttributeError):
                pass
        # Fondo root uniforme (B3)
        try:
            self.root.configure(bg=c['bg'])
        except tk.TclError:
            pass
        # Treeview: Segoe UI 11, alineado al sistema (C1, C2)
        self.style.configure("Treeview", font=("Segoe UI", 11), background=c['surface'], foreground=c['text'])
        self.style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background=c['glass'], foreground=c['text'])
        # Logo sidebar y tarjetas: forzar colores al cambiar tema (visibilidad en tema oscuro)
        try:
            self._lbl_logo.configure(foreground=c['text'])
        except (AttributeError, tk.TclError):
            pass
        if hasattr(self, 'card_widgets') and self.card_widgets:
            self._update_card_visuals()

    @property
    def style(self):
        return self.root.style

    def _cargar_config(self):
        """Carga última carpeta, tema y formato desde config.json"""
        with self._lock_config:
            try:
                if os.path.exists(self.config_file):
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                    self._ultima_carpeta = cfg.get("ultima_carpeta", "")
                    self.tema_oscuro = cfg.get("tema_oscuro", False)
                    self._formato_resumido = cfg.get("formato_resumido", False)
                    self._solo_carpetas_cotu = cfg.get("solo_carpetas_cotu", True)
                else:
                    self._ultima_carpeta = ""
                    self._formato_resumido = False
                    self._solo_carpetas_cotu = True
            except (OSError, json.JSONDecodeError, ValueError):
                self._ultima_carpeta = ""
                self._formato_resumido = False
                self._solo_carpetas_cotu = True
    
    def _guardar_config(self):
        """Guarda última carpeta, tema y formato en config.json"""
        with self._lock_config:
            try:
                cfg = {
                    "ultima_carpeta": self.ruta_base.get() or getattr(self, "_ultima_carpeta", ""),
                    "tema_oscuro": self.tema_oscuro,
                    "formato_resumido": self.formato_resumido.get(),
                    "solo_carpetas_cotu": self.solo_carpetas_cotu.get(),
                }
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(cfg, f, indent=2, ensure_ascii=False)
            except (OSError, TypeError, ValueError) as e:
                _log.warning("No se pudo guardar la configuración: %s", e)
                Messagebox.show_warning(
                    "No se pudo guardar la configuración. Si el archivo está en uso por otro programa, ciérrelo e intente de nuevo.",
                    "Guardado",
                )
    
    def _mostrar_estructura_esperada(self):
        """Muestra ventana con la estructura de carpetas que el programa espera."""
        texto = """Estructura estándar (como en el script de trabajo):

  AÑO (carpeta raíz que usted selecciona)
  └── MES (ej. 12-DICIEMBRE o DICIEMBRE)
      └── DÍA (ej. 23 DE DICIEMBRE)
          └── ASEGURADORA (ej. SOLIDARIA, AURORA, BOLIVAR)
              └── COTUxxxxx (carpeta de la factura; nombre empieza por COTU)

El programa toma desde el final de la ruta:
  AÑO = 5 niveles arriba, MES = 4, DÍA = 3, ASEGURADORA = 2, COTU = carpeta actual.

Ejemplo PC trabajo:
  FACTURACION\\2025\\12-DICIEMBRE\\23 DE DICIEMBRE\\SOLIDARIA\\COTU74335
  → AÑO=2025, MES=12-DICIEMBRE, DÍA=23 DE DICIEMBRE, ASEGURADORA=SOLIDARIA

Ejemplo PC casa (también válido):
  FACTURACION\\2025\\DICIEMBRE\\13 DE DICIEMBRE\\AURORA\\COTU 12345

• "Carpeta del Año" = la carpeta 2025 (o FACTURACION si tiene 2025 dentro).
• Solo se cuentan carpetas cuyo nombre empiece por COTU (o todas si desmarca la opción)."""
        ventana = tk.Toplevel(self.root)
        ventana.title("Estructura de carpetas esperada")
        ventana.geometry("520x340")
        ventana.transient(self.root)
        ventana.configure(bg=self.colors["bg"])
        txt = tk.Text(ventana, wrap=tk.WORD, font=("Segoe UI", 11), padx=16, pady=16, bg=self.colors["surface"], fg=self.colors["text"], insertbackground=self.colors["text"])
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", texto)
        txt.config(state=tk.DISABLED)
        ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=(0, 12))
    
    # Métodos de estilo eliminados (setup_styles, _configurar_colores_ttk, aplicar_tema)
    # ttkbootstrap maneja esto automáticamente

    def setup_main_layout(self):
        """Configura el diseño principal: Sidebar limpio + Contenido con mucho espacio en blanco"""
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        # 1. Sidebar - listas claras, iconografía sutil, separaciones limpias (menús que flotan)
        self.sidebar = ttk.Frame(main_container, style="Sidebar.TFrame", width=280)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        self._lbl_logo = ttk.Label(
            self.sidebar,
            text="COTU\nFlux",
            style="Sidebar.TLabel",
            justify=tk.CENTER
        )
        self._lbl_logo.pack(pady=56, padx=28)
        nav_container = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        nav_container.pack(fill=tk.X, padx=24)
        self._crear_boton_nav(nav_container, "📊  Reportes", "reportes")
        self._crear_boton_nav(nav_container, "📂  Historial", "historial")
        self._crear_boton_nav(nav_container, "⚙️  Ajustes", "config")
        # Separador sutil entre sidebar y contenido (capas y profundidad, sensación glass)
        self._sidebar_sep = tk.Frame(main_container, width=1, bg=self.colors["border"])
        self._sidebar_sep.pack(side=tk.LEFT, fill=tk.Y)
        self._sidebar_sep.pack_propagate(False)
        # 2. Área de contenido - mucho espacio en blanco, sensación premium
        self.content_area = ttk.Frame(main_container, padding=56)
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Inicializar páginas
        self._init_pages()

    def _crear_boton_nav(self, parent, text, page_id):
        """Crea un botón de navegación - animaciones suaves, colores balanceados"""
        btn = ttk.Button(
            parent,
            text=text,
            command=lambda: self.show_page(page_id),
            style="Nav.TButton",
            width=22,
            cursor="hand2"
        )
        btn.pack(pady=10, fill=tk.X, ipady=10)
        # Hack para alineación izquierda del texto en ttk (no siempre funciona directo en estilo)
        # Pero con nuestra fuente y padding debería verse bien centrado o ajustado.
        self.nav_buttons[page_id] = btn

    def _init_pages(self):
        """Inicializa los frames de las páginas"""
        
        # 1. Página Reportes (Generador)
        self.frame_reportes = ttk.Frame(self.content_area)
        self._crear_pagina_reportes(self.frame_reportes)
        self.pages["reportes"] = self.frame_reportes
        
        # 2. Página Historial
        self.frame_historial = ttk.Frame(self.content_area)
        self._crear_pagina_historial(self.frame_historial)
        self.pages["historial"] = self.frame_historial
        
        # 3. Página Configuración
        self.frame_config = ttk.Frame(self.content_area)
        self._crear_pagina_configuracion(self.frame_config)
        self.pages["config"] = self.frame_config
        
        # Nota: La visualización inicial se maneja en show_page con pack()
        # Tooltips de navegación (proyecto actual)
        _tooltip(self.nav_buttons["reportes"], "Generar reportes Excel/CSV (Ctrl+G, Ctrl+P)")
        _tooltip(self.nav_buttons["historial"], "Ver reportes generados anteriormente (Ctrl+H)")
        _tooltip(self.nav_buttons["config"], "Opciones y tema oscuro/claro (Ctrl+A)", get_colors=lambda: self.colors)

    def _crear_pagina_reportes(self, parent):
        """Crea la página del Generador - estética iOS: limpia, espaciado premium, tarjetas que flotan"""
        main_frame = ttk.Frame(parent, padding=56)
        main_frame.pack(fill=tk.BOTH, expand=True)
        # Título grande y seguro, mucho espacio debajo (jerarquía muy marcada)
        ttk.Label(main_frame, text="Generar Reporte", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 36))
        # 1. Carpeta - tarjeta tipo frosted, separación clara (menús que flotan)
        folder_frame = ttk.Frame(main_frame, style="Card.TFrame", padding=28)
        folder_frame.pack(fill=tk.X, pady=(0, 32))
        ttk.Label(folder_frame, text="Carpeta Origen", style="CardCaption.TLabel").pack(anchor=tk.W)
        f_input = ttk.Frame(folder_frame, style="Card.TFrame")
        f_input.pack(fill=tk.X, pady=(14, 0))
        entry = ttk.Entry(f_input, textvariable=self.ruta_base, font=("Segoe UI", 12))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))
        ttk.Button(f_input, text="Examinar", command=self.seleccionar_carpeta, bootstyle="secondary-outline").pack(side=tk.LEFT)
        # 2. Tipo de reporte - widgets protagonistas, información clara
        ttk.Label(main_frame, text="Tipo de Reporte", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 18))
        cards_container = ttk.Frame(main_frame)
        cards_container.pack(fill=tk.X, pady=(0, 32))
        self.card_widgets = {}
        tipos = [
            (self.TIPO_ANIO, "Año", "📅"),
            (self.TIPO_MES, "Mes", "📆"),
            (self.TIPO_SEMANA, "Semana", "📊"),
            (self.TIPO_DIA, "Día", "📝")
        ]
        for val, lbl, icon in tipos:
            self._crear_card_seleccion(cards_container, val, lbl, icon)
        # 3. Rango de fechas - tarjeta limpia
        self.date_frame = ttk.Frame(main_frame)
        df_inner = ttk.Frame(self.date_frame, style="Card.TFrame", padding=28)
        df_inner.pack(fill=tk.X)
        ttk.Label(df_inner, text="Rango de Fechas", style="CardCaption.TLabel").pack(anchor=tk.W, pady=(0, 14))
        d_grid = ttk.Frame(df_inner, style="Card.TFrame")
        d_grid.pack(fill=tk.X)
        ttk.Label(d_grid, text="Desde", style="CardCaption.TLabel").pack(side=tk.LEFT, padx=(0, 12))
        self.de_inicio = ttk.DateEntry(d_grid, dateformat="%d/%m/%Y", bootstyle="primary", startdate=datetime.now())
        self.de_inicio.pack(side=tk.LEFT, padx=(0, 24))
        self.de_inicio.entry.configure(textvariable=self.fecha_inicio, width=12)
        ttk.Label(d_grid, text="Hasta", style="CardCaption.TLabel").pack(side=tk.LEFT, padx=(0, 12))
        self.de_fin = ttk.DateEntry(d_grid, dateformat="%d/%m/%Y", bootstyle="primary", startdate=datetime.now())
        self.de_fin.pack(side=tk.LEFT)
        self.de_fin.entry.configure(textvariable=self.fecha_fin, width=12)
        # 4. Acciones - botones con espacio, coherentes (todo se siente predecible)
        self.action_area = ttk.Frame(main_frame, padding=(0, 32))
        self.action_area.pack(fill=tk.X, side=tk.BOTTOM)
        self.btn_generar = ttk.Button(
            self.action_area,
            text="Generar Reporte",
            command=self.generar_reporte,
            bootstyle="success",
            width=20
        )
        self.btn_generar.pack(side=tk.RIGHT, padx=8)
        self.btn_preview = ttk.Button(
            self.action_area,
            text="Vista Previa",
            command=self.mostrar_vista_previa,
            bootstyle="secondary-outline",
            width=15
        )
        self.btn_preview.pack(side=tk.RIGHT, padx=8)
        self.btn_csv = ttk.Button(
            self.action_area,
            text="CSV",
            command=self.exportar_csv,
            bootstyle="link"
        )
        self.btn_csv.pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', bootstyle="success")
        self.progress.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 16))
        self.status_label = ttk.Label(main_frame, text="Listo", style="Caption.TLabel")
        self.status_label.pack(side=tk.BOTTOM, anchor=tk.E, pady=(0, 10))
        
        # Inicializar estado visual de cards
        # Tooltips (proyecto actual: todos los botones principales)
        _tooltip(self.btn_preview, "Ver facturas encontradas antes de generar el Excel")
        _tooltip(self.btn_generar, "Generar archivo Excel con las facturas COTU")
        _tooltip(self.btn_csv, "Exportar el mismo conjunto de datos como CSV")
        
        # Atajos de teclado
        self.root.bind("<Control-o>", lambda e: self.seleccionar_carpeta())
        self.root.bind("<Control-g>", lambda e: self.generar_reporte())
        self.root.bind("<Control-p>", lambda e: self.mostrar_vista_previa())
        self.root.bind("<Control-h>", lambda e: self.show_page('historial'))
        self.root.bind("<Control-a>", lambda e: self.show_page('config'))

        # Inicializar estado visual de cards
        self._update_card_visuals()

    def _crear_card_seleccion(self, parent, value, label, icon):
        """Crea una tarjeta tipo iOS: iconos suaves, sensación de flotar sobre el fondo (foreground para tema oscuro)"""
        card = ttk.Frame(parent, style="Card.TFrame", padding=28, cursor="hand2")
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        c = self.colors
        lbl_icon = ttk.Label(card, text=icon, font=("Segoe UI Emoji", 28), background=c['surface'], foreground=c['text'], anchor=tk.CENTER)
        lbl_icon.pack(pady=(0, 10))
        lbl_text = ttk.Label(card, text=label, font=("Segoe UI", 12, "bold"), background=c['surface'], foreground=c['text'], anchor=tk.CENTER)
        lbl_text.pack()
        def _on_click(e):
            self.tipo_reporte.set(value)
            self.actualizar_campos_fecha()
            self._update_card_visuals()
        def _on_enter(e):
            if self.tipo_reporte.get() != value:
                self.style.configure("Card.TFrame", background=self.colors['card_hover'])
        def _on_leave(e):
            self.style.configure("Card.TFrame", background=self.colors['surface'])
            self._update_card_visuals()
        for w in (card, lbl_icon, lbl_text):
            w.bind("<Button-1>", _on_click)
        self.card_widgets[value] = (card, lbl_icon, lbl_text)

    def show_page(self, page_id):
        """Muestra la página solicitada con transición suave (D1: fade más fluido)"""
        alpha = 1.0
        def _fade_out():
            nonlocal alpha
            alpha -= 0.02
            if alpha > 0.90:
                self.root.attributes("-alpha", alpha)
                self.root.after(15, _fade_out)
            else:
                _switch_content()

        def _switch_content():
            # Actualizar botón activo
            for pid, btn in self.nav_buttons.items():
                if pid == page_id:
                    btn.configure(bootstyle="primary")
                else:
                    btn.configure(bootstyle="secondary-link")
            
            # Ocultar todo
            for widget in self.content_area.winfo_children():
                widget.pack_forget()
            
            # Mostrar página
            if page_id == "reportes":
                self.frame_reportes.pack(fill=tk.BOTH, expand=True)
            elif page_id == "historial":
                self.frame_historial.pack(fill=tk.BOTH, expand=True)
                self.actualizar_lista_historial()
            elif page_id == "config":
                self.frame_config.pack(fill=tk.BOTH, expand=True)
            
            _fade_in()

        def _fade_in():
            nonlocal alpha
            alpha += 0.02
            if alpha < 1.0:
                self.root.attributes("-alpha", alpha)
                self.root.after(15, _fade_in)
            else:
                self.root.attributes("-alpha", 1.0)
        
        # Iniciar transición
        _fade_out()
        
    def _update_card_visuals(self):
        """Actualiza el aspecto de la tarjeta seleccionada"""
        current = self.tipo_reporte.get()
        c = self.colors
        for val, (card, icon, txt) in self.card_widgets.items():
            if val == current:
                icon.configure(foreground=c['accent'])
                txt.configure(foreground=c['accent'])
                # Simular borde inferior
                # card.configure(bootstyle="primary") # No funciona bien con frame custom
            else:
                icon.configure(foreground=c['text'])
                txt.configure(foreground=c['text'])
        

    
    def seleccionar_carpeta(self):
        """Abre diálogo para seleccionar carpeta del año"""
        inicial = self.ruta_base.get() or getattr(self, "_ultima_carpeta", "")
        carpeta = filedialog.askdirectory(title="Selecciona la carpeta del AÑO", initialdir=inicial or None)
        if carpeta:
            self.ruta_base.set(carpeta)
            self._ultima_carpeta = carpeta
            self._guardar_config()
            self.actualizar_status(f"Carpeta seleccionada: {os.path.basename(carpeta)}", "blue")
    

    def actualizar_campos_fecha(self):
        """Muestra/oculta campos de fecha según el tipo de reporte"""
        tipo = self.tipo_reporte.get()
        
        if tipo in [self.TIPO_MES, self.TIPO_SEMANA, self.TIPO_DIA]:
            self.date_frame.pack(fill=tk.X, pady=(0, 24), before=self.action_area)
            
            if tipo == self.TIPO_DIA:
                # Para día, solo necesitamos fecha de inicio
                self.de_fin.configure(state='disabled')
                self.fecha_fin.set("")
            else:
                # Para mes y semana, necesitamos ambas fechas
                self.de_fin.configure(state='normal')
        else:
            # Para año completo, ocultar campos de fecha
            self.date_frame.pack_forget()
            self.fecha_inicio.set("")
            self.fecha_fin.set("")
    
    def actualizar_status(self, mensaje, color="text"):
        """Actualiza el mensaje de estado con colores Ethereal"""
        # Mapeo de colores legacy a tema
        c_map = {
            "green": self.colors.get('success', '#34C759'),
            "red": self.colors.get('danger', '#FF3B30'),
            "blue": self.colors.get('accent', '#007AFF'),
            "black": self.colors.get('text', '#000000'),
            "text": self.colors.get('text_sec', '#86868B'),
        }
        color_final = c_map.get(color, color)
        
        self.status_label.config(text=mensaje, foreground=color_final)
        self.root.update()
    
    # Métodos de calendario eliminados (abrir_calendario, dibujar_calendario, etc)
    # Reemplazados por ttk.DateEntry

    
    def mostrar_vista_previa(self):
        """Muestra una vista previa de las facturas encontradas (Asíncrono)"""
        _log.info("Iniciando solicitud de vista previa")
        if not self.ruta_base.get():
            Messagebox.show_warning("Por favor, selecciona primero la carpeta del año", "Aviso")
            return
        if _es_ruta_sistema(self.ruta_base.get()):
            Messagebox.show_warning(
                "La carpeta seleccionada es una carpeta de sistema. Elija otra carpeta para los reportes.",
                "Carpeta no permitida",
            )
            return

        # Validar fechas antes de lanzar hilo
        tipo = self.tipo_reporte.get()
        fecha_inicio = None
        fecha_fin = None
        
        if tipo in [self.TIPO_MES, self.TIPO_SEMANA, self.TIPO_DIA]:
            if not self.fecha_inicio.get():
                Messagebox.show_warning("Por favor, ingresa las fechas para la vista previa", "Aviso")
                return
            fecha_inicio = self.validar_fecha(self.fecha_inicio.get())
            if not fecha_inicio:
                Messagebox.show_error("Formato de fecha inválido", "Error")
                return
            if tipo != self.TIPO_DIA:
                fecha_fin = self.validar_fecha(self.fecha_fin.get()) if self.fecha_fin.get() else None
            else:
                fecha_fin = fecha_inicio

        # Preparar parámetros para el hilo
        params = {
            "ruta_base": self.ruta_base.get(),
            "tipo": tipo,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "fecha_inicio_str": self.fecha_inicio.get(),
            "fecha_fin_str": self.fecha_fin.get()
        }

        # Estado visual: Cargando
        self.progress.start()
        self.actualizar_status("Generando vista previa...", "blue")
        self.btn_preview.configure(state="disabled")
        self.btn_generar.configure(state="disabled")
        self.btn_csv.configure(state="disabled")

        # Lanzar hilo Thread
        threading.Thread(target=self._ejecutar_vista_previa_background, args=(params,), daemon=True).start()

    def _ejecutar_vista_previa_background(self, params):
        """Ejecuta la extracción de datos en segundo plano"""
        _log.info("Hilo de vista previa iniciado")
        try:
            registros = self.extraer_facturas(params["ruta_base"], params["fecha_inicio"], params["fecha_fin"])
            _log.info(f"Extracción completada: {len(registros)} facturas encontrados")
            
            if params["tipo"] != self.TIPO_ANIO:
                registros = self.filtrar_por_tipo(registros, params["tipo"], params["fecha_inicio_str"], params["fecha_fin_str"])
            
            # Éxito: Enviar registros
            self.root.after(0, lambda: self._on_vista_previa_ready(registros, None))
            
        except Exception as e:
            _log.exception("Error en hilo de vista previa")
            # Error: Enviar excepción
            self.root.after(0, lambda: self._on_vista_previa_ready(None, str(e)))

    def _on_vista_previa_ready(self, registros, error):
        """Maneja los resultados en el hilo principal"""
        _log.info("_on_vista_previa_ready llamado en Main Thread")
        
        # Restaurar estado visual
        self.progress.stop()
        self.actualizar_status("Listo", "text")
        try:
            self.btn_preview.configure(state="normal")
            self.btn_generar.configure(state="normal")
            self.btn_csv.configure(state="normal")
        except Exception as e:
            _log.error(f"Error restaurando botones: {e}")

        if error:
            Messagebox.show_error(f"Error al generar vista previa:\n{error}", "Error")
            return

        if not registros:
            Messagebox.show_info("No se encontraron facturas con los criterios seleccionados", "Vista Previa")
            return

        # Construir ventana
        _log.info("Llamando a _construir_ventana_preview")
        self._construir_ventana_preview(registros)

    def _construir_ventana_preview(self, registros):
        """Construye y muestra la ventana de resultados"""
        _log.info("Construyendo ventana de preview...")
        try:
            # Guardar referencia en self para evitar Garbage Collection
            self.ventana_preview_top = tk.Toplevel(self.root)
            ventana_preview = self.ventana_preview_top
            ventana_preview.title("Vista Previa de Facturas")
            ventana_preview.geometry("800x550")
            ventana_preview.resizable(True, True)
            ventana_preview.configure(bg=self.colors["bg"])
            # Búsqueda
            busqueda_frame = ttk.Frame(ventana_preview)
            busqueda_frame.pack(fill=tk.X, padx=16, pady=(16, 8))
            ttk.Label(busqueda_frame, text="Buscar:").pack(side=tk.LEFT, padx=(0, 5))
            var_busqueda = tk.StringVar()
            entry_busqueda = ttk.Entry(busqueda_frame, textvariable=var_busqueda, width=40)
            entry_busqueda.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Frame con scrollbar
            frame_scroll = ttk.Frame(ventana_preview)
            frame_scroll.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
            
            scrollbar = ttk.Scrollbar(frame_scroll)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Treeview para mostrar datos
            columnas = [self.COL_ANIO, self.COL_MES, self.COL_FECHA, self.COL_FACTURA, self.COL_DETALLE, self.COL_COMPANIA]
            tree = ttk.Treeview(frame_scroll, yscrollcommand=scrollbar.set, show='headings')
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=tree.yview)
            
            tree['columns'] = columnas
            for col in columnas:
                tree.heading(col, text=col)
                tree.column(col, width=120)
            
            # Insertar datos (guardar para filtrado)
            listado_preview = list(registros[:100])
            
            def _refiltrar(*_args):
                texto = var_busqueda.get().strip().upper()
                for i in tree.get_children():
                    tree.delete(i)
                for registro in listado_preview:
                    if not texto or any(texto in str(registro.get(c, "")).upper() for c in columnas):
                        valores = [registro.get(col, "") for col in columnas]
                        tree.insert("", tk.END, values=valores)
            
            for registro in listado_preview:
                valores = [registro.get(col, "") for col in columnas]
                tree.insert("", tk.END, values=valores)
            
            var_busqueda.trace_add("write", _refiltrar)
            
            # Información (si hay más de 100, indicar "Mostrando hasta 100 de N")
            total = len(registros)
            if total > 100:
                texto_info = f"Mostrando hasta 100 de {total} facturas. Escribe arriba para filtrar."
            else:
                texto_info = f"Total: {total} facturas. Escribe arriba para filtrar."
            info_label = ttk.Label(
                ventana_preview,
                text=texto_info,
                font=("Segoe UI", 11)
            )
            info_label.pack(pady=8)

            # Frame inferior con estadísticas y duplicados
            bottom_frame = ttk.Frame(ventana_preview)
            bottom_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
            
            # Estadísticas
            stats_frame = ttk.LabelFrame(bottom_frame, text="📊 Resumen por Aseguradora")
            stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            
            stats_text = tk.Text(stats_frame, height=8, width=40, font=("Segoe UI", 10), bg=self.colors["surface"], fg=self.colors["text"], insertbackground=self.colors["text"])
            stats_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            stats_text.insert("1.0", self.calcular_estadisticas(registros))
            stats_text.config(state=tk.DISABLED)
            
            # Duplicados
            dups = self.verificar_duplicados(registros)
            dup_title = f"⚠️ Posibles Duplicados ({len(dups)})" if dups else "✅ Validación de Duplicados"
            dup_color = "danger" if dups else "success"
            
            dup_frame = ttk.LabelFrame(bottom_frame, text=dup_title, bootstyle=dup_color)
            dup_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
            
            dup_text = tk.Text(dup_frame, height=8, width=50, font=("Segoe UI", 10), bg=self.colors["surface"], fg=self.colors["text"], insertbackground=self.colors["text"])
            dup_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            
            if dups:
                dup_text.insert("1.0", "\n".join(dups))
            else:
                dup_text.insert("1.0", "No se encontraron facturas con el mismo número.")
            dup_text.config(state=tk.DISABLED)

            # Forzar foco y levantar ventana
            ventana_preview.lift()
            ventana_preview.focus_force()
            _log.info("Ventana de preview mostrada exitosamente")

        except Exception as e:
            _log.exception("Error construyendo ventana preview")
            Messagebox.show_error(f"Error al generar vista previa:\n{str(e)}", "Error")
    
    def _crear_pagina_historial(self, parent):
        """Crea la página de historial - listas claras, tipografía grande y legible"""
        ttk.Label(parent, text="Historial de Reportes", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 36))
        # Separador sutil entre título y lista (B1)
        sep_h = tk.Frame(parent, height=1, bg=self.colors["glass"])
        sep_h.pack(fill=tk.X, pady=(0, 20))
        sep_h.pack_propagate(False)
        self._historial_sep = sep_h
        frame_scroll = ttk.Frame(parent)
        frame_scroll.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 20))
        scrollbar = ttk.Scrollbar(frame_scroll)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_historial = ttk.Treeview(frame_scroll, yscrollcommand=scrollbar.set, show='headings', height=16)
        self.tree_historial.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree_historial.yview)
        columnas = ["Fecha", "Tipo", "Archivo", "Ruta", "Facturas"]
        self.tree_historial['columns'] = columnas
        for col in columnas:
            self.tree_historial.heading(col, text=col)
            self.tree_historial.column(col, width=150)
        def _al_doble_clic(_event):
            sel = self.tree_historial.selection()
            if sel:
                tags = self.tree_historial.item(sel[0]).get("tags", ())
                if tags:
                    ruta = tags[0]
                    if os.path.isfile(ruta):
                        self._abrir_carpeta(os.path.dirname(ruta))
                    elif os.path.isdir(ruta):
                        self._abrir_carpeta(ruta)
        self.tree_historial.bind("<Double-1>", _al_doble_clic)
        ttk.Label(parent, text="Doble clic en una fila para abrir la carpeta", style="Caption.TLabel").pack(pady=(12, 0))
        ttk.Button(parent, text="Actualizar Lista", command=self.actualizar_lista_historial, bootstyle="secondary-outline").pack(pady=20)
        self.actualizar_lista_historial()

    def actualizar_lista_historial(self):
        """Recarga el treeview del historial"""
        if not hasattr(self, 'tree_historial'):
            return
            
        # Limpiar
        for i in self.tree_historial.get_children():
            self.tree_historial.delete(i)
            
        historial = self.cargar_historial()
        if not historial:
            return

        for item in historial:
            ruta_completa = item.get("ruta", "")
            valores = [
                item.get("fecha", ""),
                item.get("tipo", ""),
                item.get("archivo", ""),
                ruta_completa[:50] + "..." if len(ruta_completa) > 50 else ruta_completa,
                str(item.get("total_facturas", 0))
            ]
            self.tree_historial.insert("", tk.END, values=valores, tags=(ruta_completa,))

    def _crear_pagina_configuracion(self, parent):
        """Crea la página de configuración - listas claras, separaciones limpias, interruptores suaves"""
        ttk.Label(parent, text="Ajustes", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 36))
        frame_general = ttk.Frame(parent, style="Card.TFrame", padding=28)
        frame_general.pack(fill=tk.X, pady=(0, 24))
        ttk.Label(frame_general, text="Opciones Generales", style="CardSection.TLabel").pack(anchor=tk.W, pady=(0, 18))
        ttk.Checkbutton(
            frame_general,
            text="Formato resumido (solo FECHA, COTU, ASEGURADORA)",
            variable=self.formato_resumido,
            command=self._guardar_config,
            bootstyle="round-toggle"
        ).pack(anchor=tk.W, pady=10)
        ttk.Checkbutton(
            frame_general,
            text="Solo carpetas 'COTU'",
            variable=self.solo_carpetas_cotu,
            command=self._guardar_config,
            bootstyle="round-toggle"
        ).pack(anchor=tk.W, pady=10)
        ttk.Button(
            frame_general,
            text="Ver estructura de carpetas esperada",
            command=self._mostrar_estructura_esperada,
            bootstyle="link"
        ).pack(anchor=tk.W, pady=(8, 0))
        # Separador sutil entre secciones (B1)
        sep_config = tk.Frame(parent, height=1, bg=self.colors["glass"])
        sep_config.pack(fill=tk.X, pady=(0, 20))
        sep_config.pack_propagate(False)
        self._config_sep = sep_config
        frame_apariencia = ttk.Frame(parent, style="Card.TFrame", padding=28)
        frame_apariencia.pack(fill=tk.X, pady=(0, 24))
        ttk.Label(frame_apariencia, text="Apariencia", style="CardSection.TLabel").pack(anchor=tk.W, pady=(0, 18))
        self.btn_tema = ttk.Button(
            frame_apariencia,
            text="Tema Oscuro",
            command=self.toggle_tema,
            bootstyle="secondary-outline"
        )
        self.btn_tema.pack(anchor=tk.W)
        if self.tema_oscuro:
            self.btn_tema.config(text="Tema Claro")
        else:
            self.btn_tema.config(text="Tema Oscuro")
    
    def toggle_tema(self):
        """Alterna entre tema oscuro y claro - modo oscuro con grises profundos (no negro puro)."""
        self.tema_oscuro = not self.tema_oscuro
        self.colors = self.ETH_COLORS["dark"] if self.tema_oscuro else self.ETH_COLORS["light"]
        if self.tema_oscuro:
            self.btn_tema.config(text="Tema Claro")
            self.style.theme_use('darkly')
        else:
            self.btn_tema.config(text="Tema Oscuro")
            self.style.theme_use('flatly')
        self._apply_theme()
        self._guardar_config()
    
    def guardar_historial(self, tipo, archivo, ruta, total_facturas):
        """Guarda un registro en el historial"""
        with self._lock_historial:
            historial = self.cargar_historial()
            nuevo_registro = {
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tipo": tipo,
                "archivo": archivo,
                "ruta": ruta,
                "total_facturas": total_facturas
            }
            historial.insert(0, nuevo_registro)
            if len(historial) > 50:
                historial = historial[:50]
            try:
                with open(self.historial_file, 'w', encoding='utf-8') as f:
                    json.dump(historial, f, indent=2, ensure_ascii=False)
            except (OSError, TypeError, ValueError) as e:
                _log.warning("No se pudo guardar el historial: %s", e)
                Messagebox.show_warning(
                    "No se pudo guardar el historial de reportes. Si el archivo está en uso, ciérrelo e intente de nuevo.",
                    "Guardado",
                )
    
    def cargar_historial(self):
        """Carga el historial desde archivo"""
        with self._lock_historial:
            try:
                if os.path.exists(self.historial_file):
                    with open(self.historial_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except (OSError, json.JSONDecodeError, ValueError):
                pass
            return []
    
    def _abrir_carpeta(self, carpeta):
        """Abre la carpeta en el explorador del sistema"""
        if not carpeta or not os.path.isdir(carpeta):
            return
        try:
            if sys.platform == "win32":
                os.startfile(carpeta)
            elif sys.platform == "darwin":
                subprocess.run(["open", carpeta], check=False)
            else:
                subprocess.run(["xdg-open", carpeta], check=False)
        except (OSError, subprocess.SubprocessError):
            pass

    def _obtener_ruta_salida(self, params: Dict[str, Any], extension: str) -> str:
        """Devuelve la ruta del archivo de salida (Excel o CSV) según tipo y fechas."""
        ruta_base = params["ruta_base"]
        tipo = params["tipo"]
        nombre_anio = params["nombre_anio"]
        fecha_inicio = params.get("fecha_inicio")
        fecha_fin = params.get("fecha_fin")
        ext = extension if extension.startswith(".") else "." + extension
        if tipo == self.TIPO_ANIO:
            if ext == ".csv":
                nombre = f"cotus_{nombre_anio}.csv"
            else:
                nombre = f"cotus_{nombre_anio.lower().replace(' ', '_')}.xlsx"
        elif tipo == self.TIPO_DIA and fecha_inicio:
            nombre = f"cotus_dia_{fecha_inicio.strftime('%Y%m%d')}{ext}"
        elif fecha_inicio and fecha_fin:
            if ext == ".csv":
                sufijo = tipo.lower().replace("á", "a").replace("í", "i")
                nombre = f"cotus_{sufijo}_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.csv"
            else:
                pref = "semana" if tipo == self.TIPO_SEMANA else "mes"
                nombre = f"cotus_{pref}_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.xlsx"
        else:
            nombre = f"cotus_{nombre_anio}{ext}"
        return os.path.join(ruta_base, nombre)

    def _ejecutar_csv(self, params):
        """Ejecuta en segundo plano la extracción y exportación a CSV."""
        ruta_csv, total, error_msg = None, 0, None
        try:
            registros = self.extraer_facturas(params["ruta_base"], params["fecha_inicio"], params["fecha_fin"])
            if params["tipo"] != self.TIPO_ANIO:
                registros = self.filtrar_por_tipo(registros, params["tipo"], params["fecha_inicio_str"], params["fecha_fin_str"])
            if not registros:
                res = (None, 0, "No se encontraron facturas con los criterios seleccionados")
                self.root.after(0, lambda r=res: self._al_finalizar_csv(r))
                return
            df = pd.DataFrame(registros)
            if params["formato_resumido"]:
                df = df[[self.COL_FECHA, self.COL_FACTURA, self.COL_COMPANIA]].copy()
                df = df.rename(columns={self.COL_FECHA: "FECHA", self.COL_FACTURA: "COTU", self.COL_COMPANIA: "ASEGURADORA"})
            nombre_anio = params["nombre_anio"]
            tipo, fecha_inicio, fecha_fin = params["tipo"], params["fecha_inicio"], params["fecha_fin"]
            sufijo = tipo.lower().replace("á", "a").replace("í", "i")
            if tipo == self.TIPO_ANIO:
                nombre = f"cotus_{nombre_anio}.csv"
            elif tipo == self.TIPO_DIA:
                nombre = f"cotus_dia_{fecha_inicio.strftime('%Y%m%d')}.csv"
            else:
                nombre = f"cotus_{sufijo}_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.csv"
            ruta_csv = os.path.join(params["ruta_base"], nombre)
            df.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
            _log.info("CSV exportado: %s (%s facturas)", ruta_csv, len(df))
            res = (ruta_csv, len(df), None)
        except Exception as e:
            _log.exception("Error al exportar CSV")
            res = (None, 0, str(e))
        self.root.after(0, lambda r=res: self._al_finalizar_csv(r))

    def _al_finalizar_csv(self, res):
        """Callback en hilo principal tras terminar _ejecutar_csv."""
        self.progress.stop()
        self.btn_csv.config(state='normal')
        ruta_csv, total, error_msg = res
        if error_msg:
            self.actualizar_status(error_msg[:50] + "…" if len(error_msg) > 50 else error_msg, "red")
            Messagebox.show_error(f"Error al exportar CSV:\n{error_msg}", "Error")
        elif ruta_csv:
            self.actualizar_status("CSV exportado correctamente", "green")
            # Diálogo de éxito con opción Abrir carpeta (proyecto actual)
            self._mostrar_exito_abrir_carpeta(ruta_csv, total)

    def exportar_csv(self):
        """Exporta el mismo conjunto de datos que el reporte actual como CSV (en segundo plano)."""
        if not self.ruta_base.get():
            Messagebox.show_warning("Por favor, selecciona primero la carpeta del año", "Aviso")
            return
        if _es_ruta_sistema(self.ruta_base.get()):
            Messagebox.show_warning(
                "La carpeta seleccionada es una carpeta de sistema. Elija otra carpeta para los reportes.",
                "Carpeta no permitida",
            )
            return
        tipo = self.tipo_reporte.get()
        fecha_inicio, fecha_fin = None, None
        if tipo in [self.TIPO_MES, self.TIPO_SEMANA, self.TIPO_DIA]:
            if not self.fecha_inicio.get():
                Messagebox.show_warning("Ingresa las fechas para exportar", "Aviso")
                return
            fecha_inicio = self.validar_fecha(self.fecha_inicio.get())
            if not fecha_inicio:
                Messagebox.show_error("Formato de fecha inválido. Usa DD/MM/YYYY", "Error")
                return
            if tipo != self.TIPO_DIA:
                fecha_fin = self.validar_fecha(self.fecha_fin.get()) if self.fecha_fin.get() else None
                if not fecha_fin or fecha_fin < fecha_inicio:
                    Messagebox.show_error("Fecha 'Hasta' inválida o anterior a 'Desde'", "Error")
                    return
            else:
                fecha_fin = fecha_inicio
        params = {
            "ruta_base": self.ruta_base.get(),
            "tipo": tipo,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "fecha_inicio_str": self.fecha_inicio.get(),
            "fecha_fin_str": self.fecha_fin.get(),
            "formato_resumido": self.formato_resumido.get(),
            "nombre_anio": os.path.basename(self.ruta_base.get().rstrip(os.sep)),
        }
        ruta_csv = self._obtener_ruta_salida(params, ".csv")
        if os.path.exists(ruta_csv):
            if not tk_messagebox.askyesno("Sobrescribir archivo", f"El archivo ya existe:\n{ruta_csv}\n\n¿Deseas sobrescribirlo?"):
                return
        self.progress.start()
        self.btn_csv.config(state='disabled')
        self.actualizar_status("Exportando CSV...", "blue")
        threading.Thread(target=self._ejecutar_csv, args=(params,), daemon=True).start()
    
    def _mostrar_exito_abrir_carpeta(self, ruta_salida, total_facturas):
        """Muestra diálogo de éxito con botón para abrir la carpeta (F3: fondo coherente con tema)"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Éxito")
        ventana.geometry("520x220")
        ventana.transient(self.root)
        ventana.grab_set()
        ventana.configure(bg=self.colors["bg"])
        titulo = "CSV exportado exitosamente" if ruta_salida.lower().endswith(".csv") else "Excel generado exitosamente"
        ttk.Label(ventana, text=titulo, font=("Segoe UI", 13, "bold")).pack(pady=(24, 12))
        ttk.Label(ventana, text=ruta_salida, wraplength=460, font=("Segoe UI", 10)).pack(pady=6)
        ttk.Label(ventana, text=f"Total de facturas: {total_facturas}", font=("Segoe UI", 11)).pack(pady=6)
        btn_frame = ttk.Frame(ventana)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Abrir carpeta", command=lambda: (self._abrir_carpeta(os.path.dirname(ruta_salida)), ventana.destroy())).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Cerrar", command=ventana.destroy).pack(side=tk.LEFT, padx=8)
        
        ventana.focus_set()
    
    def verificar_duplicados(self, registros: List[Dict[str, Any]]) -> List[str]:
        """Retorna lista de mensajes de duplicados encontrados"""
        vistos = {} # clave: numero_cotu -> lista de indices
        duplicados = []
        
        for i, reg in enumerate(registros):
            cotu = str(reg.get(self.COL_FACTURA, "")).strip().upper()
            if not cotu or cotu == "COTU":
                continue
            if cotu in vistos:
                vistos[cotu].append(i)
            else:
                vistos[cotu] = [i]
        
        for cotu, indices in vistos.items():
            if len(indices) > 1:
                # Encontrado duplicado
                fechas = set()
                aseguradoras = set()
                for idx in indices:
                    fechas.add(registros[idx].get(self.COL_FECHA, ""))
                    aseguradoras.add(registros[idx].get(self.COL_COMPANIA, ""))
                
                msg = f"Factura {cotu} aparece {len(indices)} veces (Fechas: {', '.join(fechas)} - Cia: {', '.join(aseguradoras)})"
                duplicados.append(msg)
        return duplicados

    def calcular_estadisticas(self, registros: List[Dict[str, Any]]) -> str:
        """Genera un resumen estadístico por aseguradora"""
        total = len(registros)
        if total == 0:
            return "No hay registros."
            
        conteo = {}
        for reg in registros:
            cia = reg.get(self.COL_COMPANIA, "SIN ASEGURADORA") or "SIN ASEGURADORA"
            conteo[cia] = conteo.get(cia, 0) + 1
        
        resumen = [f"Total Facturas: {total}"]
        resumen.append("-" * 20)
        
        # Ordenar por cantidad descendente
        for cia, cant in sorted(conteo.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (cant / total) * 100
            resumen.append(f"{cia}: {cant} ({porcentaje:.1f}%)")
            
        return "\n".join(resumen)
    
    def validar_fecha(self, fecha_str: str) -> Optional[datetime]:
        """Valida formato de fecha DD/MM/YYYY"""
        try:
            return datetime.strptime(fecha_str, "%d/%m/%Y")
        except ValueError:
            return None
    
    def extraer_facturas(self, ruta_base: str, fecha_inicio: Optional[datetime] = None, fecha_fin: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Extrae todas las facturas COTU de la estructura de carpetas.
        OPTIMIZADO para carpetas de red con limitación de profundidad.
        Estructura estándar (como en script de trabajo):
          AÑO / MES / DÍA / ASEGURADORA / COTUxxxxx
        Ejemplo: 2025 / 12-DICIEMBRE / 23 DE DICIEMBRE / SOLIDARIA / COTU74335
        También admite base = carpeta padre (FACTURACION) con año en primer subnivel.
        """
        registros = []
        if not os.path.exists(ruta_base):
            raise FileNotFoundError(f"La carpeta no existe: {ruta_base}")
        # Normalizar para cálculo de profundidad (evitar fallo con ruta_base con barra final)
        ruta_base_norm = os.path.normpath(ruta_base.rstrip(os.sep))
        nombre_anio = os.path.basename(ruta_base_norm)
        solo_cotu = getattr(self, "solo_carpetas_cotu", None)
        solo_cotu = solo_cotu.get() if solo_cotu is not None else True
        
        # Contador para actualizar progreso
        carpetas_procesadas = 0
        max_depth = 6  # AÑO/MES/DÍA/ASEGURADORA/COTU = 5 niveles + margen

        for root, dirs, _ in os.walk(ruta_base):
            # OPTIMIZACIÓN 1: Limitar profundidad (ruta_base_norm evita fallo con barra final)
            suffix = root[len(ruta_base_norm):] if root.startswith(ruta_base_norm) else root[len(ruta_base):]
            depth = suffix.count(os.sep)
            if depth >= max_depth:
                dirs[:] = []  # No entrar en subdirectorios
                continue
            
            # OPTIMIZACIÓN 2: Filtrar directorios ANTES de entrar
            if solo_cotu and depth >= 4:
                dirs[:] = [d for d in dirs if d.upper().startswith("COTU")]
            
            # OPTIMIZACIÓN 3: Actualizar progreso cada 50 carpetas
            carpetas_procesadas += 1
            if carpetas_procesadas % 50 == 0:
                self.root.after(0, lambda n=carpetas_procesadas: 
                    self.actualizar_status(f"Escaneando... {n} carpetas", "blue"))
            for d in dirs:
                if solo_cotu and not d.upper().startswith("COTU"):
                    continue
                ruta_cotu = os.path.join(root, d)
                partes = d.split()
                cotu = partes[0] if partes else d
                detalle = " ".join(partes[1:]) if len(partes) > 1 else ""
                partes_ruta = Path(ruta_cotu).parts
                try:
                    # Lógica del script de trabajo: AÑO/MES/DÍA/ASEGURADORA/COTU desde el final
                    # -1=COTU, -2=ASEGURADORA, -3=DÍA, -4=MES, -5=AÑO
                    if len(partes_ruta) >= 5:
                        anio_para_fecha = partes_ruta[-5]
                        mes = partes_ruta[-4]
                        dia = partes_ruta[-3]
                        aseguradora = partes_ruta[-2]
                    else:
                        # Fallback: índices respecto a la carpeta base
                        idx_base = partes_ruta.index(os.path.basename(ruta_base))
                        anio_para_fecha = nombre_anio
                        if idx_base + 1 < len(partes_ruta):
                            primero = partes_ruta[idx_base + 1]
                            if len(primero) == 4 and primero.isdigit():
                                anio_para_fecha = primero
                                if len(partes_ruta) > idx_base + 4:
                                    mes = partes_ruta[idx_base + 2]
                                    dia = partes_ruta[idx_base + 3]
                                    aseguradora = partes_ruta[idx_base + 4]
                                else:
                                    mes = dia = aseguradora = ""
                            else:
                                if len(partes_ruta) > idx_base + 4:
                                    mes, dia = partes_ruta[idx_base + 1], partes_ruta[idx_base + 3]
                                    aseguradora = partes_ruta[idx_base + 4]
                                elif len(partes_ruta) > idx_base + 3:
                                    mes = partes_ruta[idx_base + 1]
                                    dia = partes_ruta[idx_base + 2]
                                    aseguradora = partes_ruta[idx_base + 3]
                                else:
                                    mes = partes_ruta[idx_base + 1] if idx_base + 1 < len(partes_ruta) else ""
                                    dia = partes_ruta[idx_base + 2] if idx_base + 2 < len(partes_ruta) else ""
                                    aseguradora = ""
                        else:
                            if len(partes_ruta) > idx_base + 4:
                                mes, dia = partes_ruta[idx_base + 1], partes_ruta[idx_base + 3]
                                aseguradora = partes_ruta[idx_base + 4]
                            elif len(partes_ruta) > idx_base + 3:
                                mes, dia = partes_ruta[idx_base + 1], partes_ruta[idx_base + 2]
                                aseguradora = partes_ruta[idx_base + 3]
                            else:
                                mes = partes_ruta[idx_base + 1] if idx_base + 1 < len(partes_ruta) else ""
                                dia = partes_ruta[idx_base + 2] if idx_base + 2 < len(partes_ruta) else ""
                                aseguradora = ""
                    if fecha_inicio or fecha_fin:
                        fecha_carpeta = self.parsear_fecha_carpeta(dia, mes, anio_para_fecha)
                        if fecha_carpeta:
                            if fecha_inicio and fecha_carpeta < fecha_inicio:
                                continue
                            if fecha_fin and fecha_carpeta > fecha_fin:
                                continue
                    registros.append({
                        self.COL_ANIO: anio_para_fecha,
                        self.COL_MES: mes,
                        self.COL_FECHA: dia,
                        self.COL_FACTURA: cotu,
                        self.COL_DETALLE: detalle,
                        self.COL_COMPANIA: aseguradora
                    })
                except (IndexError, ValueError):
                    registros.append({
                        self.COL_ANIO: nombre_anio,
                        self.COL_MES: "",
                        self.COL_FECHA: "",
                        self.COL_FACTURA: cotu,
                        self.COL_DETALLE: detalle,
                        self.COL_COMPANIA: ""
                    })
        
        # Actualizar estado final
        self.root.after(0, lambda: 
            self.actualizar_status(f"✓ {len(registros)} facturas encontradas", "green"))
        
        return registros
    
    def parsear_fecha_carpeta(self, dia: str, mes: str, anio: str) -> Optional[datetime]:
        """
        Intenta parsear la fecha desde los nombres de carpeta
        Maneja formatos como: "02 DE AGOSTO", "AGOSTO", "2025"
        """
        # Diccionario de meses en español
        meses_espanol = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        try:
            if not dia or not mes or not anio:
                return None
            
            # Extraer año (solo números)
            anio_num = None
            try:
                anio_num = int(re.sub(r'\D', '', str(anio)))
            except (ValueError, TypeError):
                return None
            
            # Extraer mes (convertir nombre a número)
            mes_num = None
            mes_lower = mes.lower().strip()
            
            # Buscar en el diccionario de meses
            if mes_lower in meses_espanol:
                mes_num = meses_espanol[mes_lower]
            else:
                # Intentar extraer número del mes (ej: "08-AGOSTO" -> 8)
                try:
                    mes_num = int(re.sub(r'\D', '', mes))
                    if mes_num < 1 or mes_num > 12:
                        # Si no es válido, buscar el nombre del mes en el string
                        for nombre_mes, num in meses_espanol.items():
                            if nombre_mes in mes_lower:
                                mes_num = num
                                break
                except (ValueError, TypeError):
                    # Buscar nombre del mes en el string
                    for nombre_mes, num in meses_espanol.items():
                        if nombre_mes in mes_lower:
                            mes_num = num
                            break
            
            if not mes_num:
                return None
            
            # Extraer día
            dia_num = None
            dia_str = str(dia).strip()
            
            # Formato: "02 DE AGOSTO" o "2 DE AGOSTO"
            # Extraer números del inicio
            match = re.match(r'^(\d+)', dia_str)
            if match:
                try:
                    dia_num = int(match.group(1))
                except (ValueError, TypeError):
                    pass
            
            # Si no se encontró día, intentar extraer cualquier número
            if not dia_num:
                try:
                    dia_num = int(re.sub(r'\D', '', dia_str))
                except (ValueError, TypeError):
                    return None
            
            # Validar y crear fecha
            if dia_num and mes_num and anio_num:
                try:
                    return datetime(anio_num, mes_num, dia_num)
                except ValueError:
                    # Fecha inválida (ej: 31 de febrero)
                    return None
                    
        except (ValueError, TypeError, AttributeError, KeyError):
            pass
        
        return None
    
    def filtrar_por_tipo(self, registros: List[Dict[str, Any]], tipo: str, fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filtra registros según el tipo de reporte"""
        if tipo == self.TIPO_ANIO:
            return registros
        
        df = pd.DataFrame(registros)
        if df.empty:
            return []
        
        # Convertir fechas
        df['FECHA_PARSED'] = df.apply(
            lambda row: self.parsear_fecha_carpeta(
                row[self.COL_FECHA], 
                row[self.COL_MES], 
                row[self.COL_ANIO]
            ), axis=1
        )
        
        if fecha_inicio:
            fecha_inicio_dt = self.validar_fecha(fecha_inicio)
            if fecha_inicio_dt:
                df = df[df['FECHA_PARSED'] >= fecha_inicio_dt]
        
        if fecha_fin:
            fecha_fin_dt = self.validar_fecha(fecha_fin)
            if fecha_fin_dt:
                # Para fecha fin, incluir todo el día
                fecha_fin_dt = fecha_fin_dt.replace(hour=23, minute=59, second=59)
                df = df[df['FECHA_PARSED'] <= fecha_fin_dt]
        
        # Eliminar columna temporal
        df = df.drop('FECHA_PARSED', axis=1)
        
        return df.to_dict('records')
    
    def _ejecutar_generar(self, params):
        """Ejecuta en segundo plano la extracción y exportación del reporte. Al terminar programa callback en el hilo principal."""
        ok, ruta_salida, total, tipo, nombre_archivo, error_msg, warning_msg = False, None, 0, None, None, None, None
        try:
            registros = self.extraer_facturas(params["ruta_base"], params["fecha_inicio"], params["fecha_fin"])
            if not registros:
                res = (False, None, 0, None, None, "No se encontraron facturas COTU en el rango seleccionado.", None)
                self.root.after(0, lambda r=res: self._al_finalizar_generar(r))
                return
            if params["tipo"] != self.TIPO_ANIO:
                registros = self.filtrar_por_tipo(registros, params["tipo"], params["fecha_inicio_str"], params["fecha_fin_str"])
            if not registros:
                res = (False, None, 0, None, None, "No se encontraron facturas en el rango de fechas especificado.", None)
                self.root.after(0, lambda r=res: self._al_finalizar_generar(r))
                return
            
            # Detectar duplicados en background para logging
            dups = self.verificar_duplicados(registros)
            if dups:
                _log.warning("Se detectaron %d duplicados en el reporte", len(dups))

            df = pd.DataFrame(registros)
            if params["formato_resumido"]:
                df = df[[self.COL_FECHA, self.COL_FACTURA, self.COL_COMPANIA]].copy()
                df = df.rename(columns={self.COL_FECHA: "FECHA", self.COL_FACTURA: "COTU", self.COL_COMPANIA: "ASEGURADORA"})
                columnas_orden = ["FECHA", "COTU", "ASEGURADORA"]
            else:
                columnas_orden = [self.COL_FECHA, self.COL_MES, self.COL_FACTURA]
            by_cols = [c for c in columnas_orden if c in df.columns]
            if by_cols:
                df.sort_values(by=by_cols, inplace=True)
            tipo, nombre_anio = params["tipo"], params["nombre_anio"]
            fecha_inicio, fecha_fin = params["fecha_inicio"], params["fecha_fin"]
            if tipo == self.TIPO_ANIO:
                nombre_archivo = f"cotus_{nombre_anio.lower().replace(' ', '_')}.xlsx"
            elif tipo == self.TIPO_DIA:
                nombre_archivo = f"cotus_dia_{fecha_inicio.strftime('%Y%m%d')}.xlsx"
            elif tipo == self.TIPO_SEMANA:
                nombre_archivo = f"cotus_semana_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.xlsx"
            else:
                nombre_archivo = f"cotus_mes_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.xlsx"
            ruta_salida = os.path.join(params["ruta_base"], nombre_archivo)
            carpeta_salida = os.path.dirname(ruta_salida)
            try:
                test_file = os.path.join(carpeta_salida, ".permiso_escritura_tmp")
                with open(test_file, "w") as f:
                    f.write("")
                os.remove(test_file)
            except (OSError, PermissionError):
                res = (False, None, 0, tipo, None, "No hay permisos de escritura en la carpeta seleccionada.", None)
                self.root.after(0, lambda r=res: self._al_finalizar_generar(r))
                return
            try:
                import openpyxl  # noqa: F401
                engine, usar_openpyxl = 'openpyxl', True
            except ImportError:
                try:
                    import xlsxwriter  # noqa: F401
                    engine, usar_openpyxl = 'xlsxwriter', False
                except ImportError:
                    engine, usar_openpyxl = None, False
                    warning_msg = "openpyxl no está instalado. Intentando con engine por defecto.\nPara mejores resultados, instala: pip install openpyxl"
            writer = None
            try:
                writer = pd.ExcelWriter(ruta_salida, engine=engine) if engine else pd.ExcelWriter(ruta_salida)
                nombre_hoja = {self.TIPO_ANIO: "NOVEDADES ANUALES", self.TIPO_MES: "NOVEDADES MENSUALES", self.TIPO_SEMANA: "NOVEDADES SEMANALES", self.TIPO_DIA: "NOVEDADES DIARIAS"}[tipo]
                df.to_excel(writer, index=False, sheet_name=nombre_hoja)
                if usar_openpyxl:
                    hoja = writer.sheets[nombre_hoja]
                    hoja.auto_filter.ref = hoja.dimensions
                    for column in hoja.columns:
                        max_length = 0
                        for cell in column:
                            try:
                                n = len(str(cell.value))
                                if n > max_length:
                                    max_length = n
                            except (TypeError, AttributeError):
                                pass
                        hoja.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
            except Exception as e:
                if writer is not None:
                    try:
                        writer.close()
                    except Exception:
                        pass
                ruta_csv = ruta_salida.replace('.xlsx', '.csv')
                df.to_csv(ruta_csv, index=False, encoding='utf-8-sig')
                err_text = f"No se pudo generar Excel. Se generó CSV en su lugar:\n{ruta_csv}\n\nError original: {str(e)}\n\nPara generar Excel, instala: pip install openpyxl"
                _log.exception("Error al generar reporte")
                res = (False, ruta_csv, len(df), tipo, os.path.basename(ruta_csv), err_text, warning_msg)
                self.root.after(0, lambda r=res: self._al_finalizar_generar(r))
                return
            finally:
                if writer is not None:
                    try:
                        writer.close()
                    except Exception:
                        pass
            ok, total = True, len(df)
            _log.info("Reporte generado: %s (%s facturas)", ruta_salida, total)
        except Exception as e:
            error_msg = str(e)
            _log.exception("Error al generar reporte")
        
        # Pasar registros a callback para validar duplicados
        # (truco: agregamos registros al resultado para usarlos en el callback)
        res = (ok, ruta_salida, total, tipo, nombre_archivo, error_msg, warning_msg, registros if ok else [])
        self.root.after(0, lambda r=res: self._al_finalizar_generar(r))

    def _al_finalizar_generar(self, res):
        """Callback en hilo principal tras terminar _ejecutar_generar."""
        self.progress.stop()
        self.btn_generar.config(state='normal')
        
        # Desempaquetar (manejando compatibilidad con tupla vieja por si acaso)
        if len(res) == 8:
            ok, ruta_salida, total, tipo, nombre_archivo, error_msg, warning_msg, registros = res
        else:
            ok, ruta_salida, total, tipo, nombre_archivo, error_msg, warning_msg = res
            registros = []
            
        if warning_msg:
            Messagebox.show_warning(warning_msg, "Advertencia")
        if ok and ruta_salida:
            self.guardar_historial(tipo, nombre_archivo, ruta_salida, total)
            self._guardar_config()
            self.actualizar_status("Reporte generado exitosamente", "green")
            # Toast notification
            ToastNotification(
                title="✅ Reporte Generado",
                message=f"Archivo: {nombre_archivo}\nTotal: {total} facturas",
                duration=4000,
                bootstyle="success"
            ).show_toast()
            # Actualizar historial si está visible
            self.actualizar_lista_historial()
            # Diálogo de éxito con botón Abrir carpeta (proyecto actual)
            self._mostrar_exito_abrir_carpeta(ruta_salida, total)
            
            # Alerta de duplicados si los hay
            dups = self.verificar_duplicados(registros) if registros else []

            msg_extra = ""
            if dups:
                msg_extra = f"\n\n⚠️ Se detectaron {len(dups)} facturas con número duplicado. Revise la vista previa para detalles."
                Messagebox.show_warning(f"Reporte generado con advertencias.\nTotal: {total} facturas.{msg_extra}", "Reporte Generado")
            
        elif error_msg:
            self.actualizar_status(error_msg[:50] + "…" if len(error_msg) > 50 else error_msg, "red")
            Messagebox.show_error(error_msg, "Error")

    def generar_reporte(self):
        """Genera el reporte según el tipo seleccionado (en segundo plano para no bloquear la UI)."""
        if not self.ruta_base.get():
            Messagebox.show_error("Por favor, selecciona la carpeta del año", "Error")
            return
        if _es_ruta_sistema(self.ruta_base.get()):
            Messagebox.show_warning(
                "La carpeta seleccionada es una carpeta de sistema. Elija otra carpeta para los reportes.",
                "Carpeta no permitida",
            )
            return
        tipo = self.tipo_reporte.get()
        fecha_inicio, fecha_fin = None, None
        if tipo in [self.TIPO_MES, self.TIPO_SEMANA, self.TIPO_DIA]:
            if not self.fecha_inicio.get():
                Messagebox.show_error("Por favor, ingresa la fecha de inicio", "Error")
                return
            fecha_inicio = self.validar_fecha(self.fecha_inicio.get())
            if not fecha_inicio:
                Messagebox.show_error("Formato de fecha inválido. Usa DD/MM/YYYY", "Error")
                return
            if tipo != self.TIPO_DIA:
                if not self.fecha_fin.get():
                    Messagebox.show_error("Por favor, ingresa la fecha de fin", "Error")
                    return
                fecha_fin = self.validar_fecha(self.fecha_fin.get())
                if not fecha_fin:
                    Messagebox.show_error("Formato de fecha de fin inválido. Usa DD/MM/YYYY", "Error")
                    return
                if fecha_fin < fecha_inicio:
                    Messagebox.show_error("La fecha 'Hasta' debe ser posterior o igual a la fecha 'Desde'.", "Error")
                    return
            else:
                fecha_fin = fecha_inicio
        params = {
            "ruta_base": self.ruta_base.get(),
            "tipo": tipo,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "fecha_inicio_str": self.fecha_inicio.get(),
            "fecha_fin_str": self.fecha_fin.get(),
            "formato_resumido": self.formato_resumido.get(),
            "nombre_anio": os.path.basename(self.ruta_base.get().rstrip(os.sep)),
        }
        ruta_excel = self._obtener_ruta_salida(params, ".xlsx")
        if os.path.exists(ruta_excel):
            if not tk_messagebox.askyesno("Sobrescribir archivo", f"El archivo ya existe:\n{ruta_excel}\n\n¿Deseas sobrescribirlo?"):
                return
        self.progress.start()
        self.btn_generar.config(state='disabled')
        self.actualizar_status("Extrayendo facturas...", "blue")
        threading.Thread(target=self._ejecutar_generar, args=(params,), daemon=True).start()


def main():
    # Usar ttkbootstrap Window en lugar de tk.Tk
    root = ttk.Window(themename="flatly")
    GeneradorFacturasCOTU(root)
    root.mainloop()


if __name__ == "__main__":
    main()
