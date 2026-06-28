"""
Centralised colour palette + QSS stylesheet.
All colours follow the Catppuccin Mocha dark theme.
"""

# ---------------------------------------------------------------------------
# Colour constants
# ---------------------------------------------------------------------------
BG          = "#1e1e2e"   # Window background
CARD        = "#181825"   # Cards / inputs
CARD2       = "#252538"   # Slightly lighter card (headers, sidebar hover)
BORDER      = "#313244"   # Borders
BORDER2     = "#45475a"   # Secondary borders / hover outlines

PRIMARY     = "#89b4fa"   # Primary accent (blue)
PRIMARY_H   = "#74c7ec"   # Primary hover
PRIMARY_P   = "#5bcefa"   # Primary pressed

SUCCESS     = "#a6e3a1"   # Green
WARNING     = "#f9e2af"   # Yellow
ERROR       = "#f38ba8"   # Red
MUTED       = "#cba6f7"   # Purple / muted

TEXT        = "#cdd6f4"   # Main text
SUBTEXT     = "#a6adc8"   # Secondary text / placeholders

SIDEBAR_W   = 200         # Sidebar width in pixels

# ---------------------------------------------------------------------------
# Main QSS stylesheet
# ---------------------------------------------------------------------------
QSS = f"""
/* ===== BASE ===== */
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI Variable", "Segoe UI", "Roboto", sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {BG};
}}

/* ===== SCROLLBARS ===== */
QScrollBar:vertical {{
    background: {CARD};
    width: 10px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER2};
    min-height: 24px;
    border-radius: 5px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: {SUBTEXT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none; background: none; height: 0;
}}
QScrollBar:horizontal {{
    background: {CARD};
    height: 10px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER2};
    min-width: 24px;
    border-radius: 5px;
    margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {SUBTEXT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    border: none; background: none; width: 0;
}}

/* ===== TOOLBAR ===== */
QToolBar {{
    background-color: {CARD};
    border-bottom: 1px solid {BORDER};
    padding: 4px 8px;
    spacing: 4px;
}}
QToolBar QToolButton {{
    background: transparent;
    color: {SUBTEXT};
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}
QToolBar QToolButton:hover {{
    background: {BORDER};
    color: {TEXT};
}}
QToolBar QToolButton:pressed {{
    background: {CARD2};
    color: {PRIMARY};
}}

/* ===== SIDEBAR ===== */
QListWidget#Sidebar {{
    background-color: {CARD};
    border: none;
    border-right: 1px solid {BORDER};
    outline: none;
    padding: 8px 4px;
}}
QListWidget#Sidebar::item {{
    color: {SUBTEXT};
    padding: 10px 14px;
    border-radius: 8px;
    margin: 2px 6px;
    font-size: 13px;
    font-weight: 500;
}}
QListWidget#Sidebar::item:hover {{
    background: {BORDER};
    color: {TEXT};
}}
QListWidget#Sidebar::item:selected {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {PRIMARY}33, stop:1 {PRIMARY}11);
    color: {PRIMARY};
    border-left: 3px solid {PRIMARY};
    font-weight: bold;
}}

/* ===== HEADER WIDGET ===== */
QWidget#Header {{
    background-color: {CARD};
    border-bottom: 1px solid {BORDER};
}}
QLabel#AppTitle {{
    color: {PRIMARY};
    font-size: 16px;
    font-weight: bold;
}}
QLabel#AppSubtitle {{
    color: {SUBTEXT};
    font-size: 11px;
}}
QLabel#StatusReady {{
    color: {SUCCESS};
    font-size: 11px;
    font-weight: bold;
}}
QLabel#StatusBusy {{
    color: {WARNING};
    font-size: 11px;
    font-weight: bold;
}}

/* ===== CARDS ===== */
QFrame#Card {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 0px;
}}
QLabel#CardIcon {{
    font-size: 24px;
    background: transparent;
}}
QLabel#CardValue {{
    color: {TEXT};
    font-size: 20px;
    font-weight: bold;
    background: transparent;
}}
QLabel#CardLabel {{
    color: {SUBTEXT};
    font-size: 11px;
    background: transparent;
}}

/* ===== BUTTONS ===== */
QPushButton {{
    background-color: {BORDER};
    color: {TEXT};
    border: 1px solid {BORDER2};
    border-radius: 7px;
    padding: 7px 16px;
    font-weight: 500;
    min-height: 30px;
}}
QPushButton:hover {{
    background-color: {BORDER2};
    border-color: {SUBTEXT};
}}
QPushButton:pressed {{
    background-color: {CARD};
}}
QPushButton:disabled {{
    background-color: {CARD};
    color: {BORDER2};
    border-color: {BORDER};
}}
QPushButton#BtnPrimary {{
    background-color: {PRIMARY};
    color: #11111b;
    border: none;
    font-weight: bold;
    font-size: 14px;
    min-height: 48px;
    border-radius: 8px;
    letter-spacing: 0.5px;
}}
QPushButton#BtnPrimary:hover {{
    background-color: {PRIMARY_H};
}}
QPushButton#BtnPrimary:pressed {{
    background-color: {PRIMARY_P};
}}
QPushButton#BtnPrimary:disabled {{
    background-color: {BORDER};
    color: {SUBTEXT};
}}
QPushButton#BtnStop {{
    background-color: {ERROR};
    color: #11111b;
    border: none;
    font-weight: bold;
    font-size: 14px;
    min-height: 48px;
    border-radius: 8px;
}}
QPushButton#BtnStop:hover {{
    background-color: #ff7f9e;
}}
QPushButton#BtnSuccess {{
    background-color: {SUCCESS};
    color: #11111b;
    border: none;
    font-weight: bold;
    font-size: 13px;
    min-height: 36px;
    border-radius: 7px;
}}
QPushButton#BtnSuccess:hover {{
    background-color: {PRIMARY_H};
}}
QPushButton#BtnSmall {{
    padding: 4px 10px;
    font-size: 12px;
    min-height: 24px;
    border-radius: 5px;
}}

/* ===== INPUTS ===== */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {CARD};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 6px 10px;
    selection-background-color: {PRIMARY}55;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {PRIMARY};
}}
QLineEdit[readOnly="true"] {{
    color: {SUBTEXT};
}}
QTextEdit#TxtLogs {{
    background-color: #11111b;
    color: {SUCCESS};
    font-family: "Consolas", "Cascadia Code", "Courier New", monospace;
    font-size: 12px;
    border: 1px solid {BORDER};
    border-radius: 7px;
}}

/* ===== COMBOBOX ===== */
QComboBox {{
    background-color: {CARD};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 5px 12px;
    min-width: 6em;
    min-height: 28px;
}}
QComboBox:focus {{
    border: 1px solid {PRIMARY};
}}
QComboBox QAbstractItemView {{
    background-color: {CARD};
    color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: {BORDER};
    selection-color: {PRIMARY};
    padding: 4px;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

/* ===== CHECKBOXES & RADIOBUTTONS ===== */
QCheckBox, QRadioButton {{
    color: {TEXT};
    spacing: 8px;
}}
QCheckBox:hover, QRadioButton:hover {{
    color: {PRIMARY};
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {BORDER2};
    border-radius: 4px;
    background: {CARD};
}}
QRadioButton::indicator {{
    border-radius: 8px;
}}
QCheckBox::indicator:checked {{
    background: {PRIMARY};
    border-color: {PRIMARY};
}}
QRadioButton::indicator:checked {{
    background: {PRIMARY};
    border-color: {PRIMARY};
}}

/* ===== GROUPBOX ===== */
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 1.4em;
    padding-top: 16px;
    background-color: {CARD};
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: {PRIMARY};
}}

/* ===== TABLE ===== */
QTableWidget {{
    background-color: {CARD};
    alternate-background-color: {BG};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    border-radius: 8px;
    outline: none;
}}
QHeaderView::section {{
    background-color: {CARD2};
    color: {TEXT};
    padding: 8px;
    border: none;
    border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    font-weight: bold;
    font-size: 12px;
}}
QHeaderView::section:last {{
    border-right: none;
}}
QTableWidget::item {{
    padding: 6px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {BORDER};
    color: {PRIMARY};
}}

/* ===== LIST WIDGET (generic) ===== */
QListWidget {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 8px 12px;
    border-radius: 5px;
    color: {TEXT};
}}
QListWidget::item:hover {{
    background-color: {BORDER};
}}
QListWidget::item:selected {{
    background-color: {BORDER};
    color: {PRIMARY};
    font-weight: bold;
}}

/* ===== PROGRESS BAR ===== */
QProgressBar {{
    border: none;
    border-radius: 6px;
    background-color: {BORDER};
    text-align: center;
    color: transparent;
    min-height: 10px;
    max-height: 10px;
}}
QProgressBar::chunk {{
    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {PRIMARY}, stop:1 {PRIMARY_H});
    border-radius: 6px;
}}

/* ===== SPLITTER ===== */
QSplitter::handle {{
    background-color: {BORDER};
    width: 1px;
    height: 1px;
}}

/* ===== DRAG DROP FRAME ===== */
QFrame#DropArea {{
    border: 2px dashed {PRIMARY};
    border-radius: 12px;
    background-color: {CARD2};
}}
QFrame#DropArea[dragOver="true"] {{
    border: 2px dashed {SUCCESS};
    background-color: {BORDER};
}}

/* ===== STATUS BAR ===== */
QStatusBar {{
    background-color: {CARD};
    border-top: 1px solid {BORDER};
    color: {SUBTEXT};
    font-size: 12px;
    padding: 2px 8px;
}}
QStatusBar QLabel {{
    background: transparent;
    color: {SUBTEXT};
    font-size: 12px;
    padding: 0 8px;
}}

/* ===== TOOLTIPS ===== */
QToolTip {{
    background-color: {CARD2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}}

/* ===== MESSAGE BOX ===== */
QMessageBox {{
    background-color: {BG};
}}
QMessageBox QLabel {{
    color: {TEXT};
    font-size: 13px;
}}
"""
