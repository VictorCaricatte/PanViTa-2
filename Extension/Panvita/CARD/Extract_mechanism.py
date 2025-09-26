import os
import argparse
import pandas as pd
import glob
from typing import Dict, Tuple

def build_card_annotation_map(db_directory: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Parses the aro_index.tsv file from the CARD database to create dictionaries
    mapping each gene to its resistance mechanism and drug class.

    Args:
        db_directory: The path to PanViTa's 'DB' folder.

    Returns:
        A tuple containing two dictionaries:
        1. A map from gene name to its resistance mechanism.
        2. A map from gene name to its drug class.
    """
    card_tsv_path = os.path.join(db_directory, 'aro_index.tsv')
    if not os.path.exists(card_tsv_path):
        print(f"ERROR: CARD annotation file not found at: {card_tsv_path}")
        print("Please provide the correct path to PanViTa's 'DB' folder using the --db argument.")
        exit(1)

    print(f"Building CARD annotation map from {card_tsv_path}...")
    
    try:
        df_aro = pd.read_csv(card_tsv_path, sep='\t')
        
        # Fill any missing values with "Unknown" to prevent errors
        df_aro['Resistance Mechanism'] = df_aro['Resistance Mechanism'].fillna('Unknown Mechanism')
        df_aro['Drug Class'] = df_aro['Drug Class'].fillna('Unknown Drug Class')

        # Create dictionaries directly from the pandas Series for efficiency
        # Key: ARO Name (e.g., 'adeF'), Value: Resistance Mechanism or Drug Class
        mechanism_map = pd.Series(
            df_aro['Resistance Mechanism'].values, index=df_aro['ARO Name']).to_dict()
        drug_class_map = pd.Series(
            df_aro['Drug Class'].values, index=df_aro['ARO Name']).to_dict()

    except Exception as e:
        print(f"ERROR: Failed to read or process {card_tsv_path}. Error: {e}")
        exit(1)

    print(f"Map built successfully. {len(mechanism_map)} resistance genes mapped.")
    return mechanism_map, drug_class_map

def find_card_result_files(results_directory: str) -> Tuple[str, str]:
    """
    Finds the necessary CARD result files within the PanViTa results folder.
    
    Args:
        results_directory: Path to the PanViTa results folder (e.g., Results_card_...).
        
    Returns:
        A tuple containing the paths to the gene_count file and the matrix file.
    """
    if not os.path.isdir(results_directory):
        print(f"ERROR: Results directory '{results_directory}' not found.")
        exit(1)
        
    gene_count_files = glob.glob(os.path.join(results_directory, 'card_gene_count*.csv'))
    matrix_files = glob.glob(os.path.join(results_directory, 'matriz_card*.csv'))
    
    if not gene_count_files:
        print(f"ERROR: No 'card_gene_count*.csv' file found in '{results_directory}'.")
        exit(1)
    if not matrix_files:
        print(f"ERROR: No 'matriz_card*.csv' file found in '{results_directory}'.")
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
        gene_count_file: Path to the card_gene_count.csv file.
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
        
        # Determine category based on presence across genomes
        if presence == total_genomes:
            gene_categories[gene] = 'Core'
        elif presence == 1:
            gene_categories[gene] = 'Exclusive'
        else:
            gene_categories[gene] = 'Accessory'
            
    print(f"{len(gene_categories)} genes categorized.")
    return gene_categories

def process_card_data(matrix_file: str, mechanism_map: Dict[str, str], drug_class_map: Dict[str, str], category_map: Dict[str, str]) -> pd.DataFrame:
    """
    Processes the PanViTa identity matrix for CARD to create a detailed report.

    Args:
        matrix_file: Path to the matriz_card.csv file.
        mechanism_map: Dictionary mapping genes to resistance mechanisms.
        drug_class_map: Dictionary mapping genes to drug classes.
        category_map: Dictionary mapping genes to categories.

    Returns:
        A pandas DataFrame with the detailed results.
    """
    print("Processing identity matrix to extract detailed results...")
    df_matrix = pd.read_csv(matrix_file, sep=';', index_col='Strains')
    
    # Unpivot the matrix from wide to long format for easier processing
    df_long = df_matrix.melt(ignore_index=False, var_name='Resistance_Gene', value_name='Identity_Percentage').reset_index()
    
    # Filter out genes that are not present (identity > 0)
    df_present = df_long[df_long['Identity_Percentage'] > 0].copy()
    df_present.rename(columns={'Strains': 'Genome'}, inplace=True)
    
    # Add the Category, Mechanism, and Drug Class columns using the maps
    df_present['Category'] = df_present['Resistance_Gene'].map(category_map)
    df_present['Resistance_Mechanism'] = df_present['Resistance_Gene'].map(mechanism_map)
    df_present['Drug_Class'] = df_present['Resistance_Gene'].map(drug_class_map)
    
    # Reorder columns for the final report
    final_df = df_present[[
        'Genome', 'Resistance_Gene', 'Identity_Percentage', 
        'Category', 'Resistance_Mechanism', 'Drug_Class'
    ]]
    
    return final_df.sort_values(by=['Genome', 'Resistance_Gene']).reset_index(drop=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyzes PanViTa (-card) results to identify resistance genes, their identity, "
                    "category (Core, Accessory, Exclusive), resistance mechanism, and drug class. "
                    "Generates CSV, TXT, and Excel reports in the current directory.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Path to the results folder generated by PanViTa (e.g., 'Results_card_...')."
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Path to the 'DB' folder containing the PanViTa databases (e.g., './DB')."
    )
    
    args = parser.parse_args()
    
    # Define Output Filenames 
    CSV_OUTPUT_FILENAME = "card_resistance_report.csv"
    TXT_OUTPUT_FILENAME = "card_resistance_report.txt"
    EXCEL_OUTPUT_FILENAME = "card_resistance_report.xlsx"
    
    # Build the gene -> mechanism and gene -> drug_class maps from aro_index.tsv
    resistance_mechanism_map, drug_class_map = build_card_annotation_map(args.db)
    
    # Find the necessary CARD result files
    gene_count_csv, matrix_csv = find_card_result_files(args.results)
    
    # Get total number of genomes from the matrix file
    total_genomes = len(pd.read_csv(matrix_csv, sep=';').index)
    print(f"Found {total_genomes} genomes in the analysis.")
    
    # Create the gene -> category map (Core, Accessory, Exclusive)
    gene_category_map = create_gene_category_map(gene_count_csv, total_genomes)
    
    # Process all data to create the final, detailed report
    final_report_df = process_card_data(
        matrix_csv, resistance_mechanism_map, drug_class_map, gene_category_map
    )
    
    # Save the results to various formats and display a summary
    if not final_report_df.empty:
        # Save to CSV
        final_report_df.to_csv(CSV_OUTPUT_FILENAME, index=False)
        
        # Save to Excel
        final_report_df.to_excel(EXCEL_OUTPUT_FILENAME, index=False, sheet_name='CARD Resistance Report')
        
        # Create summaries for the text report
        summary_mech = final_report_df.groupby(['Category', 'Resistance_Mechanism']).size().reset_index(name='Count')
        summary_drug = final_report_df.groupby(['Category', 'Drug_Class']).size().reset_index(name='Count')

        # Save to TXT with detailed data and summaries
        with open(TXT_OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            f.write("--- Detailed CARD Resistance Gene Report ---\n\n")
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
