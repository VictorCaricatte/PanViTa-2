import os
import argparse
import pandas as pd
import glob
from typing import Dict, Tuple

def build_megares_annotation_map(db_directory: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Parses the megares_v3.fasta file to create dictionaries mapping each gene
    to its resistance mechanism and drug class from the FASTA header.

    Args:
        db_directory: The path to PanViTa's 'DB' folder.

    Returns:
        A tuple containing two dictionaries:
        1. A map from gene name to its resistance mechanism.
        2. A map from gene name to its drug class.
    """
    megares_fasta_path = os.path.join(db_directory, 'megares_v3.fasta')
    if not os.path.exists(megares_fasta_path):
        print(f"ERROR: MEGARes database file not found at: {megares_fasta_path}")
        print("Please provide the correct path to PanViTa's 'DB' folder using the --db argument.")
        exit(1)

    print(f"Building MEGARes annotation map from {megares_fasta_path}...")
    
    mechanism_map = {}
    drug_class_map = {}

    try:
        with open(megares_fasta_path, 'rt', encoding='utf-8') as f:
            for line in f:
                if not line.startswith('>'):
                    continue
                
                # Header format: >MEG_1|Drugs|Aminoglycosides|Aminoglycoside-resistant...|A16S|...
                parts = line.strip().split('|')
                if len(parts) >= 5:
                    # parts[2] is Drug Class
                    # parts[3] is Resistance Mechanism
                    # parts[4] is the Gene Name used in PanViTa's matrix
                    drug_class = parts[2].strip()
                    mechanism = parts[3].strip()
                    gene_name = parts[4].strip()

                    if gene_name:
                        mechanism_map[gene_name] = mechanism
                        drug_class_map[gene_name] = drug_class

    except Exception as e:
        print(f"ERROR: Failed to read or process {megares_fasta_path}. Error: {e}")
        exit(1)

    print(f"Map built successfully. {len(mechanism_map)} resistance genes mapped.")
    return mechanism_map, drug_class_map

def find_megares_result_files(results_directory: str) -> Tuple[str, str]:
    """
    Finds the necessary MEGARes result files within the PanViTa results folder.
    
    Args:
        results_directory: Path to the PanViTa results folder (e.g., Results_megares_...).
        
    Returns:
        A tuple containing the paths to the gene_count file and the matrix file.
    """
    if not os.path.isdir(results_directory):
        print(f"ERROR: Results directory '{results_directory}' not found.")
        exit(1)
        
    gene_count_files = glob.glob(os.path.join(results_directory, 'megares_gene_count*.csv'))
    matrix_files = glob.glob(os.path.join(results_directory, 'matriz_megares*.csv'))
    
    if not gene_count_files:
        print(f"ERROR: No 'megares_gene_count*.csv' file found in '{results_directory}'.")
        exit(1)
    if not matrix_files:
        print(f"ERROR: No 'matriz_megares*.csv' file found in '{results_directory}'.")
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
        gene_count_file: Path to the megares_gene_count.csv file.
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

def process_megares_data(matrix_file: str, mechanism_map: Dict[str, str], drug_class_map: Dict[str, str], category_map: Dict[str, str]) -> pd.DataFrame:
    """
    Processes the PanViTa identity matrix for MEGARes to create a detailed report.

    Args:
        matrix_file: Path to the matriz_megares.csv file.
        mechanism_map: Dictionary mapping genes to resistance mechanisms.
        drug_class_map: Dictionary mapping genes to drug classes.
        category_map: Dictionary mapping genes to categories.

    Returns:
        A pandas DataFrame with the detailed results.
    """
    print("Processing identity matrix to extract detailed results...")
    df_matrix = pd.read_csv(matrix_file, sep=';', index_col='Strains')
    
    df_long = df_matrix.melt(ignore_index=False, var_name='Resistance_Gene', value_name='Identity_Percentage').reset_index()
    
    df_present = df_long[df_long['Identity_Percentage'] > 0].copy()
    df_present.rename(columns={'Strains': 'Genome'}, inplace=True)
    
    # Add the Category, Mechanism, and Drug Class columns using the maps
    df_present['Category'] = df_present['Resistance_Gene'].map(category_map)
    df_present['Resistance_Mechanism'] = df_present['Resistance_Gene'].map(mechanism_map)
    df_present['Drug_Class'] = df_present['Resistance_Gene'].map(drug_class_map)
    
    # Fill any potential missing annotations with "Unknown"
    df_present['Resistance_Mechanism'] = df_present['Resistance_Mechanism'].fillna('Unknown Mechanism')
    df_present['Drug_Class'] = df_present['Drug_Class'].fillna('Unknown Drug Class')

    # Reorder columns for the final report
    final_df = df_present[[
        'Genome', 'Resistance_Gene', 'Identity_Percentage', 
        'Category', 'Resistance_Mechanism', 'Drug_Class'
    ]]
    
    return final_df.sort_values(by=['Genome', 'Resistance_Gene']).reset_index(drop=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyzes PanViTa (-megares) results to identify resistance genes, their identity, "
                    "category (Core, Accessory, Exclusive), resistance mechanism, and drug class. "
                    "Generates CSV, TXT, and Excel reports in the current directory.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Path to the results folder generated by PanViTa (e.g., 'Results_megares_...')."
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Path to the 'DB' folder containing the PanViTa databases (e.g., './DB')."
    )
    
    args = parser.parse_args()
    
    # Define Output Filenames 
    CSV_OUTPUT_FILENAME = "megares_resistance_report.csv"
    TXT_OUTPUT_FILENAME = "megares_resistance_report.txt"
    EXCEL_OUTPUT_FILENAME = "megares_resistance_report.xlsx"
    
    # Build the gene -> mechanism and gene -> drug_class maps from the FASTA file
    resistance_mechanism_map, drug_class_map = build_megares_annotation_map(args.db)
    
    # Find the necessary MEGARes result files
    gene_count_csv, matrix_csv = find_megares_result_files(args.results)
    
    # Get total number of genomes from the matrix file
    total_genomes = len(pd.read_csv(matrix_csv, sep=';').index)
    print(f"Found {total_genomes} genomes in the analysis.")
    
    # Create the gene -> category map (Core, Accessory, Exclusive)
    gene_category_map = create_gene_category_map(gene_count_csv, total_genomes)
    
    # Process all data to create the final, detailed report
    final_report_df = process_megares_data(
        matrix_csv, resistance_mechanism_map, drug_class_map, gene_category_map
    )
    
    # Save the results to various formats and display a summary
    if not final_report_df.empty:
        # Save to CSV and Excel
        final_report_df.to_csv(CSV_OUTPUT_FILENAME, index=False)
        final_report_df.to_excel(EXCEL_OUTPUT_FILENAME, index=False, sheet_name='MEGARes Resistance Report')
        
        # Create summaries for the text report
        summary_mech = final_report_df.groupby(['Category', 'Resistance_Mechanism']).size().reset_index(name='Count')
        summary_drug = final_report_df.groupby(['Category', 'Drug_Class']).size().reset_index(name='Count')

        # Save to TXT with detailed data and summaries
        with open(TXT_OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            f.write("--- Detailed MEGARes Resistance Gene Report ---\n\n")
            f.write(final_report_df.to_string())
            f.write("\n\n\n--- Summary by Category and Resistance Mechanism ---\n\n")
            f.write(summary_mech.to_string())
            f.write("\n\n\n--- Summary by Category and Drug Class ---\n\n")
            f.write(summary_drug.to_string())

        print("\n--- Final Report (Sample) ---")
        print(final_report_df.head(10).to_string())
        
        print("\n--- Summary by Category ---")
        print(final_report_df['Category'].value_counts().to_string())

        print(f"\n Analysis complete! Reports saved to:")
        print(f"  - Excel: {os.path.abspath(EXCEL_OUTPUT_FILENAME)}")
        print(f"  - CSV:   {os.path.abspath(CSV_OUTPUT_FILENAME)}")
        print(f"  - TXT:   {os.path.abspath(TXT_OUTPUT_FILENAME)}")
    else:
        print("\nNo resistance genes with identity > 0 were found in the provided results.")
