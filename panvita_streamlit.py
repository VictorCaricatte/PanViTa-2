import streamlit as st
import sys
import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path
import glob
from PIL import Image
import io
import base64
from datetime import datetime
import warnings
import threading
import time
from typing import Callable, Optional
import shutil
warnings.filterwarnings('ignore')

# Adicionar o diretório pai ao path para importar o panvita original
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from panvita import PanViTa, PanViTaConfig
except ImportError:
    st.error("Erro ao importar o módulo panvita.py. Verifique se o arquivo está no diretório correto.")
    st.stop()

class PanViTaProgressTracker:
    """Classe para monitorar o progresso da análise PanViTa"""
    
    def __init__(self):
        self.progress = 0.0
        self.status = "Inicializando..."
        self.is_running = False
        self.is_complete = False
        self.error_message = None
        self.steps = [
            "Verificando dependências",
            "Configurando alinhadores", 
            "Processando arquivos de entrada",
            "Extraindo posições",
            "Extraindo proteínas",
            "Executando alinhamentos",
            "Processando resultados",
            "Gerando visualizações",
            "Finalizando análise"
        ]
        self.current_step = 0
        
    def update_progress(self, step: int, substep_progress: float = 0.0):
        """Atualiza o progresso baseado no passo atual"""
        if step < len(self.steps):
            self.current_step = step
            self.status = self.steps[step]
            # Cada passo representa ~11% do progresso total
            base_progress = (step / len(self.steps)) * 100
            # Adicionar progresso do sub-passo
            step_increment = (substep_progress / len(self.steps)) * 100
            self.progress = min(100.0, base_progress + step_increment)
            
    def set_complete(self):
        """Marca a análise como completa"""
        self.progress = 100.0
        self.status = "Análise concluída com sucesso!"
        self.is_complete = True
        self.is_running = False
        
    def set_error(self, error_msg: str):
        """Marca a análise como erro"""
        self.error_message = error_msg
        self.status = f"Erro: {error_msg}"
        self.is_running = False
        
    def start(self):
        """Inicia o monitoramento"""
        self.is_running = True
        self.is_complete = False
        self.error_message = None
        self.progress = 0.0
        self.current_step = 0
        self.status = "Iniciando análise..."

class PanViTaWithProgress(PanViTa):
    """Versão do PanViTa com suporte a callbacks de progresso"""
    
    def __init__(self, progress_tracker: PanViTaProgressTracker):
        super().__init__()
        self.tracker = progress_tracker
        
    def run(self):
        """Execução principal com monitoramento de progresso"""
        try:
            self.tracker.update_progress(0)  # Verificando dependências
            self._handle_help_and_version()
            
            # Setup dependencies and databases
            dependency_manager = self._get_dependency_manager()
            self.dppath = dependency_manager.check_dependencies()
            
            self.tracker.update_progress(1)  # Configurando alinhadores
            
            # Determine which aligner(s) to use
            aligner = self._get_aligner()
            aligner_types, aligner_exes, aligner_names = self._determine_aligners(aligner)
            
            if aligner_types is None:
                raise Exception("No aligners available")

            # Initialize variables
            self._setup_databases_and_dicts(aligner_exes)
            
            self.tracker.update_progress(2)  # Processando arquivos de entrada
            
            # Download operations
            if "-b" in sys.argv:
                self._download_genbank_files()
            if "-a" in sys.argv or "-g" in sys.argv:
                self._download_fasta_files()
                
            # Process files and parameters
            self._process_files_and_parameters()
            
            # If no analysis parameters, just organize downloaded files
            if len(self.parameters) == 0:
                self._organize_downloaded_files()
                self.tracker.set_complete()
                return
                
            self.tracker.update_progress(3)  # Extraindo posições
            
            # Extract and save positions
            self._extract_and_save_positions()
            
            self.tracker.update_progress(4)  # Extraindo proteínas
            
            # Extract and save proteins
            self._extract_and_save_proteins()
            
            self.tracker.update_progress(5)  # Executando alinhamentos
            
            # Align and mine
            self._align_and_mine(aligner_types, aligner_exes, aligner_names)
            
            self.tracker.update_progress(6)  # Processando resultados
            
            # Run main analysis workflow
            self._run_analysis_workflow(aligner_types, aligner_names)
            
            self.tracker.update_progress(7)  # Gerando visualizações
            
            # Cleanup
            self._remove_intermediate_files()
            
            self.tracker.update_progress(8)  # Finalizando análise
            
            # Final messages
            self._print_final_messages()
            
            # Marcar como completo
            self.tracker.set_complete()
            
        except Exception as e:
            self.tracker.set_error(str(e))
            raise e
    
    def _get_dependency_manager(self):
        """Obter gerenciador de dependências"""
        # Importar aqui para evitar problemas de importação circular
        from panvita import DependencyManager
        return DependencyManager()
    
    def _get_aligner(self):
        """Obter alinhador"""
        # Importar aqui para evitar problemas de importação circular
        from panvita import Aligner
        return Aligner(self.dppath)

# Configuração da página
st.set_page_config(
    page_title="PanViTa Web Interface",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.sub-header {
    font-size: 1.5rem;
    color: #ff7f0e;
    margin-top: 1rem;
    margin-bottom: 1rem;
}
.info-box {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}
.about-panvita {
    background-color: #000000;
    color: #ffffff;
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
    border: 2px solid #1f77b4;
}
.about-panvita h3 {
    color: #ffffff;
    margin-bottom: 1rem;
}
.about-panvita h4 {
    color: #1f77b4;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}
.about-panvita ul {
    color: #ffffff;
}
.about-panvita li {
    color: #ffffff;
    margin-bottom: 0.3rem;
}
.logo-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 1rem;
}
.success-box {
    background-color: #d4edda;
    color: #155724;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}
.error-box {
    background-color: #f8d7da;
    color: #721c24;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

def main():
    # Adicionar logotipo
    try:
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            st.markdown('<div class="logo-container">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(logo_path, width=200)
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        pass  # Se não conseguir carregar o logo, continua sem ele
    
    st.markdown('<h1 class="main-header">🧬 PanViTa - Interface Web</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem;">Pan Virulence and resisTance Analysis</p>', unsafe_allow_html=True)
    
    # Sidebar para navegação
    st.sidebar.title("Navegação")
    tab_selection = st.sidebar.radio(
        "Selecione uma aba:",
        ["🏠 Início", "⚙️ Configuração", "🚀 Execução", "📊 Visualização", "📋 Ajuda"]
    )
    
    if tab_selection == "🏠 Início":
        show_home_tab()
    elif tab_selection == "⚙️ Configuração":
        show_configuration_tab()
    elif tab_selection == "🚀 Execução":
        show_execution_tab()
    elif tab_selection == "📊 Visualização":
        show_visualization_tab()
    elif tab_selection == "📋 Ajuda":
        show_help_tab()

def show_home_tab():
    st.markdown('<h2 class="sub-header">Bem-vindo ao PanViTa Web</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="about-panvita">
        <h3>Sobre o PanViTa</h3>
        <p>O PanViTa é uma ferramenta avançada para análise comparativa de genomas contra bases de dados de virulência e resistência.</p>
        
        <h4>Funcionalidades principais:</h4>
        <ul>
            <li>Comparação de múltiplos genomas</li>
            <li>Análise contra bases de dados especializadas (CARD, VFDB, BacMet, MEGARes)</li>
            <li>Geração de mapas de calor e matrizes de presença</li>
            <li>Visualizações interativas</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="about-panvita">
        <h4>Versão</h4>
        <p><strong>PanViTa v2.0.0</strong></p>
        
        <h4>Contato</h4>
        <p>dlnrodrigues@ufmg.br<br>
        victorsc@ufmg.br<br>
        vinicius.oliveira.1444802@sga.pucminas.br</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Status do sistema
    st.markdown('<h3 class="sub-header">Status do Sistema</h3>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if check_panvita_availability():
            st.success("✅ PanViTa disponível")
        else:
            st.error("❌ PanViTa não encontrado")
    
    with col2:
        if check_dependencies():
            st.success("✅ Dependências OK")
        else:
            st.warning("⚠️ Verificar dependências")
    
    with col3:
        results_count = count_results_folders()
        st.info(f"📊 {results_count} resultados disponíveis")
    
    # Seção expandida de dependências
    st.markdown('<h4 class="sub-header">Dependências</h4>', unsafe_allow_html=True)
    
    dependencies = get_detailed_dependencies()
    
    # Dropdown de dependências
    with st.expander("📦 Ver todas as dependências", expanded=False):
        for module, info in dependencies.items():
            status_icon = "✅" if info['status'] == 'OK' else "❌"
            st.write(f"{status_icon} **{info['name']}**: {info['description']} - Status: {info['status']}")
    
    # Seção de resultados disponíveis
    st.markdown('<h4 class="sub-header">Resultados Disponíveis</h4>', unsafe_allow_html=True)
    
    results_info = get_results_with_status()
    
    if results_info:
        with st.expander(f"📊 Ver todos os resultados ({len(results_info)} disponíveis)", expanded=False):
            for result in results_info:
                st.write(f"**{result['name']}**")
                st.write(f"  - Status: {result['status']}")
                st.write(f"  - Arquivos: {result['files']}")
                st.write(f"  - Modificado: {result['modified']}")
                st.write("---")
    else:
        st.info("Nenhum resultado encontrado")
    
    # Seção de limpeza de dados
    st.markdown('<h4 class="sub-header">Gerenciamento de Dados</h4>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("**Exclusão de Dados de Análise**")
        st.write("Remove completamente as pastas 'results', 'Positions' e pastas 'Results_*' para iniciar uma nova análise.")
    
    with col2:
        # Inicializar session state para controle de confirmação
        if 'show_delete_confirmation' not in st.session_state:
            st.session_state.show_delete_confirmation = False
        
        # Botão principal de exclusão
        if not st.session_state.show_delete_confirmation:
            if st.button("🗑️ Excluir Dados de Análise", type="secondary", help="Exclui todas as pastas de resultados e posições"):
                st.session_state.show_delete_confirmation = True
                st.rerun()
        
        # Mostrar confirmação se solicitada
        if st.session_state.show_delete_confirmation:
            st.warning("⚠️ **ATENÇÃO**: Esta ação irá excluir permanentemente todas as pastas de análise!")
            
            col_confirm1, col_confirm2 = st.columns(2)
            
            with col_confirm1:
                if st.button("✅ Confirmar Exclusão", type="primary", key="confirm_delete"):
                    success, message = delete_analysis_folders()
                    if success:
                        st.success(message)
                        st.session_state.show_delete_confirmation = False
                        st.rerun()  # Recarregar a página para atualizar contadores
                    else:
                        st.error(message)
                        st.session_state.show_delete_confirmation = False
            
            with col_confirm2:
                if st.button("❌ Cancelar", key="cancel_delete"):
                    st.session_state.show_delete_confirmation = False
                    st.info("Operação cancelada.")
                    st.rerun()

def show_configuration_tab():
    st.markdown('<h2 class="sub-header">Configuração da Análise</h2>', unsafe_allow_html=True)
    
    # Inicializar session state
    if 'config' not in st.session_state:
        st.session_state.config = {
            'databases': [],
            'files': [],
            'csv_file': None,
            'identity': 70.0,
            'coverage': 70.0,
            'aligner': 'diamond',
            'output_format': 'pdf',
            'additional_options': []
        }
    
    # Seleção de bases de dados
    st.markdown('<h3 class="sub-header">Bases de Dados</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        bacmet = st.checkbox("BacMet - Antibacterial Biocide and Metal Resistance", key="bacmet")
        card = st.checkbox("CARD - Comprehensive Antibiotic Resistance Database", key="card")
    
    with col2:
        megares = st.checkbox("MEGARes - Antimicrobial Resistance Database", key="megares")
        vfdb = st.checkbox("VFDB - Virulence Factor Database", key="vfdb")
    
    # Atualizar configuração
    databases = []
    if bacmet: databases.append('-bacmet')
    if card: databases.append('-card')
    if megares: databases.append('-megares')
    if vfdb: databases.append('-vfdb')
    
    st.session_state.config['databases'] = databases
    
    # Upload de arquivos
    st.markdown('<h3 class="sub-header">Arquivos de Entrada</h3>', unsafe_allow_html=True)
    
    file_input_method = st.radio(
        "Método de entrada:",
        ["Upload de arquivos GenBank", "Tabela CSV do NCBI"]
    )
    
    if file_input_method == "Upload de arquivos GenBank":
        uploaded_files = st.file_uploader(
            "Selecione arquivos GenBank (.gbk, .gbf, .gbff)",
            type=['gbk', 'gbf', 'gbff'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)")
            for file in uploaded_files:
                st.write(f"- {file.name}")
            
            # Salvar arquivos temporariamente
            temp_files = []
            for file in uploaded_files:
                temp_path = f"temp_{file.name}"
                with open(temp_path, "wb") as f:
                    f.write(file.getbuffer())
                temp_files.append(temp_path)
            
            st.session_state.config['files'] = temp_files
    
    else:
        csv_file = st.file_uploader(
            "Selecione tabela CSV do NCBI",
            type=['csv']
        )
        
        if csv_file:
            st.success("✅ Arquivo CSV carregado")
            
            # Salvar CSV temporariamente
            temp_csv = f"temp_{csv_file.name}"
            with open(temp_csv, "wb") as f:
                f.write(csv_file.getbuffer())
            
            st.session_state.config['csv_file'] = temp_csv
            
            # Opções de download
            st.markdown('<h4>Opções de Download</h4>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                download_genbank = st.checkbox("Download GenBank files (-b)")
            with col2:
                download_fasta = st.checkbox("Download FASTA files (-g)")
            with col3:
                annotate_prokka = st.checkbox("Anotar com PROKKA (-a)")
            
            get_metadata = st.checkbox("Obter metadados BioSample (-m)")
            keep_locus_tag = st.checkbox("Manter locus_tag como strain (-s)")
    
    # Parâmetros de análise
    st.markdown('<h3 class="sub-header">Parâmetros de Análise</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        identity = st.slider(
            "Identidade mínima (%)",
            min_value=0.0,
            max_value=100.0,
            value=70.0,
            step=0.1,
            help="Identidade mínima para inferir presença (padrão: 70%)"
        )
        
        coverage = st.slider(
            "Cobertura mínima (%)",
            min_value=0.0,
            max_value=100.0,
            value=70.0,
            step=0.1,
            help="Cobertura mínima para inferir presença (padrão: 70%)"
        )
    
    with col2:
        aligner = st.selectbox(
            "Alinhador",
            ["diamond", "blast", "both"],
            help="Escolha o alinhador para usar"
        )
        
        output_format = st.selectbox(
            "Formato de saída",
            ["pdf", "png"],
            help="Formato das figuras geradas"
        )
    
    # Opções adicionais
    st.markdown('<h3 class="sub-header">Opções Adicionais</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        keep_files = st.checkbox("Manter arquivos intermediários (-keep)")
        save_genes = st.checkbox("Salvar genes encontrados (-save-genes)")
    
    with col2:
        use_system_diamond = st.checkbox("Usar DIAMOND do sistema (-d)")
        update_databases = st.checkbox("Atualizar bases de dados (-update)")
    
    # Atualizar configuração
    st.session_state.config.update({
        'identity': identity,
        'coverage': coverage,
        'aligner': aligner,
        'output_format': output_format
    })
    
    additional_options = []
    if keep_files: additional_options.append('-keep')
    if save_genes: additional_options.append('-save-genes')
    if use_system_diamond: additional_options.append('-d')
    if update_databases: additional_options.append('-update')
    
    st.session_state.config['additional_options'] = additional_options
    
    # Resumo da configuração
    if st.button("📋 Mostrar Resumo da Configuração"):
        show_configuration_summary()

def show_configuration_summary():
    st.markdown('<h4>Resumo da Configuração</h4>', unsafe_allow_html=True)
    
    config = st.session_state.config
    
    with st.expander("Ver configuração completa", expanded=True):
        st.write("**Bases de dados selecionadas:**")
        if config['databases']:
            for db in config['databases']:
                st.write(f"- {db}")
        else:
            st.write("Nenhuma base de dados selecionada")
        
        st.write("**Arquivos:**")
        if config['files']:
            st.write(f"- {len(config['files'])} arquivo(s) GenBank")
        elif config['csv_file']:
            st.write(f"- Arquivo CSV: {config['csv_file']}")
        else:
            st.write("Nenhum arquivo selecionado")
        
        st.write("**Parâmetros:**")
        st.write(f"- Identidade: {config['identity']}%")
        st.write(f"- Cobertura: {config['coverage']}%")
        st.write(f"- Alinhador: {config['aligner']}")
        st.write(f"- Formato: {config['output_format']}")
        
        if config['additional_options']:
            st.write("**Opções adicionais:**")
            for opt in config['additional_options']:
                st.write(f"- {opt}")

def show_execution_tab():
    st.markdown('<h2 class="sub-header">Execução da Análise</h2>', unsafe_allow_html=True)
    
    if 'config' not in st.session_state:
        st.warning("⚠️ Configure a análise primeiro na aba 'Configuração'")
        return
    
    config = st.session_state.config
    
    # Verificar se há configuração mínima
    if not config['databases']:
        st.error("❌ Selecione pelo menos uma base de dados")
        return
    
    if not config['files'] and not config['csv_file']:
        st.error("❌ Selecione arquivos de entrada")
        return
    
    # Mostrar resumo antes da execução
    show_configuration_summary()
    
    # Botão de execução
    if st.button("🚀 Executar Análise", type="primary"):
        execute_panvita_analysis()

def execute_panvita_analysis():
    """Executa a análise PanViTa com os parâmetros configurados e barra de progresso"""
    
    config = st.session_state.config
    
    # Construir argumentos sys.argv
    argv_args = ['panvita.py']
    
    # Adicionar bases de dados
    argv_args.extend(config['databases'])
    
    # Adicionar parâmetros
    if config['identity'] != 70.0:
        argv_args.extend(['-i', str(config['identity'])])
    
    if config['coverage'] != 70.0:
        argv_args.extend(['-c', str(config['coverage'])])
    
    # Adicionar alinhador
    if config['aligner'] == 'diamond':
        argv_args.append('-diamond')
    elif config['aligner'] == 'blast':
        argv_args.append('-blast')
    elif config['aligner'] == 'both':
        argv_args.append('-both')
    
    # Adicionar formato
    if config['output_format'] == 'png':
        argv_args.append('-png')
    else:
        argv_args.append('-pdf')
    
    # Adicionar opções adicionais
    argv_args.extend(config['additional_options'])
    
    # Adicionar arquivos
    if config['files']:
        argv_args.extend(config['files'])
    elif config['csv_file']:
        argv_args.append(config['csv_file'])
    
    # Mostrar comando que será executado
    st.code(' '.join(argv_args))
    
    # Inicializar tracker de progresso
    if 'progress_tracker' not in st.session_state:
        st.session_state.progress_tracker = PanViTaProgressTracker()
    
    tracker = st.session_state.progress_tracker
    tracker.start()
    
    # Criar containers para a barra de progresso
    progress_container = st.container()
    
    with progress_container:
        st.markdown("""
        <div style="
            background: black;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #1f77b4;
            margin: 10px 0;
        ">
            <h3 style="margin: 0; color: #1f77b4; display: flex; align-items: center;">
                🔄 Progresso da Análise
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Barra de progresso principal com estilo customizado
        progress_bar = st.progress(0)
        
        # Status e percentual com melhor layout
        status_col1, status_col2, status_col3 = st.columns([2, 1, 1])
        with status_col1:
            status_text = st.empty()
        with status_col2:
            percent_text = st.empty()
        with status_col3:
            step_indicator = st.empty()
        
        # Indicador de tempo estimado
        time_col1, time_col2 = st.columns(2)
        with time_col1:
            elapsed_time = st.empty()
        with time_col2:
            estimated_time = st.empty()
        
        # Log em tempo real com melhor apresentação
        log_expander = st.expander("📋 Log de Execução em Tempo Real", expanded=False)
        with log_expander:
            log_container = st.empty()
    
    # Executar análise em thread separada com contexto adequado
    def run_analysis_with_progress():
        # Configurar contexto do Streamlit de forma mais robusta
        try:
            from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
            import threading
            
            # Tentar obter o contexto atual e aplicá-lo à thread
            try:
                ctx = get_script_run_ctx()
                if ctx:
                    add_script_run_ctx(threading.current_thread(), ctx)
            except:
                # Fallback: tentar adicionar contexto sem parâmetros
                add_script_run_ctx(threading.current_thread())
        except Exception:
            # Se não conseguir configurar contexto, suprimir warnings localmente
            import warnings
            warnings.filterwarnings('ignore', message='.*missing ScriptRunContext.*')
            import logging
            logging.getLogger('streamlit').setLevel(logging.ERROR)
        
        try:
            # Backup do sys.argv original
            original_argv = sys.argv.copy()
            
            # Substituir sys.argv
            sys.argv = argv_args
            
            # Capturar saída
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            # Criar PanViTa com monitoramento
            panvita = PanViTaWithProgress(tracker)
            
            # Executar PanViTa
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                panvita.run()
            
            # Restaurar sys.argv
            sys.argv = original_argv
            
            # Marcar como completo
            tracker.set_complete()
            
            # Armazenar resultados usando um mecanismo thread-safe
            import threading
            results_lock = threading.Lock()
            with results_lock:
                st.session_state.analysis_stdout = stdout_buffer.getvalue()
                st.session_state.analysis_stderr = stderr_buffer.getvalue()
                st.session_state.analysis_success = True
                st.session_state.analysis_running = False  # Reset do estado
            
        except Exception as e:
            # Restaurar sys.argv em caso de erro
            if 'original_argv' in locals():
                sys.argv = original_argv
            tracker.set_error(str(e))
            
            # Armazenar erro usando mecanismo thread-safe
            import threading
            results_lock = threading.Lock()
            with results_lock:
                st.session_state.analysis_error = str(e)
                st.session_state.analysis_success = False
                st.session_state.analysis_running = False  # Reset do estado
    
    # Verificar se já existe uma análise em execução
    if 'analysis_running' not in st.session_state:
        st.session_state.analysis_running = False
    
    if st.session_state.analysis_running:
        st.warning("⚠️ Uma análise já está em execução. Aguarde a conclusão.")
        return
    
    # Marcar análise como em execução
    st.session_state.analysis_running = True
    
    # Suprimir warnings específicos de ScriptRunContext
    import warnings
    import logging
    
    # Configurar filtros para suprimir avisos específicos
    warnings.filterwarnings('ignore', message='.*missing ScriptRunContext.*')
    
    # Configurar logging para suprimir avisos do Streamlit
    streamlit_logger = logging.getLogger('streamlit')
    original_level = streamlit_logger.level
    streamlit_logger.setLevel(logging.ERROR)  # Só mostrar erros, não warnings
    
    # Criar thread com contexto adequado
    def create_thread_with_context():
        """Cria thread com contexto do Streamlit adequado"""
        try:
            from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
            import threading
            
            # Obter contexto atual
            current_ctx = get_script_run_ctx()
            
            # Criar thread
            thread = threading.Thread(target=run_analysis_with_progress)
            thread.daemon = True
            
            # Adicionar contexto à thread antes de iniciar
            if current_ctx:
                add_script_run_ctx(thread, current_ctx)
            
            return thread
        except Exception:
            # Fallback: criar thread normal
            thread = threading.Thread(target=run_analysis_with_progress)
            thread.daemon = True
            return thread
    
    # Executar análise
    analysis_thread = create_thread_with_context()
    analysis_thread.start()
    
    # Loop de atualização da interface com melhorias visuais
    log_content = ""
    start_time = time.time()
    
    while tracker.is_running or analysis_thread.is_alive():
        # Calcular tempo decorrido
        elapsed = time.time() - start_time
        elapsed_minutes = int(elapsed // 60)
        elapsed_seconds = int(elapsed % 60)
        
        # Estimar tempo restante baseado no progresso
        if tracker.progress > 5:  # Evitar divisão por zero
            estimated_total = elapsed / (tracker.progress / 100)
            remaining = max(0, estimated_total - elapsed)
            remaining_minutes = int(remaining // 60)
            remaining_seconds = int(remaining % 60)
        else:
            remaining_minutes = 0
            remaining_seconds = 0
        
        # Determinar cor da barra baseada no progresso
        if tracker.progress < 25:
            progress_color = "🔴"  # Vermelho para início
        elif tracker.progress < 50:
            progress_color = "🟡"  # Amarelo para meio
        elif tracker.progress < 75:
            progress_color = "🟠"  # Laranja para quase lá
        else:
            progress_color = "🟢"  # Verde para quase completo
        
        # Atualizar barra de progresso
        progress_bar.progress(tracker.progress / 100.0)
        
        # Atualizar status com melhor formatação
        status_text.markdown(f"**📍 Status:** {tracker.status}")
        
        # Atualizar percentual com cor dinâmica
        percent_text.markdown(f"**{progress_color} {tracker.progress:.1f}%**")
        
        # Indicador de etapa
        total_steps = len(tracker.steps)
        current_step = min(tracker.current_step + 1, total_steps)
        step_indicator.markdown(f"**Etapa {current_step}/{total_steps}**")
        
        # Atualizar tempos
        elapsed_time.markdown(f"**⏱️ Decorrido:** {elapsed_minutes:02d}:{elapsed_seconds:02d}")
        if remaining_minutes > 0 or remaining_seconds > 0:
            estimated_time.markdown(f"**⏳ Restante:** ~{remaining_minutes:02d}:{remaining_seconds:02d}")
        else:
            estimated_time.markdown(f"**⏳ Restante:** Calculando...")
        
        # Atualizar log com melhor formatação
        if tracker.current_step > 0:
            # Construir log com ícones e formatação
            log_lines = []
            for i, step in enumerate(tracker.steps[:tracker.current_step]):
                log_lines.append(f"✅ {step}")
            
            # Adicionar etapa atual se em progresso
            if tracker.current_step < len(tracker.steps):
                current_step_name = tracker.steps[tracker.current_step]
                log_lines.append(f"🔄 {current_step_name} (em progresso...)")
            
            log_content = "\n".join(log_lines)
            
            # Limitar o log para melhor performance
            if len(log_lines) > 15:
                display_log = "\n".join(log_lines[-15:])
                display_log = "... (etapas anteriores ocultas)\n" + display_log
            else:
                display_log = log_content
                
            # Usar um container simples para evitar problemas de chave duplicada
            log_container.text(display_log)
        
        # Aguardar antes da próxima atualização (mais responsivo)
        time.sleep(0.3)
        
        # Verificar se a thread terminou
        if not analysis_thread.is_alive():
            break
    
    # Aguardar thread terminar completamente com gestão de recursos
    try:
        analysis_thread.join(timeout=2.0)  # Timeout aumentado
        
        # Verificar se a thread ainda está viva após timeout
        if analysis_thread.is_alive():
            st.warning("⚠️ A análise está demorando mais que o esperado. Aguarde...")
            analysis_thread.join(timeout=5.0)  # Timeout adicional
            
        # Limpeza de recursos da thread
        del analysis_thread
        
    except Exception as e:
        st.error(f"Erro ao finalizar análise: {str(e)}")
    finally:
        # Sempre restaurar configurações originais
        try:
            streamlit_logger.setLevel(original_level)
            # Limpar filtros de warnings
            warnings.resetwarnings()
        except:
            pass
        
        # Garantir que o estado seja resetado mesmo em caso de erro
        if 'analysis_running' in st.session_state:
            st.session_state.analysis_running = False
    
    # Atualização final com indicadores visuais aprimorados
    if tracker.is_complete:
        # Animação de conclusão
        progress_bar.progress(1.0)
        
        # Status final com estilo especial
        status_text.markdown("""
        <div style="
            background: linear-gradient(90deg, #d4edda 0%, #c3e6cb 100%);
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #28a745;
            text-align: center;
        ">
            <strong>🎉 Análise Concluída com Sucesso!</strong>
        </div>
        """, unsafe_allow_html=True)
        
        percent_text.markdown("**🟢 100%**")
        step_indicator.markdown("**✅ Finalizado**")
        
        # Calcular tempo total
        total_time = time.time() - start_time
        total_minutes = int(total_time // 60)
        total_seconds = int(total_time % 60)
        elapsed_time.markdown(f"**⏱️ Tempo Total:** {total_minutes:02d}:{total_seconds:02d}")
        estimated_time.markdown("**🎯 Concluído!**")
        
        # Mostrar resultados com melhor apresentação
        if hasattr(st.session_state, 'analysis_success') and st.session_state.analysis_success:
            
            # Card de sucesso personalizado
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            ">
                <h3 style="margin: 0; color: white;">✅ Análise PanViTa Concluída!</h3>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Todos os dados foram processados com sucesso. Você pode visualizar os resultados na aba "Visualização".</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Logs com melhor organização
            col1, col2 = st.columns(2)
            
            with col1:
                if hasattr(st.session_state, 'analysis_stdout') and st.session_state.analysis_stdout:
                    with st.expander("📋 Ver Log Completo de Execução", expanded=False):
                        st.code(st.session_state.analysis_stdout, language="text")
            
            with col2:
                if hasattr(st.session_state, 'analysis_stderr') and st.session_state.analysis_stderr:
                    with st.expander("⚠️ Ver Avisos e Alertas", expanded=False):
                        st.code(st.session_state.analysis_stderr, language="text")
    
    elif tracker.error_message:
        # Indicadores de erro aprimorados
        progress_bar.progress(0.0)
        
        # Status de erro com estilo especial
        status_text.markdown("""
        <div style="
            background: linear-gradient(90deg, #f8d7da 0%, #f5c6cb 100%);
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #dc3545;
            text-align: center;
        ">
            <strong>❌ Erro na Execução</strong>
        </div>
        """, unsafe_allow_html=True)
        
        percent_text.markdown("**🔴 Erro**")
        step_indicator.markdown("**❌ Interrompido**")
        
        # Tempo até o erro
        error_time = time.time() - start_time
        error_minutes = int(error_time // 60)
        error_seconds = int(error_time % 60)
        elapsed_time.markdown(f"**⏱️ Tempo até Erro:** {error_minutes:02d}:{error_seconds:02d}")
        estimated_time.markdown("**❌ Interrompido**")
        
        # Card de erro personalizado
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <h3 style="margin: 0; color: white;">❌ Erro Durante a Análise</h3>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">A análise foi interrompida devido a um erro. Verifique os detalhes abaixo.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Detalhes do erro
        with st.expander("🔍 Detalhes do Erro", expanded=True):
            st.code(tracker.error_message, language="text")
            
            # Sugestões de solução
            st.markdown("""
            **💡 Possíveis Soluções:**
            - Verifique se todos os arquivos de entrada estão corretos
            - Confirme se as dependências estão instaladas
            - Verifique se há espaço suficiente em disco
            - Tente executar novamente com configurações diferentes
            """)
    
    # Limpar arquivos temporários
    cleanup_temp_files(config)

def cleanup_temp_files(config):
    """Remove arquivos temporários"""
    try:
        if config['files']:
            for file in config['files']:
                if os.path.exists(file) and file.startswith('temp_'):
                    os.remove(file)
        
        if config['csv_file'] and os.path.exists(config['csv_file']) and config['csv_file'].startswith('temp_'):
            os.remove(config['csv_file'])
    except Exception as e:
        st.warning(f"Aviso: Não foi possível remover alguns arquivos temporários: {e}")

def show_visualization_tab():
    st.markdown('<h2 class="sub-header">Visualização dos Resultados</h2>', unsafe_allow_html=True)
    
    # Procurar pastas de resultados
    results_folders = find_results_folders()
    
    if not results_folders:
        st.info("📊 Nenhum resultado encontrado. Execute uma análise primeiro.")
        return
    
    # Seletor de pasta de resultados
    selected_folder = st.selectbox(
        "Selecione uma pasta de resultados:",
        results_folders,
        format_func=lambda x: os.path.basename(x)
    )
    
    if selected_folder:
        display_results(selected_folder)

def find_results_folders():
    """Encontra pastas de resultados"""
    results_folders = []
    
    # Usar o diretório onde o script está sendo executado
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Procurar pastas que começam com "Results_"
        for item in os.listdir(script_dir):
            item_path = os.path.join(script_dir, item)
            if os.path.isdir(item_path) and item.startswith("Results_"):
                results_folders.append(item_path)
        
        # Procurar na pasta results se existir
        results_dir = os.path.join(script_dir, "results")
        if os.path.exists(results_dir) and os.path.isdir(results_dir):
            for item in os.listdir(results_dir):
                item_path = os.path.join(results_dir, item)
                if os.path.isdir(item_path):
                    results_folders.append(item_path)
    except Exception as e:
        # Em caso de erro, retornar lista vazia
        print(f"Erro ao procurar pastas de resultados: {e}")
        return []
    
    return sorted(results_folders, key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)

def display_results(folder_path):
    """Exibe os resultados de uma pasta"""
    st.markdown(f'<h3 class="sub-header">Resultados: {os.path.basename(folder_path)}</h3>', unsafe_allow_html=True)
    
    # Listar arquivos na pasta
    files = os.listdir(folder_path)
    
    # Separar por tipo
    images = [f for f in files if f.lower().endswith(('.png', '.pdf', '.jpg', '.jpeg'))]
    csvs = [f for f in files if f.lower().endswith('.csv')]
    
    # Tabs para diferentes tipos de conteúdo (removida aba "Arquivos")
    tab1, tab2, tab3 = st.tabs(["📊 Gráficos", "📋 Tabelas", "ℹ️ Informações"])
    
    with tab1:
        display_images(folder_path, images)
    
    with tab2:
        display_tables(folder_path, csvs)
    
    with tab3:
        display_folder_info(folder_path)

def display_images(folder_path, images):
    """Exibe imagens/gráficos já gerados"""
    if not images:
        st.info("Nenhum gráfico encontrado nesta pasta.")
        return
    
    st.write(f"**{len(images)} gráfico(s) encontrado(s):**")
    
    # Opções de visualização (removida "Análise Interativa")
    view_mode = st.radio(
        "Modo de visualização:",
        ["🖼️ Galeria", "🔍 Individual"],
        horizontal=True
    )
    
    if view_mode == "🖼️ Galeria":
        display_image_gallery(folder_path, images)
    elif view_mode == "🔍 Individual":
        display_individual_images(folder_path, images)

def display_image_gallery(folder_path, images):
    """Exibe galeria de imagens"""
    cols = st.columns(2)
    
    for i, image_file in enumerate(images):
        col = cols[i % 2]
        
        with col:
            image_path = os.path.join(folder_path, image_file)
            
            with st.container():
                st.markdown(f"**{image_file}**")
                
                try:
                    if image_file.lower().endswith('.pdf'):
                        # Renderizar PDF usando iframe com base64
                        with open(image_path, "rb") as file:
                            base64_pdf = base64.b64encode(file.read()).decode('utf-8')
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                    else:
                        image = Image.open(image_path)
                        st.image(image, use_container_width=True)
                        
                        # Informações da imagem
                        st.caption(f"Dimensões: {image.size[0]}x{image.size[1]} pixels")
                
                except Exception as e:
                    st.error(f"Erro ao carregar {image_file}: {e}")
                
                st.divider()

def display_individual_images(folder_path, images):
    """Exibe imagens individualmente com controles"""
    selected_image = st.selectbox(
        "Selecione uma imagem para visualizar:",
        images,
        format_func=lambda x: x
    )
    
    if selected_image:
        image_path = os.path.join(folder_path, selected_image)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            try:
                if selected_image.lower().endswith('.pdf'):
                    # Renderizar PDF usando iframe com base64
                    with open(image_path, "rb") as file:
                        base64_pdf = base64.b64encode(file.read()).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                else:
                    image = Image.open(image_path)
                    
                    # Controles de zoom e ajuste
                    zoom_level = st.slider("Nível de zoom:", 0.1, 3.0, 1.0, 0.1)
                    
                    # Redimensionar imagem
                    new_size = (int(image.size[0] * zoom_level), int(image.size[1] * zoom_level))
                    resized_image = image.resize(new_size, Image.Resampling.LANCZOS)
                    
                    st.image(resized_image, use_container_width=True)
            
            except Exception as e:
                st.error(f"Erro ao carregar {selected_image}: {e}")
        
        with col2:
            st.markdown("**Informações do Arquivo:**")
            
            try:
                file_size = os.path.getsize(image_path)
                creation_time = datetime.fromtimestamp(os.path.getctime(image_path))
                
                st.write(f"**Nome:** {selected_image}")
                st.write(f"**Tamanho:** {file_size:,} bytes")
                st.write(f"**Criado:** {creation_time.strftime('%d/%m/%Y %H:%M')}")
                
                if not selected_image.lower().endswith('.pdf'):
                    image = Image.open(image_path)
                    st.write(f"**Dimensões:** {image.size[0]}x{image.size[1]}")
                    st.write(f"**Modo:** {image.mode}")
                
                # Informações do arquivo (sem botão de download)
            
            except Exception as e:
                st.error(f"Erro ao obter informações: {e}")



def display_tables(folder_path, csvs):
    """Exibe tabelas CSV com análise avançada"""
    if not csvs:
        st.info("Nenhuma tabela encontrada nesta pasta.")
        return
    
    st.write(f"**{len(csvs)} tabela(s) encontrada(s):**")
    
    # Modo de visualização
    table_view_mode = st.radio(
        "Modo de visualização das tabelas:",
        ["📋 Visualização Simples", "📊 Análise Avançada", "🔍 Exploração Interativa"],
        horizontal=True
    )
    
    for csv_file in csvs:
        csv_path = os.path.join(folder_path, csv_file)
        
        with st.expander(f"📋 {csv_file}", expanded=True):
            try:
                df = load_csv_smart(csv_path)
                
                if df is not None and not df.empty:
                    if table_view_mode == "📋 Visualização Simples":
                        display_simple_table(df, csv_file, csv_path)
                    elif table_view_mode == "📊 Análise Avançada":
                        display_advanced_analysis(df, csv_file, csv_path)
                    elif table_view_mode == "🔍 Exploração Interativa":
                        display_interactive_table(df, csv_file, csv_path)
                else:
                    st.error("Não foi possível ler o arquivo CSV")
            
            except Exception as e:
                st.error(f"Erro ao carregar {csv_file}: {e}")

def load_csv_smart(csv_path):
    """Carrega CSV com detecção inteligente de separador"""
    separators = [',', ';', '\t', '|']
    encodings = ['utf-8', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(csv_path, sep=sep, encoding=encoding)
                if len(df.columns) > 1 and len(df) > 0:
                    return df
            except:
                continue
    
    # Fallback: tentar com parâmetros padrão
    try:
        return pd.read_csv(csv_path)
    except:
        return None

def display_simple_table(df, csv_file, csv_path):
    """Visualização simples da tabela"""
    st.dataframe(df, use_container_width=True, height=400)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Linhas", df.shape[0])
    with col2:
        st.metric("Colunas", df.shape[1])
    with col3:
        file_size = os.path.getsize(csv_path)
        st.metric("Tamanho", f"{file_size:,} bytes")
    
    # Informações da tabela (sem botão de download)

def display_advanced_analysis(df, csv_file, csv_path):
    """Análise avançada da tabela"""
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dados", "📈 Estatísticas", "🔍 Qualidade", "📋 Resumo"])
    
    with tab1:
        # Filtros
        st.markdown("**Filtros de Dados:**")
        
        # Filtro por colunas
        if len(df.columns) > 5:
            selected_columns = st.multiselect(
                "Selecionar colunas para exibir:",
                df.columns.tolist(),
                default=df.columns.tolist()[:5]
            )
            if selected_columns:
                df_filtered = df[selected_columns]
            else:
                df_filtered = df
        else:
            df_filtered = df
        
        # Filtro por linhas
        max_possible_rows = min(1000, len(df))
        default_rows = min(100, len(df))
        # Garantir que min_value < max_value
        if max_possible_rows > 10:
            max_rows = st.slider("Número máximo de linhas:", 10, max_possible_rows, default_rows, key=f"slider_rows_{csv_file}")
        else:
            max_rows = len(df)
            st.info(f"Exibindo todas as {len(df)} linhas disponíveis.")
        df_display = df_filtered.head(max_rows)
        
        st.dataframe(df_display, use_container_width=True, height=400)
        
        if len(df) > max_rows:
            st.info(f"Mostrando {max_rows} de {len(df)} linhas")
    
    with tab2:
        st.markdown("**Estatísticas Descritivas:**")
        
        # Separar colunas numéricas e categóricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if numeric_cols:
            st.markdown("**Colunas Numéricas:**")
            st.dataframe(df[numeric_cols].describe(), use_container_width=True)
            
            # Correlação
            if len(numeric_cols) > 1:
                st.markdown("**Matriz de Correlação:**")
                corr_matrix = df[numeric_cols].corr()
                
                fig = px.imshow(
                    corr_matrix,
                    text_auto=True,
                    aspect="auto",
                    title="Matriz de Correlação",
                    color_continuous_scale="RdBu_r"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Gráficos de colunas categóricas removidos - mantendo apenas matriz de correlação
    
    with tab3:
        st.markdown("**Qualidade dos Dados:**")
        
        # Valores ausentes
        missing_data = df.isnull().sum()
        missing_percent = (missing_data / len(df)) * 100
        
        quality_df = pd.DataFrame({
            'Coluna': df.columns,
            'Valores Ausentes': missing_data.values,
            'Percentual (%)': missing_percent.values,
            'Tipo de Dados': df.dtypes.astype(str).values
        })
        
        st.dataframe(quality_df, use_container_width=True)
        
        # Gráfico de valores ausentes removido - mantendo apenas matriz de correlação
        if missing_data.sum() > 0:
            st.info(f"Total de valores ausentes: {missing_data.sum()}")
        else:
            st.success("✅ Nenhum valor ausente encontrado!")
    
    with tab4:
        st.markdown("**Resumo Geral:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total de Linhas", f"{len(df):,}")
            st.metric("Total de Colunas", len(df.columns))
            st.metric("Colunas Numéricas", len(numeric_cols))
            st.metric("Colunas Categóricas", len(categorical_cols))
        
        with col2:
            memory_usage = df.memory_usage(deep=True).sum()
            st.metric("Uso de Memória", f"{memory_usage:,} bytes")
            st.metric("Valores Únicos", df.nunique().sum())
            st.metric("Valores Ausentes", f"{df.isnull().sum().sum():,}")
            st.metric("Taxa de Completude", f"{((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100):.1f}%")
        
        # Análise completa disponível (sem botão de download)

def display_interactive_table(df, csv_file, csv_path):
    """Exploração interativa da tabela"""
    st.markdown("**Exploração Interativa de Dados:**")
    
    # Tabela com filtros avançados
    st.markdown("**Filtros Avançados:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Filtro por texto
        if len(df.select_dtypes(include=['object']).columns) > 0:
            text_column = st.selectbox(
                "Filtrar por coluna de texto:",
                ['Nenhum'] + df.select_dtypes(include=['object']).columns.tolist(),
                key=f"text_column_{csv_file}"
            )
            
            if text_column != 'Nenhum':
                text_filter = st.text_input(f"Filtrar {text_column} (contém):", key=f"text_filter_{text_column}_{csv_file}")
                if text_filter:
                    df = df[df[text_column].astype(str).str.contains(text_filter, case=False, na=False)]
    
    with col2:
        # Filtro numérico
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            numeric_column = st.selectbox(
                "Filtrar por coluna numérica:",
                ['Nenhum'] + numeric_cols,
                key=f"numeric_column_{csv_file}"
            )
            
            if numeric_column != 'Nenhum':
                min_val = float(df[numeric_column].min())
                max_val = float(df[numeric_column].max())
                
                # Garantir que min_val < max_val para o slider
                if min_val < max_val:
                    range_filter = st.slider(
                        f"Faixa de valores para {numeric_column}:",
                        min_val, max_val, (min_val, max_val),
                        key=f"range_filter_{numeric_column}_{csv_file}"
                    )
                else:
                    st.info(f"Coluna {numeric_column} tem valores constantes: {min_val}")
                    range_filter = (min_val, max_val)
                
                df = df[(df[numeric_column] >= range_filter[0]) & (df[numeric_column] <= range_filter[1])]
    
    # Exibir dados filtrados
    st.markdown(f"**Dados Filtrados ({len(df)} linhas):**")
    st.dataframe(df, use_container_width=True, height=400)
    
    # Dados filtrados exibidos (sem botão de download)





def display_folder_info(folder_path):
    """Exibe informações sobre a pasta"""
    try:
        # Informações básicas
        folder_size = sum(os.path.getsize(os.path.join(folder_path, f)) 
                         for f in os.listdir(folder_path) 
                         if os.path.isfile(os.path.join(folder_path, f)))
        
        file_count = len([f for f in os.listdir(folder_path) 
                         if os.path.isfile(os.path.join(folder_path, f))])
        
        creation_time = datetime.fromtimestamp(os.path.getctime(folder_path))
        modification_time = datetime.fromtimestamp(os.path.getmtime(folder_path))
        
        st.write("**Informações da pasta:**")
        st.write(f"- **Caminho:** {folder_path}")
        st.write(f"- **Número de arquivos:** {file_count}")
        st.write(f"- **Tamanho total:** {folder_size:,} bytes")
        st.write(f"- **Criado em:** {creation_time.strftime('%d/%m/%Y %H:%M:%S')}")
        st.write(f"- **Modificado em:** {modification_time.strftime('%d/%m/%Y %H:%M:%S')}")
        
    except Exception as e:
        st.error(f"Erro ao obter informações da pasta: {e}")

def show_help_tab():
    st.markdown('<h2 class="sub-header">Ajuda e Documentação</h2>', unsafe_allow_html=True)
    
    # Guia de uso
    with st.expander("📖 Guia de Uso", expanded=True):
        st.markdown("""
        ### Como usar o PanViTa Web
        
        1. **Configuração**: Na aba "Configuração", selecione:
           - Bases de dados para análise
           - Arquivos de entrada (GenBank ou CSV do NCBI)
           - Parâmetros de análise (identidade, cobertura, etc.)
           - Opções adicionais
        
        2. **Execução**: Na aba "Execução":
           - Revise a configuração
           - Execute a análise
           - Acompanhe o progresso
        
        3. **Visualização**: Na aba "Visualização":
           - Explore os resultados gerados
           - Visualize gráficos e tabelas
           - Faça download dos arquivos
        """)
    
    # Bases de dados
    with st.expander("🗄️ Bases de Dados"):
        st.markdown("""
        ### Bases de Dados Disponíveis
        
        - **BacMet**: Antibacterial Biocide and Metal Resistance Genes Database
        - **CARD**: Comprehensive Antibiotic Resistance Database  
        - **MEGARes**: MEGARes Antimicrobial Resistance Database
        - **VFDB**: Virulence Factor Database
        """)
    
    # Parâmetros
    with st.expander("⚙️ Parâmetros"):
        st.markdown("""
        ### Parâmetros Principais
        
        - **Identidade mínima**: Percentual mínimo de identidade para considerar uma correspondência (padrão: 70%)
        - **Cobertura mínima**: Percentual mínimo de cobertura para considerar uma correspondência (padrão: 70%)
        - **Alinhador**: Ferramenta para alinhamento (DIAMOND, BLAST, ou ambos)
        - **Formato de saída**: PDF (padrão) ou PNG para as figuras
        """)
    
    # Formatos de arquivo
    with st.expander("📁 Formatos de Arquivo"):
        st.markdown("""
        ### Arquivos de Entrada Aceitos
        
        - **GenBank**: .gbk, .gbf, .gbff
        - **CSV**: Tabela de genomas do NCBI
        
        ### Arquivos de Saída Gerados
        
        - **Gráficos**: PDF ou PNG
        - **Tabelas**: CSV com resultados
        - **Matrizes**: Presença/ausência de genes
        """)
    
    # Citação
    with st.expander("📚 Citação"):
        st.markdown("""
        ### Como Citar
        
        Se você usar o PanViTa em sua pesquisa, por favor cite:
        
        **PanViTa**: https://doi.org/10.3389/fbinf.2023.1070406 (2023)
        
        Não se esqueça de citar também as bases de dados utilizadas:
        - **BacMet**: https://doi.org/10.1093/nar/gkt1252 (2014)
        - **CARD**: https://doi.org/10.1093/nar/gkz935 (2020)
        - **MEGARes**: https://doi.org/10.1093/nar/gkac1047 (2022)
        - **VFDB**: https://doi.org/10.1093/nar/gky1080 (2019)
        """)
    
    # Contato
    with st.expander("📞 Contato"):
        st.markdown("""
        ### Equipe de Desenvolvimento
        
        - **Diego Neres**: dlnrodrigues@ufmg.br
        - **Victor S Caricatte De Araújo**: victorsc@ufmg.br
        - **Vinicius Oliveira**: vinicius.oliveira.1444802@sga.pucminas.br
        
        **Instituição**: Universidade Federal de Minas Gerais
        """)

# Funções auxiliares
def check_panvita_availability():
    """Verifica se o PanViTa está disponível"""
    try:
        from panvita import PanViTa
        return True
    except ImportError:
        return False

def check_dependencies():
    """Verifica dependências básicas"""
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        return True
    except ImportError:
        return False

def count_results_folders():
    """Conta o número de pastas de resultados"""
    return len(find_results_folders())

def get_detailed_dependencies():
    """Retorna informações detalhadas sobre dependências"""
    dependencies = {
        'pandas': {'name': 'Pandas', 'status': 'NOK', 'description': 'Análise de dados'},
        'matplotlib': {'name': 'Matplotlib', 'status': 'NOK', 'description': 'Visualização de gráficos'},
        'seaborn': {'name': 'Seaborn', 'status': 'NOK', 'description': 'Visualização estatística'},
        'numpy': {'name': 'NumPy', 'status': 'NOK', 'description': 'Computação numérica'},
        'plotly': {'name': 'Plotly', 'status': 'NOK', 'description': 'Gráficos interativos'},
        'PIL': {'name': 'Pillow', 'status': 'NOK', 'description': 'Processamento de imagens'},
        'wget': {'name': 'Wget', 'status': 'NOK', 'description': 'Download de arquivos'}
    }
    
    for module, info in dependencies.items():
        try:
            if module == 'PIL':
                from PIL import Image
            else:
                __import__(module)
            info['status'] = 'OK'
        except ImportError:
            info['status'] = 'NOK'
    
    return dependencies

def get_results_with_status():
    """Retorna resultados disponíveis com status detalhado"""
    results_folders = find_results_folders()
    results_info = []
    
    for folder in results_folders:
        folder_name = os.path.basename(folder)
        try:
            files = os.listdir(folder)
            file_count = len([f for f in files if os.path.isfile(os.path.join(folder, f))])
            
            # Verificar tipos de arquivos
            has_images = any(f.lower().endswith(('.png', '.pdf', '.jpg', '.jpeg')) for f in files)
            has_csvs = any(f.lower().endswith('.csv') for f in files)
            
            # Determinar status
            if has_images and has_csvs:
                status = '✅ Completo'
            elif has_images or has_csvs:
                status = '⚠️ Parcial'
            else:
                status = '❌ Vazio'
            
            modification_time = datetime.fromtimestamp(os.path.getmtime(folder))
            
            results_info.append({
                'name': folder_name,
                'path': folder,
                'status': status,
                'files': file_count,
                'modified': modification_time.strftime('%d/%m/%Y %H:%M')
            })
        except Exception as e:
            results_info.append({
                'name': folder_name,
                'path': folder,
                'status': '❌ Erro',
                'files': 0,
                'modified': 'N/A'
            })
    
    return results_info

def delete_analysis_folders():
    """Exclui completamente as pastas 'results' e 'Positions'"""
    # Usar o diretório onde o script está sendo executado
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folders_to_delete = []
    
    # Verificar pasta 'results'
    results_path = os.path.join(script_dir, 'Results_')
    if os.path.exists(results_path) and os.path.isdir(results_path):
        folders_to_delete.append(results_path)
    
    # Verificar pasta 'Positions'
    positions_path = os.path.join(script_dir, 'Positions')
    if os.path.exists(positions_path) and os.path.isdir(positions_path):
        folders_to_delete.append(positions_path)
    
    # Verificar pastas que começam com 'Results_'
    try:
        for item in os.listdir(script_dir):
            item_path = os.path.join(script_dir, item)
            if os.path.isdir(item_path) and item.startswith('Results_'):
                folders_to_delete.append(item_path)
    except PermissionError:
        return False, "Erro de permissão ao acessar o diretório."
    except Exception as e:
        return False, f"Erro ao listar diretório: {str(e)}"
    
    if not folders_to_delete:
        return False, "Nenhuma pasta de análise encontrada para exclusão."
    
    try:
        import shutil
        deleted_folders = []
        errors = []
        
        for folder_path in folders_to_delete:
            try:
                if os.path.exists(folder_path) and os.path.isdir(folder_path):
                    # Tentar alterar permissões se necessário (Windows)
                    if os.name == 'nt':  # Windows
                        import stat
                        def handle_remove_readonly(func, path, exc):
                            if os.path.exists(path):
                                os.chmod(path, stat.S_IWRITE)
                                func(path)
                        shutil.rmtree(folder_path, onerror=handle_remove_readonly)
                    else:
                        shutil.rmtree(folder_path)
                    deleted_folders.append(os.path.basename(folder_path))
            except PermissionError:
                errors.append(f"Sem permissão para excluir: {os.path.basename(folder_path)}")
            except Exception as e:
                errors.append(f"Erro ao excluir {os.path.basename(folder_path)}: {str(e)}")
        
        if deleted_folders and not errors:
            return True, f"Pastas excluídas com sucesso: {', '.join(deleted_folders)}"
        elif deleted_folders and errors:
            return True, f"Parcialmente concluído. Excluídas: {', '.join(deleted_folders)}. Erros: {'; '.join(errors)}"
        else:
            return False, f"Falha na exclusão. Erros: {'; '.join(errors) if errors else 'Nenhuma pasta foi encontrada.'}"
            
    except Exception as e:
        return False, f"Erro geral ao excluir pastas: {str(e)}"

if __name__ == "__main__":
    main()