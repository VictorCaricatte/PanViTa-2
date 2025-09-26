import os
import re
import argparse
import pandas as pd
import glob
from typing import Dict, Tuple

def build_vfdb_mechanism_map(db_directory: str) -> Dict[str, str]:
    """
    Parses the vfdb_core.fasta file to create a dictionary mapping a gene name
    to its virulence mechanism, replicating PanViTa's logic.

    Args:
        db_directory: The path to PanViTa's 'DB' folder.

    Returns:
        A dictionary where the key is the gene name and the value is the virulence mechanism.
    """
    vfdb_fasta_path = os.path.join(db_directory, 'vfdb_core.fasta')
    if not os.path.exists(vfdb_fasta_path):
        print(f"ERROR: Database file not found at: {vfdb_fasta_path}")
        print("Please provide the correct path to PanViTa's 'DB' folder using the --db argument.")
        exit(1)

    print(f"Building virulence mechanism map from {vfdb_fasta_path}...")
    
    # This dictionary will map, for example, 'plc1' to 'Exotoxin'
    gene_to_mechanism_map = {}

    with open(vfdb_fasta_path, 'rt') as vfdb_file:
        for line in vfdb_file:
            if not line.startswith('>'):
                continue

            # This logic is a replica of PanViTa's DataProcessor.extract_keys for '-vfdb'
            mechanism_search = re.findall(r"(?<=\)\s-\s)[A-z\/\-\s]*(?=\s\()", line, flags=0)
            mechanism = mechanism_search[0].strip() if mechanism_search else "Unknown Mechanism"

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

    print(f"Map built successfully. {len(gene_to_mechanism_map)} virulence genes mapped.")
    return gene_to_mechanism_map

def find_panvita_result_files(results_directory: str) -> Tuple[str, str]:
    """
    Finds the necessary result files within the PanViTa results folder.
    
    Args:
        results_directory: Path to the PanViTa results folder (e.g., Results_vfdb_...).
        
    Returns:
        A tuple containing the paths to the gene_count file and the matrix file.
    """
    if not os.path.isdir(results_directory):
        print(f"ERROR: Results directory '{results_directory}' not found.")
        exit(1)
        
    gene_count_files = glob.glob(os.path.join(results_directory, 'vfdb_gene_count*.csv'))
    matrix_files = glob.glob(os.path.join(results_directory, 'matriz_vfdb*.csv'))
    
    if not gene_count_files:
        print(f"ERROR: No 'vfdb_gene_count*.csv' file found in '{results_directory}'.")
        exit(1)
    if not matrix_files:
        print(f"ERROR: No 'matriz_vfdb*.csv' file found in '{results_directory}'.")
        exit(1)
        
    gene_count_file = gene_count_files[0]
    matrix_file = matrix_files[0]
    
    print(f"Found gene count file: {os.path.basename(gene_count_file)}")
    print(f"Found identity matrix file: {os.path.basename(matrix_file)}")
    
    return gene_count_file, matrix_file

def create_gene_category_map(gene_count_file: str, total_genomes: int) -> Dict[str, str]:
    """
    Creates a dictionary mapping each gene to its category (Core, Accessory, Exclusive).

    Args:
        gene_count_file: Path to the vfdb_gene_count.csv file.
        total_genomes: The total number of genomes analyzed.

    Returns:
        A dictionary mapping a gene name to its category.
    """
    print("Categorizing genes into Core, Accessory, and Exclusive...")
    gene_categories = {}
    df_genes = pd.read_csv(gene_count_file, sep=';')
    
    for _, row in df_genes.iterrows():
        gene = row['Genes']
        presence = row['Presence Number']
        
        if presence == total_genomes:
            gene_categories[gene] = 'Core'
        elif presence == 1:
            gene_categories[gene] = 'Exclusive'
        else:
            gene_categories[gene] = 'Accessory'
            
    print(f"{len(gene_categories)} genes categorized.")
    return gene_categories

def process_virulence_data(matrix_file: str, mechanism_map: Dict[str, str], category_map: Dict[str, str]) -> pd.DataFrame:
    """
    Processes the PanViTa identity matrix to create a detailed report with identity,
    category, and mechanism for each found gene.

    Args:
        matrix_file: Path to the matriz_vfdb.csv file.
        mechanism_map: Dictionary mapping genes to mechanisms.
        category_map: Dictionary mapping genes to categories.

    Returns:
        A pandas DataFrame with the detailed results.
    """
    print("Processing identity matrix to extract detailed results...")
    df_matrix = pd.read_csv(matrix_file, sep=';', index_col='Strains')
    
    # Unpivot the matrix from wide to long format
    df_long = df_matrix.melt(ignore_index=False, var_name='Virulence_Gene', value_name='Identity_Percentage').reset_index()
    
    # Filter out genes that are not present (identity > 0)
    df_present = df_long[df_long['Identity_Percentage'] > 0].copy()
    df_present.rename(columns={'Strains': 'Genome'}, inplace=True)
    
    # Add the Category and Mechanism columns using the maps
    df_present['Category'] = df_present['Virulence_Gene'].map(category_map)
    df_present['Virulence_Mechanism'] = df_present['Virulence_Gene'].map(mechanism_map)
    
    # Reorder columns for clarity
    final_df = df_present[['Genome', 'Virulence_Gene', 'Identity_Percentage', 'Category', 'Virulence_Mechanism']]
    
    return final_df.sort_values(by=['Genome', 'Virulence_Gene']).reset_index(drop=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyzes PanViTa (-vfdb) results to identify virulence genes, their identity, "
                    "category (Core, Accessory, Exclusive), and mechanism. "
                    "Generates CSV, TXT, and Excel reports in the current directory.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Path to the results folder generated by PanViTa (e.g., 'Results_vfdb_...')."
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Path to the 'DB' folder containing the PanViTa databases (e.g., './DB')."
    )
    
    args = parser.parse_args()
    
    # Define Output Filenames 
    CSV_OUTPUT_FILENAME = "virulence_mechanisms_report.csv"
    TXT_OUTPUT_FILENAME = "virulence_mechanisms_report.txt"
    EXCEL_OUTPUT_FILENAME = "virulence_mechanisms_report.xlsx"
    
    #Build the gene -> mechanism map
    virulence_mechanism_map = build_vfdb_mechanism_map(args.db)
    
    # Find the necessary result files
    gene_count_csv, matrix_csv = find_panvita_result_files(args.results)
    
    #  Get total number of genomes from the matrix file
    total_genomes = len(pd.read_csv(matrix_csv, sep=';').index)
    print(f"Found {total_genomes} genomes in the analysis.")
    
    # Create the gene -> category map
    gene_category_map = create_gene_category_map(gene_count_csv, total_genomes)
    
    # Process all data to create the final report
    final_report_df = process_virulence_data(matrix_csv, virulence_mechanism_map, gene_category_map)
    
    # Save and display the results
    if not final_report_df.empty:
        # Save to CSV
        final_report_df.to_csv(CSV_OUTPUT_FILENAME, index=False)
        
        # Save to Excel
        final_report_df.to_excel(EXCEL_OUTPUT_FILENAME, index=False, sheet_name='Virulence Report')
        
        # Save to TXT with summary
        summary = final_report_df.groupby(['Category', 'Virulence_Mechanism']).size().reset_index(name='Count')
        with open(TXT_OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            f.write("--- Detailed Virulence Gene Report ---\n\n")
            f.write(final_report_df.to_string())
            f.write("\n\n\n--- Summary by Category and Mechanism ---\n\n")
            f.write(summary.to_string())

        print("\n--- Final Report (Sample) ---")
        print(final_report_df.head(10).to_string())
        
        print("\n--- Summary by Category ---")
        print(final_report_df['Category'].value_counts().to_string())

        print(f"\n Analysis complete! Reports saved to:")
        print(f"  - Excel: {os.path.abspath(EXCEL_OUTPUT_FILENAME)}")
        print(f"  - CSV:   {os.path.abspath(CSV_OUTPUT_FILENAME)}")
        print(f"  - TXT:   {os.path.abspath(TXT_OUTPUT_FILENAME)}")
    else:
        print("\nNo virulence genes with identity > 0 were found in the provided results.")
