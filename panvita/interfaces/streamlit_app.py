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

# Adicionar o diretório parent ao path para importar o core
sys.path.append(str(Path(__file__).parent.parent))

try:
    from core.engine import PanViTaEngine
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
        if 'engine_initialized' not in st.session_state:
            st.session_state.engine_initialized = False
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
        
        # Inicialização do sistema
        if not st.session_state.engine_initialized:
            if st.sidebar.button("🚀 Inicializar Sistema", type="primary"):
                with st.spinner("Inicializando dependências..."):
                    success = self.engine.initialize_system()
                    if success:
                        st.session_state.engine_initialized = True
                        st.sidebar.success("✅ Sistema inicializado com sucesso!")
                    else:
                        st.sidebar.error("❌ Erro na inicialização")
                        for erro in self.engine.get_errors():
                            st.sidebar.error(erro)
        else:
            st.sidebar.success("✅ Sistema inicializado")
        
        # Configurações de análise
        st.sidebar.subheader("🎯 Parâmetros de Análise")
        
        # Databases
        databases = st.sidebar.multiselect(
            "Selecione as databases:",
            ["bacmet", "card", "vfdb", "megares"],
            default=["card", "vfdb"],
            help="Escolha quais databases usar para análise"
        )
        
        # Thresholds
        identity_threshold = st.sidebar.slider(
            "Threshold de Identidade (%)",
            min_value=50.0,
            max_value=100.0,
            value=70.0,
            step=1.0,
            help="Porcentagem mínima de identidade para considerar um hit"
        )
        
        coverage_threshold = st.sidebar.slider(
            "Threshold de Cobertura (%)",
            min_value=50.0,
            max_value=100.0,
            value=70.0,
            step=1.0,
            help="Porcentagem mínima de cobertura da query para considerar um hit"
        )
        
        return {
            'databases': databases,
            'identity_threshold': identity_threshold,
            'coverage_threshold': coverage_threshold
        }
    
    def render_main_content(self):
        """Renderiza o conteúdo principal"""
        if not st.session_state.engine_initialized:
            st.warning("⚠️ Por favor, inicialize o sistema primeiro usando o botão na barra lateral.")
            return
        
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
            ["Upload de arquivos GenBank (.gbf/.gbk)", "Download automático do NCBI", "Upload de proteínas (.faa)"],
            help="Escolha como fornecer os dados para análise"
        )
        
        if upload_method == "Upload de arquivos GenBank (.gbf/.gbk)":
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
            type=['gbf', 'gbk', 'gb'],
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
            csv_file = st.file_uploader(
                "Upload arquivo CSV com dados das cepas:",
                type=['csv'],
                help="CSV deve conter colunas: nome, ftp_genbank, ftp_assembly, strain"
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
                    strain_name = st.text_input("Nome da cepa:")
                    ftp_genbank = st.text_input("FTP GenBank:")
                with col2:
                    ftp_assembly = st.text_input("FTP Assembly:")
                    strain_id = st.text_input("ID da cepa:")
                
                submit = st.form_submit_button("➕ Adicionar cepa")
                
                if submit and strain_name:
                    # Adicionar à sessão
                    if 'manual_strains' not in st.session_state:
                        st.session_state.manual_strains = []
                    
                    st.session_state.manual_strains.append({
                        'nome': strain_name,
                        'ftp_genbank': ftp_genbank,
                        'ftp_assembly': ftp_assembly,
                        'strain': strain_id
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
        
        config = self.render_sidebar()
        
        st.subheader("Arquivos processados:")
        if 'protein_files' in st.session_state:
            for name, path in st.session_state.protein_files.items():
                st.write(f"• {name}: {path}")
        
        st.subheader("Configurações da análise:")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Databases", len(config['databases']))
        with col2:
            st.metric("Identidade (%)", config['identity_threshold'])
        with col3:
            st.metric("Cobertura (%)", config['coverage_threshold'])
        
        if st.button("🚀 Iniciar Análise", type="primary"):
            if not config['databases']:
                st.error("❌ Selecione pelo menos uma database!")
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
        
        with col1:
            st.metric("Total de Genes", total_genes)
        with col2:
            st.metric("Total de Cepas", total_strains)
        with col3:
            st.metric("Databases Analisadas", len(results))
        with col4:
            st.metric("Arquivos Gerados", len(self.engine.get_outputs()))
        
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
                    df = pd.read_csv(matrix_file, sep=';')
                    st.dataframe(df)
                    
                    # Download da matriz
                    csv = df.to_csv(sep=';', index=False)
                    st.download_button(
                        f"⬇️ Baixar matriz {db_name}",
                        csv,
                        f"matriz_{db_name}.csv",
                        "text/csv"
                    )
            
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
    
    def render_logs_tab(self):
        """Tab para mostrar logs e erros"""
        st.header("📋 Logs e Erros")
        
        errors = self.engine.get_errors()
        outputs = self.engine.get_outputs()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("❌ Erros")
            if errors:
                for i, error in enumerate(errors, 1):
                    st.error(f"{i}. {error}")
            else:
                st.success("✅ Nenhum erro encontrado")
        
        with col2:
            st.subheader("📄 Arquivos Gerados")
            if outputs:
                for output in outputs:
                    if os.path.exists(output):
                        st.success(f"✅ {output}")
                    else:
                        st.warning(f"⚠️ {output} (não encontrado)")
            else:
                st.info("ℹ️ Nenhum arquivo gerado ainda")
    
    def process_genbank_files(self, uploaded_files):
        """Processa arquivos GenBank carregados"""
        try:
            # Salvar arquivos temporariamente
            temp_dir = tempfile.mkdtemp()
            gbk_files = []
            
            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                gbk_files.append(file_path)
            
            # Extrair proteínas
            protein_files = self.engine.extract_proteins_from_genbank(gbk_files)
            
            st.session_state.processed_files = True
            st.session_state.protein_files = protein_files
            
            st.success(f"✅ {len(protein_files)} arquivo(s) de proteínas extraído(s)")
            
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivos GenBank: {str(e)}")
    
    def process_ncbi_download(self, df):
        """Processa download do NCBI"""
        try:
            # Converter DataFrame para dicionário no formato esperado
            strain_dict = {}
            for idx, row in df.iterrows():
                strain_dict[idx] = (
                    row.get('nome', ''),
                    row.get('ftp_genbank', ''),
                    row.get('ftp_assembly', ''),
                    row.get('strain', '')
                )
            
            # Baixar arquivos GenBank
            gbk_files = self.engine.download_genbank_files(strain_dict)
            
            # Extrair proteínas
            protein_files = self.engine.extract_proteins_from_genbank(gbk_files)
            
            st.session_state.processed_files = True
            st.session_state.protein_files = protein_files
            
            st.success(f"✅ {len(protein_files)} cepa(s) baixada(s) e processada(s)")
            
        except Exception as e:
            st.error(f"❌ Erro no download do NCBI: {str(e)}")
    
    def process_protein_files(self, uploaded_proteins):
        """Processa arquivos de proteínas carregados"""
        try:
            # Salvar arquivos temporariamente
            temp_dir = tempfile.mkdtemp()
            protein_files = {}
            
            for uploaded_file in uploaded_proteins:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                # Nome base sem extensão
                base_name = os.path.splitext(uploaded_file.name)[0]
                protein_files[base_name] = file_path
            
            st.session_state.processed_files = True
            st.session_state.protein_files = protein_files
            
            st.success(f"✅ {len(protein_files)} arquivo(s) de proteínas processado(s)")
            
        except Exception as e:
            st.error(f"❌ Erro ao processar proteínas: {str(e)}")
    
    def run_analysis(self, config):
        """Executa a análise completa"""
        try:
            # Setup databases
            aligner_types, aligner_exes, aligner_names = self.engine.get_available_aligners()
            if not aligner_types:
                st.error("❌ Nenhum aligner disponível!")
                return
            
            success = self.engine.setup_databases(aligner_exes)
            if not success:
                st.error("❌ Erro ao configurar databases!")
                return
            
            # Executar alinhamentos
            alignment_results = self.engine.run_alignments(
                st.session_state.protein_files,
                config['databases'],
                aligner_types,
                aligner_exes,
                config['identity_threshold'],
                config['coverage_threshold']
            )
            
            # Gerar resultados da análise
            analysis_results = self.engine.generate_analysis_results(
                alignment_results,
                config['databases']
            )
            
            st.session_state.analysis_complete = True
            st.session_state.results = analysis_results
            
            st.success("✅ Análise concluída com sucesso!")
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ Erro na análise: {str(e)}")


def main():
    """Função principal da aplicação Streamlit"""
    app = PanViTaStreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
