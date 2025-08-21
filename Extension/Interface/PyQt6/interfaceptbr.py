#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Interface gráfica básica para quem não gosta de utilizar linha de comando ou tem preferência por utilizar interface.
#Esta é uma interface leve para poder rodar milhares de genomas de uma só vez. Outra interface bem mais elaborada está sendo produzida com streamlit.


from __future__ import annotations

import os
import sys
import traceback
from dataclasses import dataclass, field
from typing import List

# ===== PanViTa import (arquivo panvita.py precisa estar no mesmo diretório)
try:
    import panvita  # panvita.py must exist in the same directory
except Exception as e:
    print("Error to import panvita.py:", e)
    raise

# ===== PyQt6
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread, QTimer, QSize
from PyQt6.QtGui import QPixmap, QAction, QIcon, QFont, QFontDatabase
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QListWidget, QListWidgetItem, QGroupBox, QFormLayout, QSpinBox,
    QCheckBox, QRadioButton, QLineEdit, QTextEdit, QComboBox, QProgressBar,
    QMessageBox, QToolBar, QStatusBar, QStyle, QToolButton, QSizePolicy, QSplashScreen
)

APP_TITLE = "PanViTa"

# ===== Temas (QSS)
DARK_QSS = """
* { font-family: Inter, "Segoe UI", Roboto, Arial; }
QMainWindow { background-color: #0f172a; }
QToolBar { background: #0b1220; border-bottom: 1px solid #334155; spacing: 6px; padding: 6px; }
QStatusBar { background: #0b1220; color: #cbd5e1; border-top: 1px solid #334155; }
QGroupBox { color: #e2e8f0; border: 1px solid #334155; border-radius: 12px; margin-top: 16px; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 12px; padding: 6px 10px; background: #0b1220; color: #93c5fd; border-radius: 8px; font-weight: 700; }
QLabel { color: #e5e7eb; }
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QListWidget {
    background: #0b1220; color: #e5e7eb; border: 1px solid #334155; border-radius: 10px; padding: 8px;
}
QListWidget::item { padding: 6px; }
QPushButton { background: #2563eb; color: white; border: none; padding: 10px 14px; border-radius: 12px; font-weight: 600; }
QPushButton:hover { background: #1d4ed8; }
QPushButton:disabled { background: #334155; color: #A0AEC0; }
QPushButton[secondary="true"] { background: #1f2937; color: #e5e7eb; }
QPushButton[secondary="true"]:hover { background: #374151; }

QProgressBar { background: #0b1220; border: 1px solid #334155; border-radius: 10px; color: #e5e7eb; text-align: center; height: 18px; }
QProgressBar::chunk { border-radius: 10px; background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #22c55e, stop:1 #16a34a); }

QToolButton#collapseBtn {
    border: none; color: #93c5fd; padding: 4px 6px; border-radius: 8px;
}
QToolButton#collapseBtn:hover { background: rgba(147,197,253,0.1); }
"""


# ===== Modelo de execução
@dataclass
class RunConfig:
    use_card: bool = False
    use_vfdb: bool = False
    use_bacmet: bool = False
    use_megares: bool = False

    aligner: str = "auto"  # "auto", "diamond", "blast", "both"

    identity: int = 70
    coverage: int = 70

    image_format: str = "pdf"  # "pdf" ou "png"
    keep_intermediate: bool = False
    save_genes: bool = False

    do_download_gbk: bool = False  # -b
    do_download_fasta: bool = False  # -g
    do_run_prokka: bool = False  # -a
    keep_locus_tag: bool = False  # -s
    fetch_metadata: bool = False  # -m
    do_update: bool = False  # -u/-update

    input_files: List[str] = field(default_factory=list)
    csv_ncbi: str | None = None
    workdir: str = os.getcwd()

    def build_argv(self) -> List[str]:
        argv = ["panvita.py"]
        if self.use_card: argv.append("-card")
        if self.use_vfdb: argv.append("-vfdb")
        if self.use_bacmet: argv.append("-bacmet")
        if self.use_megares: argv.append("-megares")

        if self.aligner == "diamond": argv.append("-diamond")
        elif self.aligner == "blast": argv.append("-blast")
        elif self.aligner == "both": argv.append("-both")

        argv.extend(["-i", str(self.identity)])
        argv.extend(["-c", str(self.coverage)])

        argv.append("-pdf" if self.image_format == "pdf" else "-png")
        if self.keep_intermediate: argv.append("-keep")
        if self.save_genes: argv.append("-save-genes")

        if self.do_update: argv.append("-u")
        if self.do_download_gbk: argv.append("-b")
        if self.do_download_fasta: argv.append("-g")
        if self.do_run_prokka: argv.append("-a")
        if self.keep_locus_tag: argv.append("-s")
        if self.fetch_metadata: argv.append("-m")

        if self.csv_ncbi: argv.append(self.csv_ncbi)
        for f in self.input_files: argv.append(f)
        return argv

# ===== Worker thread
class Worker(QThread):
    log = pyqtSignal(str)
    finished_ok = pyqtSignal()
    finished_error = pyqtSignal(str)

    def __init__(self, cfg: RunConfig):
        super().__init__()
        self.cfg = cfg

    def run(self):
        import contextlib
        from io import StringIO
        original_cwd = os.getcwd()
        original_argv = list(sys.argv)
        try:
            os.makedirs(self.cfg.workdir, exist_ok=True)
            os.chdir(self.cfg.workdir)

            sys.argv = self.cfg.build_argv()
            self.log.emit("\n Executando: " + " ".join(sys.argv) + "\n")

            buffer = StringIO()

            class Tee:
                def __init__(self, *streams): self.streams = streams
                def write(self, s):
                    for st in self.streams: st.write(s)
                    return len(s)
                def flush(self):
                    for st in self.streams:
                        try: st.flush()
                        except Exception: pass

            tee_out = Tee(sys.__stdout__, buffer)
            tee_err = Tee(sys.__stderr__, buffer)

            with contextlib.redirect_stdout(tee_out), contextlib.redirect_stderr(tee_err):
                pv = panvita.PanViTa()
                pv.run()

            self.log.emit(buffer.getvalue())
            self.finished_ok.emit()
        except SystemExit:
            self.log.emit("\nProcesso finalizado.\n")
            self.finished_ok.emit()
        except Exception as e:
            self.log.emit(traceback.format_exc())
            self.finished_error.emit(str(e))
        finally:
            sys.argv = original_argv
            os.chdir(original_cwd)

# ===== Seção colapsável (wrapper simples)
class CollapsibleSection(QWidget):
    def __init__(self, title: str, content: QWidget, starts_open: bool = True):
        super().__init__()
        self.content = content
        self.btn = QToolButton(text=title)
        self.btn.setCheckable(True)
        self.btn.setChecked(starts_open)
        self.btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn.setArrowType(Qt.ArrowType.DownArrow if starts_open else Qt.ArrowType.RightArrow)
        self.btn.setObjectName("collapseBtn")
        self.btn.clicked.connect(self.toggle)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(self.btn)
        header.addStretch(1)

        self.v = QVBoxLayout(self)
        self.v.setContentsMargins(0, 0, 0, 0)
        self.v.setSpacing(6)
        self.v.addLayout(header)
        self.v.addWidget(self.content)
        self.content.setVisible(starts_open)

    def toggle(self):
        opened = self.btn.isChecked()
        self.btn.setArrowType(Qt.ArrowType.DownArrow if opened else Qt.ArrowType.RightArrow)
        self.content.setVisible(opened)

# ===== Janela principal
class MainWindow(QMainWindow):
    theme_dark = True

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1200, 820)
        self._apply_theme(self.theme_dark)

        self.cfg = RunConfig()
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        self.resize(1200, 820)
        self._apply_theme(self.theme_dark)

        # ======== Toolbar
        self._build_toolbar()

        # ======== Conteúdo
        container = QWidget()
        main = QHBoxLayout(container)
        main.setContentsMargins(16, 12, 16, 12)
        main.setSpacing(16)

        # ----- Sidebar com branding e ações
        sidebar = self._build_sidebar()

        # ----- Coluna direita (formularios + log) com seções colapsáveis
        right_col = self._build_forms_and_log()

        main.addLayout(sidebar, stretch=0)
        main.addLayout(right_col, stretch=1)
        self.setCentralWidget(container)

        # ======== Status bar
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.statusBar().showMessage("Pronto")

    # === UI building helpers ===
    def _build_toolbar(self):
        tb = QToolBar("Principal")
        tb.setIconSize(QSize(18, 18))
        self.addToolBar(tb)

        style = self.style()
        act_new = QAction(style.standardIcon(QStyle.StandardPixmap.SP_FileIcon), "Novo projeto", self)
        act_open = QAction(style.standardIcon(QStyle.StandardPixmap.SP_DirIcon), "Abrir diretório", self)


        act_open.triggered.connect(self.pick_workdir)

        tb.addAction(act_new)
        tb.addAction(act_open)
        tb.addSeparator()

    def _build_sidebar(self) -> QVBoxLayout:
        style = self.style()
        sidebar = QVBoxLayout()
        sidebar.setContentsMargins(12, 8, 12, 8)
        sidebar.setSpacing(10)

        # Logo
        logo_lbl = QLabel()
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            if not pix.isNull():
                # Reduz agressivamente para evitar limites de alocação de imagem
                target_w = min(220, pix.width())
                logo_lbl.setPixmap(pix.scaledToWidth(target_w, Qt.TransformationMode.SmoothTransformation))

        brand = QLabel("<div style='text-align:center'><div style='font-size:20px;font-weight:800'>PanViTa</div>"
                       "<div style='color:#94a3b8'>Pan Virulence &amp; Resistance</div></div>")
        brand.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Botões
        self.btn_run = QPushButton("▶️ Iniciar análise")
        self.btn_run.clicked.connect(self.start_run)
        self.btn_stop = QPushButton("⏹️ Cancelar (fecha app)")
        self.btn_stop.setProperty("secondary", True)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.clicked.connect(self.close)

        # Barra de progresso
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminado
        self.progress.setVisible(False)

        sidebar.addSpacing(8)
        sidebar.addWidget(logo_lbl)
        sidebar.addWidget(brand)
        sidebar.addSpacing(8)
        sidebar.addWidget(self.btn_run)
        sidebar.addWidget(self.btn_stop)
        sidebar.addWidget(self.progress)
        sidebar.addStretch(1)


        self.btn_help = QPushButton("❓ Help")
        self.btn_help.setProperty("secondary", True)
        self.btn_help.clicked.connect(self.show_help)
        sidebar.addWidget(logo_lbl)
        sidebar.addWidget(brand)
        sidebar.addWidget(self.btn_run)
        sidebar.addWidget(self.btn_stop)
        sidebar.addWidget(self.progress)
        sidebar.addStretch(1)
        sidebar.addWidget(self.btn_help)

        return sidebar

    def _build_forms_and_log(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(12)

        # ===== Entradas & Diretório
        gb_io = QGroupBox("Entradas & Diretório de trabalho")
        f_io = QFormLayout()
        f_io.setContentsMargins(12, 10, 12, 10)
        f_io.setSpacing(10)

        self.le_workdir = QLineEdit(self.cfg.workdir)
        self.le_workdir.setPlaceholderText("Escolha onde os resultados serão salvos…")
        btn_browse_workdir = QPushButton("Escolher…")
        btn_browse_workdir.setProperty("secondary", True)
        btn_browse_workdir.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        btn_browse_workdir.clicked.connect(self.pick_workdir)
        row_wd = self._row(self.le_workdir, btn_browse_workdir)
        f_io.addRow("Diretório de trabalho:", row_wd)

        self.list_files = QListWidget()
        self.list_files.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list_files.setMinimumHeight(90)
        btn_add_files = QPushButton("Adicionar .gbk/.gbff/.gbf…")
        btn_add_files.setProperty("secondary", True)
        btn_add_files.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        btn_add_files.clicked.connect(self.add_input_files)
        btn_rm_files = QPushButton("Remover selecionados")
        btn_rm_files.setProperty("secondary", True)
        btn_rm_files.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        btn_rm_files.clicked.connect(self.remove_selected_files)
        row_files_btns = self._row(btn_add_files, btn_rm_files)
        f_io.addRow("Arquivos GenBank (opcional):", self.list_files)
        f_io.addRow("", row_files_btns)

        self.le_csv = QLineEdit()
        self.le_csv.setPlaceholderText("CSV NCBI (obrigatório para -a/-g/-b)…")
        btn_csv = QPushButton("Selecionar CSV NCBI…")
        btn_csv.setProperty("secondary", True)
        btn_csv.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        btn_csv.clicked.connect(self.pick_csv)
        row_csv = self._row(self.le_csv, btn_csv)
        f_io.addRow("CSV NCBI (p/ -a/-g/-b):", row_csv)
        gb_io.setLayout(f_io)

        # ===== Bases de dados
        gb_db = QGroupBox("Bases de dados para análise")
        l_db = QHBoxLayout(); l_db.setContentsMargins(12,10,12,10); l_db.setSpacing(10)
        self.cb_card = QCheckBox("CARD")
        self.cb_vfdb = QCheckBox("VFDB")
        self.cb_bacmet = QCheckBox("BacMet")
        self.cb_megares = QCheckBox("MEGARes")
        for w in (self.cb_card, self.cb_vfdb, self.cb_bacmet, self.cb_megares):
            w.setCursor(Qt.CursorShape.PointingHandCursor)
        l_db.addWidget(self.cb_card); l_db.addWidget(self.cb_vfdb); l_db.addWidget(self.cb_bacmet); l_db.addWidget(self.cb_megares); l_db.addStretch(1)
        gb_db.setLayout(l_db)

        # ===== Alinhador
        gb_align = QGroupBox("Alinhador")
        row_al = QHBoxLayout(); row_al.setContentsMargins(12,10,12,10); row_al.setSpacing(10)
        self.rb_auto = QRadioButton("Automático"); self.rb_auto.setChecked(True)
        self.rb_dia = QRadioButton("DIAMOND")
        self.rb_bla = QRadioButton("BLAST")
        self.rb_both = QRadioButton("Ambos")
        for w in (self.rb_auto, self.rb_dia, self.rb_bla, self.rb_both):
            w.setCursor(Qt.CursorShape.PointingHandCursor)
        row_al.addWidget(self.rb_auto); row_al.addWidget(self.rb_dia); row_al.addWidget(self.rb_bla); row_al.addWidget(self.rb_both); row_al.addStretch(1)
        gb_align.setLayout(row_al)

        # ===== Parâmetros
        gb_params = QGroupBox("Parâmetros")
        f_params = QFormLayout(); f_params.setContentsMargins(12,10,12,10); f_params.setSpacing(10)
        self.sp_id = QSpinBox(); self.sp_id.setRange(0, 100); self.sp_id.setValue(70); self.sp_id.setSuffix(" %"); self.sp_id.setToolTip("Identidade mínima (-i)")
        self.sp_cov = QSpinBox(); self.sp_cov.setRange(0, 100); self.sp_cov.setValue(70); self.sp_cov.setSuffix(" %"); self.sp_cov.setToolTip("Cobertura mínima (-c)")
        self.cb_keep = QCheckBox("Manter intermediários (-keep)")
        self.cb_save_genes = QCheckBox("Salvar genes encontrados (-save-genes)")
        self.cmb_format = QComboBox(); self.cmb_format.addItems(["pdf", "png"])
        f_params.addRow("Identidade mínima (-i):", self.sp_id)
        f_params.addRow("Cobertura mínima (-c):", self.sp_cov)
        f_params.addRow("Formato das figuras:", self.cmb_format)
        f_params.addRow("Opções:", self._row(self.cb_keep, self.cb_save_genes))
        gb_params.setLayout(f_params)

        # ===== Downloads / Extras (COLAPSÁVEL)
        extras_content = QWidget()
        row_ops = QVBoxLayout(extras_content); row_ops.setContentsMargins(12,10,12,10); row_ops.setSpacing(6)
        self.cb_u = QCheckBox("Atualizar dependências & bancos (-u/-update)")
        self.cb_b = QCheckBox("Baixar GBK/GBFF (-b)")
        self.cb_g = QCheckBox("Baixar FASTA (-g)")
        self.cb_a = QCheckBox("Anotar com PROKKA (-a)")
        self.cb_s = QCheckBox("Manter locus_tag como cepa (-s, requer -b)")
        self.cb_m = QCheckBox("Buscar metadata BioSample (-m)")
        for w in (self.cb_u, self.cb_b, self.cb_g, self.cb_a, self.cb_s, self.cb_m):
            w.setCursor(Qt.CursorShape.PointingHandCursor)
        for w in (self.cb_u, self.cb_b, self.cb_g, self.cb_a, self.cb_s, self.cb_m): row_ops.addWidget(w)
        extras_section = CollapsibleSection("Downloads / Anotação / Extras", extras_content, starts_open=False)

        # ===== Log (fonte monoespaçada)
        gb_log = QGroupBox("Saída / Log de execução")
        v_log = QVBoxLayout(); v_log.setContentsMargins(12,10,12,12)
        self.txt_log = QTextEdit(); self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("Logs do PanViTa aparecerão aqui…")
        # fonte monoespaçada amigável
        mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        mono.setPointSize(mono.pointSize() + 1)
        self.txt_log.setFont(mono)
        v_log.addWidget(self.txt_log)
        gb_log.setLayout(v_log)

        # ===== Ordem e colapsáveis
        col.addWidget(gb_io)
        col.addWidget(gb_db)
        col.addWidget(gb_align)
        col.addWidget(gb_params)
        col.addWidget(extras_section)
        col.addWidget(gb_log, stretch=1)

        return col

    # Pequenos helpers
    @staticmethod
    def _row(*widgets: QWidget) -> QWidget:
        h = QHBoxLayout(); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(8)
        for w in widgets:
            if isinstance(w, QPushButton):
                w.setCursor(Qt.CursorShape.PointingHandCursor)
            h.addWidget(w)
        wrap = QWidget(); wrap.setLayout(h)
        return wrap

    def _apply_theme(self, dark: bool):
        self.setStyleSheet(DARK_QSS)

    def show_help(self):
        text = ("<b>How to use PanViTa GUI:</b><br>"
                "1) Select working directory<br>"
                "2) Configure options<br>"
                "3) Click 'Run Analysis'<br><br>"
                "<a href='https://github.com/VictorCaricatte/PanViTa-2/tree/main'>"
                "Open full documentation on GitHub</a>")
        box = QMessageBox(self)
        box.setWindowTitle("Help")
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setText(text)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.exec()

    # === Slots ===
    def pick_workdir(self):
        d = QFileDialog.getExistingDirectory(self, "Escolher diretório de trabalho", self.le_workdir.text() or os.getcwd())
        if d:
            self.le_workdir.setText(d)
            self.statusBar().showMessage(f"Diretório definido: {d}", 4000)

    def add_input_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Escolher arquivos GenBank", self.le_workdir.text() or os.getcwd(),
            "GenBank (*.gbk *.gbff *.gbf);;Todos (*.*)"
        )
        for f in files:
            if f and not any(f == self.list_files.item(i).text() for i in range(self.list_files.count())):
                self.list_files.addItem(QListWidgetItem(f))
        if files:
            self.statusBar().showMessage(f"{len(files)} arquivo(s) adicionado(s).", 3000)

    def remove_selected_files(self):
        count = len(self.list_files.selectedItems())
        for item in self.list_files.selectedItems():
            self.list_files.takeItem(self.list_files.row(item))
        if count:
            self.statusBar().showMessage(f"{count} arquivo(s) removido(s).", 3000)

    def pick_csv(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Selecionar CSV (tabela NCBI)", self.le_workdir.text() or os.getcwd(),
            "CSV (*.csv);;Todos (*.*)"
        )
        if f:
            self.le_csv.setText(f)
            self.statusBar().showMessage("CSV selecionado.", 3000)

    def collect_config(self) -> RunConfig:
        cfg = RunConfig()
        cfg.use_card = self.cb_card.isChecked()
        cfg.use_vfdb = self.cb_vfdb.isChecked()
        cfg.use_bacmet = self.cb_bacmet.isChecked()
        cfg.use_megares = self.cb_megares.isChecked()

        if self.rb_dia.isChecked(): cfg.aligner = "diamond"
        elif self.rb_bla.isChecked(): cfg.aligner = "blast"
        elif self.rb_both.isChecked(): cfg.aligner = "both"
        else: cfg.aligner = "auto"

        cfg.identity = int(self.sp_id.value())
        cfg.coverage = int(self.sp_cov.value())
        cfg.image_format = self.cmb_format.currentText()
        cfg.keep_intermediate = self.cb_keep.isChecked()
        cfg.save_genes = self.cb_save_genes.isChecked()

        cfg.do_update = self.cb_u.isChecked()
        cfg.do_download_gbk = self.cb_b.isChecked()
        cfg.do_download_fasta = self.cb_g.isChecked()
        cfg.do_run_prokka = self.cb_a.isChecked()
        cfg.keep_locus_tag = self.cb_s.isChecked()
        cfg.fetch_metadata = self.cb_m.isChecked()

        cfg.workdir = self.le_workdir.text().strip() or os.getcwd()
        cfg.csv_ncbi = self.le_csv.text().strip() or None
        cfg.input_files = [self.list_files.item(i).text() for i in range(self.list_files.count())]
        return cfg

    def validate_config(self, cfg: RunConfig) -> bool:
        if not (cfg.use_card or cfg.use_vfdb or cfg.use_bacmet or cfg.use_megares or cfg.do_update or cfg.do_download_fasta or cfg.do_download_gbk or cfg.do_run_prokka):
            QMessageBox.warning(self, APP_TITLE, "Selecione ao menos uma base de dados ou uma operação (ex.: -u, -a, -g, -b).")
            return False
        if (cfg.do_download_gbk or cfg.do_download_fasta or cfg.do_run_prokka) and not cfg.csv_ncbi:
            QMessageBox.warning(self, APP_TITLE, "Para -a/-g/-b é necessário um CSV do NCBI.")
            return False
        if not (cfg.do_download_gbk or cfg.do_download_fasta or cfg.do_run_prokka) and len(cfg.input_files) == 0:
            QMessageBox.information(self, APP_TITLE, "Nenhum arquivo de entrada selecionado. Você pode usar -a/-g/-b com CSV ou adicionar .gbk/.gbff.")
        return True

    def start_run(self):
        cfg = self.collect_config()
        if not self.validate_config(cfg):
            return
        # Desabilitar UI
        self.btn_run.setEnabled(False)
        self.progress.setVisible(True)
        self.statusBar().showMessage("Executando…")
        self.txt_log.append("<b>Iniciando…</b>")

        self.worker = Worker(cfg)
        self.worker.log.connect(lambda t: self.txt_log.append(self.htmlize(t)))
        self.worker.finished_ok.connect(self.finish_ok)
        self.worker.finished_error.connect(self.finish_error)
        self.worker.start()

    def finish_ok(self):
        self.progress.setVisible(False)
        self.btn_run.setEnabled(True)
        self.statusBar().showMessage("Concluído com sucesso.", 4000)
        self.txt_log.append("<b>Concluído com sucesso.</b>")

    def finish_error(self, msg: str):
        self.progress.setVisible(False)
        self.btn_run.setEnabled(True)
        self.statusBar().showMessage("Falha na execução.", 4000)
        self.txt_log.append(f"<b style='color:#fca5a5;'>Falha:</b> {msg}")
        QMessageBox.critical(self, APP_TITLE, f"Ocorreu um erro durante a execução:\n{msg}")

    @staticmethod
    def htmlize(text: str) -> str:
        import html
        return html.escape(text).replace("\n", "<br>")

# ====== Splash & main
def main():
    app = QApplication(sys.argv)

    # Splash com logo (opcional)
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    splash = None
    if os.path.exists(logo_path):
        pix = QPixmap(logo_path)
        if not pix.isNull():
            scaled = pix.scaled(360, 360, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            splash = QSplashScreen(scaled)
            splash.showMessage("Carregando PanViTa…", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, Qt.GlobalColor.white)
            splash.show()

    win = MainWindow()

    # pequeno delay só para transição suave do splash (sem bloquear)
    def show_main():
        if splash: splash.finish(win)
        win.show()

    QTimer.singleShot(600, show_main)  # ~0.6s

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
