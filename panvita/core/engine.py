"""
Engine principal do PanViTa - Lógica de análise desacoplada das interfaces
"""

import os
from typing import List, Tuple, Dict, Any

from .downloader import NCBIDownloader
from .dependencies import DependencyManager
from .databases import DatabaseManager
from .aligner import Aligner


class PanViTaEngine:
    """
    Engine principal do PanViTa que contém toda a lógica de análise
    desacoplada das interfaces (CLI ou Streamlit)
    """
    
    def __init__(self):
        self.erro = []
        self.dppath = None
        self.dbpath = None
        self.dic = None
        self.dic2 = None
        self.dic3 = None
        self.strains = None
        self.gbff = None
        self.pkgbf = None
        self.files = None
        self.parameters = None
        self.outputs = []
        
    def initialize_system(self) -> bool:
        """
        Inicializa dependências e databases
        Returns: True se sucesso, False se erro crítico
        """
        try:
            # Setup dependencies and databases
            dependency_manager = DependencyManager()
            self.dppath = dependency_manager.check_dependencies()
            
            return True
        except Exception as e:
            self.erro.append(f"Erro na inicialização: {str(e)}")
            return False
    
    def get_available_aligners(self) -> Tuple[List[str], List[str], List[str]]:
        """
        Determina quais aligners estão disponíveis
        Returns: (tipos, executáveis, nomes)
        """
        aligner = Aligner(self.dppath)
        return aligner.choose_aligner()
    
    def setup_databases(self, aligner_exes: List[str]) -> bool:
        """
        Configura as databases necessárias
        """
        try:
            database_manager = DatabaseManager(self.dppath)
            
            # Determinar qual executável do DIAMOND usar
            diamond_exe = None
            for exe in aligner_exes:
                if "diamond" in exe:
                    diamond_exe = exe
                    break
            
            if diamond_exe is None:
                # Se não tem DIAMOND, usar BLAST para makedb
                diamond_exe = aligner_exes[0] if aligner_exes else ""
            
            self.dbpath = database_manager.check_databases(diamond_exe)
            return True
        except Exception as e:
            self.erro.append(f"Erro ao configurar databases: {str(e)}")
            return False
    
    def download_genbank_files(self, strain_dict: Dict) -> List[str]:
        """
        Baixa arquivos GenBank do NCBI
        """
        try:
            downloader = NCBIDownloader(strain_dict)
            gbff_files = downloader.get_ncbi_gbf()
            self.gbff = gbff_files
            return gbff_files
        except Exception as e:
            self.erro.append(f"Erro ao baixar GenBank: {str(e)}")
            return []
    
    def download_fasta_files(self, strain_dict: Dict) -> List[str]:
        """
        Baixa arquivos FASTA do NCBI e opcionalmente anota com PROKKA
        """
        try:
            downloader = NCBIDownloader(strain_dict)
            fasta_files = downloader.get_ncbi_fna()
            self.pkgbf = fasta_files
            return fasta_files
        except Exception as e:
            self.erro.append(f"Erro ao baixar FASTA: {str(e)}")
            return []
    
    def extract_proteins_from_genbank(self, gbk_files: List[str]) -> Dict[str, str]:
        """
        Extrai proteínas dos arquivos GenBank
        """
        try:
            protein_files = {}
            for gbk_file in gbk_files:
                # Extrair nome base do arquivo
                base_name = os.path.splitext(os.path.basename(gbk_file))[0]
                faa_file = f"{base_name}.faa"
                
                # Extrair sequências de proteínas
                from .processor import GBKProcessor
                proteins = GBKProcessor.extract_faa(gbk_file)
                
                # Salvar arquivo .faa
                with open(faa_file, 'w') as f:
                    f.writelines(proteins)
                
                protein_files[base_name] = faa_file
            
            return protein_files
        except Exception as e:
            self.erro.append(f"Erro ao extrair proteínas: {str(e)}")
            return {}
    
    def run_alignments(self, 
                      protein_files: Dict[str, str],
                      databases: List[str],
                      aligner_types: List[str],
                      aligner_exes: List[str],
                      identity_threshold: float = 70.0,
                      coverage_threshold: float = 70.0) -> Dict[str, Dict[str, str]]:
        """
        Executa alinhamentos contra as databases selecionadas
        """
        try:
            results = {}
            aligner = Aligner(self.dppath)
            
            for db in databases:
                results[db] = {}
                db_path = os.path.join(self.dbpath, self._get_db_filename(db))
                
                for protein_name, protein_file in protein_files.items():
                    output_file = f"{protein_name}_{db}_alignment.tab"
                    
                    # Executar alinhamento
                    for i, aligner_type in enumerate(aligner_types):
                        aligner.align(
                            protein_file, 
                            db_path, 
                            output_file, 
                            aligner_type,
                            self._get_db_type(db)
                        )
                    
                    results[db][protein_name] = output_file
            
            return results
        except Exception as e:
            self.erro.append(f"Erro nos alinhamentos: {str(e)}")
            return {}
    
    def generate_analysis_results(self, 
                                alignment_results: Dict[str, Dict[str, str]],
                                databases: List[str]) -> Dict[str, Any]:
        """
        Gera matrizes de presença/ausência e visualizações
        """
        try:
            analysis_results = {}
            
            for db in databases:
                # Extrair chaves dos genes
                from .data_processor import DataProcessor
                comp, genes_comp = DataProcessor.extract_keys(f"-{db}", self.dbpath)
                
                # Gerar matriz de presença/ausência
                from .visualization import Visualization
                matrix_file = f"matriz_{db}.csv"
                Visualization.generate_matrix(f"-{db}", self.outputs, comp)
                
                # Gerar heatmap
                heatmap_file = f"heatmap_{db}.pdf"
                Visualization.generate_heatmap(matrix_file, f"-{db}", self.outputs, self.erro)
                
                analysis_results[db] = {
                    'matrix_file': matrix_file,
                    'heatmap_file': heatmap_file,
                    'gene_count': len(comp),
                    'strain_count': len(alignment_results[db])
                }
            
            return analysis_results
        except Exception as e:
            self.erro.append(f"Erro na análise: {str(e)}")
            return {}
    
    def _get_db_filename(self, db: str) -> str:
        """Retorna o nome do arquivo da database"""
        db_filenames = {
            'bacmet': 'bacmet_2',
            'card': 'card_protein_homolog_model', 
            'vfdb': 'vfdb_core',
            'megares': 'megares_v3'
        }
        return db_filenames.get(db, db)
    
    def _get_db_type(self, db: str) -> str:
        """Retorna o tipo da database (protein ou nucleotide)"""
        if db == 'megares':
            return 'nucleotide'
        return 'protein'
    
    def get_errors(self) -> List[str]:
        """Retorna lista de erros ocorridos"""
        return self.erro
    
    def get_outputs(self) -> List[str]:
        """Retorna lista de arquivos de saída gerados"""
        return self.outputs
