# ==============================================================================
# Author:       Victor Caricatte
# Project:      PanVita 2 - Advanced Bioinformatics GUI
# Description:  Interface for Panvita 2
# ==============================================================================

import sys
import os
import json
import shutil
import csv
import multiprocessing
import webbrowser
import sqlite3
from datetime import datetime

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                             QCheckBox, QRadioButton, QSlider, QSpinBox, 
                             QFileDialog, QTextEdit, QStackedWidget, QFrame, 
                             QButtonGroup, QListWidget, QGraphicsDropShadowEffect,
                             QMessageBox, QColorDialog, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QProgressBar, QListWidgetItem, QComboBox,
                             QSystemTrayIcon, QDialog, QLineEdit, QFormLayout, 
                             QDialogButtonBox, QTabWidget, QScrollArea, QTextBrowser,
                             QMenu, QSplitter)
from PyQt6.QtGui import (QPixmap, QFont, QTextCursor, QColor, QImageReader, 
                         QIcon, QPainter, QPdfWriter, QAction, QKeySequence, QShortcut)
from PyQt6.QtCore import (Qt, QProcess, QProcessEnvironment, QPoint, QSize, 
                          QSettings, QThread, pyqtSignal, QTimer, QUrl)

# Try to import WebEngine for Interactive HTML Graphs
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False

# Try to import psutil for Hardware Monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# I18N DICTIONARY (TRANSLATIONS)

LANGUAGES = {
    "EN": {
        "menu_home": "≡   Home", "menu_db": "🗄  Inputs & Databases", "menu_align": "🧬  Filters & Aligner",
        "menu_ncbi": "🌐  NCBI Settings", "menu_term": "💻  Execution Terminal", "menu_res": "📊  Results Viewer",
        "menu_queue": "📝  Queue & History", "menu_help": "📖  Help & Documentation",
        "global_actions": "⚙ Global Actions", "desc_home": "Bioinformatics Software", "sys_check": "<b>System Check:</b>",
        "btn_color": "🎨 Accent Color", "btn_theme": "🌗 Light/Dark", "btn_save_p": "💾 Save Preset",
        "btn_load_p": "📂 Load Preset", "btn_update": "🔄 Update Dependencies", "btn_add_queue": "➕ ADD TO QUEUE",
        "btn_run": "▶ START QUEUE", "btn_stop": "🛑 STOP / CANCEL", "lbl_status_idle": "Status: Idle", 
        "gb_files": "Input Files (Drag & Drop | Double-Click to Remove)",
        "btn_browse": "Browse Files", "btn_clear": "Clear List", "gb_db": "Target Databases", "cb_custom": "Custom DB (FASTA)",
        "gb_align": "Alignment Engine & CPUs", "rb_auto": "Automatic (Recommended)", "rb_diamond": "DIAMOND Only (-diamond)",
        "rb_blast": "BLAST Only (-blast)", "rb_both": "Both DIAMOND and BLAST (-both)", "cb_force_d": "Force Local DIAMOND (-d)",
        "lbl_threads": "CPU Threads:", "gb_thr": "Filtering Thresholds", "lbl_i": "Minimum Identity:", "lbl_c": "Minimum Coverage:",
        "gb_ncbi": "NCBI Integration & Modifiers", "btn_csv": "Import Table (CSV/TSV/TXT)", "cb_b": "Download GenBank (-b)",
        "cb_a": "Annotate via PROKKA (-a)", "cb_g": "Download FASTA (-g)", "cb_m": "Download Metadata (-m)",
        "cb_s": "Locus_Tag matches strain (-s)", "gb_out": "Outputs and Plotting", "rb_pdf": "Graphs in PDF",
        "rb_png": "Graphs in PNG", "cb_save": "Save found genes (.faa) (-save-genes)", "cb_keep": "Keep temporary files (-keep)",
        "btn_exp_log": "💾 Export Log as .TXT", "btn_clear_term": "🧹 Clear Terminal", "btn_load_res": "📂 Open CSV Result", 
        "btn_exp_pdf": "📄 Export PDF Report", "btn_paths": "⚙ Configure Paths", "btn_load_graph": "🖼 Load PNG Graph", 
        "lbl_search": "🔍 Filter Results:", "btn_exp_filt": "💾 Export Filtered CSV", "btn_load_html": "🌐 Load Interactive HTML Graph",
        "metrics_hits": "Total Hits: ", "metrics_id": "Avg Identity: ", "metrics_db": "Top DB: ", "q_title": "Task Queue", 
        "q_hist": "Run History", "q_clear": "Clear Queue", "h_clear": "Clear History"
    },
    "PT": {
        "menu_home": "≡   Início", "menu_db": "🗄  Entradas e Bancos", "menu_align": "🧬  Filtros e Alinhador",
        "menu_ncbi": "🌐  Configurações NCBI", "menu_term": "💻  Terminal de Execução", "menu_res": "📊  Visualizar Resultados",
        "menu_queue": "📝  Fila e Histórico", "menu_help": "📖  Ajuda e Documentação",
        "global_actions": "⚙ Ações Globais", "desc_home": "Software de Bioinformática", "sys_check": "<b>Verificação do Sistema:</b>",
        "btn_color": "🎨 Cor de Destaque", "btn_theme": "🌗 Claro/Escuro", "btn_save_p": "💾 Salvar Preset",
        "btn_load_p": "📂 Carregar Preset", "btn_update": "🔄 Atualizar Dependências", "btn_add_queue": "➕ ADICIONAR À FILA",
        "btn_run": "▶ INICIAR FILA", "btn_stop": "🛑 PARAR / CANCELAR", "lbl_status_idle": "Status: Ocioso", 
        "gb_files": "Arquivos de Entrada (Arraste aqui | Duplo-clique remove)",
        "btn_browse": "Procurar Arquivos", "btn_clear": "Limpar Lista", "gb_db": "Bancos de Dados Alvo", "cb_custom": "Banco Customizado (FASTA)",
        "gb_align": "Motor de Alinhamento e CPUs", "rb_auto": "Automático (Recomendado)", "rb_diamond": "Apenas DIAMOND (-diamond)",
        "rb_blast": "Apenas BLAST (-blast)", "rb_both": "Ambos (-both)", "cb_force_d": "Forçar DIAMOND local (-d)",
        "lbl_threads": "Threads de CPU:", "gb_thr": "Limiares de Filtragem", "lbl_i": "Identidade Mínima:", "lbl_c": "Cobertura Mínima:",
        "gb_ncbi": "Integração NCBI e Modificadores", "btn_csv": "Importar Tabela (CSV/TSV/TXT)", "cb_b": "Baixar GenBank (-b)",
        "cb_a": "Anotar via PROKKA (-a)", "cb_g": "Baixar FASTA (-g)", "cb_m": "Baixar Metadata (-m)",
        "cb_s": "Locus_Tag igual à cepa (-s)", "gb_out": "Saídas e Gráficos", "rb_pdf": "Gráficos em PDF",
        "rb_png": "Gráficos em PNG", "cb_save": "Salvar genes encontrados (.faa)", "cb_keep": "Manter arquivos temporários (-keep)",
        "btn_exp_log": "💾 Exportar Log (.TXT)", "btn_clear_term": "🧹 Limpar Terminal", "btn_load_res": "📂 Abrir Resultado CSV", 
        "btn_exp_pdf": "📄 Exportar Relatório PDF", "btn_paths": "⚙ Configurar Caminhos", "btn_load_graph": "🖼 Carregar Gráfico PNG", 
        "lbl_search": "🔍 Filtrar Resultados:", "btn_exp_filt": "💾 Exportar CSV Filtrado", "btn_load_html": "🌐 Carregar Gráfico Interativo HTML",
        "metrics_hits": "Total de Hits: ", "metrics_id": "Identidade Média: ", "metrics_db": "Banco Topo: ", "q_title": "Fila de Tarefas", 
        "q_hist": "Histórico de Execuções", "q_clear": "Limpar Fila", "h_clear": "Limpar Histórico"
    }
}

# MULTITHREADING WORKER FOR CSV LOADING

class CSVLoaderThread(QThread):
    finished = pyqtSignal(list, list) # headers, data_rows
    error = pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            with open(self.path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                data = list(reader)
                if not data or len(data) < 2:
                    self.error.emit("Empty or invalid CSV file.")
                    return
                # Convert numeric columns to float for proper sorting in QTableWidget
                processed_data = []
                for row in data[1:]:
                    processed_row = []
                    for val in row:
                        try:
                            processed_row.append(float(val))
                        except ValueError:
                            processed_row.append(val)
                    processed_data.append(processed_row)
                self.finished.emit(data[0], processed_data)
        except Exception as e:
            self.error.emit(str(e))

# CUSTOM DIALOG FOR DEPENDENCY PATHS

class PathConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Executable Paths")
        self.setMinimumWidth(550)
        
        self.settings = QSettings("VictorCaricatte", "PanVita2")
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("<b>Important:</b> Select the <b>DIRECTORIES (folders)</b> where the executables are located, not the files themselves (except for the PanVita script).")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #bd93f9; margin-bottom: 10px;")
        layout.addWidget(lbl_info)

        form_layout = QFormLayout()
        
        def create_path_row(label_text, setting_key, is_file=False):
            hbox = QHBoxLayout()
            le = QLineEdit(self.settings.value(setting_key, "", type=str))
            btn = QPushButton("...")
            btn.setFixedWidth(30)
            if is_file:
                btn.clicked.connect(lambda: self.browse_file(le))
            else:
                btn.clicked.connect(lambda: self.browse_dir(le))
            hbox.addWidget(le)
            hbox.addWidget(btn)
            form_layout.addRow(label_text, hbox)
            return le

        self.le_panvita = create_path_row("PanVita Core Script (.py):", "path_panvita", is_file=True)
        self.le_diamond = create_path_row("DIAMOND Directory:", "dir_diamond")
        self.le_blast = create_path_row("BLAST Directory (makeblastdb, blastp...):", "dir_blast")
        self.le_prokka = create_path_row("PROKKA Directory:", "dir_prokka")
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse_file(self, line_edit):
        path, _ = QFileDialog.getOpenFileName(self, "Select PanVita Python Script", "", "Python Scripts (*.py);;All Files (*)")
        if path: line_edit.setText(path)

    def browse_dir(self, line_edit):
        path = QFileDialog.getExistingDirectory(self, "Select Directory with Executables")
        if path: line_edit.setText(path)
        
    def accept(self):
        self.settings.setValue("path_panvita", self.le_panvita.text() if self.le_panvita.text() else "panvita.py")
        self.settings.setValue("dir_diamond", self.le_diamond.text())
        self.settings.setValue("dir_blast", self.le_blast.text())
        self.settings.setValue("dir_prokka", self.le_prokka.text())
        super().accept()

# CUSTOM WIDGETS (Drag & Drop Lists and Tables with Visual Feedback)

class DropListWidget(QListWidget):
    def __init__(self, add_file_callback, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.add_file_callback = add_file_callback
        self.default_style = ""

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): 
            event.accept()
            self.default_style = self.styleSheet()
            accent = QSettings("VictorCaricatte", "PanVita2").value("accent_color", "#bd93f9")
            self.setStyleSheet(f"border: 2px dashed {accent}; background-color: rgba(189, 147, 249, 0.1);")
        else: event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.default_style)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        self.setStyleSheet(self.default_style)
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        self.add_file_callback(files)

class DropTableWidget(QTableWidget):
    def __init__(self, load_csv_callback, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.load_csv_callback = load_csv_callback
        self.default_style = ""

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and event.mimeData().urls()[0].toLocalFile().lower().endswith('.csv'):
            event.accept()
            self.default_style = self.styleSheet()
            accent = QSettings("VictorCaricatte", "PanVita2").value("accent_color", "#bd93f9")
            self.setStyleSheet(f"border: 2px dashed {accent};")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.default_style)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() and event.mimeData().urls()[0].toLocalFile().lower().endswith('.csv'):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.setStyleSheet(self.default_style)
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.load_csv_callback(file_path)


# NUMERIC TABLE WIDGET ITEM (For accurate sorting)
class NumericItem(QTableWidgetItem):
    def __init__(self, value):
        super().__init__(str(value))
        self.value = value

    def __lt__(self, other):
        if isinstance(self.value, float) and isinstance(other.value, float):
            return self.value < other.value
        return super().__lt__(other)

# DYNAMIC THEME GENERATOR

def get_stylesheet(is_dark_mode, accent_color):
    if is_dark_mode:
        bg_main = "#282c34"
        bg_menu = "#1b1b27"
        bg_box = "#21252d"
        text_main = "#f8f8f2"
        text_muted = "#8a95aa"
        border_color = "#44475a"
        hover_color = "#282a36"
        input_bg = "#1b1b27"
        header_bg = "#282a36"
    else:
        bg_main = "#f5f6fa"
        bg_menu = "#dcdde1"
        bg_box = "#e8e8e8"
        text_main = "#2f3640"
        text_muted = "#718093"
        border_color = "#bdc3c7"
        hover_color = "#ecf0f1"
        input_bg = "#ffffff"
        header_bg = "#bdc3c7"

    accent_encoded = accent_color.replace('#', '%23')
    svg_x = f"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='{accent_encoded}' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'><line x1='18' y1='6' x2='6' y2='18'/><line x1='6' y1='6' x2='18' y2='18'/></svg>"

    return f"""
    /* ================== GENERAL ================== */
    QWidget {{
        color: {text_main};
        font-family: 'Segoe UI', sans-serif;
        font-size: 10pt;
    }}
    QToolTip {{
        background-color: {bg_menu};
        color: {text_main};
        border: 1px solid {border_color};
        padding: 4px;
        border-radius: 4px;
        font-size: 9pt;
    }}

    /* ================== SIDEBAR (LEFT MENU) ================== */
    #LeftMenuBg, #TopLogoInfo {{
        background-color: {bg_menu};
    }}
    #TitleLeftApp {{
        font-size: 13pt;
        font-weight: bold;
        color: {accent_color};
    }}
    #TitleLeftDescription {{
        font-size: 8pt;
        color: {text_muted};
    }}
    #MenuButton {{
        background-color: transparent;
        border: none;
        text-align: left;
        padding-left: 20px;
        color: {text_muted};
        font-weight: bold;
    }}
    #MenuButton:hover {{
        background-color: {hover_color};
        color: {text_main};
    }}
    #MenuButton:checked {{
        background-color: {hover_color};
        color: {text_main};
        border-left: 3px solid {accent_color};
    }}

    /* ================== LEFT BOX (SECONDARY PANEL) ================== */
    #LeftBoxBg {{
        background-color: {bg_main};
    }}
    #LeftBoxHeader {{
        background-color: {accent_color};
        border-top-left-radius: 0px;
    }}
    #LeftBoxHeaderLabel {{
        color: #ffffff;
        font-weight: bold;
        font-size: 11pt;
    }}
    #LeftBoxBody {{
        background-color: {bg_box};
    }}

    /* ================== MAIN CONTENT ================== */
    #MainBg {{
        background-color: {bg_main};
    }}
    #TopBar {{
        background-color: {bg_menu};
    }}
    #RightButtons QPushButton {{
        background-color: transparent;
        border: none;
        font-weight: bold;
        color: {text_muted};
    }}
    #RightButtons QPushButton:hover {{
        background-color: {hover_color};
        color: {text_main};
    }}
    #CloseButton:hover {{
        background-color: #ff5555;
    }}

    /* ================== INTERNAL COMPONENTS ================== */
    QGroupBox {{
        border: 1px solid {border_color};
        border-radius: 8px;
        margin-top: 20px;
        font-weight: bold;
        color: {accent_color};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 15px;
        padding: 0 5px;
    }}
    QPushButton {{
        background-color: {border_color};
        border: 1px solid {border_color};
        border-radius: 5px;
        padding: 8px 15px;
        font-weight: bold;
        color: {text_main};
    }}
    QPushButton:hover {{
        background-color: {accent_color};
        border: 1px solid {accent_color};
        color: #ffffff;
    }}
    
    /* Master Button */
    #RunMasterBtn {{
        background-color: #50fa7b;
        color: #282a36;
        font-size: 11pt;
        border: none;
    }}
    #RunMasterBtn:hover {{
        background-color: #40c863;
    }}
    #RunMasterBtn:disabled {{
        background-color: {border_color};
        color: {text_muted};
    }}
    
    #AddQueueBtn {{
        background-color: #f1fa8c;
        color: #282a36;
        font-size: 10pt;
        border: none;
    }}
    #AddQueueBtn:hover {{
        background-color: #d7e07b;
    }}

    /* Inputs, Lists, Tables and TextBrowser */
    QListWidget, QTextEdit, QTableWidget, QTabWidget::pane, QTextBrowser {{
        background-color: {input_bg};
        border: 1px solid {border_color};
        border-radius: 5px;
        padding: 5px;
        gridline-color: {border_color};
    }}
    QTextEdit {{
        color: {accent_color};
        font-family: Consolas, monospace;
    }}
    
    /* Help Documentation Link Colors */
    QTextBrowser a {{
        color: {accent_color};
    }}
    
    /* QTabWidget */
    QTabBar::tab {{
        background: {bg_box};
        border: 1px solid {border_color};
        padding: 8px 12px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        color: {text_muted};
    }}
    QTabBar::tab:selected {{
        background: {accent_color};
        color: #ffffff;
    }}

    /* Table Headers */
    QHeaderView::section {{
        background-color: {header_bg};
        color: {text_main};
        border: 1px solid {border_color};
        padding: 4px;
        font-weight: bold;
    }}
    QTableCornerButton::section {{
        background-color: {header_bg};
        border: 1px solid {border_color};
    }}
    
    /* Context Menu */
    QMenu {{
        background-color: {bg_menu};
        color: {text_main};
        border: 1px solid {border_color};
    }}
    QMenu::item:selected {{
        background-color: {accent_color};
        color: #ffffff;
    }}

    /* Checkboxes & Radio Buttons */
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 2px solid {border_color};
        background-color: {input_bg};
    }}
    QRadioButton::indicator {{
        border-radius: 9px;
    }}
    
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background-color: transparent;
        border: 2px solid {accent_color};
        image: url("{svg_x}");
    }}

    /* Sliders */
    QSlider::groove:horizontal {{
        background: {input_bg};
        height: 8px;
        border-radius: 4px;
    }}
    QSlider::sub-page:horizontal {{
        background: {accent_color};
        border-radius: 4px;
    }}
    QSlider::handle:horizontal {{
        background: {text_main};
        width: 14px;
        margin: -3px 0;
        border-radius: 7px;
        border: 1px solid {border_color};
    }}

    /* SpinBoxes & ComboBoxes & LineEdits */
    QSpinBox, QComboBox, QLineEdit {{
        background-color: {input_bg};
        border: 1px solid {border_color};
        padding: 4px;
        border-radius: 4px;
        color: {text_main};
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: {bg_box};
        border: 1px solid {border_color};
        border-radius: 4px;
        text-align: center;
        color: {text_main};
        font-weight: bold;
    }}
    QProgressBar::chunk {{
        background-color: {accent_color};
        border-radius: 3px;
    }}
    
    /* Hardware Bar Overrides */
    #HwBar {{
        font-size: 8pt;
        border: none;
        background-color: transparent;
        color: {text_muted};
    }}
    #HwBar::chunk {{
        background-color: {accent_color};
        border-radius: 2px;
    }}
    
    /* Metrics Dash */
    #MetricBox {{
        background-color: {bg_box};
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
    }}
    #MetricVal {{
        font-size: 14pt;
        font-weight: bold;
        color: {accent_color};
    }}
    """

class PanVitaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(1300, 800)

        # QSettings (Continuous Memory)
        self.settings = QSettings("VictorCaricatte", "PanVita2")
        self.is_dark_mode = self.settings.value("is_dark_mode", True, type=bool)
        self.accent_color = self.settings.value("accent_color", "#bd93f9", type=str)
        self.last_dir = self.settings.value("last_dir", "", type=str)
        self.lang = self.settings.value("lang", "EN", type=str)

        # State Variables
        self.dragPos = QPoint()
        self.input_files = []
        self.csv_file = ""
        self.custom_db_path = ""
        self.process = None 
        self.csv_thread = None
        self.current_run_results = None
        
        # Queue System
        self.task_queue = []
        self.is_processing_queue = False
        self.current_task_start_time = None

        # System Tray Notification
        self.tray_icon = QSystemTrayIcon(self)
        pix_logo = self.load_logo_pixmap(64)
        if not pix_logo.isNull():
            self.tray_icon.setIcon(QIcon(pix_logo))
        self.tray_icon.show()
        
        # SQLite DB Initialization
        self.init_db()
        
        self.init_ui()
        self.apply_theme()
        self.apply_language()
        self.run_preflight_check()
        self.setup_shortcuts()
        self.load_history()
        
        # Hardware Monitor Setup
        if PSUTIL_AVAILABLE:
            self.hw_timer = QTimer(self)
            self.hw_timer.timeout.connect(self.update_hardware_monitor)
            self.hw_timer.start(2000) # Update every 2 seconds

    def init_db(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "panvita_history.db")
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS history 
                             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                              date TEXT, 
                              files TEXT, 
                              dbs TEXT, 
                              duration TEXT, 
                              status TEXT)''')
        self.conn.commit()

    def load_logo_pixmap(self, size):
        for ext in ["png", "jpg", "jpeg"]:
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"logo.{ext}")
            if os.path.exists(logo_path):
                reader = QImageReader(logo_path)
                reader.setScaledSize(QSize(size, size))
                img = reader.read()
                if not img.isNull():
                    return QPixmap.fromImage(img)
        return QPixmap()

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.toggle_run_state)
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.browse_files)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_preset)

    def apply_theme(self):
        stylesheet = get_stylesheet(self.is_dark_mode, self.accent_color)
        self.central_widget.setStyleSheet(stylesheet)
        self.populate_help_page() 

    def apply_language(self):
        t = LANGUAGES[self.lang]
        
        # Sidebar
        self.btn_home.setText(t["menu_home"])
        self.btn_db.setText(t["menu_db"])
        self.btn_align.setText(t["menu_align"])
        self.btn_ncbi.setText(t["menu_ncbi"])
        self.btn_term.setText(t["menu_term"])
        self.btn_res.setText(t["menu_res"])
        self.btn_queue.setText(t["menu_queue"])
        self.btn_help.setText(t["menu_help"])
        
        # Left Box
        self.lbl_box_title.setText(t["global_actions"])
        self.lbl_app_desc.setText(t["desc_home"])
        
        self.btn_color.setText(t["btn_color"])
        self.btn_theme.setText(t["btn_theme"])
        self.btn_save_p.setText(t["btn_save_p"])
        self.btn_load_p.setText(t["btn_load_p"])
        self.btn_update.setText(t["btn_update"])
        self.btn_config_paths.setText(t["btn_paths"])
        
        self.btn_add_to_queue.setText(t["btn_add_queue"])
        
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.btn_run_master.setText(t["btn_stop"])
        else:
            self.btn_run_master.setText(t["btn_run"])
            
        # Databases Page
        self.gb_files.setTitle(t["gb_files"])
        self.btn_add.setText(t["btn_browse"])
        self.btn_clear.setText(t["btn_clear"])
        self.gb_db.setTitle(t["gb_db"])
        self.cb_custom.setText(t["cb_custom"])
        
        # Alignment Page
        self.gb_alg.setTitle(t["gb_align"])
        self.rb_auto.setText(t["rb_auto"])
        self.rb_diamond.setText(t["rb_diamond"])
        self.rb_blast.setText(t["rb_blast"])
        self.rb_both.setText(t["rb_both"])
        self.cb_force_d.setText(t["cb_force_d"])
        self.lbl_threads.setText(t["lbl_threads"])
        self.gb_thr.setTitle(t["gb_thr"])
        self.lbl_i.setText(t["lbl_i"])
        self.lbl_c.setText(t["lbl_c"])
        
        # NCBI Page
        self.gb_ncbi.setTitle(t["gb_ncbi"])
        self.btn_csv.setText(t["btn_csv"])
        self.ncbi_cbs["-b"].setText(t["cb_b"])
        self.ncbi_cbs["-a"].setText(t["cb_a"])
        self.ncbi_cbs["-g"].setText(t["cb_g"])
        self.ncbi_cbs["-m"].setText(t["cb_m"])
        self.ncbi_cbs["-s"].setText(t["cb_s"])
        
        self.gb_out.setTitle(t["gb_out"])
        self.rb_pdf.setText(t["rb_pdf"])
        self.rb_png.setText(t["rb_png"])
        self.cb_save.setText(t["cb_save"])
        self.cb_keep.setText(t["cb_keep"])
        
        # Terminal & Results Pages
        self.btn_export_log.setText(t["btn_exp_log"])
        self.btn_clear_term.setText(t["btn_clear_term"])
        self.btn_load_res.setText(t["btn_load_res"])
        self.btn_export_pdf.setText(t["btn_exp_pdf"])
        self.btn_export_filtered.setText(t["btn_exp_filt"])
        self.btn_load_graph.setText(t["btn_load_graph"])
        if WEB_ENGINE_AVAILABLE:
            self.btn_load_html.setText(t["btn_load_html"])
        self.lbl_search_table.setText(t["lbl_search"])
        
        # Queue Page
        self.gb_queue.setTitle(t["q_title"])
        self.gb_history.setTitle(t["q_hist"])
        self.btn_clear_queue.setText(t["q_clear"])
        self.btn_clear_history.setText(t["h_clear"])
        
        # Populate Help Data
        self.populate_help_page()

        # Update current top title
        current_idx = self.stacked_widget.currentIndex()
        for btn in self.nav_group.buttons():
            if self.nav_group.id(btn) == current_idx:
                self.set_page(current_idx, btn.text())
                break

    def change_accent_color(self):
        color = QColorDialog.getColor(QColor(self.accent_color), self, "Select Accent Color")
        if color.isValid():
            self.accent_color = color.name()
            self.apply_theme()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def change_language(self, index):
        self.lang = "EN" if index == 0 else "PT"
        self.apply_language()
        self.run_preflight_check()

    def open_path_config(self):
        dlg = PathConfigDialog(self)
        if dlg.exec():
            self.run_preflight_check()

    def closeEvent(self, event):
        self.settings.setValue("is_dark_mode", self.is_dark_mode)
        self.settings.setValue("accent_color", self.accent_color)
        self.settings.setValue("last_dir", self.last_dir)
        self.settings.setValue("lang", self.lang)
        self.conn.close()
        
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
        event.accept()

    
    # PRE-FLIGHT CHECK
    
    def run_preflight_check(self):
        status_lines = [LANGUAGES[self.lang]["sys_check"]]
        
        panvita_path = self.settings.value("path_panvita", "panvita.py", type=str)
        if os.path.exists(panvita_path) or shutil.which(panvita_path):
            status_lines.append(f"• PanVita Core: <span style='color:#50fa7b;'>✅ Found</span>")
        else:
            status_lines.append(f"• PanVita Core: <span style='color:#ff5555;'>❌ Missing</span>")

        tools = [("BLAST", "dir_blast", "blastp"), ("DIAMOND", "dir_diamond", "diamond"), ("PROKKA", "dir_prokka", "prokka")]

        for name, setting_key, exe_name in tools:
            directory = self.settings.value(setting_key, "", type=str)
            if directory and os.path.isdir(directory):
                target_exe = os.path.join(directory, exe_name)
                if os.name == 'nt' and not target_exe.endswith('.exe'): target_exe += '.exe'
                if os.path.exists(target_exe):
                    status_lines.append(f"• {name}: <span style='color:#50fa7b;'>✅ Custom</span>")
                else:
                    status_lines.append(f"• {name}: <span style='color:#ff5555;'>❌ Custom Fail</span>")
            else:
                if shutil.which(exe_name):
                    status_lines.append(f"• {name}: <span style='color:#50fa7b;'>✅ System PATH</span>")
                else:
                    status_lines.append(f"• {name}: <span style='color:#ff5555;'>❌ Missing</span>")
        
        if PSUTIL_AVAILABLE:
            status_lines.append(f"• HW Monitor: <span style='color:#50fa7b;'>✅ Active</span>")
        else:
            status_lines.append(f"• HW Monitor: <span style='color:#f1fa8c;'>⚠️ pip install psutil</span>")
            
        self.lbl_sys_check.setText("<br>".join(status_lines))

    def validate_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for _ in range(5):
                    line = f.readline()
                    if not line: break
                    if line.startswith(">") or "LOCUS" in line: return True
            return False
        except: 
            return False

    def save_preset(self):
        preset = {
            "identity": self.spn_i.value(), "coverage": self.spn_c.value(),
            "threads": self.spn_threads.value(),
            "databases": {k: v.isChecked() for k, v in self.db_checkboxes.items()},
            "ncbi": {k: v.isChecked() for k, v in self.ncbi_cbs.items()},
            "aligner": { "-diamond": self.rb_diamond.isChecked(), "-blast": self.rb_blast.isChecked(), "-both": self.rb_both.isChecked() },
            "force_d": self.cb_force_d.isChecked(),
            "outputs": { "pdf": self.rb_pdf.isChecked(), "png": self.rb_png.isChecked(), "save_genes": self.cb_save.isChecked(), "keep_temp": self.cb_keep.isChecked() }
        }
        path, _ = QFileDialog.getSaveFileName(self, "Save Preset", self.last_dir, "JSON Files (*.json)")
        if path:
            self.last_dir = os.path.dirname(path)
            try:
                with open(path, 'w', encoding='utf-8') as f: json.dump(preset, f, indent=4)
                QMessageBox.information(self, "Success", "Preset saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save preset:\n{str(e)}")

    def load_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Preset", self.last_dir, "JSON Files (*.json)")
        if path:
            self.last_dir = os.path.dirname(path)
            try:
                with open(path, 'r', encoding='utf-8') as f: preset = json.load(f)
                self.spn_i.setValue(preset.get("identity", 70))
                self.spn_c.setValue(preset.get("coverage", 70))
                self.spn_threads.setValue(preset.get("threads", multiprocessing.cpu_count()))
                
                for k, v in preset.get("databases", {}).items():
                    if k in self.db_checkboxes: self.db_checkboxes[k].setChecked(v)
                for k, v in preset.get("ncbi", {}).items():
                    if k in self.ncbi_cbs: self.ncbi_cbs[k].setChecked(v)
                
                aligners = preset.get("aligner", {})
                if aligners.get("-diamond"): self.rb_diamond.setChecked(True)
                elif aligners.get("-blast"): self.rb_blast.setChecked(True)
                elif aligners.get("-both"): self.rb_both.setChecked(True)
                else: self.rb_auto.setChecked(True)
                
                self.cb_force_d.setChecked(preset.get("force_d", False))
                outputs = preset.get("outputs", {})
                if outputs.get("pdf"): self.rb_pdf.setChecked(True)
                if outputs.get("png"): self.rb_png.setChecked(True)
                self.cb_save.setChecked(outputs.get("save_genes", False))
                self.cb_keep.setChecked(outputs.get("keep_temp", False))
                QMessageBox.information(self, "Success", "Preset loaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load preset:\n{str(e)}")

    
    # NITIALIZATION
    
    def init_ui(self):
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.central_widget.setGraphicsEffect(shadow)

        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        #  LEFT MENU 
        self.left_menu = QFrame()
        self.left_menu.setObjectName("LeftMenuBg")
        self.left_menu.setFixedWidth(240)
        left_menu_layout = QVBoxLayout(self.left_menu)
        left_menu_layout.setContentsMargins(0, 0, 0, 0)
        left_menu_layout.setSpacing(0)

        top_logo_info = QFrame()
        top_logo_info.setObjectName("TopLogoInfo")
        top_logo_info.setMinimumHeight(80)
        top_logo_layout = QHBoxLayout(top_logo_info)
        top_logo_layout.setContentsMargins(15, 10, 15, 10)
        
        lbl_logo = QLabel()
        pix = self.load_logo_pixmap(40)
        if not pix.isNull(): lbl_logo.setPixmap(pix)
        top_logo_layout.addWidget(lbl_logo)

        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 0, 0, 0)
        lbl_title = QLabel("PanVita 2")
        lbl_title.setObjectName("TitleLeftApp")
        
        self.lbl_app_desc = QLabel("Bioinformatics Software")
        self.lbl_app_desc.setObjectName("TitleLeftDescription")
        
        title_layout.addWidget(lbl_title)
        title_layout.addWidget(self.lbl_app_desc)
        top_logo_layout.addWidget(title_frame)
        
        left_menu_layout.addWidget(top_logo_info)

        self.nav_group = QButtonGroup(self)
        self.btn_home = self.create_menu_button("≡   Home", 0)
        self.btn_db = self.create_menu_button("🗄  Inputs & Databases", 1)
        self.btn_align = self.create_menu_button("🧬  Filters & Aligner", 2)
        self.btn_ncbi = self.create_menu_button("🌐  NCBI Settings", 3)
        self.btn_term = self.create_menu_button("💻  Execution Terminal", 4)
        self.btn_res = self.create_menu_button("📊  Results Viewer", 5)
        self.btn_queue = self.create_menu_button("📝  Queue & History", 6)
        self.btn_help = self.create_menu_button("📖  Help & Documentation", 7)

        for btn in [self.btn_home, self.btn_db, self.btn_align, self.btn_ncbi, self.btn_term, self.btn_res, self.btn_queue, self.btn_help]:
            left_menu_layout.addWidget(btn)
        left_menu_layout.addStretch()

        main_layout.addWidget(self.left_menu)

        #  LEFT BOX 
        self.left_box = QFrame()
        self.left_box.setObjectName("LeftBoxBg")
        self.left_box.setFixedWidth(240)
        left_box_layout = QVBoxLayout(self.left_box)
        left_box_layout.setContentsMargins(0, 0, 0, 0)
        left_box_layout.setSpacing(0)

        box_header = QFrame()
        box_header.setObjectName("LeftBoxHeader")
        box_header.setFixedHeight(45)
        header_layout = QHBoxLayout(box_header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        self.lbl_box_title = QLabel("⚙ Global Actions")
        self.lbl_box_title.setObjectName("LeftBoxHeaderLabel")
        
        header_layout.addWidget(self.lbl_box_title)
        left_box_layout.addWidget(box_header)

        box_body = QFrame()
        box_body.setObjectName("LeftBoxBody")
        body_layout = QVBoxLayout(box_body)
        body_layout.setContentsMargins(20, 20, 20, 20)
        body_layout.setSpacing(10)

        lbl_info = QLabel("<b>PanVita 2</b><br>Author: Victor Caricatte")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_info.setObjectName("TitleLeftDescription")
        
        self.lbl_sys_check = QLabel("<b>System Check:</b>")
        self.lbl_sys_check.setObjectName("TitleLeftDescription")
        self.lbl_sys_check.setWordWrap(True)

        self.cmb_lang = QComboBox()
        self.cmb_lang.addItems(["English", "Português"])
        self.cmb_lang.setCurrentIndex(0 if self.lang == "EN" else 1)
        self.cmb_lang.currentIndexChanged.connect(self.change_language)

        self.btn_color = QPushButton("🎨 Accent Color")
        self.btn_color.clicked.connect(self.change_accent_color)
        
        self.btn_theme = QPushButton("🌗 Light/Dark")
        self.btn_theme.clicked.connect(self.toggle_theme)

        self.btn_config_paths = QPushButton("⚙ Configure Paths")
        self.btn_config_paths.clicked.connect(self.open_path_config)
        
        self.btn_save_p = QPushButton("💾 Save Preset")
        self.btn_save_p.clicked.connect(self.save_preset)
        
        self.btn_load_p = QPushButton("📂 Load Preset")
        self.btn_load_p.clicked.connect(self.load_preset)

        self.btn_update = QPushButton("🔄 Update Dependencies")
        self.btn_update.clicked.connect(self.run_update)

        self.btn_add_to_queue = QPushButton("➕ ADD TO QUEUE")
        self.btn_add_to_queue.setObjectName("AddQueueBtn")
        self.btn_add_to_queue.clicked.connect(self.add_to_queue)
        self.btn_add_to_queue.setFixedHeight(35)

        self.btn_run_master = QPushButton("▶ START QUEUE")
        self.btn_run_master.setObjectName("RunMasterBtn")
        self.btn_run_master.clicked.connect(self.toggle_run_state)
        self.btn_run_master.setFixedHeight(45)

        for w in [lbl_info, self.cmb_lang, self.lbl_sys_check, self.btn_config_paths, self.btn_color, self.btn_theme, self.btn_save_p, self.btn_load_p, self.btn_update]:
            body_layout.addWidget(w)
            
        body_layout.addStretch()
        body_layout.addWidget(self.btn_add_to_queue)
        body_layout.addWidget(self.btn_run_master)

        left_box_layout.addWidget(box_body)
        main_layout.addWidget(self.left_box)

        #  RIGHT BOX (MAIN) 
        self.right_box = QFrame()
        self.right_box.setObjectName("MainBg")
        right_box_layout = QVBoxLayout(self.right_box)
        right_box_layout.setContentsMargins(0, 0, 0, 0)
        right_box_layout.setSpacing(0)

        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(45)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(10, 0, 10, 0)

        top_bar.mousePressEvent = self.mousePressEvent
        top_bar.mouseMoveEvent = self.mouseMoveEvent

        self.lbl_top_title = QLabel("PanVita 2 - Home")
        self.lbl_top_title.setObjectName("TitleLeftDescription")
        self.lbl_top_title.setStyleSheet("font-weight: bold;")
        top_bar_layout.addWidget(self.lbl_top_title)
        top_bar_layout.addStretch()

        right_buttons = QFrame()
        right_buttons.setObjectName("RightButtons")
        rb_layout = QHBoxLayout(right_buttons)
        rb_layout.setContentsMargins(0, 0, 0, 0)
        rb_layout.setSpacing(0)
        
        btn_min = QPushButton("🗕")
        btn_min.setFixedSize(40, 45)
        btn_min.clicked.connect(self.showMinimized)
        
        btn_max = QPushButton("🗖")
        btn_max.setFixedSize(40, 45)
        btn_max.clicked.connect(self.toggle_maximize)
        
        btn_close = QPushButton("✕")
        btn_close.setObjectName("CloseButton")
        btn_close.setFixedSize(40, 45)
        btn_close.clicked.connect(self.close)

        for b in [btn_min, btn_max, btn_close]: rb_layout.addWidget(b)
        top_bar_layout.addWidget(right_buttons)

        right_box_layout.addWidget(top_bar)

        self.stacked_widget = QStackedWidget()
        right_box_layout.addWidget(self.stacked_widget)

        self.build_page_home()
        self.build_page_db()
        self.build_page_align()
        self.build_page_ncbi()
        self.build_page_terminal()
        self.build_page_results()
        self.build_page_queue_history()
        self.build_page_help()

        # BOTTOM BAR WITH PROGRESS AND HW MONITORS
        bottom_bar = QFrame()
        bottom_bar.setFixedHeight(30)
        bottom_bar.setObjectName("TopBar")
        bb_layout = QHBoxLayout(bottom_bar)
        bb_layout.setContentsMargins(10, 0, 10, 0)
        
        lbl_bb_left = QLabel("By: Victor Caricatte")
        lbl_bb_left.setObjectName("TitleLeftDescription")
        
        # Hardware bars (if psutil)
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setObjectName("HwBar")
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setFormat("CPU: %p%")
        self.cpu_bar.setFixedWidth(100)
        
        self.ram_bar = QProgressBar()
        self.ram_bar.setObjectName("HwBar")
        self.ram_bar.setRange(0, 100)
        self.ram_bar.setFormat("RAM: %p%")
        self.ram_bar.setFixedWidth(100)
        
        self.lbl_status = QLabel("Status: Idle")
        self.lbl_status.setObjectName("TitleLeftDescription")
        self.lbl_status.setFixedWidth(200)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(12)
        
        lbl_bb_right = QLabel("Version 2.0")
        lbl_bb_right.setObjectName("TitleLeftDescription")
        
        bb_layout.addWidget(lbl_bb_left)
        bb_layout.addSpacing(20)
        bb_layout.addWidget(self.cpu_bar)
        bb_layout.addWidget(self.ram_bar)
        bb_layout.addStretch()
        bb_layout.addWidget(self.lbl_status)
        bb_layout.addWidget(self.progress_bar)
        bb_layout.addStretch()
        bb_layout.addWidget(lbl_bb_right)

        right_box_layout.addWidget(bottom_bar)
        main_layout.addWidget(self.right_box)

        self.btn_home.setChecked(True)

    def update_hardware_monitor(self):
        if PSUTIL_AVAILABLE:
            self.cpu_bar.setValue(int(psutil.cpu_percent()))
            self.ram_bar.setValue(int(psutil.virtual_memory().percent))

    # FRAMELESS WINDOW EVENTS

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: 
            self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
            self.dragPos = event.globalPosition().toPoint()
            event.accept()

    def toggle_maximize(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def create_menu_button(self, text, index):
        btn = QPushButton(text)
        btn.setObjectName("MenuButton")
        btn.setCheckable(True)
        btn.setFixedHeight(45)
        self.nav_group.addButton(btn, index)
        btn.clicked.connect(lambda: self.set_page(index, btn.text()))
        return btn

    def set_page(self, index, title):
        self.stacked_widget.setCurrentIndex(index)
        clean_title = title.replace('  ', '').replace('≡', '').replace('🗄', '').replace('🧬', '').replace('🌐', '').replace('💻', '').replace('📊', '').replace('📝', '').replace('📖', '').strip()
        self.lbl_top_title.setText(f"PanVita 2 - {clean_title}")


    # PAGE CONSTRUCTION

    def build_page_home(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(50, 50, 50, 50)
        
        lbl_big_logo = QLabel()
        pix = self.load_logo_pixmap(250)
        if not pix.isNull(): lbl_big_logo.setPixmap(pix)
        lbl_big_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_title = QLabel("PanVita 2")
        lbl_title.setStyleSheet("font-size: 36pt; font-weight: bold;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_description = QLabel(
            "<b>Bioinformatics Software</b><br><br>"
            "PanVita 2 maps resistance genes, virulence factors, and aligns genomic data without "
            "the traditional command-line friction. Features JSON tracking, Batch Queues, and Hardware Metrics.<br><br>"
            "Drag and drop your input files, select the necessary databases, and add to the queue or start the run."
        )
        lbl_description.setObjectName("TitleLeftDescription")
        lbl_description.setStyleSheet("font-size: 11pt; line-height: 1.5;")
        lbl_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_description.setWordWrap(True)

        layout.addStretch()
        layout.addWidget(lbl_big_logo)
        layout.addSpacing(20)
        layout.addWidget(lbl_title)
        layout.addSpacing(20)
        layout.addWidget(lbl_description)
        layout.addStretch()
        self.stacked_widget.addWidget(page)

    def build_page_db(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        self.gb_files = QGroupBox("Input Files")
        l_files = QVBoxLayout(self.gb_files)
        
        h_btn = QHBoxLayout()
        self.btn_add = QPushButton("Browse Files")
        self.btn_add.clicked.connect(self.browse_files)
        
        self.btn_clear = QPushButton("Clear List")
        self.btn_clear.clicked.connect(self.clear_files)
        
        h_btn.addWidget(self.btn_add)
        h_btn.addWidget(self.btn_clear)
        h_btn.addStretch()

        self.list_files = DropListWidget(self.add_file_paths)
        self.list_files.setFixedHeight(120)
        self.list_files.itemDoubleClicked.connect(self.remove_selected_file)

        l_files.addLayout(h_btn)
        l_files.addWidget(self.list_files)
        layout.addWidget(self.gb_files)

        self.gb_db = QGroupBox("Target Databases")
        l_db = QGridLayout(self.gb_db)

        self.db_checkboxes = {
            "-card": QCheckBox("CARD"), "-bacmet": QCheckBox("BacMet"),
            "-vfdb": QCheckBox("VFDB"), "-megares": QCheckBox("MEGARes"),
            "-resfinder": QCheckBox("ResFinder"), "-argannot": QCheckBox("ARG-ANNOT"),
            "-victors": QCheckBox("Victors (Prot)"), "-victors-nucl": QCheckBox("Victors (Nucl)")
        }

        r, c = 0, 0
        for flag, cb in self.db_checkboxes.items():
            l_db.addWidget(cb, r, c)
            c += 1
            if c > 3: c = 0; r += 1

        self.cb_custom = QCheckBox("Custom DB (FASTA)")
        self.cb_custom.toggled.connect(lambda checked: self.btn_custom.setEnabled(checked))
        self.btn_custom = QPushButton("Browse Fasta...")
        self.btn_custom.setEnabled(False)
        self.btn_custom.clicked.connect(self.select_custom_db)
        self.lbl_custom = QLabel("No custom DB selected.")
        
        l_db.addWidget(self.cb_custom, r+1, 0)
        l_db.addWidget(self.btn_custom, r+1, 1)
        l_db.addWidget(self.lbl_custom, r+1, 2, 1, 2)
        
        layout.addWidget(self.gb_db)
        layout.addStretch()
        self.stacked_widget.addWidget(page)

    def build_page_align(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        self.gb_alg = QGroupBox("Alignment Engine")
        l_alg = QGridLayout(self.gb_alg)
        
        self.rb_auto = QRadioButton("Automatic (Recommended)")
        self.rb_auto.setChecked(True)
        self.rb_diamond = QRadioButton("DIAMOND Only (-diamond)")
        self.rb_blast = QRadioButton("BLAST Only (-blast)")
        self.rb_both = QRadioButton("Both DIAMOND and BLAST (-both)")
        self.cb_force_d = QCheckBox("Force Local DIAMOND (-d)")
        
        self.lbl_threads = QLabel("CPU Threads:")
        self.spn_threads = QSpinBox()
        self.spn_threads.setRange(1, multiprocessing.cpu_count())
        self.spn_threads.setValue(multiprocessing.cpu_count())

        l_alg.addWidget(self.rb_auto, 0, 0)
        l_alg.addWidget(self.rb_diamond, 0, 1)
        l_alg.addWidget(self.rb_blast, 1, 0)
        l_alg.addWidget(self.rb_both, 1, 1)
        l_alg.addWidget(self.cb_force_d, 2, 0, 1, 2)
        
        h_thr = QHBoxLayout()
        h_thr.addWidget(self.lbl_threads)
        h_thr.addWidget(self.spn_threads)
        h_thr.addStretch()
        l_alg.addLayout(h_thr, 3, 0, 1, 2)
        
        layout.addWidget(self.gb_alg)

        self.gb_thr = QGroupBox("Filtering Thresholds")
        l_thr = QGridLayout(self.gb_thr)
        
        self.lbl_i = QLabel("Minimum Identity:")
        self.sld_i = QSlider(Qt.Orientation.Horizontal)
        self.sld_i.setRange(0, 100); self.sld_i.setValue(70)
        self.spn_i = QSpinBox()
        self.spn_i.setRange(0, 100); self.spn_i.setValue(70); self.spn_i.setSuffix("%")
        self.sld_i.valueChanged.connect(self.spn_i.setValue)
        self.spn_i.valueChanged.connect(self.sld_i.setValue)

        self.lbl_c = QLabel("Minimum Coverage:")
        self.sld_c = QSlider(Qt.Orientation.Horizontal)
        self.sld_c.setRange(0, 100); self.sld_c.setValue(70)
        self.spn_c = QSpinBox()
        self.spn_c.setRange(0, 100); self.spn_c.setValue(70); self.spn_c.setSuffix("%")
        self.sld_c.valueChanged.connect(self.spn_c.setValue)
        self.spn_c.valueChanged.connect(self.sld_c.setValue)

        l_thr.addWidget(self.lbl_i, 0, 0); l_thr.addWidget(self.sld_i, 0, 1); l_thr.addWidget(self.spn_i, 0, 2)
        l_thr.addWidget(self.lbl_c, 1, 0); l_thr.addWidget(self.sld_c, 1, 1); l_thr.addWidget(self.spn_c, 1, 2)
        
        layout.addWidget(self.gb_thr)
        layout.addStretch()
        self.stacked_widget.addWidget(page)

    def build_page_ncbi(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        self.gb_ncbi = QGroupBox("NCBI Integration & Modifiers")
        l_ncbi = QVBoxLayout(self.gb_ncbi)

        h_csv = QHBoxLayout()
        self.btn_csv = QPushButton("Import Table (CSV/TSV/TXT)")
        self.btn_csv.clicked.connect(self.select_csv)
        self.lbl_csv = QLabel("No file imported.")
        h_csv.addWidget(self.btn_csv)
        h_csv.addWidget(self.lbl_csv)
        h_csv.addStretch()
        l_ncbi.addLayout(h_csv)

        self.ncbi_cbs = {
            "-b": QCheckBox("Download GenBank (-b)"), 
            "-a": QCheckBox("Annotate via PROKKA (-a)"),
            "-g": QCheckBox("Download FASTA (-g)"), 
            "-m": QCheckBox("Download Metadata (-m)"),
            "-s": QCheckBox("Locus_Tag matches strain (-s)")
        }

        for cb in self.ncbi_cbs.values(): 
            l_ncbi.addWidget(cb)
            
        layout.addWidget(self.gb_ncbi)

        self.gb_out = QGroupBox("Outputs and Plotting")
        l_out = QVBoxLayout(self.gb_out)
        self.rb_pdf = QRadioButton("Graphs in PDF"); self.rb_pdf.setChecked(True)
        self.rb_png = QRadioButton("Graphs in PNG")
        self.cb_save = QCheckBox("Save found genes (.faa) (-save-genes)")
        self.cb_keep = QCheckBox("Keep temporary files (-keep)")
        
        for w in [self.rb_pdf, self.rb_png, self.cb_save, self.cb_keep]: 
            l_out.addWidget(w)
            
        layout.addWidget(self.gb_out)
        layout.addStretch()
        self.stacked_widget.addWidget(page)

    def build_page_terminal(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        h_btn = QHBoxLayout()
        self.btn_clear_term = QPushButton("🧹 Clear Terminal")
        self.btn_clear_term.clicked.connect(lambda: self.terminal.clear())
        self.btn_export_log = QPushButton("💾 Export Log as .TXT")
        self.btn_export_log.clicked.connect(self.export_log)
        
        h_btn.addStretch()
        h_btn.addWidget(self.btn_clear_term)
        h_btn.addWidget(self.btn_export_log)
        layout.addLayout(h_btn)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.terminal)
        self.stacked_widget.addWidget(page)

    def build_page_results(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        h_btn = QHBoxLayout()
        self.btn_load_res = QPushButton("📂 Open CSV Result")
        self.btn_load_res.clicked.connect(self.prompt_load_results_csv)
        self.btn_export_pdf = QPushButton("📄 Export PDF Report")
        self.btn_export_pdf.clicked.connect(self.export_pdf_report)
        self.btn_export_filtered = QPushButton("💾 Export Filtered CSV")
        self.btn_export_filtered.clicked.connect(self.export_filtered_csv)
        
        h_btn.addWidget(self.btn_load_res)
        h_btn.addWidget(self.btn_export_pdf)
        h_btn.addWidget(self.btn_export_filtered)
        h_btn.addStretch()
        layout.addLayout(h_btn)

        # Tab Widget for Table vs Graph
        self.tabs_res = QTabWidget()
        
        # TAB 1: CSV Table
        self.tab_table = QWidget()
        layout_table = QVBoxLayout(self.tab_table)
        layout_table.setContentsMargins(0, 0, 0, 0)
        
        # METRICS DASHBOARD
        self.metrics_dash = QFrame()
        self.metrics_dash.setObjectName("MetricBox")
        h_metrics = QHBoxLayout(self.metrics_dash)
        
        self.lbl_m_hits = QLabel("Total Hits: <span id='MetricVal'>0</span>")
        self.lbl_m_id = QLabel("Avg Identity: <span id='MetricVal'>0%</span>")
        self.lbl_m_db = QLabel("Top DB: <span id='MetricVal'>None</span>")
        
        for m in [self.lbl_m_hits, self.lbl_m_id, self.lbl_m_db]:
            m.setAlignment(Qt.AlignmentFlag.AlignCenter)
            h_metrics.addWidget(m)
            
        layout_table.addWidget(self.metrics_dash)
        
        # Search Filter Header
        h_search = QHBoxLayout()
        self.lbl_search_table = QLabel("🔍 Filter Results:")
        self.le_search_table = QLineEdit()
        self.le_search_table.setPlaceholderText("Type a gene name, identity, etc...")
        self.le_search_table.textChanged.connect(self.filter_results_table)
        
        self.lbl_row_count = QLabel("Rows: 0/0")
        self.lbl_row_count.setObjectName("TitleLeftDescription")
        
        h_search.addWidget(self.lbl_search_table)
        h_search.addWidget(self.le_search_table)
        h_search.addWidget(self.lbl_row_count)
        layout_table.addLayout(h_search)
        
        self.res_table = DropTableWidget(self.execute_load_csv)
        self.res_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.res_table.setAlternatingRowColors(True)
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.res_table.horizontalHeader().setStretchLastSection(True)
        self.res_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.res_table.customContextMenuRequested.connect(self.show_table_context_menu)
        
        layout_table.addWidget(self.res_table)
        
        # TAB 2: Static Image Viewer (PNG)
        self.tab_graph_png = QWidget()
        layout_graph_png = QVBoxLayout(self.tab_graph_png)
        self.btn_load_graph = QPushButton("🖼 Load PNG Graph")
        self.btn_load_graph.clicked.connect(self.load_graph_png)
        self.lbl_graph_view = QLabel("No graph loaded.")
        self.lbl_graph_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_graph = QScrollArea()
        scroll_graph.setWidgetResizable(True)
        scroll_graph.setWidget(self.lbl_graph_view)
        layout_graph_png.addWidget(self.btn_load_graph, alignment=Qt.AlignmentFlag.AlignLeft)
        layout_graph_png.addWidget(scroll_graph)
        
        self.tabs_res.addTab(self.tab_table, "CSV Data")
        self.tabs_res.addTab(self.tab_graph_png, "Static Graphs (PNG)")
        
        # TAB 3: Interactive Web Engine (HTML)
        if WEB_ENGINE_AVAILABLE:
            self.tab_graph_html = QWidget()
            layout_graph_html = QVBoxLayout(self.tab_graph_html)
            self.btn_load_html = QPushButton("🌐 Load Interactive HTML Graph")
            self.btn_load_html.clicked.connect(self.load_graph_html)
            self.web_view = QWebEngineView()
            self.web_view.setHtml("<div style='display:flex; justify-content:center; align-items:center; height:100%; color:gray; font-family:sans-serif;'>No interactive HTML graph loaded.</div>")
            layout_graph_html.addWidget(self.btn_load_html, alignment=Qt.AlignmentFlag.AlignLeft)
            layout_graph_html.addWidget(self.web_view)
            self.tabs_res.addTab(self.tab_graph_html, "Interactive Graphs (HTML)")
        
        layout.addWidget(self.tabs_res)
        self.stacked_widget.addWidget(page)

    def build_page_queue_history(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Queue Section
        self.gb_queue = QGroupBox("Task Queue")
        l_queue = QVBoxLayout(self.gb_queue)
        
        self.list_queue = QListWidget()
        l_queue.addWidget(self.list_queue)
        
        h_q_btns = QHBoxLayout()
        self.btn_clear_queue = QPushButton("Clear Queue")
        self.btn_clear_queue.clicked.connect(self.clear_queue)
        h_q_btns.addStretch()
        h_q_btns.addWidget(self.btn_clear_queue)
        l_queue.addLayout(h_q_btns)
        
        # History Section
        self.gb_history = QGroupBox("Run History")
        l_history = QVBoxLayout(self.gb_history)
        
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(5)
        self.table_history.setHorizontalHeaderLabels(["ID", "Date", "Files", "Duration", "Status"])
        self.table_history.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_history.horizontalHeader().setStretchLastSection(True)
        l_history.addWidget(self.table_history)
        
        h_h_btns = QHBoxLayout()
        self.btn_clear_history = QPushButton("Clear History")
        self.btn_clear_history.clicked.connect(self.clear_history)
        h_h_btns.addStretch()
        h_h_btns.addWidget(self.btn_clear_history)
        l_history.addLayout(h_h_btns)
        
        splitter.addWidget(self.gb_queue)
        splitter.addWidget(self.gb_history)
        layout.addWidget(splitter)
        
        self.stacked_widget.addWidget(page)

    def build_page_help(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        self.text_browser_help = QTextBrowser()
        self.text_browser_help.setOpenExternalLinks(True)
        layout.addWidget(self.text_browser_help)
        self.stacked_widget.addWidget(page)

    def populate_help_page(self):
        color = self.accent_color
        
        html_pt = f"""
        <h1 style="color: {color};">PanVita 2 - Documentação </h1>
        <p>O <b>PanVita</b> é um software avançado de bioinformática desenvolvido para identificação de genes de resistência, fatores de virulência e tolerância a metais pesados a partir de sequências genômicas completas ou rascunhos de genomas (FASTA/GenBank).</p>
        
        <hr>

        <h2 style="color: {color};">⌨️ Atalhos de Teclado (Shortcuts)</h2>
        <ul>
            <li><b>Ctrl + R:</b> Executar / Parar Análise</li>
            <li><b>Ctrl + O:</b> Abrir Arquivos de Entrada</li>
            <li><b>Ctrl + S:</b> Salvar Preset</li>
            <li><b>Ctrl + Q:</b> Fechar o Programa</li>
        </ul>

        <hr>
        
        <h2 style="color: {color};">⚙️ Motores de Alinhamento</h2>
        <p>O PanVita utiliza dois dos alinhadores mais consagrados do mundo científico:</p>
        <ul>
            <li><b>BLAST (Basic Local Alignment Search Tool):</b> Altamente sensível e exato. O PanVita utiliza o <i>makeblastdb</i> para criar os bancos locais e o <i>blastp</i> ou <i>blastn</i> para o alinhamento. Ideal quando a precisão é necessária.</li>
            <li><b>DIAMOND:</b> Uma alternativa moderna ao BLASTP para alinhamentos de proteínas. É consideravelmente mais rápido que o BLAST tradicional para grandes conjuntos de dados genômicos e metagenômicos, mantendo um grau de sensibilidade comparável no modo sensível.</li>
        </ul>
        
        <hr>

        <h2 style="color: {color};">🗄️ Bancos de Dados Suportados</h2>
        <ul>
            <li><b>CARD (Comprehensive Antibiotic Resistance Database):</b> Focado exclusivamente na base molecular da resistência antimicrobiana (AMR). É rigorosamente curado e excelente para delinear resistomas.</li>
            <li><b>BacMet:</b> Especializado em genes de resistência a biocidas antibacterianos e metais pesados. Fundamental para estudos de biorremediação e toxicidade ambiental.</li>
            <li><b>VFDB (Virulence Factor Database):</b> Focado em fatores de virulência patogênicos. Mapeia toxinas, sistemas de secreção, fímbrias e outros mecanismos de ataque/defesa da bactéria.</li>
            <li><b>MEGARes:</b> Um banco consolidado projetado para análises metagenômicas e genômicas de resistência antimicrobiana de alto rendimento.</li>
            <li><b>ResFinder:</b> Base de dados altamente focada em genes de resistência antimicrobiana <i>adquiridos</i> (plasmídeos, transposons), isolando a resistência inata da bactéria.</li>
            <li><b>ARG-ANNOT:</b> (Antibiotic Resistance Gene-ANNOTation) Otimizado para detectar mutações pontuais e genes de resistência.</li>
            <li><b>Victors:</b> Banco de dados que integra pesquisa de patógenos humanos, animais e de plantas, mapeando fatores de virulência de forma extensiva.</li>
        </ul>
        
        <hr>

        <h2 style="color: {color};">📊 Resultados Gerados</h2>
        <p>Após a conclusão, o software produzirá uma pasta contendo:</p>
        <ol>
            <li><b>Arquivos CSV:</b> Tabelas padronizadas contendo as identificações (ID), o nome do gene mapeado, a % de Identidade e a % de Cobertura do alinhamento.</li>
            <li><b>Gráficos Interativos (HTML) ou Estáticos (PDF/PNG):</b> Representações visuais tipo <i>heatmap</i> ou gráficos de dispersão mostrando o perfil de resistência e virulência das cepas.</li>
            <li><b>Logs e Metadados:</b> Se as opções NCBI foram ativadas, o software fará o download da árvore de metadados das amostras para enriquecer as tabelas.</li>
        </ol>
        """

        html_en = f"""
        <h1 style="color: {color};">PanVita 2 - Documentation</h1>
        <p><b>PanVita</b> is an advanced bioinformatics software designed to identify resistance genes, virulence factors, and heavy metal tolerance from whole genome sequences or draft genomes (FASTA/GenBank).</p>
        
        <hr>

        <h2 style="color: {color};">⌨️ Keyboard Shortcuts</h2>
        <ul>
            <li><b>Ctrl + R:</b> Run / Stop Analysis</li>
            <li><b>Ctrl + O:</b> Open Input Files</li>
            <li><b>Ctrl + S:</b> Save Preset</li>
            <li><b>Ctrl + Q:</b> Quit Software</li>
        </ul>

        <hr>
        
        <h2 style="color: {color};">⚙️ Alignment Engines</h2>
        <p>PanVita utilizes two established aligners in the scientific community:</p>
        <ul>
            <li><b>BLAST (Basic Local Alignment Search Tool):</b> Highly sensitive and exact. PanVita uses <i>makeblastdb</i> to build local databases and <i>blastp/blastn</i> for alignment. Ideal when precision is required.</li>
            <li><b>DIAMOND:</b> A modern alternative to BLASTP for protein alignments. It is considerably faster than traditional BLAST for large genomic and metagenomic datasets, while maintaining a comparable degree of sensitivity.</li>
        </ul>
        
        <hr>

        <h2 style="color: {color};">🗄️ Supported Databases</h2>
        <ul>
            <li><b>CARD (Comprehensive Antibiotic Resistance Database):</b> Focused exclusively on the molecular basis of antimicrobial resistance (AMR). It is rigorously curated and excellent for resistome profiling.</li>
            <li><b>BacMet:</b> Specialized in antibacterial biocide and heavy metal resistance genes. Fundamental for bioremediation and environmental toxicity studies.</li>
            <li><b>VFDB (Virulence Factor Database):</b> Focused on pathogenic virulence factors. Maps toxins, secretion systems, fimbriae, and other bacterial attack/defense mechanisms.</li>
            <li><b>MEGARes:</b> A consolidated database designed for high-throughput metagenomic and genomic analysis of antimicrobial resistance.</li>
            <li><b>ResFinder:</b> Database highly focused on <i>acquired</i> antimicrobial resistance genes (plasmids, transposons), isolating the innate resistance of the bacteria.</li>
            <li><b>ARG-ANNOT:</b> (Antibiotic Resistance Gene-ANNOTation) Optimized to detect point mutations and resistance genes.</li>
            <li><b>Victors:</b> Database integrating human, animal, and plant pathogen research, mapping virulence factors extensively.</li>
        </ul>
        
        <hr>

        <h2 style="color: {color};">📊 Generated Results</h2>
        <p>Upon completion, the software will produce a folder containing:</p>
        <ol>
            <li><b>CSV Files:</b> Standardized tables containing the sequence IDs, the mapped gene name, % Identity, and % Coverage of the alignment.</li>
            <li><b>Interactive HTML or Static PDF/PNG Graphs:</b> Visual representations such as heatmaps or scatter plots showing the resistance and virulence profile of the strains.</li>
            <li><b>Logs and Metadata:</b> If NCBI options were activated, the software will download the metadata tree of the samples to enrich the final tables.</li>
        </ol>
        """

        if hasattr(self, 'text_browser_help'):
            self.text_browser_help.setHtml(html_en if self.lang == "EN" else html_pt)

    # DATA HANDLING LOGIC

    def browse_files(self):
        self.btn_db.setChecked(True)
        self.set_page(1, self.btn_db.text())
        files, _ = QFileDialog.getOpenFileNames(self, "Select GenBank/Fasta Files", self.last_dir, "Genome Files (*.gbk *.gbf *.gbff *.fasta *.fna *.faa);;All (*.*)")
        if files:
            self.last_dir = os.path.dirname(files[0])
            self.add_file_paths(files)

    def add_file_paths(self, files):
        for f in files:
            if not self.validate_file(f):
                QMessageBox.warning(self, "Invalid File", f"The file '{os.path.basename(f)}' does not appear to be a valid FASTA or GenBank file.")
                continue
            if f not in self.input_files:
                self.input_files.append(f)
                item = QListWidgetItem(os.path.basename(f))
                item.setData(Qt.ItemDataRole.UserRole, f)
                self.list_files.addItem(item)

    def remove_selected_file(self, item):
        f_path = item.data(Qt.ItemDataRole.UserRole)
        if f_path in self.input_files: self.input_files.remove(f_path)
        self.list_files.takeItem(self.list_files.row(item))

    def clear_files(self):
        self.input_files.clear()
        self.list_files.clear()

    def select_custom_db(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Custom DB", self.last_dir, "FASTA (*.fasta *.fas *.fna *.faa)")
        if f:
            self.last_dir = os.path.dirname(f)
            self.custom_db_path = f
            self.lbl_custom.setText(os.path.basename(f))

    def select_csv(self):
        f, _ = QFileDialog.getOpenFileName(self, "NCBI Table Import", self.last_dir, "Tables (*.csv *.tsv *.txt)")
        if f:
            self.last_dir = os.path.dirname(f)
            self.csv_file = f
            self.lbl_csv.setText(os.path.basename(f))

    # QUEUE AND HISTORY MANAGEMENT

    def add_to_queue(self):
        args = self.build_args()
        has_db = any(cb.isChecked() for cb in self.db_checkboxes.values()) or self.cb_custom.isChecked()
        has_ncbi = self.ncbi_cbs["-a"].isChecked() or self.ncbi_cbs["-b"].isChecked() or self.ncbi_cbs["-g"].isChecked()
        if not has_db and not has_ncbi:
            QMessageBox.warning(self, "Warning", "Please select at least one database or NCBI action.")
            return
        if not self.input_files and not (has_ncbi and self.csv_file):
            QMessageBox.warning(self, "Warning", "Please provide genome files or a valid CSV.")
            return
            
        task_info = {
            "args": args,
            "files": [os.path.basename(f) for f in self.input_files],
            "dbs": [flag for flag, cb in self.db_checkboxes.items() if cb.isChecked()]
        }
        self.task_queue.append(task_info)
        
        display_text = f"Task {len(self.task_queue)}: {len(self.input_files)} files against {', '.join(task_info['dbs'])}"
        self.list_queue.addItem(display_text)
        QMessageBox.information(self, "Queue", "Task added to Queue.")

    def clear_queue(self):
        self.task_queue.clear()
        self.list_queue.clear()
        
    def load_history(self):
        self.cursor.execute("SELECT id, date, files, duration, status FROM history ORDER BY id DESC")
        rows = self.cursor.fetchall()
        self.table_history.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                self.table_history.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))
        self.table_history.resizeColumnsToContents()

    def add_history_entry(self, task_info, duration, status):
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        files_str = f"{len(task_info['files'])} files"
        dbs_str = ", ".join(task_info['dbs'])
        
        self.cursor.execute("INSERT INTO history (date, files, dbs, duration, status) VALUES (?, ?, ?, ?, ?)",
                            (date_str, files_str, dbs_str, duration, status))
        self.conn.commit()
        self.load_history()

    def clear_history(self):
        self.cursor.execute("DELETE FROM history")
        self.conn.commit()
        self.load_history()

    # MULTITHREADED CSV LOADER & TABLE LOGIC

    def prompt_load_results_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PanVita CSV Result", self.last_dir, "CSV Files (*.csv)")
        if path:
            self.last_dir = os.path.dirname(path)
            self.execute_load_csv(path)

    def execute_load_csv(self, path):
        self.lbl_status.setText("Status: Loading CSV data... ⏳")
        self.res_table.clear()
        self.csv_thread = CSVLoaderThread(path)
        self.csv_thread.finished.connect(self.on_csv_loaded)
        self.csv_thread.error.connect(lambda e: QMessageBox.critical(self, "Error Loading CSV", str(e)))
        self.csv_thread.start()

    def on_csv_loaded(self, headers, data):
        self.res_table.setSortingEnabled(False)
        self.res_table.setRowCount(len(data))
        self.res_table.setColumnCount(len(headers))
        self.res_table.setHorizontalHeaderLabels(headers)
        
        for row_idx, row in enumerate(data):
            for col_idx, val in enumerate(row):
                self.res_table.setItem(row_idx, col_idx, NumericItem(val))
                
        self.res_table.resizeColumnsToContents()
        self.lbl_status.setText("Status: CSV Loaded ✅")
        self.current_run_results = (headers, data)
        self.update_row_count()
        self.update_metrics_dash(headers, data)
        self.res_table.setSortingEnabled(True)

    def update_metrics_dash(self, headers, data):
        t = LANGUAGES[self.lang]
        total_hits = len(data)
        self.lbl_m_hits.setText(f"{t['metrics_hits']}<span id='MetricVal'>{total_hits}</span>")
        
        # Calculate Average Identity
        id_col = None
        for i, h in enumerate(headers):
            if "ident" in h.lower() or "pident" in h.lower():
                id_col = i; break
                
        if id_col is not None and total_hits > 0:
            total_id = sum(float(row[id_col]) for row in data if str(row[id_col]).replace('.','',1).isdigit())
            avg_id = total_id / total_hits
            self.lbl_m_id.setText(f"{t['metrics_id']}<span id='MetricVal'>{avg_id:.1f}%</span>")
        else:
            self.lbl_m_id.setText(f"{t['metrics_id']}<span id='MetricVal'>N/A</span>")
            
        # Determine Top Database
        db_col = None
        for i, h in enumerate(headers):
            if "database" in h.lower() or "db" in h.lower() or "banco" in h.lower():
                db_col = i; break
                
        if db_col is not None and total_hits > 0:
            db_counts = {}
            for row in data:
                db_name = str(row[db_col])
                db_counts[db_name] = db_counts.get(db_name, 0) + 1
            top_db = max(db_counts, key=db_counts.get)
            self.lbl_m_db.setText(f"{t['metrics_db']}<span id='MetricVal'>{top_db}</span>")
        else:
            self.lbl_m_db.setText(f"{t['metrics_db']}<span id='MetricVal'>N/A</span>")

    def filter_results_table(self, text):
        text_lower = text.lower()
        for row in range(self.res_table.rowCount()):
            match = False
            for col in range(self.res_table.columnCount()):
                item = self.res_table.item(row, col)
                if item and text_lower in item.text().lower():
                    match = True
                    break
            self.res_table.setRowHidden(row, not match)
        self.update_row_count()

    def update_row_count(self):
        total = self.res_table.rowCount()
        visible = sum(1 for row in range(total) if not self.res_table.isRowHidden(row))
        self.lbl_row_count.setText(f"Rows: {visible}/{total}")

    def export_filtered_csv(self):
        if not self.current_run_results: return
        path, _ = QFileDialog.getSaveFileName(self, "Export Filtered CSV", self.last_dir, "CSV Files (*.csv)")
        if not path: return
        self.last_dir = os.path.dirname(path)
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                headers = [self.res_table.horizontalHeaderItem(i).text() for i in range(self.res_table.columnCount())]
                writer.writerow(headers)
                for row in range(self.res_table.rowCount()):
                    if not self.res_table.isRowHidden(row):
                        row_data = [self.res_table.item(row, col).text() for col in range(self.res_table.columnCount())]
                        writer.writerow(row_data)
            QMessageBox.information(self, "Success", "Filtered CSV exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export CSV:\n{str(e)}")

    def show_table_context_menu(self, pos):
        item = self.res_table.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        
        view_fasta_action = QAction("🧬 Visualizar Sequência FASTA", self)
        copy_action = QAction("📋 Copiar Conteúdo", self)
        search_ncbi_action = QAction("🌐 Pesquisar no NCBI", self)
        
        view_fasta_action.triggered.connect(lambda: self.view_fasta_sequence(item.text()))
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(item.text()))
        search_ncbi_action.triggered.connect(lambda: webbrowser.open(f"https://www.ncbi.nlm.nih.gov/search/all/?term={item.text()}"))
        
        menu.addAction(view_fasta_action)
        menu.addSeparator()
        menu.addAction(copy_action)
        menu.addAction(search_ncbi_action)
        menu.exec(self.res_table.mapToGlobal(pos))
        
    def view_fasta_sequence(self, gene_name):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"FASTA Viewer - {gene_name}")
        dlg.setMinimumSize(600, 400)
        layout = QVBoxLayout(dlg)
        
        info = QLabel(f"<b>Sequence View:</b> Data for <i>{gene_name}</i> (Placeholder implementation)")
        layout.addWidget(info)
        
        te = QTextEdit()
        te.setReadOnly(True)
        te.setStyleSheet(f"font-family: Consolas, monospace; color: {self.accent_color};")
        # Placeholder sequence - In a real scenario, fetch this from the generated .faa file
        mock_seq = f">{gene_name} | PanVita Output\nATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGTACGTAGCTAGC\nTAGCATCGATCGATCGATCGATCGATCGTACGTAGCTAGCTAGCATCGATCGATCGA\nTCGATCGATC"
        te.setText(mock_seq)
        
        layout.addWidget(te)
        dlg.exec()

    # GRAPH VIEWERS

    def load_graph_png(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Graph Image", self.last_dir, "Images (*.png *.jpg *.jpeg)")
        if path:
            self.last_dir = os.path.dirname(path)
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.lbl_graph_view.setPixmap(pixmap)
                self.lbl_graph_view.setScaledContents(True)
                self.lbl_graph_view.setMaximumSize(pixmap.size())
            else:
                QMessageBox.warning(self, "Error", "Failed to load image.")

    def load_graph_html(self):
        if not WEB_ENGINE_AVAILABLE: return
        path, _ = QFileDialog.getOpenFileName(self, "Open Interactive Graph", self.last_dir, "HTML Files (*.html *.htm)")
        if path:
            self.last_dir = os.path.dirname(path)
            local_url = QUrl.fromLocalFile(os.path.abspath(path))
            self.web_view.load(local_url)

    # REPORTS EXPORT

    def export_log(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Log", self.last_dir, "Text Files (*.txt)")
        if path:
            self.last_dir = os.path.dirname(path)
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.terminal.toPlainText())
                QMessageBox.information(self, "Success", "Log exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save log:\n{str(e)}")

    def export_pdf_report(self):
        if not self.current_run_results:
            QMessageBox.warning(self, "Warning", "Load a CSV result first to generate a report.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export PDF Report", self.last_dir, "PDF Files (*.pdf)")
        if not path: return
        self.last_dir = os.path.dirname(path)

        try:
            writer = QPdfWriter(path)
            writer.setPageSize(QPdfWriter.PageSize.A4)
            writer.setResolution(300)
            painter = QPainter(writer)
            
            font_title = QFont("Arial", 20, QFont.Weight.Bold)
            font_body = QFont("Arial", 12)
            
            painter.setFont(font_title)
            painter.drawText(200, 400, "PanVita 2 - Executive Analysis Report")
            
            painter.setFont(font_body)
            y = 800
            painter.drawText(200, y, f"Total records analyzed: {len(self.current_run_results[1])}")
            y += 200
            painter.drawText(200, y, f"Identity Threshold: {self.spn_i.value()}%  |  Coverage: {self.spn_c.value()}%")
            y += 200
            painter.drawText(200, y, f"Threads Used: {self.spn_threads.value()}")
                
            painter.end()
            QMessageBox.information(self, "Success", "PDF Report exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF:\n{str(e)}")

    # EXECUTION LOGIC (WITH JSON AND QUEUE SUPPORT)

    def log(self, text, is_error=False):
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        color = QColor(self.central_widget.palette().text().color())
        lower_text = text.lower()
        if is_error or "error" in lower_text or "exception" in lower_text or "failed" in lower_text:
            color = QColor("#ff5555")
        elif "success" in lower_text or "completed" in lower_text or "done" in lower_text:
            color = QColor("#50fa7b")
        elif "warning" in lower_text:
            color = QColor("#f1fa8c")
        elif "aborted" in lower_text:
            color = QColor("#ff5555")
            
        self.terminal.setTextColor(color)
        self.terminal.insertPlainText(text)
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)

    def build_args(self):
        core_path = self.settings.value("path_panvita", "panvita.py", type=str)
        args = [core_path, "-t", str(self.spn_threads.value())]
        
        # Add PROKKA path explicitly using the new argument feature
        prokka_dir = self.settings.value("dir_prokka", "", type=str)
        if prokka_dir and os.path.isdir(prokka_dir):
            prokka_exe = os.path.join(prokka_dir, "prokka")
            if os.name == 'nt' and not prokka_exe.endswith('.exe'):
                # Handle possible windows extension safely (though prokka usually runs without one)
                pass 
            args.extend(["--prokka", prokka_exe])
            
        for flag, cb in self.db_checkboxes.items():
            if cb.isChecked(): args.append(flag)
        if self.cb_custom.isChecked() and self.custom_db_path: args.extend(["-custom", self.custom_db_path])
        
        if self.rb_diamond.isChecked(): args.append("-diamond")
        elif self.rb_blast.isChecked(): args.append("-blast")
        elif self.rb_both.isChecked(): args.append("-both")
        if self.cb_force_d.isChecked(): args.append("-d")

        args.extend(["-i", str(self.spn_i.value())])
        args.extend(["-c", str(self.spn_c.value())])

        for flag, cb in self.ncbi_cbs.items():
            if cb.isChecked(): args.append(flag)
        if self.csv_file: args.append(self.csv_file)

        if self.rb_png.isChecked(): args.append("-png")
        if self.cb_save.isChecked(): args.append("-save-genes")
        if self.cb_keep.isChecked(): args.append("-keep")

        args.extend(self.input_files)
        return args

    def run_update(self):
        core_path = self.settings.value("path_panvita", "panvita.py", type=str)
        self.btn_term.setChecked(True)
        self.set_page(4, self.btn_term.text())
        self.execute_script([core_path, "-update", "-diamond"])

    def toggle_run_state(self):
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.log(f"\n{'='*70}\n[!] ATTEMPTING GRACEFUL SHUTDOWN...\n{'='*70}\n", is_error=True)
            self.is_processing_queue = False # Stop queue sequence
            self.process.terminate()
            QTimer.singleShot(3000, self.force_kill_process)
        else:
            if self.task_queue:
                self.is_processing_queue = True
                self.process_next_in_queue()
            else:
                self.start_analysis(self.build_args(), single_run=True)

    def process_next_in_queue(self):
        if not self.task_queue:
            self.is_processing_queue = False
            self.lbl_status.setText("Status: Queue Finished ✅")
            self.tray_icon.showMessage("PanVita Queue", "All tasks completed.", QSystemTrayIcon.MessageIcon.Information, 5000)
            return
            
        task = self.task_queue.pop(0)
        self.list_queue.takeItem(0)
        
        # Save info for history
        self.current_task_info = task
        self.start_analysis(task["args"], single_run=False)

    def force_kill_process(self):
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.log(f"\n[!] PROCESS FORCEFULLY KILLED.\n", is_error=True)
        self.reset_run_button()
        self.lbl_status.setText("Status: Aborted 🛑")
        if hasattr(self, 'current_task_info'):
            self.add_history_entry(self.current_task_info, "Aborted", "Failed")

    def start_analysis(self, args, single_run=True):
        core_path = self.settings.value("path_panvita", "panvita.py", type=str)
        if not os.path.exists(core_path) and not shutil.which(core_path):
            QMessageBox.critical(self, "Core Not Found", f"The PanVita core script was not found at:\n{core_path}\n\nPlease update the path in 'Configure Paths'.")
            return

        if single_run:
            has_db = any(cb.isChecked() for cb in self.db_checkboxes.values()) or self.cb_custom.isChecked()
            has_ncbi = self.ncbi_cbs["-a"].isChecked() or self.ncbi_cbs["-b"].isChecked() or self.ncbi_cbs["-g"].isChecked()
            if not has_db and not has_ncbi:
                QMessageBox.warning(self, "Warning", "Please select at least one database or NCBI action.")
                return
            if not self.input_files and not (has_ncbi and self.csv_file):
                QMessageBox.warning(self, "Warning", "Please provide genome files or a valid CSV.")
                return
            self.current_task_info = {
                "files": [os.path.basename(f) for f in self.input_files],
                "dbs": [flag for flag, cb in self.db_checkboxes.items() if cb.isChecked()]
            }

        self.btn_term.setChecked(True)
        self.set_page(4, self.btn_term.text())
        self.lbl_status.setText("Status: Starting analysis... 🚀")
        self.progress_bar.setValue(0)
        self.current_task_start_time = datetime.now()
        self.execute_script(args)

    def execute_script(self, args):
        self.terminal.clear()
        self.log(f"$ python {' '.join(args)}\n{'='*70}\n\n")
        
        t = LANGUAGES[self.lang]
        self.btn_run_master.setText(t["btn_stop"])
        self.btn_run_master.setStyleSheet("background-color: #ff5555; color: #ffffff;")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(5)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)

        env = QProcessEnvironment.systemEnvironment()
        path_list = []
        for p in ["dir_blast", "dir_diamond", "dir_prokka"]:
            val = self.settings.value(p, "", type=str)
            if val and os.path.isdir(val): path_list.append(val)
        
        current_path = env.value("PATH")
        separator = ";" if os.name == "nt" else ":"
        if path_list:
            new_path = separator.join(path_list) + separator + current_path
            env.insert("PATH", new_path)

        env.insert("PYTHONIOENCODING", "utf-8")
        env.insert("PYTHONUNBUFFERED", "1") # Crucial for JSON realtime
        self.process.setProcessEnvironment(env)
        
        self.process.start("python", args)

    def reset_run_button(self):
        t = LANGUAGES[self.lang]
        self.btn_run_master.setText(t["btn_run"])
        self.btn_run_master.setStyleSheet("")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode("utf8", errors="replace").strip()
        
        for line in text.split('\n'):
            if not line: continue
            
            # Attempt to parse as JSON (Structured Communication)
            try:
                msg = json.loads(line)
                if 'progresso' in msg:
                    self.progress_bar.setValue(msg['progresso'])
                if 'etapa' in msg:
                    self.lbl_status.setText(f"Status: {msg['etapa']}...")
                if 'log' in msg:
                    self.log(msg['log'] + "\n")
            except json.JSONDecodeError:
                # Normal Text Fallback
                self.log(line + "\n")
                low_txt = line.lower()
                if "aligning" in low_txt or "running diamond" in low_txt or "running blast" in low_txt:
                    self.lbl_status.setText("Status: Aligning sequences... 🧬")
                    if self.progress_bar.value() < 30: self.progress_bar.setValue(30)
                elif "downloading" in low_txt or "ncbi" in low_txt:
                    self.lbl_status.setText("Status: Downloading from NCBI... 🌐")
                    if self.progress_bar.value() < 60: self.progress_bar.setValue(60)
                elif "plotting" in low_txt or "generating graph" in low_txt:
                    self.lbl_status.setText("Status: Generating output graphs... 📊")
                    if self.progress_bar.value() < 90: self.progress_bar.setValue(90)

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        text = bytes(data).decode("utf8", errors="replace")
        self.log(text, is_error=True)
        self.lbl_status.setText("Status: Running with warnings/errors ⚠️")

    def process_finished(self, exit_code, exit_status):
        self.reset_run_button()
        
        end_time = datetime.now()
        duration_str = "Unknown"
        if self.current_task_start_time:
            dur = end_time - self.current_task_start_time
            m, s = divmod(dur.total_seconds(), 60)
            duration_str = f"{int(m)}m {int(s)}s"
            
        if exit_status == QProcess.ExitStatus.CrashExit:
            status_text = "Crashed"
        else:
            self.log(f"\n{'='*70}\nProcess completed. Exit code: {exit_code}\n")
            if exit_code == 0:
                self.lbl_status.setText("Status: Successfully Completed ✅")
                status_text = "Success"
            else:
                self.lbl_status.setText("Status: Failed or Terminated ❌")
                self.progress_bar.setValue(0)
                status_text = "Failed"

        # Log to DB History
        if hasattr(self, 'current_task_info'):
            self.add_history_entry(self.current_task_info, duration_str, status_text)

        # Check Queue Sequence
        if self.is_processing_queue:
            self.process_next_in_queue()
        elif exit_code == 0:
            self.tray_icon.showMessage("PanVita 2", "Analysis has been completed successfully!", QSystemTrayIcon.MessageIcon.Information, 5000)
        else:
            self.tray_icon.showMessage("PanVita 2", "Analysis finished with errors or was aborted.", QSystemTrayIcon.MessageIcon.Warning, 5000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = PanVitaApp()
    window.show()
    sys.exit(app.exec())
