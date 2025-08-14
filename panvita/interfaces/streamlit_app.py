"""
Interface Streamlit para PanViTa
Interface web amigável para análise pan-genômica de virulência e resistência
"""

import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
import tempfile
from typing import Dict, List, Any
import io
import zipfile
from datetime import datetime

# Adicionar o diretório parent ao path para importar o core
sys.path.append(str(Path(__file__).parent.parent))

try:
    from core.engine import PanViTaEngine
    from core.processor import GBKProcessor
    from core.downloader import NCBIDownloader
    from core.file_handler import FileHandler
except ImportError:
    st.error("Erro ao importar o engine do PanViTa. Verifique a instalação.")
    st.stop()


class PanViTaStreamlitApp:
    """Aplicação Streamlit para PanViTa"""
    
    def __init__(self):
        self.engine = PanViTaEngine()
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Inicializa o estado da sessão"""
        if 'analysis_complete' not in st.session_state:
            st.session_state.analysis_complete = False
        if 'results' not in st.session_state:
            st.session_state.results = {}
    
    def run(self):
        """Executa a aplicação Streamlit"""
        st.set_page_config(
            page_title="PanViTa - Análise Pan-genômica",
            page_icon="🧬",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        self.render_header()
        self.render_sidebar()
        self.render_main_content()
    
    def render_header(self):
        """Renderiza o cabeçalho da aplicação"""
        st.title("🧬 PanViTa - Pan Virulence and Resistance Analysis")
        st.markdown("### Análise Pan-genômica de Virulência e Resistência")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("📊 **Análise Comparativa**\nCompare genes de virulência e resistência entre cepas")
        with col2:
            st.info("🔍 **Múltiplas Databases**\nBacMet, CARD, VFDB, MEGARes")
        with col3:
            st.info("📈 **Visualizações**\nHeatmaps, gráficos e matrizes interativas")
    
    def render_sidebar(self):
        """Renderiza a barra lateral com configurações"""
        st.sidebar.header("⚙️ Configurações")
        
        # Sistema sempre pronto (engine inicializa automaticamente)
        st.sidebar.success("✅ Sistema pronto")
        
        # Configurações de análise
        st.sidebar.subheader("🎯 Parâmetros de Análise")
        
        # Databases
        databases = st.sidebar.multiselect(
            "Selecione as databases:",
            ["bacmet", "card", "vfdb", "megares"],
            default=["card", "vfdb"],
            help="Escolha quais databases usar para análise",
            key="databases_selector"
        )
        
        # Thresholds
        identity_threshold = st.sidebar.slider(
            "Threshold de Identidade (%)",
            min_value=0.0,
            max_value=100.0,
            value=70.0,
            step=1.0,
            help="Porcentagem mínima de identidade para considerar um hit",
            key="identity_threshold_slider"
        )
        
        coverage_threshold = st.sidebar.slider(
            "Threshold de Cobertura (%)",
            min_value=0.0,
            max_value=100.0,
            value=70.0,
            step=1.0,
            help="Porcentagem mínima de cobertura da query para considerar um hit",
            key="coverage_threshold_slider"
        )
        
        # Seleção de alinhador
        st.sidebar.subheader("🔧 Alinhador")
        aligner = st.sidebar.selectbox(
            "Escolha o alinhador:",
            ["diamond", "blast", "both"],
            index=0,  # Diamond como padrão
            help="Escolha qual ferramenta de alinhamento usar:\n"
                 "• DIAMOND: Mais rápido, ideal para análises grandes\n"
                 "• BLAST: Mais sensível, análise mais detalhada\n"
                 "• Both: Executa ambos para comparação",
            key="aligner_selector"
        )
        
        return {
            'databases': databases,
            'identity_threshold': identity_threshold,
            'coverage_threshold': coverage_threshold,
            'aligner': aligner
        }
    
    def render_main_content(self):
        """Renderiza o conteúdo principal"""        
        # Tabs principais
        tab1, tab2, tab3, tab4 = st.tabs([
            "📁 Upload de Dados", 
            "🔬 Análise", 
            "📊 Resultados", 
            "📋 Logs"
        ])
        
        with tab1:
            self.render_upload_tab()
        
        with tab2:
            self.render_analysis_tab()
        
        with tab3:
            self.render_results_tab()
        
        with tab4:
            self.render_logs_tab()
    
    def render_upload_tab(self):
        """Tab para upload de arquivos"""
        st.header("📁 Upload de Dados")
        
        upload_method = st.radio(
            "Método de entrada:",
            ["Upload de arquivos GenBank (.gbff/.gbk)", "Download automático do NCBI", "Upload de proteínas (.faa)"],
            help="Escolha como fornecer os dados para análise"
        )
        
        if upload_method == "Upload de arquivos GenBank (.gbff/.gbk)":
            self.render_genbank_upload()
        
        elif upload_method == "Download automático do NCBI":
            self.render_ncbi_download()
        
        elif upload_method == "Upload de proteínas (.faa)":
            self.render_protein_upload()
    
    def render_genbank_upload(self):
        """Upload de arquivos GenBank"""
        st.subheader("Upload de arquivos GenBank")
        
        uploaded_files = st.file_uploader(
            "Selecione arquivos GenBank:",
            type=['gbff', 'gbk', 'gb'],
            accept_multiple_files=True,
            help="Faça upload dos arquivos GenBank das cepas a serem analisadas"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)")
            
            # Mostrar preview dos arquivos
            with st.expander("📋 Arquivos carregados"):
                for file in uploaded_files:
                    st.write(f"• {file.name} ({file.size} bytes)")
            
            # Salvar arquivos temporariamente
            if st.button("💾 Processar arquivos GenBank"):
                with st.spinner("Processando arquivos..."):
                    self.process_genbank_files(uploaded_files)
    
    def render_ncbi_download(self):
        """Download automático do NCBI"""
        st.subheader("Download automático do NCBI")
        
        # Upload de arquivo CSV ou input manual
        input_method = st.radio(
            "Como fornecer os IDs das cepas:",
            ["Upload de arquivo CSV", "Input manual"]
        )
        
        if input_method == "Upload de arquivo CSV":
            st.markdown("**📋 Formato do arquivo CSV:**")
            
            # Mostrar exemplo de CSV
            with st.expander("💡 Ver exemplo de formato CSV"):
                exemplo_csv = pd.DataFrame({
                    '#Organism Name': ['Escherichia coli', 'Salmonella enterica'],
                    'Strain': ['K-12', 'LT2'],
                    'GenBank FTP': [
                        'https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/005/825/GCF_000005825.2_ASM582v2',
                        'https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/006/945/GCF_000006945.2_ASM694v2'
                    ],
                    'RefSeq FTP': [
                        'https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/005/825/GCF_000005825.2_ASM582v2',
                        ''
                    ]
                })
                st.dataframe(exemplo_csv)
                
                # Botão para baixar CSV de exemplo
                csv_exemplo = exemplo_csv.to_csv(index=False)
                st.download_button(
                    "⬇️ Baixar CSV de exemplo",
                    csv_exemplo,
                    "exemplo_cepas.csv",
                    "text/csv"
                )
            
            csv_file = st.file_uploader(
                "Upload arquivo CSV com dados das cepas:",
                type=['csv'],
                help="CSV deve conter colunas: '#Organism Name', 'Strain', 'GenBank FTP' (obrigatórias) e opcionalmente 'RefSeq FTP'"
            )
            
            if csv_file:
                df = pd.read_csv(csv_file)
                st.dataframe(df)
                
                if st.button("🌐 Baixar do NCBI"):
                    with st.spinner("Baixando arquivos do NCBI..."):
                        self.process_ncbi_download(df)
        
        else:
            st.markdown("**Adicione cepas manualmente:**")
            
            # Formulário para adicionar cepas
            with st.form("add_strain_form"):
                col1, col2 = st.columns(2)
                with col1:
                    organism_name = st.text_input("Nome do organismo:", placeholder="Escherichia coli")
                    genbank_ftp = st.text_input("FTP GenBank:", placeholder="https://ftp.ncbi.nlm.nih.gov/...")
                with col2:
                    refseq_ftp = st.text_input("FTP RefSeq (opcional):", placeholder="https://ftp.ncbi.nlm.nih.gov/...")
                    strain_name = st.text_input("Nome da cepa:", placeholder="K-12")
                
                submit = st.form_submit_button("➕ Adicionar cepa")
                
                if submit and organism_name and strain_name:
                    # Validar se pelo menos um FTP foi fornecido
                    if not genbank_ftp and not refseq_ftp:
                        st.error("❌ Forneça pelo menos um FTP (GenBank ou RefSeq)")
                    else:
                        # Adicionar à sessão
                        if 'manual_strains' not in st.session_state:
                            st.session_state.manual_strains = []
                        
                        st.session_state.manual_strains.append({
                            '#Organism Name': organism_name,
                            'GenBank FTP': genbank_ftp,
                            'RefSeq FTP': refseq_ftp,
                            'Strain': strain_name
                        })
                        st.success(f"✅ Cepa {strain_name} adicionada!")
            
            # Mostrar cepas adicionadas
            if 'manual_strains' in st.session_state and st.session_state.manual_strains:
                st.subheader("Cepas adicionadas:")
                df_manual = pd.DataFrame(st.session_state.manual_strains)
                st.dataframe(df_manual)
                
                if st.button("🌐 Baixar cepas do NCBI"):
                    with st.spinner("Baixando arquivos do NCBI..."):
                        self.process_ncbi_download(df_manual)
    
    def render_protein_upload(self):
        """Upload direto de arquivos de proteínas"""
        st.subheader("Upload de arquivos de proteínas (.faa)")
        
        uploaded_proteins = st.file_uploader(
            "Selecione arquivos de proteínas:",
            type=['faa', 'fa', 'fasta'],
            accept_multiple_files=True,
            help="Faça upload dos arquivos FASTA com sequências de proteínas"
        )
        
        if uploaded_proteins:
            st.success(f"✅ {len(uploaded_proteins)} arquivo(s) de proteínas carregado(s)")
            
            with st.expander("📋 Arquivos de proteínas"):
                for file in uploaded_proteins:
                    st.write(f"• {file.name} ({file.size} bytes)")
            
            if st.button("💾 Processar proteínas"):
                with st.spinner("Processando arquivos de proteínas..."):
                    self.process_protein_files(uploaded_proteins)
    
    def render_analysis_tab(self):
        """Tab para executar análise"""
        st.header("🔬 Análise")
        
        if 'processed_files' not in st.session_state:
            st.warning("⚠️ Primeiro faça upload dos dados na aba 'Upload de Dados'")
            return
        
        # Obter configurações da sidebar (já renderizada no main)
        config = {
            'databases': st.session_state.get('databases_selector', ['card', 'vfdb']),
            'identity_threshold': st.session_state.get('identity_threshold_slider', 70.0),
            'coverage_threshold': st.session_state.get('coverage_threshold_slider', 70.0),
            'aligner': st.session_state.get('aligner_selector', 'diamond')
        }
        
        st.subheader("Arquivos processados:")
        input_type = st.session_state.get('input_type', 'protein')
        
        if input_type == 'genbank' and 'genbank_files' in st.session_state:
            for name, path in st.session_state.genbank_files.items():
                st.write(f"• {name}: {os.path.basename(path)} (GenBank)")
        elif input_type == 'protein' and 'protein_files' in st.session_state:
            for name, path in st.session_state.protein_files.items():
                st.write(f"• {name}: {os.path.basename(path)} (Proteína)")
        else:
            st.warning("⚠️ Nenhum arquivo processado encontrado")
        
        st.subheader("Configurações da análise:")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Databases", len(config['databases']))
        with col2:
            st.metric("Identidade (%)", config['identity_threshold'])
        with col3:
            st.metric("Cobertura (%)", config['coverage_threshold'])
        with col4:
            st.metric("Alinhador", config['aligner'].upper())
        
        # Mostrar informações sobre os arquivos processados
        with st.expander("🔍 Informações dos arquivos processados"):
            input_type = st.session_state.get('input_type', 'protein')
            
            if input_type == 'genbank' and 'genbank_files' in st.session_state:
                for name, path in st.session_state.genbank_files.items():
                    if os.path.exists(path):
                        file_size = os.path.getsize(path)
                        st.success(f"✅ {name}: {file_size} bytes (GenBank)")
                    else:
                        st.error(f"❌ {name}: Arquivo não encontrado - {path}")
            elif input_type == 'protein' and 'protein_files' in st.session_state:
                for name, path in st.session_state.protein_files.items():
                    if os.path.exists(path):
                        try:
                            with open(path, 'r') as f:
                                content = f.read()
                                protein_count = content.count('>')
                            st.success(f"✅ {name}: {protein_count} proteínas")
                        except Exception as e:
                            st.warning(f"⚠️ {name}: Erro ao ler arquivo - {str(e)}")
                    else:
                        st.error(f"❌ {name}: Arquivo não encontrado - {path}")
            else:
                st.warning("⚠️ Nenhum arquivo processado para verificar")
        
        if st.button("🚀 Iniciar Análise", type="primary"):
            if not config['databases']:
                st.error("❌ Selecione pelo menos uma database!")
                return
            
            # Verificar se há arquivos válidos
            input_type = st.session_state.get('input_type', 'protein')
            if input_type == 'genbank' and 'genbank_files' in st.session_state:
                valid_files = sum(1 for path in st.session_state.genbank_files.values() if os.path.exists(path))
            elif input_type == 'protein' and 'protein_files' in st.session_state:
                valid_files = sum(1 for path in st.session_state.protein_files.values() if os.path.exists(path))
            else:
                valid_files = 0
            
            if valid_files == 0:
                st.error("❌ Nenhum arquivo válido encontrado!")
                return
            
            with st.spinner("Executando análise..."):
                self.run_analysis(config)
    
    def render_results_tab(self):
        """Tab para mostrar resultados"""
        st.header("📊 Resultados")
        
        if not st.session_state.analysis_complete:
            st.info("ℹ️ Execute uma análise primeiro para ver os resultados")
            return
        
        results = st.session_state.results
        
        # Resumo geral
        st.subheader("📈 Resumo da Análise")
        col1, col2, col3, col4 = st.columns(4)
        
        total_genes = sum(result.get('gene_count', 0) for result in results.values())
        total_strains = max((result.get('strain_count', 0) for result in results.values()), default=0)
        total_files = sum(len(result.get('files', [])) for result in results.values())
        
        with col1:
            st.metric("Total de Genes", total_genes)
        with col2:
            st.metric("Total de Cepas", total_strains)
        with col3:
            st.metric("Databases Analisadas", len(results))
        with col4:
            st.metric("Arquivos Gerados", total_files)
        
        # Resultados por database
        for db_name, result in results.items():
            st.subheader(f"🗄️ {db_name.upper()}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(f"Genes encontrados ({db_name})", result.get('gene_count', 0))
            with col2:
                st.metric(f"Cepas analisadas ({db_name})", result.get('strain_count', 0))
            
            # Mostrar matriz se disponível
            matrix_file = result.get('matrix_file')
            if matrix_file and os.path.exists(matrix_file):
                with st.expander(f"📋 Matriz de presença/ausência - {db_name}"):
                    try:
                        df = pd.read_csv(matrix_file, sep=';')
                        st.dataframe(df, use_container_width=True)
                        
                        # Download da matriz
                        csv = df.to_csv(sep=';', index=False)
                        st.download_button(
                            f"⬇️ Baixar matriz {db_name}",
                            csv,
                            f"matriz_{db_name}.csv",
                            "text/csv"
                        )
                    except Exception as e:
                        st.error(f"Erro ao carregar matriz: {str(e)}")
            
            # Mostrar heatmap se disponível
            heatmap_file = result.get('heatmap_file')
            if heatmap_file and os.path.exists(heatmap_file):
                with st.expander(f"🔥 Heatmap - {db_name}"):
                    try:
                        st.image(heatmap_file, caption=f"Heatmap {db_name}")
                        
                        # Download do heatmap
                        with open(heatmap_file, "rb") as file:
                            st.download_button(
                                f"⬇️ Baixar heatmap {db_name}",
                                file,
                                f"heatmap_{db_name}.pdf",
                                "application/pdf"
                            )
                    except Exception as e:
                        st.error(f"Erro ao carregar heatmap: {str(e)}")
            
            # Mostrar outros arquivos gerados
            files = result.get('files', [])
            if files:
                with st.expander(f"📁 Outros arquivos gerados - {db_name}"):
                    for file_path in files:
                        if os.path.exists(file_path):
                            file_name = os.path.basename(file_path)
                            file_size = os.path.getsize(file_path)
                            
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.text(f"📄 {file_name} ({file_size} bytes)")
                            with col2:
                                # Botão de download para cada arquivo
                                try:
                                    with open(file_path, "rb") as file:
                                        st.download_button(
                                            "⬇️",
                                            file,
                                            file_name,
                                            key=f"download_{file_name}_{db_name}"
                                        )
                                except Exception:
                                    st.text("❌")
        
        # Seção para download de todos os resultados
        st.subheader("📦 Download Completo")
        if st.button("🗂️ Preparar ZIP com todos os resultados"):
            self.create_results_zip(results)
    
    def render_logs_tab(self):
        """Tab para mostrar logs e erros"""
        st.header("📋 Logs e Erros")
        
        # Informações do sistema
        st.subheader("💻 Informações do Sistema")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Sistema Operacional:** {os.name}")
            st.info(f"**Python:** {sys.version.split()[0]}")
        
        with col2:
            st.info(f"**Diretório de trabalho:** {os.getcwd()}")
            if 'analysis_temp_dir' in st.session_state:
                st.info(f"**Diretório da análise:** {st.session_state.analysis_temp_dir}")
        
        # Logs de erro do engine
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("❌ Erros do Engine")
            if hasattr(self.engine, 'erro') and self.engine.erro:
                for i, error in enumerate(self.engine.erro, 1):
                    st.error(f"{i}. {error}")
            else:
                st.success("✅ Nenhum erro encontrado no engine")
        
        with col2:
            st.subheader("📄 Status dos Arquivos")
            if st.session_state.analysis_complete and 'results' in st.session_state:
                results = st.session_state.results
                for db_name, result in results.items():
                    files = result.get('files', [])
                    if files:
                        st.write(f"**{db_name.upper()}:**")
                        for file_path in files:
                            if os.path.exists(file_path):
                                st.success(f"✅ {os.path.basename(file_path)}")
                            else:
                                st.warning(f"⚠️ {os.path.basename(file_path)} (não encontrado)")
                    else:
                        st.info(f"ℹ️ {db_name}: Nenhum arquivo gerado")
            else:
                st.info("ℹ️ Execute uma análise primeiro")
        
        # Informações de debug
        with st.expander("🔧 Informações de Debug"):
            st.write("**Session State:**")
            debug_info = {
                'processed_files': st.session_state.get('processed_files', False),
                'analysis_complete': st.session_state.get('analysis_complete', False),
                'protein_files_count': len(st.session_state.get('protein_files', {})),
                'results_count': len(st.session_state.get('results', {}))
            }
            st.json(debug_info)
            
            if st.button("🗑️ Limpar Session State"):
                keys_to_clear = ['processed_files', 'analysis_complete', 'protein_files', 'results', 'manual_strains']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("✅ Session state limpo!")
                st.rerun()
    
    def process_genbank_files(self, uploaded_files):
        """Processa arquivos GenBank carregados"""
        try:
            # Usar diretório de trabalho atual
            working_dir = os.getcwd()
            gbk_files = []
            
            # Salvar arquivos GenBank no diretório de trabalho atual
            for uploaded_file in uploaded_files:
                file_path = os.path.join(working_dir, uploaded_file.name)
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                gbk_files.append(file_path)
                st.info(f"📁 Arquivo GenBank salvo: {uploaded_file.name}")
            
            # Para arquivos GenBank, vamos armazenar os caminhos dos arquivos .gbff/.gbk
            # O engine vai processar estes arquivos diretamente
            genbank_files = {}
            for gbk_file in gbk_files:
                base_name = os.path.splitext(os.path.basename(gbk_file))[0]
                genbank_files[base_name] = gbk_file
            
            if genbank_files:
                st.session_state.processed_files = True
                st.session_state.genbank_files = genbank_files  # Armazenar arquivos GenBank
                st.session_state.input_type = 'genbank'  # Marcar tipo de entrada
                st.success(f"✅ {len(genbank_files)} arquivo(s) GenBank processado(s) com sucesso!")
                
                # Mostrar preview dos arquivos GenBank
                with st.expander("📊 Arquivos GenBank carregados"):
                    for name, path in genbank_files.items():
                        st.write(f"• **{name}**: {os.path.basename(path)}")
            else:
                st.error("❌ Não foi possível processar os arquivos GenBank")
            
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivos GenBank: {str(e)}")
    
    def process_ncbi_download(self, df):
        """Processa download do NCBI"""
        try:
            # Verificar se as colunas necessárias existem
            required_columns = ['#Organism Name', 'Strain', 'GenBank FTP']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Colunas obrigatórias ausentes no CSV: {', '.join(missing_columns)}")
                st.info("💡 Certifique-se de que o CSV contém as colunas: '#Organism Name', 'Strain', 'GenBank FTP'")
                return
            
            # Converter DataFrame para dicionário no formato esperado pelo NCBIDownloader
            strain_dict = {}
            valid_strains = []
            
            for idx, row in df.iterrows():
                organism_name = row.get('#Organism Name', '')
                strain = row.get('Strain', f'strain_{idx}')
                genbank_ftp = row.get('GenBank FTP', '')
                refseq_ftp = row.get('RefSeq FTP', '')
                
                # Pular linhas sem FTP
                if not genbank_ftp and not refseq_ftp:
                    st.warning(f"⚠️ Cepa {strain} ignorada: sem FTP GenBank ou RefSeq")
                    continue
                
                strain_dict[idx] = (
                    organism_name,
                    genbank_ftp if genbank_ftp else None,
                    refseq_ftp if refseq_ftp else None,
                    strain
                )
                valid_strains.append(strain)
            
            if not strain_dict:
                st.error("❌ Nenhuma cepa válida encontrada no CSV")
                return
            
            st.info(f"📥 Iniciando download de {len(strain_dict)} cepa(s)...")
            
            # Usar diretório de trabalho atual (como na versão CLI)
            working_dir = os.getcwd()
            
            # Inicializar downloader
            downloader = NCBIDownloader(strain_dict)
            
            # Simular sys.argv para o downloader funcionar
            original_argv = sys.argv.copy()
            sys.argv = ["streamlit_app.py", "-b"]  # -b para GenBank files
            
            # Fazer download dos arquivos GenBank
            with st.spinner("Baixando arquivos GenBank do NCBI..."):
                gbff_files = downloader.get_ncbi_gbf()
            
            # Restaurar sys.argv
            sys.argv = original_argv
            
            if gbff_files:
                # Para arquivos baixados do NCBI, vamos armazenar os arquivos GenBank originais
                genbank_files = {}
                progress_bar = st.progress(0)
                
                st.info("🔄 Processando arquivos baixados...")
                
                for idx, gbff_file in enumerate(gbff_files):
                    if os.path.exists(gbff_file):
                        # Mover arquivo para diretório de trabalho com nome mais limpo
                        base_name = os.path.splitext(os.path.basename(gbff_file))[0]
                        dest_file = os.path.join(working_dir, f"{base_name}.gbff")
                        
                        try:
                            if os.path.abspath(gbff_file) != os.path.abspath(dest_file):
                                import shutil
                                shutil.move(gbff_file, dest_file)
                            
                            genbank_files[base_name] = dest_file
                            st.success(f"✅ {base_name}: Arquivo GenBank processado")
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao processar {os.path.basename(gbff_file)}: {str(e)}")
                            continue
                    
                    # Atualizar barra de progresso
                    progress = (idx + 1) / len(gbff_files)
                    progress_bar.progress(progress)
                
                progress_bar.empty()
                
                if genbank_files:
                    st.session_state.processed_files = True
                    st.session_state.genbank_files = genbank_files  # Armazenar arquivos GenBank
                    st.session_state.input_type = 'genbank'  # Marcar tipo de entrada
                    
                    st.success(f"✅ {len(genbank_files)} cepa(s) processada(s) com sucesso!")
                    
                    # Mostrar resumo
                    with st.expander("📊 Resumo dos downloads"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Cepas baixadas", len(gbff_files))
                            st.metric("Arquivos GenBank", len(genbank_files))
                        with col2:
                            st.write("**Arquivos processados:**")
                            for name in genbank_files.keys():
                                st.write(f"• {name}.gbff")
                    
                    # Listar erros se houver
                    if downloader.erro:
                        st.warning("⚠️ Alguns erros ocorreram durante o download:")
                        for error in downloader.erro:
                            st.text(error)
                else:
                    st.error("❌ Não foi possível processar os arquivos baixados")
            else:
                st.error("❌ Nenhum arquivo foi baixado com sucesso")
                if downloader.erro:
                    st.error("Erros encontrados:")
                    for error in downloader.erro:
                        st.text(error)
        
        except Exception as e:
            st.error(f"❌ Erro no download do NCBI: {str(e)}")
            import traceback
            st.error(f"Detalhes: {traceback.format_exc()}")
    
    def process_protein_files(self, uploaded_proteins):
        """Processa arquivos de proteínas carregados"""
        try:
            # Usar diretório de trabalho atual
            working_dir = os.getcwd()
            protein_files = {}
            
            for uploaded_file in uploaded_proteins:
                # Salvar arquivo no diretório de trabalho atual
                file_path = os.path.join(working_dir, uploaded_file.name)
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                # Nome base sem extensão
                base_name = os.path.splitext(uploaded_file.name)[0]
                protein_files[base_name] = file_path
                st.info(f"📁 Arquivo de proteína salvo: {uploaded_file.name}")
            
            st.session_state.processed_files = True
            st.session_state.protein_files = protein_files
            st.session_state.input_type = 'protein'  # Marcar tipo de entrada
            
            st.success(f"✅ {len(protein_files)} arquivo(s) de proteínas processado(s)")
            
        except Exception as e:
            st.error(f"❌ Erro ao processar proteínas: {str(e)}")
    
    def run_analysis(self, config):
        """Executa a análise completa usando o engine atualizado"""
        try:
            # Salvar o sys.argv original
            original_argv = sys.argv.copy()
            
            # Usar o diretório de trabalho atual (como a versão CLI)
            working_dir = os.getcwd()
            st.info(f"🗂️ Diretório de trabalho: {working_dir}")
            
            # Determinar tipo de entrada e preparar arquivos
            input_type = st.session_state.get('input_type', 'protein')
            
            if input_type == 'genbank':
                # Para arquivos GenBank, passar os arquivos .gbff/.gbk
                working_files = {}
                if 'genbank_files' in st.session_state:
                    for name, file_path in st.session_state.genbank_files.items():
                        if os.path.exists(file_path):
                            working_files[name] = file_path
                            st.write(f"📁 Arquivo GenBank: {name} -> {os.path.basename(file_path)}")
                        else:
                            st.warning(f"⚠️ Arquivo GenBank não encontrado: {file_path}")
                
                if not working_files:
                    st.error("❌ Nenhum arquivo GenBank válido encontrado!")
                    return
                
                # Para arquivos GenBank, adicionar os nomes dos arquivos ao sys.argv
                file_args = [os.path.basename(path) for path in working_files.values()]
                st.write(f"📋 Arquivos GenBank a serem processados: {file_args}")
                
            else:
                # Para arquivos de proteína, usar como antes
                working_files = {}
                if 'protein_files' in st.session_state:
                    for protein_name, protein_file in st.session_state.protein_files.items():
                        # Definir caminho de destino no diretório atual
                        dest_file = os.path.join(working_dir, f"{protein_name}.faa")
                        
                        if os.path.exists(protein_file):
                            # Se o arquivo não está no diretório atual, copiar
                            if os.path.abspath(protein_file) != os.path.abspath(dest_file):
                                import shutil
                                shutil.copy2(protein_file, dest_file)
                                st.write(f"📁 Arquivo copiado: {protein_name}.faa -> {dest_file}")
                            else:
                                st.write(f"📁 Arquivo já no diretório de trabalho: {protein_name}.faa")
                            
                            working_files[protein_name] = dest_file
                        else:
                            st.warning(f"⚠️ Arquivo de proteína não encontrado: {protein_file}")
                
                if not working_files:
                    st.error("❌ Nenhum arquivo de proteína válido encontrado!")
                    return
                
                # Para arquivos de proteína, adicionar apenas os nomes dos arquivos .faa
                file_args = [f"{name}.faa" for name in working_files.keys()]
            
            # Verificar arquivos no diretório atual
            current_files = os.listdir('.')
            if input_type == 'genbank':
                relevant_files = [f for f in current_files if f.endswith(('.gbff', '.gbk', '.gb'))]
                st.write(f"🔍 Arquivos GenBank encontrados no diretório de trabalho: {relevant_files}")
            else:
                faa_files = [f for f in current_files if f.endswith('.faa')]
                st.write(f"🔍 Arquivos .faa encontrados no diretório de trabalho: {faa_files}")
            
            # Configurar sys.argv para o engine
            new_argv = ["streamlit_app.py"]  # Nome do script
            
            # Adicionar databases selecionadas
            for db in config['databases']:
                new_argv.append(f"-{db}")
            
            # Adicionar thresholds se diferentes do padrão
            if config['identity_threshold'] != 70.0:
                new_argv.extend(["-i", str(config['identity_threshold'])])
            if config['coverage_threshold'] != 70.0:
                new_argv.extend(["-c", str(config['coverage_threshold'])])
            
            # Adicionar aligner
            if config.get('aligner') == 'diamond':
                new_argv.append("-diamond")
            elif config.get('aligner') == 'blast':
                new_argv.append("-blast")
            elif config.get('aligner') == 'both':
                new_argv.append("-both")
            
            # Adicionar arquivos de entrada
            new_argv.extend(file_args)
            
            # Debug: mostrar comando que será executado
            st.write(f"🚀 Comando PanViTa: {' '.join(new_argv)}")
            
            # Substituir sys.argv temporariamente
            sys.argv = new_argv
            
            # Executar o engine
            progress_text = st.empty()
            progress_text.text("🚀 Inicializando engine PanViTa...")
            
            # Verificar diretório atual antes da execução
            st.write(f"📍 Diretório atual antes do engine: {os.getcwd()}")
            st.write(f"📋 Arquivos no diretório: {os.listdir('.')}")
            
            engine = PanViTaEngine()
            
            progress_text.text("⚙️ Executando análise...")
            engine.run()
            
            progress_text.text("📊 Coletando resultados...")
            
            # Verificar diretório atual após a execução
            st.write(f"📍 Diretório atual após o engine: {os.getcwd()}")
            st.write(f"📋 Arquivos gerados no diretório: {os.listdir('.')}")
            
            # Coletar resultados gerados
            results = {}
            
            # Processar resultados por database
            for db in config['databases']:
                db_results = {
                    'database': db,
                    'gene_count': 0,
                    'strain_count': len(working_files),
                    'files': []
                }
                
                # Procurar arquivos específicos da database no diretório atual
                current_files = os.listdir('.')
                st.write(f"🔍 Procurando arquivos para {db} em: {current_files}")
                
                for file in current_files:
                    if file.lower().startswith(db.lower()) and (file.endswith('.csv') or file.endswith('.pdf') or file.endswith('.png')):
                        file_path = os.path.abspath(file)
                        db_results['files'].append(file_path)
                        st.write(f"✅ Arquivo encontrado para {db}: {file}")
                        
                        # Se for arquivo de contagem de genes
                        if 'gene_count' in file.lower() and file.endswith('.csv'):
                            try:
                                df = pd.read_csv(file, sep=';')
                                db_results['gene_count'] = len(df)
                                st.write(f"📊 Gene count para {db}: {len(df)} genes")
                            except Exception as e:
                                st.warning(f"⚠️ Erro ao ler arquivo de contagem {file}: {e}")
                        
                        # Se for matriz de presença/ausência
                        elif file.lower() == f"matriz_{db.lower()}.csv" or (file.startswith(f"matriz_{db}") and file.endswith('.csv')):
                            db_results['matrix_file'] = file_path
                            st.write(f"📋 Matriz encontrada para {db}: {file}")
                            # Tentar contar genes da matriz
                            try:
                                df = pd.read_csv(file, sep=';')
                                if 'Strains' in df.columns:
                                    db_results['gene_count'] = len(df.columns) - 1
                                else:
                                    db_results['gene_count'] = len(df.columns)
                                st.write(f"📊 Genes na matriz {db}: {db_results['gene_count']}")
                            except Exception as e:
                                st.warning(f"⚠️ Erro ao ler matriz {file}: {e}")
                        
                        # Se for heatmap
                        elif any(keyword in file.lower() for keyword in ['heatmap', 'clustermap']):
                            db_results['heatmap_file'] = file_path
                            st.write(f"🔥 Heatmap encontrado para {db}: {file}")
                
                # Verificar se há diretórios de resultados específicos
                for item in current_files:
                    if os.path.isdir(item) and db.lower() in item.lower():
                        st.write(f"📁 Diretório encontrado para {db}: {item}")
                        # Procurar arquivos dentro do diretório
                        try:
                            for subfile in os.listdir(item):
                                subfile_path = os.path.join(item, subfile)
                                if os.path.isfile(subfile_path):
                                    db_results['files'].append(os.path.abspath(subfile_path))
                                    st.write(f"📄 Arquivo no subdiretório: {subfile}")
                        except Exception as e:
                            st.warning(f"⚠️ Erro ao listar diretório {item}: {e}")
                
                results[db] = db_results
                st.write(f"📈 Resumo {db}: {db_results['gene_count']} genes, {len(db_results['files'])} arquivos")
            
            # Salvar resultados no session state
            st.session_state.results = results
            st.session_state.analysis_complete = True
            st.session_state.analysis_temp_dir = working_dir  # Usar diretório de trabalho atual
            
            progress_text.empty()
            
            # Verificar se houve erros durante a análise
            if hasattr(engine, 'erro') and engine.erro:
                st.warning("⚠️ A análise foi concluída, mas alguns erros foram encontrados:")
                for error in engine.erro:
                    st.error(error)
                
                # Se todos os resultados estão vazios, considerar como falha
                total_genes = sum(result.get('gene_count', 0) for result in results.values())
                if total_genes == 0:
                    st.error("❌ Nenhum gene foi encontrado em nenhuma database. Verifique os dados de entrada.")
                else:
                    st.success("✅ Análise concluída com alguns avisos!")
            else:
                st.success("✅ Análise concluída com sucesso!")
                st.balloons()
            
            # Mostrar resumo rápido
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Databases analisadas", len(results))
            with col2:
                total_genes = sum(result.get('gene_count', 0) for result in results.values())
                st.metric("Total de genes encontrados", total_genes)
            with col3:
                total_files = sum(len(result.get('files', [])) for result in results.values())
                st.metric("Arquivos gerados", total_files)
            
        except Exception as e:
            st.error(f"❌ Erro na análise: {str(e)}")
            import traceback
            st.error(f"Detalhes: {traceback.format_exc()}")
        finally:
            # Restaurar sys.argv original
            sys.argv = original_argv
            # Manter no diretório de trabalho atual (não precisa voltar)
    
    def create_results_zip(self, results):
        """Cria um arquivo ZIP com todos os resultados da análise"""
        try:
            # Criar buffer para o ZIP
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                files_added = 0
                
                for db_name, result in results.items():
                    files = result.get('files', [])
                    
                    for file_path in files:
                        if os.path.exists(file_path):
                            # Adicionar arquivo ao ZIP com caminho relativo
                            arc_name = f"{db_name}/{os.path.basename(file_path)}"
                            zip_file.write(file_path, arc_name)
                            files_added += 1
                
                # Adicionar arquivo de resumo
                summary_content = self.generate_analysis_summary(results)
                zip_file.writestr("resumo_analise.txt", summary_content)
                files_added += 1
            
            zip_buffer.seek(0)
            
            if files_added > 0:
                # Nome do arquivo ZIP com timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                zip_filename = f"panvita_resultados_{timestamp}.zip"
                
                st.download_button(
                    "⬇️ Baixar todos os resultados (ZIP)",
                    zip_buffer.getvalue(),
                    zip_filename,
                    "application/zip"
                )
                st.success(f"✅ ZIP preparado com {files_added} arquivos!")
            else:
                st.warning("⚠️ Nenhum arquivo encontrado para incluir no ZIP")
                
        except Exception as e:
            st.error(f"❌ Erro ao criar ZIP: {str(e)}")
    
    def generate_analysis_summary(self, results):
        """Gera um resumo textual da análise"""
        summary = f"""
RESUMO DA ANÁLISE PANVITA
=========================
Data da análise: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

CONFIGURAÇÕES:
- Databases analisadas: {', '.join(results.keys())}
- Número de cepas: {max((result.get('strain_count', 0) for result in results.values()), default=0)}

RESULTADOS POR DATABASE:
"""
        
        for db_name, result in results.items():
            summary += f"""
{db_name.upper()}:
- Genes encontrados: {result.get('gene_count', 0)}
- Cepas analisadas: {result.get('strain_count', 0)}
- Arquivos gerados: {len(result.get('files', []))}
"""
        
        summary += f"""

TOTAL GERAL:
- Total de genes encontrados: {sum(result.get('gene_count', 0) for result in results.values())}
- Total de arquivos gerados: {sum(len(result.get('files', [])) for result in results.values())}

---
Gerado por PanViTa Interface Streamlit
"""
        
        return summary


def main():
    """Função principal da aplicação Streamlit"""
    app = PanViTaStreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
