"""
Interface de linha de comando para PanViTa
Mantém compatibilidade com a versão original
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Adicionar o diretório parent ao path para importar o core
sys.path.append(str(Path(__file__).parent.parent))

try:
    from core.engine import PanViTaEngine
except ImportError:
    print("Erro ao importar o engine do PanViTa. Verifique a instalação.")
    sys.exit(1)


class PanViTaCLI:
    """Interface de linha de comando para PanViTa"""
    
    def __init__(self):
        self.engine = PanViTaEngine()
        self.args = sys.argv
    
    def run(self):
        """Executa a interface CLI"""
        # Verificar help e version
        if self._handle_help_and_version():
            return
        
        # Inicializar sistema
        print("Inicializando sistema...")
        if not self.engine.initialize_system():
            print("ERRO: Falha na inicialização do sistema")
            for erro in self.engine.get_errors():
                print(f"ERRO: {erro}")
            sys.exit(1)
        
        # Determinar aligners disponíveis
        aligner_types, aligner_exes, aligner_names = self.engine.get_available_aligners()
        if not aligner_types:
            print("ERRO: Nenhum aligner disponível")
            sys.exit(1)
        
        # Setup databases
        if not self.engine.setup_databases(aligner_exes):
            print("ERRO: Falha ao configurar databases")
            for erro in self.engine.get_errors():
                print(f"ERRO: {erro}")
            sys.exit(1)
        
        # Processar argumentos da linha de comando
        strain_dict = self._parse_input_files()
        
        # Downloads se solicitados
        gbk_files = []
        if "-b" in self.args:
            print("Baixando arquivos GenBank...")
            gbk_files = self.engine.download_genbank_files(strain_dict)
        
        if "-a" in self.args or "-g" in self.args:
            print("Baixando arquivos FASTA...")
            fasta_files = self.engine.download_fasta_files(strain_dict)
        
        # Extrair proteínas dos arquivos locais
        protein_files = self._get_protein_files(gbk_files)
        
        if not protein_files:
            print("ERRO: Nenhum arquivo de proteína encontrado")
            sys.exit(1)
        
        # Determinar databases a analisar
        databases = self._get_databases_to_analyze()
        if not databases:
            print("AVISO: Nenhuma database selecionada para análise")
            return
        
        # Obter thresholds
        identity_threshold = self._get_threshold("-i", 70.0)
        coverage_threshold = self._get_threshold("-c", 70.0)
        
        # Executar alinhamentos
        print("Executando alinhamentos...")
        alignment_results = self.engine.run_alignments(
            protein_files,
            databases,
            aligner_types,
            aligner_exes,
            identity_threshold,
            coverage_threshold
        )
        
        # Gerar análises
        print("Gerando resultados...")
        analysis_results = self.engine.generate_analysis_results(
            alignment_results,
            databases
        )
        
        # Mostrar resultados
        self._print_results(analysis_results)
        
        # Mostrar erros se houver
        errors = self.engine.get_errors()
        if errors:
            print("\n=== ERROS ENCONTRADOS ===")
            for erro in errors:
                print(f"ERRO: {erro}")
    
    def _handle_help_and_version(self) -> bool:
        """Trata comandos de help e version"""
        if "-v" in self.args or "-version" in self.args:
            print("-----------------------------------------------")
            print("PanViTa - Pan Virulence and resisTance Analysis")
            print("Version: 2.0.0")
            print("Authors: Victor S Caricatte De Araújo, Diego Neres, Vinicius Oliveira")
            print("Institution: Universidade Federal de Minas Gerais")
            print("-----------------------------------------------")
            return True
        
        if "-h" in self.args or "--help" in self.args:
            self._print_help()
            return True
        
        return False
    
    def _print_help(self):
        """Imprime ajuda da linha de comando"""
        print("""
=== PanViTa - Pan Virulence and Resistance Analysis ===

USO:
    python panvita_cli.py [opções] arquivo_entrada

OPÇÕES DE ENTRADA:
    -b                  Baixar arquivos GenBank do NCBI
    -a                  Baixar arquivos FASTA e anotar com PROKKA
    -g                  Baixar apenas arquivos FASTA (sem anotação)

DATABASES:
    -bacmet            Analisar database BacMet (resistência a metais)
    -card              Analisar database CARD (resistência antimicrobiana)
    -vfdb              Analisar database VFDB (fatores de virulência)
    -megares           Analisar database MEGARes (resistência antimicrobiana)

THRESHOLDS:
    -i VALOR           Threshold de identidade (padrão: 70%)
    -c VALOR           Threshold de cobertura (padrão: 70%)

FORMATO DE SAÍDA:
    -pdf               Gerar gráficos em PDF (padrão)
    -png               Gerar gráficos em PNG

OUTRAS OPÇÕES:
    -s                 Usar nome curto das cepas
    -save-genes        Salvar genes encontrados por cepa
    -v, -version       Mostrar versão
    -h, --help         Mostrar esta ajuda

EXEMPLOS:
    python panvita_cli.py -b -card -vfdb arquivo_cepas.csv
    python panvita_cli.py -bacmet -i 80 -c 75 *.faa
    python panvita_cli.py -a -megares -pdf arquivo_ncbi.txt

FORMATO DO ARQUIVO DE ENTRADA:
    CSV com colunas: nome, ftp_genbank, ftp_assembly, strain
    ou arquivos .faa/.gbf/.gbk diretamente
        """)
    
    def _parse_input_files(self) -> Dict:
        """Analisa arquivos de entrada da linha de comando"""
        strain_dict = {}
        
        # Procurar por arquivos na linha de comando
        input_files = [arg for arg in self.args[1:] if not arg.startswith('-') and os.path.exists(arg)]
        
        if not input_files:
            print("ERRO: Nenhum arquivo de entrada válido fornecido")
            sys.exit(1)
        
        # Se for CSV, carregar como strain dict
        for file_path in input_files:
            if file_path.endswith('.csv'):
                strain_dict.update(self._load_csv_strains(file_path))
            elif file_path.endswith(('.txt', '.tsv')):
                strain_dict.update(self._load_text_strains(file_path))
        
        return strain_dict
    
    def _load_csv_strains(self, csv_path: str) -> Dict:
        """Carrega cepas de um arquivo CSV"""
        import pandas as pd
        
        try:
            df = pd.read_csv(csv_path)
            strain_dict = {}
            
            for idx, row in df.iterrows():
                strain_dict[idx] = (
                    row.get('nome', ''),
                    row.get('ftp_genbank', ''),
                    row.get('ftp_assembly', ''),
                    row.get('strain', '')
                )
            
            return strain_dict
        except Exception as e:
            print(f"ERRO ao carregar CSV {csv_path}: {e}")
            return {}
    
    def _load_text_strains(self, txt_path: str) -> Dict:
        """Carrega cepas de um arquivo de texto"""
        strain_dict = {}
        
        try:
            with open(txt_path, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 4:
                        strain_dict[i] = (parts[0], parts[1], parts[2], parts[3])
                    elif len(parts) >= 1:
                        # Assumir que é apenas o nome da cepa
                        strain_dict[i] = (parts[0], '', '', parts[0])
            
            return strain_dict
        except Exception as e:
            print(f"ERRO ao carregar arquivo texto {txt_path}: {e}")
            return {}
    
    def _get_protein_files(self, gbk_files: List[str]) -> Dict[str, str]:
        """Obtém arquivos de proteínas (extraindo de GenBank ou procurando .faa)"""
        protein_files = {}
        
        # Se há arquivos GenBank, extrair proteínas
        if gbk_files:
            protein_files = self.engine.extract_proteins_from_genbank(gbk_files)
        
        # Procurar por arquivos .faa na linha de comando e diretório atual
        faa_files = []
        for arg in self.args[1:]:
            if arg.endswith('.faa') and os.path.exists(arg):
                faa_files.append(arg)
        
        # Procurar .faa no diretório atual se não especificado
        if not faa_files and not gbk_files:
            for file in os.listdir('.'):
                if file.endswith('.faa'):
                    faa_files.append(file)
        
        # Adicionar arquivos .faa encontrados
        for faa_file in faa_files:
            base_name = os.path.splitext(os.path.basename(faa_file))[0]
            protein_files[base_name] = faa_file
        
        return protein_files
    
    def _get_databases_to_analyze(self) -> List[str]:
        """Determina quais databases analisar baseado nos argumentos"""
        databases = []
        
        if "-bacmet" in self.args:
            databases.append("bacmet")
        if "-card" in self.args:
            databases.append("card")
        if "-vfdb" in self.args:
            databases.append("vfdb")
        if "-megares" in self.args:
            databases.append("megares")
        
        return databases
    
    def _get_threshold(self, arg: str, default: float) -> float:
        """Obtém valor de threshold da linha de comando"""
        try:
            if arg in self.args:
                idx = self.args.index(arg)
                if idx + 1 < len(self.args):
                    return float(self.args[idx + 1])
        except (ValueError, IndexError):
            pass
        
        return default
    
    def _print_results(self, results: Dict[str, Any]):
        """Imprime resultados da análise"""
        print("\n" + "="*60)
        print("RESULTADOS DA ANÁLISE")
        print("="*60)
        
        for db_name, result in results.items():
            print(f"\n--- {db_name.upper()} ---")
            print(f"Genes encontrados: {result.get('gene_count', 0)}")
            print(f"Cepas analisadas: {result.get('strain_count', 0)}")
            print(f"Matriz: {result.get('matrix_file', 'N/A')}")
            print(f"Heatmap: {result.get('heatmap_file', 'N/A')}")
        
        outputs = self.engine.get_outputs()
        if outputs:
            print(f"\nArquivos gerados: {len(outputs)}")
            for output in outputs:
                print(f"  - {output}")
        
        print("\nAnálise concluída!")


def main():
    """Função principal da CLI"""
    cli = PanViTaCLI()
    cli.run()


if __name__ == "__main__":
    main()
