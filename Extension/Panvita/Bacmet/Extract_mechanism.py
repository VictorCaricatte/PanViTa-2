import os
import argparse
import pandas as pd
import glob
from typing import Dict, List, Tuple

def build_bacmet_annotation_map(db_directory: str) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Parses the bacmet_2.txt file to create dictionaries mapping each gene to its
    associated compounds and specifically to heavy metals.

    Args:
        db_directory: The path to PanViTa's 'DB' folder.

    Returns:
        A tuple containing two dictionaries:
        1. A map from gene name to a list of all its associated compounds.
        2. A map from gene name to a list of its associated heavy metals.
    """
    bacmet_tsv_path = os.path.join(db_directory, 'bacmet_2.txt')
    if not os.path.exists(bacmet_tsv_path):
        print(f"ERROR: BacMet annotation file not found at: {bacmet_tsv_path}")
        print("Please provide the correct path to PanViTa's 'DB' folder using the --db argument.")
        exit(1)

    print(f"Building BacMet annotation map from {bacmet_tsv_path}...")
    
    compounds_map = {}
    heavy_metals_map = {}

    try:
        df_bacmet = pd.read_csv(bacmet_tsv_path, sep='\t')
        
        for _, row in df_bacmet.iterrows():
            gene_name = row['Gene_name']
            compounds_str = str(row['Compound']) if pd.notna(row['Compound']) else ''

            # Compounds can be a comma-separated list
            all_compounds = [c.strip() for c in compounds_str.split(',') if c.strip()]
            
            # Identify heavy metals using the heuristic that they contain parentheses, e.g., "Copper (Cu)"
            heavy_metals = [c for c in all_compounds if '(' in c and '[' not in c]

            if gene_name not in compounds_map:
                compounds_map[gene_name] = []
            compounds_map[gene_name].extend(all_compounds)

            if heavy_metals:
                if gene_name not in heavy_metals_map:
                    heavy_metals_map[gene_name] = []
                heavy_metals_map[gene_name].extend(heavy_metals)

    except Exception as e:
        print(f"ERROR: Failed to read or process {bacmet_tsv_path}. Error: {e}")
        exit(1)

    print(f"Map built successfully. {len(compounds_map)} genes mapped to compounds.")
    return compounds_map, heavy_metals_map

def find_bacmet_result_files(results_directory: str) -> Tuple[str, str]:
    """
    Finds the necessary BacMet result files within the PanViTa results folder.
    
    Args:
        results_directory: Path to the PanViTa results folder (e.g., Results_bacmet_...).
        
    Returns:
        A tuple containing the paths to the gene_count file and the matrix file.
    """
    if not os.path.isdir(results_directory):
        print(f"ERROR: Results directory '{results_directory}' not found.")
        exit(1)
        
    gene_count_files = glob.glob(os.path.join(results_directory, 'bacmet_gene_count*.csv'))
    matrix_files = glob.glob(os.path.join(results_directory, 'matriz_bacmet*.csv'))
    
    if not gene_count_files:
        print(f"ERROR: No 'bacmet_gene_count*.csv' file found in '{results_directory}'.")
        exit(1)
    if not matrix_files:
        print(f"ERROR: No 'matriz_bacmet*.csv' file found in '{results_directory}'.")
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
        gene_count_file: Path to the bacmet_gene_count.csv file.
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

def process_bacmet_data(matrix_file: str, compounds_map: Dict[str, List[str]], heavy_metals_map: Dict[str, List[str]], category_map: Dict[str, str]) -> pd.DataFrame:
    """
    Processes the PanViTa identity matrix for BacMet to create a detailed report.

    Args:
        matrix_file: Path to the matriz_bacmet.csv file.
        compounds_map: Dictionary mapping genes to a list of all compounds.
        heavy_metals_map: Dictionary mapping genes to a list of heavy metals.
        category_map: Dictionary mapping genes to categories.

    Returns:
        A pandas DataFrame with the detailed results.
    """
    print("Processing identity matrix to extract detailed results...")
    df_matrix = pd.read_csv(matrix_file, sep=';', index_col='Strains')
    
    df_long = df_matrix.melt(ignore_index=False, var_name='Resistance_Gene', value_name='Identity_Percentage').reset_index()
    
    df_present = df_long[df_long['Identity_Percentage'] > 0].copy()
    df_present.rename(columns={'Strains': 'Genome'}, inplace=True)
    
    # Map the annotations. The result of the map will be a list or None.
    df_present['Category'] = df_present['Resistance_Gene'].map(category_map)
    df_present['Associated_Compounds'] = df_present['Resistance_Gene'].map(compounds_map)
    df_present['Heavy_Metals'] = df_present['Resistance_Gene'].map(heavy_metals_map)

    # Convert lists to a clean, comma-separated string for the final report
    df_present['Associated_Compounds'] = df_present['Associated_Compounds'].apply(
        lambda x: ', '.join(sorted(list(set(x)))) if isinstance(x, list) else ''
    )
    df_present['Heavy_Metals'] = df_present['Heavy_Metals'].apply(
        lambda x: ', '.join(sorted(list(set(x)))) if isinstance(x, list) else ''
    )
    
    # Reorder columns for clarity
    final_df = df_present[[
        'Genome', 'Resistance_Gene', 'Identity_Percentage', 
        'Category', 'Associated_Compounds', 'Heavy_Metals'
    ]]
    
    return final_df.sort_values(by=['Genome', 'Resistance_Gene']).reset_index(drop=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyzes PanViTa (-bacmet) results to identify resistance genes, their identity, "
                    "category (Core, Accessory, Exclusive), associated compounds, and heavy metals. "
                    "Generates CSV, TXT, and Excel reports in the current directory.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Path to the results folder generated by PanViTa (e.g., 'Results_bacmet_...')."
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Path to the 'DB' folder containing the PanViTa databases (e.g., './DB')."
    )
    
    args = parser.parse_args()
    
    # Define Output Filenames 
    CSV_OUTPUT_FILENAME = "bacmet_resistance_report.csv"
    TXT_OUTPUT_FILENAME = "bacmet_resistance_report.txt"
    EXCEL_OUTPUT_FILENAME = "bacmet_resistance_report.xlsx"
    
    # Build the gene -> compounds and gene -> heavy_metals maps
    compounds_map, heavy_metals_map = build_bacmet_annotation_map(args.db)
    
    # Find the necessary BacMet result files
    gene_count_csv, matrix_csv = find_bacmet_result_files(args.results)
    
    # Get total number of genomes from the matrix file
    total_genomes = len(pd.read_csv(matrix_csv, sep=';').index)
    print(f"Found {total_genomes} genomes in the analysis.")
    
    # Create the gene -> category map (Core, Accessory, Exclusive)
    gene_category_map = create_gene_category_map(gene_count_csv, total_genomes)
    
    # Process all data to create the final, detailed report
    final_report_df = process_bacmet_data(
        matrix_csv, compounds_map, heavy_metals_map, gene_category_map
    )
    
    # Save the results and display a summary
    if not final_report_df.empty:
        # Save to CSV and Excel
        final_report_df.to_csv(CSV_OUTPUT_FILENAME, index=False)
        final_report_df.to_excel(EXCEL_OUTPUT_FILENAME, index=False, sheet_name='BacMet Resistance Report')
        
        # Create summaries for the text report
        summary_category = final_report_df['Category'].value_counts().to_frame(name='Gene Count')
        
        # Create a summary of heavy metals found
        heavy_metals_flat_list = final_report_df['Heavy_Metals'].str.split(', ').explode()
        summary_metals = heavy_metals_flat_list[heavy_metals_flat_list != ''].value_counts().to_frame(name='Gene Occurrences')

        # Save to TXT with detailed data and summaries
        with open(TXT_OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            f.write("--- Detailed BacMet Resistance Gene Report ---\n\n")
            f.write(final_report_df.to_string())
            f.write("\n\n\n--- Summary by Gene Category ---\n\n")
            f.write(summary_category.to_string())
            f.write("\n\n\n--- Summary of Heavy Metal Associated Genes ---\n\n")
            if not summary_metals.empty:
                f.write(summary_metals.to_string())
            else:
                f.write("No heavy metal-associated genes were found.")

        print("\n--- Final Report (Sample) ---")
        print(final_report_df.head(10).to_string())
        
        print("\n--- Summary by Category ---")
        print(summary_category.to_string())
        
        print(f"\n Analysis complete! Reports saved to:")
        print(f"  - Excel: {os.path.abspath(EXCEL_OUTPUT_FILENAME)}")
        print(f"  - CSV:   {os.path.abspath(CSV_OUTPUT_FILENAME)}")
        print(f"  - TXT:   {os.path.abspath(TXT_OUTPUT_FILENAME)}")
    else:
        print("\nNo resistance genes with identity > 0 were found in the provided results.")
