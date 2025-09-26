import os
import re
import argparse
import pandas as pd
import glob
from typing import Dict, Tuple

def build_vfdb_mechanism_map(db_directory: str) -> Dict[str, str]:
    vfdb_fasta_path = os.path.join(db_directory, 'vfdb_core.fasta')
    if not os.path.exists(vfdb_fasta_path):
        print(f"ERRO: Arquivo de banco de dados não encontrado em: {vfdb_fasta_path}")
        print("Por favor, forneça o caminho correto para a pasta 'DB' do PanViTa usando o argumento --db.")
        exit(1)

    print(f"Construindo mapa de mecanismos de virulência a partir de {vfdb_fasta_path}...")
    gene_to_mechanism_map = {}

    with open(vfdb_fasta_path, 'rt') as vfdb_file:
        for line in vfdb_file:
            if not line.startswith('>'):
                continue

            mechanism_search = re.findall(r"(?<=\)\s-\s)[A-z\/\-\s]*(?=\s\()", line, flags=0)
            mechanism = mechanism_search[0].strip() if mechanism_search else "Mecanismo Desconhecido"

            gene_name = ""
            first_paren_end = line.find(')')
            if first_paren_end != -1:
                second_paren_start = line.find('(', first_paren_end)
                if second_paren_start != -1:
                    second_paren_end = line.find(')', second_paren_start)
                    if second_paren_end != -1:
                        gene_name = line[second_paren_start + 1:second_paren_end].strip()

            if gene_name:
                gene_to_mechanism_map[gene_name] = mechanism

    print(f"Mapa construído com sucesso. {len(gene_to_mechanism_map)} genes de virulência mapeados.")
    return gene_to_mechanism_map


def find_panvita_result_files(results_directory: str) -> str:

    if not os.path.isdir(results_directory):
        print(f"ERRO: O diretório de resultados '{results_directory}' não foi encontrado.")
        exit(1)
        
    strain_count_files = glob.glob(os.path.join(results_directory, 'vfdb_strain_count*.csv'))
    
    if not strain_count_files:
        print(f"ERRO: Nenhum arquivo 'vfdb_strain_count*.csv' encontrado em '{results_directory}'.")
        print("Verifique se o caminho do diretório está correto e se o PanViTa foi executado com a flag '-vfdb'.")
        exit(1)
        
    strain_count_file = strain_count_files[0]
    print(f"Arquivo de contagem por genoma encontrado: {os.path.basename(strain_count_file)}")
    
    return strain_count_file


def analyze_virulence_genes(strain_count_file: str, mechanism_map: Dict[str, str]) -> pd.DataFrame:

    print("Analisando os genes de virulência encontrados em cada genoma...")
    try:
        df_strains = pd.read_csv(strain_count_file, sep=';')
    except FileNotFoundError:
        print(f"ERRO: O arquivo de contagem de genomas não foi encontrado: {strain_count_file}")
        return pd.DataFrame()

    results_list = []
    
    for index, row in df_strains.iterrows():
        strain_name = row['Strains']
        if pd.isna(row['Genes']):
            continue
            
        found_genes = str(row['Genes']).split(',')
        
        for gene in found_genes:
            gene = gene.strip()
            if not gene:
                continue
            
            mechanism = mechanism_map.get(gene, "Mecanismo não encontrado no DB")
            
            results_list.append({
                'Genoma': strain_name,
                'Gene_de_Virulencia': gene,
                'Mecanismo_de_Virulencia': mechanism
            })
            
    return pd.DataFrame(results_list)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analisa os resultados do PanViTa (-vfdb) para identificar genes e seus mecanismos de virulência. "
                    "Gera dois arquivos de saída (CSV e TXT) no diretório atual.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Caminho para a pasta de resultados gerada pelo PanViTa (ex: 'Results_vfdb_...')."
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Caminho para a pasta 'DB' que contém os bancos de dados do PanViTa (ex: './DB')."
    )
    
    args = parser.parse_args()
    
    CSV_OUTPUT_FILENAME = "relatorio_mecanismos_virulencia.csv"
    TXT_OUTPUT_FILENAME = "relatorio_mecanismos_virulencia.txt"
    
    virulence_mechanism_map = build_vfdb_mechanism_map(args.db)
    
    strain_count_csv = find_panvita_result_files(args.results)
    
    final_report_df = analyze_virulence_genes(strain_count_csv, virulence_mechanism_map)
    
    if not final_report_df.empty:
        final_report_df.to_csv(CSV_OUTPUT_FILENAME, index=False)
        
        mechanism_counts = final_report_df['Mecanismo_de_Virulencia'].value_counts()
        with open(TXT_OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            f.write("--- Relatório Detalhado de Genes de Virulência ---\n\n")
            f.write(final_report_df.to_string())
            f.write("\n\n\n--- Resumo por Mecanismo de Virulência (Contagem) ---\n\n")
            f.write(mechanism_counts.to_string())

        print("\n Relatório Final (Amostra)")
        print(final_report_df.to_string())
        
        print("\nResumo por Mecanismo de Virulência")
        print(mechanism_counts.to_string())

        print(f"\nAnálise concluída! Relatórios salvos em:")
        print(f"  - {os.path.abspath(CSV_OUTPUT_FILENAME)}")
        print(f"  - {os.path.abspath(TXT_OUTPUT_FILENAME)}")
    else:
        print("\nNenhum gene de virulência foi encontrado nos arquivos de resultado fornecidos.")
