"""
Engine principal do PanViTa - Lógica de análise desacoplada das interfaces
"""

import datetime
import os
import shutil
import sys
import pandas as pd
from datetime import datetime as dt

from .data_processor import DataProcessor
from .processor import GBKProcessor
from .visualization import Visualization
from .config import PanViTaConfig
from .downloader import NCBIDownloader
from .dependencies import DependencyManager
from .databases import DatabaseManager
from .aligner import Aligner


class PanViTaEngine:
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

    def run(self):
        """Main execution method for PanViTa"""
        self._handle_help_and_version()
        
        # Setup dependencies and databases
        dependency_manager = DependencyManager()
        self.dppath = dependency_manager.check_dependencies()
        
        # Determine which aligner(s) to use
        aligner = Aligner(self.dppath)
        aligner_types, aligner_exes, aligner_names = self._determine_aligners(aligner)
        
        if aligner_types is None:
            print("ERROR: No aligners available. Exiting.")
            exit(1)

        # Initialize variables
        self._setup_databases_and_dicts(aligner_exes)
        
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
            return
            
        # Extract and save positions
        self._extract_and_save_positions()
        
        # Extract and save proteins
        self._extract_and_save_proteins()
        
        # Align and mine
        self._align_and_mine(aligner_types, aligner_exes, aligner_names)
        
        # Run main analysis workflow
        self._run_analysis_workflow(aligner_types, aligner_names)
        
        # Cleanup
        self._remove_intermediate_files()
        
        # Final messages
        self._print_final_messages()
        
    def _handle_help_and_version(self):
        """Handle version and help commands"""
        if ("-v" in sys.argv) or ("-version" in sys.argv):
            print("-----------------------------------------------")
            print("PanViTa - Pan Virulence and resisTance Analysis")
            print("https://doi.org/10.3389/fbinf.2023.1070406")
            print("version", PanViTaConfig.VERSION)
            print("-----------------------------------------------")
            exit()

        if (("-card" not in sys.argv) and ("-bacmet" not in sys.argv) and ("-vfdb" not in sys.argv) and 
            ("-megares" not in sys.argv) and ("-u" not in sys.argv) and ("-update" not in sys.argv) and
            ("-g" not in sys.argv) and ("-a" not in sys.argv) and ("-m" not in sys.argv) and 
            ("-b" not in sys.argv)) or ("-h" in sys.argv) or ("-help" in sys.argv):
            self._print_help()
            exit()

        print('''
Hello user!

This script has the function of comparing multiple genomes against previously selected databases.
The result consists of a clustermap and a presence matrix.

Contact: dlnrodrigues@ufmg.br - victorsc@ufmg.br - vinicius.oliveira.1444802@sga.pucminas.br

Let's continue with your analysis.''')

    def _print_help(self):
        """Print help information"""
        print('''
Hello user!

PanViTa has the function of comparing multiple genomes against previously selected databases.
The result consists of a clustermap and a presence matrix.

As input use GBF or GBK files derived from Prokka or available on NCBI.
WARNING! Files from NCBI MUST have .gbf or .gbff extension.

USAGE:
python3 ''' + sys.argv[0] + ''' -card -vfdb -bacmet -megares files.gbk\n
Databases:
-bacmet\tAntibacterial Biocide and Metal Resistance Genes Database
-card\tComprehensive Antibiotic Resistance Database
-megares\tMEGARes Antimicrobial Resistance Database
-vfdb\tVirulence Factor Database

Parameters:
-update\tUpdate databases and dependences
-u\tSame as -update
-help\tPrint this help
-h\tSame as -help
-v\tPrint version and exit
-keep\tMaintains the protein sequences used, as well as the CDS position files
-k\tSame as -keep
-i\tMinimum identity to infer presence (default = 70)
-c\tMinimum coverage to infer presence (default = 70)
-d\tForce to use DIAMOND from system
-diamond\tForce to use DIAMOND only for alignments
-blast\tForce to use BLAST only for alignments
-both\tUse both DIAMOND and BLAST for alignments
-pdf\tFigures will be saved as PDF (default)
-png\tFigures will be saved as PNG (WARNING! High memory consumption)
-save-genes\tSave found genes in individual .faa files for each genome
-g\tDownload the genomes fasta files (require CSV table from NCBI)
-a\tDownload and annote the genomes using PROKKA pipeline (require CSV table from NCBI)
-b\tDownload the genome GenBank files (require CSV table from NCBI)
-s\tKeep the locus_tag as same as the strain (require -b)
-m\tGet the metadata from BioSample IDs (require CSV table from NCBI)

Note: If no aligner is specified, the program will prompt you to choose between DIAMOND, BLAST, or both.

Contact: dlnrodrigues@ufmg.br
        ''')

    def _determine_aligners(self, aligner):
        """Determine which aligner(s) to use based on command line arguments"""
        if "-diamond" in sys.argv:
            aligner_types = ["diamond"]
            diamond_exe = os.path.join(self.dppath, "diamond.exe" if PanViTaConfig.is_windows() else "diamond")
            if "-d" in sys.argv:
                if isinstance(shutil.which("diamond-aligner"), str):
                    diamond_exe = shutil.which("diamond-aligner")
                elif isinstance(shutil.which("diamond"), str):
                    diamond_exe = shutil.which("diamond")
                else:
                    erro_string = "\nWe couldn't locate DIAMOND on your system.\nWe'll try to use the default option.\nPlease verify the alignment outputs.\n"
                    print(erro_string)
                    self.erro.append(erro_string)
            aligner_exes = [diamond_exe]
            aligner_names = ["DIAMOND"]
        elif "-blast" in sys.argv:
            aligner_types = ["blast"]
            blastp_exe = os.path.join(self.dppath, "blastp.exe" if PanViTaConfig.is_windows() else "blastp")
            aligner_exes = [blastp_exe]
            aligner_names = ["BLAST"]
        elif "-both" in sys.argv:
            aligner_types = ["diamond", "blast"]
            diamond_exe = os.path.join(self.dppath, "diamond.exe" if PanViTaConfig.is_windows() else "diamond")
            blastp_exe = os.path.join(self.dppath, "blastp.exe" if PanViTaConfig.is_windows() else "blastp")
            if "-d" in sys.argv:
                if isinstance(shutil.which("diamond-aligner"), str):
                    diamond_exe = shutil.which("diamond-aligner")
                elif isinstance(shutil.which("diamond"), str):
                    diamond_exe = shutil.which("diamond")
                else:
                    erro_string = "\nWe couldn't locate DIAMOND on your system.\nWe'll try to use the default option.\nPlease verify the alignment outputs.\n"
                    print(erro_string)
                    self.erro.append(erro_string)
            aligner_exes = [diamond_exe, blastp_exe]
            aligner_names = ["DIAMOND", "BLAST"]
        else:
            # Let user choose interactively
            return aligner.choose_aligner()
            
        return aligner_types, aligner_exes, aligner_names

    def _setup_databases_and_dicts(self, aligner_exes):
        """Setup databases and dictionaries if needed"""
        if "-a" in sys.argv or "-b" in sys.argv or "-g" in sys.argv or "-m" in sys.argv:
            db_manager = DatabaseManager(self.dppath)
            self.dbpath = db_manager.check_databases(aligner_exes[0])
            
            for i in sys.argv:
                if i.endswith(".csv"):
                    table = i
                    
            df = pd.read_csv(table, sep=',')
            species = df["#Organism Name"].tolist()
            self.strains = df["Strain"].tolist()
            biosample = df["BioSample"].tolist()
            size = df["Size(Mb)"].tolist()
            GC = df["GC%"].tolist()
            refseq = df["RefSeq FTP"].tolist()
            genbank = df["GenBank FTP"].tolist()
            data = df["Release Date"].tolist()
            self.dic = {}
            self.dic2 = {}
            self.dic3 = {}
            
            ind = 0
            while ind in range(0, len(self.strains)):
                if "-b" in sys.argv:
                    self.dic[biosample[ind]] = (
                        species[ind], refseq[ind], genbank[ind], self.strains[ind], 
                        size[ind], GC[ind], data[ind])
                if "-m" in sys.argv:
                    self.dic2[biosample[ind]] = (
                        species[ind], refseq[ind], genbank[ind], self.strains[ind], 
                        size[ind], GC[ind], data[ind])
                if "-a" in sys.argv or "-g" in sys.argv:
                    self.dic3[biosample[ind]] = (
                        species[ind], refseq[ind], genbank[ind], self.strains[ind], 
                        size[ind], GC[ind], data[ind])
                ind = ind + 1
        else:
            # If no CSV operations, still need to setup databases
            db_manager = DatabaseManager(self.dppath)
            self.dbpath = db_manager.check_databases(aligner_exes[0])

    def _download_genbank_files(self):
        """Download GenBank files from NCBI"""
        downloader = NCBIDownloader(self.dic)
        self.gbff = downloader.get_ncbi_gbf()
        self.erro.extend(downloader.erro)

    def _download_fasta_files(self):
        """Download FASTA files from NCBI and optionally annotate with PROKKA"""
        downloader = NCBIDownloader(self.dic3)
        self.pkgbf = downloader.get_ncbi_fna()
        self.erro.extend(downloader.erro)

    def _process_files_and_parameters(self):
        """Process input files and parameters"""
        print("Separating files")
        self.files = []
        for i in sys.argv:
            if i.endswith(".gbk") or i.endswith(".gbf") or i.endswith(".gbff"):
                self.files.append(i)
                
        for i in sys.argv:
            if i.endswith(".csv"):
                prokaryotes = i
                break
                
        if "-a" in sys.argv and "-b" not in sys.argv:
            if self.pkgbf and self.pkgbf[0] != "":
                for i in self.pkgbf:
                    self.files.append(i)
        elif "-b" in sys.argv:
            if self.gbff:
                for i in self.gbff:
                    self.files.append(i)
                    
        print("Separating parameters")
        self.parameters = []
        for i in sys.argv:
            if i in ["-card", "-bacmet", "-vfdb", "-megares"]:
                self.parameters.append(i)

    def _organize_downloaded_files(self):
        """Organize downloaded files if no analysis parameters"""
        if "-b" in sys.argv:
            pasta = "GenBank_" + dt.now().strftime("%d-%m-%Y_%H-%M-%S")
            os.mkdir(pasta)
            for i in self.gbff:
                try:
                    shutil.move(i, pasta)
                except BaseException:
                    erro_string = "It was not possible to move the file " + str(i) + " to the final directory.\nPlease, check the output path.\n"
                    self.erro.append(erro_string)
                    print(erro_string)
        
        if len(self.erro) > 0:
            final_erro = self._write_error_file()
            print("\nNumber of errors reported: " + str(len(self.erro)))
            print("Please check the " + str(final_erro) + " file.\n")
        else:
            print("\nNo error reported!")
        print("\nThat's all folks...\nThank you so much for using this program!\n")
        exit()

    def _extract_and_save_positions(self):
        """Extract and save CDS positions from GenBank files"""
        print("\nExtracting CDS positions from GenBank files\n")
        if self.strains is None:
            self.strains = []
            
        pos = {}
        tempfiles = []
        
        for i in self.files:
            try:
                k = GBKProcessor.extract_positions(i)
            except BaseException:
                try:
                    f = i.replace(".gbff", ".gbk")
                    k = GBKProcessor.extract_positions(f)
                except BaseException:
                    try:
                        f = i.replace(".gbf", ".gbk")
                        k = GBKProcessor.extract_positions(f)
                    except BaseException:
                        if os.path.exists(i):
                            erro_string = "\n**WARNING**\nIt was not possible to handle the file " + str(i) + "...\nIt will be skipped.\nPlease verify the input format.\n"
                            print(erro_string)
                            self.erro.append(erro_string)
                            continue
                        else:
                            erro_string = "\n**WARNING**\nIt was not possible to handle the file " + str(i) + "...\nIt will be skipped.\\Please verify the absolute path of the files.\n"
                            print(erro_string)
                            self.erro.append(erro_string)
                            continue
                            
            if len(k) < 10:
                erro_string = "\n**WARNING**\nThe file " + str(i) + " seems to be empty...\nIt will be skipped.\nPlease verify the input format.\n"
                print(erro_string)
                self.erro.append(erro_string)
                continue
                
            print("The positions of the " + i + " file have been extracted")
            tempfiles.append(i)
            strain = str(i)[::-1].split('/')[0][::-1].replace(".gbk", "").replace(".gbff", "").replace(".gbf", "")
            self.strains.append(strain)
            pos[i] = k
            
        self.files = tempfiles
        del tempfiles
        
        if "Positions_1" not in os.listdir():
            os.mkdir("Positions_1")
        else:
            shutil.rmtree("Positions_1")
            os.mkdir("Positions_1")
            
        for i in self.strains:
            for j in pos.keys():
                tempName = j[::-1].split("/")[0][::-1].replace(".gbk", "").replace(".gbff", "").replace(".gbf", "")
                if i == tempName:
                    with open(os.path.join("Positions_1", i + ".tab"), 'w') as positions:
                        for k in pos[j].keys():
                            positions.write(k + '\t')
                            positions.write(pos[j][k])
                            positions.write('\n')

    def _extract_and_save_proteins(self):
        """Extract and save protein sequences from GenBank files"""
        if "faa" not in os.listdir():
            os.mkdir("faa")
        else:
            shutil.rmtree("faa")
            os.mkdir("faa")
            
        print("\nExtracting protein sequences from GenBank files\n")
        
        for i in self.files:
            for j in self.strains:
                tempName = i[::-1].split("/")[0][::-1].replace(".gbk", "").replace(".gbff", "").replace(".gbf", "")
                if j == tempName:
                    print("Extracting " + j)
                    with open(os.path.join("faa", j + ".faa"), 'w') as faa:
                        try:
                            k = GBKProcessor.extract_faa(i)
                        except BaseException:
                            try:
                                temp = i.replace(".gbff", ".gbk")
                                k = GBKProcessor.extract_faa(temp)
                            except BaseException:
                                try:
                                    temp = i.replace(".gbf", ".gbk")
                                    k = GBKProcessor.extract_faa(temp)
                                except BaseException:
                                    print(f"Error extracting proteins from {i}")
                                    k = []
                        for l in k:
                            faa.write(l)

    def _align_and_mine(self, aligner_types, aligner_exes, aligner_names):
        """Perform alignments and mining for each database"""
        for p in self.parameters:
            outputs = []
            current_files = os.listdir()
            
            # Create specific directories for each database and aligner combination
            db_name = p[1:]  # Remove the '-' from parameter name
            
            # Loop through each aligner
            for aligner_type, aligner_exe, aligner_name in zip(aligner_types, aligner_exes, aligner_names):
                # Create directories with aligner suffix if using multiple aligners
                if len(aligner_types) > 1:
                    tabular1_dir = f"Tabular_1_{db_name}_{aligner_name.lower()}"
                    tabular2_dir = f"Tabular_2_{db_name}_{aligner_name.lower()}"
                else:
                    tabular1_dir = f"Tabular_1_{db_name}"
                    tabular2_dir = f"Tabular_2_{db_name}"
                
                # Align
                if tabular1_dir not in os.listdir():
                    os.mkdir(tabular1_dir)
                    outputs.append(tabular1_dir)
                else:
                    shutil.rmtree(tabular1_dir)
                    os.mkdir(tabular1_dir)
                    outputs.append(tabular1_dir)
                    
                # Select database path based on aligner type
                if "-card" == p:
                    b = os.path.join(self.dbpath, "card_protein_homolog_model")
                elif "-vfdb" == p:
                    b = os.path.join(self.dbpath, "vfdb_core")
                elif "-bacmet" == p:
                    b = os.path.join(self.dbpath, "bacmet_2")
                elif "-megares" == p:
                    b = os.path.join(self.dbpath, "megares_v3")
                    
                print(f"\nStarting {aligner_name} alignments for {db_name.upper()}\n")
                aligner = Aligner(self.dppath)
                
                for i in self.strains:
                    a = os.path.join("faa", i + ".faa")
                    c = os.path.join(tabular1_dir, i + ".tab")
                    
                    # Determine database type for alignment
                    if "-megares" == p:
                        db_type = "nucleotide"  # MEGARes contains nucleotide sequences
                    else:
                        db_type = "protein"     # CARD, VFDB, BacMet contain protein sequences
                    
                    aligner.align(a, b, c, aligner_type, db_type)
                    
                # Mine
                if tabular2_dir not in os.listdir():
                    os.mkdir(tabular2_dir)
                    outputs.append(tabular2_dir)
                else:
                    shutil.rmtree(tabular2_dir)
                    os.mkdir(tabular2_dir)
                    outputs.append(tabular2_dir)
                    
                print(f"\nMining {aligner_name} alignments for {db_name.upper()}...\n")
                for i in os.listdir(tabular1_dir):
                    DataProcessor.blastmining_specific(i, tabular1_dir, tabular2_dir)

    def _run_analysis_workflow(self, aligner_types, aligner_names):
        """Run the main analysis workflow for each database"""
        for p in self.parameters:
            db_name = p[1:]  

            # Extract keys and handle MEGARes special case with mechanisms mapping
            if p == "-megares":
                comp, genes_comp, mechanisms_comp = DataProcessor.extract_keys(p, self.dbpath)
                self.genes_comp = genes_comp
                self.mechanisms_comp = mechanisms_comp  # Store mechanisms for MEGARes
            else:
                comp, genes_comp = DataProcessor.extract_keys(p, self.dbpath)
                self.genes_comp = genes_comp
            
            # Check if we have multiple aligners by looking for directories with suffixes
            aligner_dirs = []
            for dir_name in os.listdir('.'):
                if dir_name.startswith(f"Tabular_2_{db_name}_"):
                    aligner_suffix = dir_name.replace(f"Tabular_2_{db_name}_", "")
                    aligner_dirs.append(aligner_suffix)
            
            # If no aligner-specific directories found, check for unified directory
            if not aligner_dirs and os.path.exists(f"Tabular_2_{db_name}"):
                aligner_dirs.append("")  # Empty suffix for unified directory
            
            if not aligner_dirs:
                print(f"Warning: No analysis directories found for {p}")
                continue
                
            # Process each aligner separately
            for aligner_suffix in aligner_dirs:
                outputs = []
                
                print(f"\nProcessing analysis for {p}{f' with {aligner_suffix}' if aligner_suffix else ''}...")
                
                # Extract keys for the current database
                if p == "-megares":
                    comp, genes_comp, mechanisms_comp = DataProcessor.extract_keys(p, self.dbpath)
                    self.mechanisms_comp = mechanisms_comp  # Store mechanisms for MEGARes
                else:
                    comp, genes_comp = DataProcessor.extract_keys(p, self.dbpath)
                
                self.genes_comp = genes_comp
                
                # Generate matrix
                titulo, dicl, totalgenes, found_genes_per_strain = Visualization.generate_matrix(p, outputs, comp, aligner_suffix)
                
                # Verify that the matrix file was created successfully
                if not os.path.exists(titulo):
                    erro_string = f"ERROR: Matrix file {titulo} was not created. Skipping analysis for {p}{f' with {aligner_suffix}' if aligner_suffix else ''}."
                    print(erro_string)
                    self.erro.append(erro_string)
                    continue
                
                # Check if the matrix file has content
                if os.path.getsize(titulo) == 0:
                    erro_string = f"ERROR: Matrix file {titulo} is empty. Skipping analysis for {p}{f' with {aligner_suffix}' if aligner_suffix else ''}."
                    print(erro_string)
                    self.erro.append(erro_string)
                    continue
                
                # Save found genes to individual .faa files if requested
                if "-save-genes" in sys.argv:
                    self._save_found_genes(found_genes_per_strain, p, aligner_suffix)
                
                # Generate positions files (only for the first aligner to avoid conflicts)
                if aligner_suffix == aligner_dirs[0]:
                    self._generate_positions_files(p, comp, aligner_suffix)
                
                # Load matrix for visualization
                try:
                    df = pd.read_csv(titulo, sep=';')
                    df = df.set_index('Strains')
                except Exception as e:
                    erro_string = f"ERROR: Could not read matrix file {titulo}: {str(e)}. Skipping analysis for {p}{f' with {aligner_suffix}' if aligner_suffix else ''}."
                    print(erro_string)
                    self.erro.append(erro_string)
                    continue
                
                # Generate heatmap
                Visualization.generate_heatmap(titulo, p, outputs, self.erro, aligner_suffix)
                Visualization.generate_clustermap(titulo, p, outputs, self.erro, aligner_suffix)
                Visualization.generate_scatterplot_heatmap(titulo, p, outputs, self.erro, aligner_suffix)
                Visualization.generate_joint_and_marginal_distributions(titulo, p, outputs, self.erro, aligner_suffix)
                
                # Process omics analysis
                lines = list(df.index.values)
                analysis_outputs = self._process_omics_analysis(df, lines, p, aligner_suffix)
                outputs.extend(analysis_outputs)
                
                # Organize results
                self._organize_results(outputs, p, aligner_suffix)

    def _save_found_genes(self, found_genes_per_strain, db_param, aligner_suffix=""):
        """Save found genes in individual .faa files for each genome"""
        print(f"\nSaving found genes to individual .faa files for {db_param}{f' ({aligner_suffix})' if aligner_suffix else ''}...")
        
        db_name = db_param[1:]  # Remove the '-' from parameter name
        
        # Create output directory
        if aligner_suffix:
            output_dir = f"Found_genes_{db_name}_{aligner_suffix}"
        else:
            output_dir = f"Found_genes_{db_name}"
            
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.mkdir(output_dir)
        
        # Read all .faa files to create a lookup dictionary
        faa_sequences = {}
        faa_dir = "faa"
        
        if not os.path.exists(faa_dir):
            print(f"Warning: {faa_dir} directory not found. Cannot extract gene sequences.")
            return
            
        # Load all sequences from faa files
        for strain_name, strain_genes in found_genes_per_strain.items():
            faa_file = os.path.join(faa_dir, strain_name + ".faa")
            
            if not os.path.exists(faa_file):
                print(f"Warning: {faa_file} not found. Skipping strain {strain_name}.")
                continue
                
            # Parse the .faa file to extract sequences
            strain_sequences = {}
            try:
                with open(faa_file, 'r') as f:
                    current_header = None
                    current_seq = []
                    
                    for line in f:
                        line = line.strip()
                        if line.startswith('>'):
                            # Save previous sequence if exists
                            if current_header and current_seq:
                                # Extract locus_tag from header (first part after >)
                                locus_tag = current_header.split()[0].replace('>', '')
                                strain_sequences[locus_tag] = {
                                    'header': current_header,
                                    'sequence': ''.join(current_seq)
                                }
                            
                            # Start new sequence
                            current_header = line
                            current_seq = []
                        else:
                            current_seq.append(line)
                    
                    # Save last sequence
                    if current_header and current_seq:
                        locus_tag = current_header.split()[0].replace('>', '')
                        strain_sequences[locus_tag] = {
                            'header': current_header,
                            'sequence': ''.join(current_seq)
                        }
                        
            except Exception as e:
                print(f"Error reading {faa_file}: {e}")
                continue
            
            # Create output file for this strain
            output_file = os.path.join(output_dir, f"{strain_name}_{db_name}_genes.faa")
            genes_saved = 0
            
            try:
                with open(output_file, 'w') as out:
                    for gene_name, locus_tags in strain_genes.items():
                        for locus_tag in locus_tags:
                            if locus_tag in strain_sequences:
                                # Write header with gene annotation
                                original_header = strain_sequences[locus_tag]['header']
                                # Add gene annotation to header
                                annotated_header = f"{original_header} | {db_name.upper()}_GENE:{gene_name}"
                                out.write(annotated_header + '\n')
                                
                                # Write sequence
                                sequence = strain_sequences[locus_tag]['sequence']
                                # Write sequence in lines of 80 characters
                                for i in range(0, len(sequence), 80):
                                    out.write(sequence[i:i+80] + '\n')
                                
                                genes_saved += 1
                            else:
                                print(f"Warning: Locus tag {locus_tag} not found in {strain_name}.faa")
                
                if genes_saved > 0:
                    print(f"  - {strain_name}: {genes_saved} genes saved to {output_file}")
                else:
                    # Remove empty file
                    os.remove(output_file)
                    print(f"  - {strain_name}: No genes found, file not created")
                    
            except Exception as e:
                print(f"Error writing to {output_file}: {e}")
        
        print(f"Found genes saved in directory: {output_dir}")

    def _generate_positions_files(self, db_param, comp, aligner_suffix=""):
        """Generate position files for genes"""
        if "Positions" not in os.listdir():
            os.mkdir("Positions")
        else:
            shutil.rmtree("Positions")
            os.mkdir("Positions")
            
        print(f"\nExtracting positions from specific factors for {db_param}{f' ({aligner_suffix})' if aligner_suffix else ''}...")
        
        for i in self.strains:
            pos = {}
            positions = os.path.join("Positions_1", i + ".tab")
            positions2 = os.path.join("Positions", i + ".tab")
            
            with open(positions, 'rt') as tab:
                arq = tab.readlines()
            
            for j in arq:
                line = j.split("\t")
                try:
                    pos[line[0]] = [line[1], line[2]]
                except BaseException:
                    pass
            
            # Determine the specific tabular directory for this database
            db_name = db_param[1:]
            if aligner_suffix:
                tabular_dir = f"Tabular_2_{db_name}_{aligner_suffix}"
            else:
                tabular_dir = f"Tabular_2_{db_name}"
                
            file_path = os.path.join(tabular_dir, i + ".tab")
            # Check if file exists before trying to read it
            if not os.path.exists(file_path):
                print(f"Warning: File {file_path} not found!")
                continue
                
            with open(file_path, 'rt') as tab:
                file_lines = tab.readlines()
            
            final = {}
            for j in file_lines:
                linha = j.split('\t')
                gene = None
                for k in comp.keys():
                    if k in linha[1]:
                        gene = comp[k]
                        break
                if gene and linha[0] in pos:
                    final[linha[0]] = gene, pos[linha[0]]
            
            with open(positions2, 'w') as out:
                for j in final.keys():
                    if "-card" == db_param:
                        color = "blue\n"
                    elif "-vfdb" == db_param:
                        color = "red\n"
                    elif "-bacmet" == db_param:
                        color = "green\n"
                    elif "-megares" == db_param:
                        color = "yellow\n"
                    else:
                        color = "black\n"
                    out.write(final[j][1][0] + '\t' + final[j][1][1].strip() + '\t' + final[j][0] + '\t' + color)

    def _process_omics_analysis(self, df, lines, db_param, aligner_suffix=""):
        """Process omics analysis and generate output files"""
        fileType = "pdf"
        if "-pdf" in sys.argv:
            fileType = "pdf"
        elif "-png" in sys.argv:
            fileType = "png"
        
        print("\nDoing presence analysis...")
        
        # Setup output files based on database type
        output_setup = self._setup_output_files(db_param, fileType, aligner_suffix)
        
        # Unpack based on actual length returned
        if len(output_setup) == 17:  # CARD and MEGARes case (17 elements: 7 base + 10 specific)
            outputs, t1, t2, t3, t4, l1, l2, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15 = output_setup
        elif len(output_setup) == 16:  # VFDB and BACMET case (16 elements: 7 base + 9 specific)
            outputs, t1, t2, t3, t4, l1, l2, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15 = output_setup + [None]
        else:  # Fallback for any other case
            outputs, t1, t2, t3, t4, l1, l2, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15 = output_setup + [None] * (17 - len(output_setup))
        
        t5 = t3.replace("csv", fileType)
        outputs.append(t5)
        
        # Per genes analysis - improved binary conversion
        df2 = df.copy()
        headers = list(df2.columns.values)
        
        # Remove unnamed columns first
        headers_to_remove = []
        for i in headers:
            if "Unnamed:" in i:
                headers_to_remove.append(i)
        
        for col in headers_to_remove:
            df2 = df2.drop(columns=[col])
        
        # Update headers after removing unnamed columns
        headers = list(df2.columns.values)
        
        # Convert to binary (presence/absence) data
        # Any non-zero value (including identity percentages) becomes 1
        df2_binary = df2.copy()
        for col in headers:
            df2_binary[col] = (df2[col] != 0).astype(int)
        
        with open(t1, "w") as count:
            count.write("Genes;Presence Number;Strains\n")
            
            for gene in headers:
                # Get list of strains where this gene is present
                present_strains = []
                for idx, strain in enumerate(df2_binary.index):
                    if df2_binary[gene].iloc[idx] == 1:
                        present_strains.append(str(strain))
                
                presence_count = len(present_strains)
                strains_str = ','.join(present_strains) if present_strains else ""
                count.write(f"{gene};{presence_count};{strains_str}\n")
        
        # Per strains analysis
        strain_list = list(df2_binary.index.values)
        with open(t2, "w") as count:
            count.write("Strains;Presence Number;Genes\n")
            dic = {}
            
            for strain in strain_list:
                # Get list of genes present in this strain
                present_genes = []
                for gene in headers:
                    if df2_binary.loc[strain, gene] == 1:
                        present_genes.append(gene)
                
                dic[strain] = present_genes
                genes_str = ','.join(present_genes) if present_genes else ""
                count.write(f"{strain};{len(present_genes)};{genes_str}\n")
        
        # PanOmic analysis - corrected to calculate cumulative pan and core genomes
        with open(t3, "w") as panomic:
            panomic.write("Strains;Core;Pan\n")
            
            # Get strain names in order
            strain_names = list(dic.keys())
            
            # Initialize containers for cumulative analysis
            pan_results = []
            
            # Calculate pan and core genomes progressively
            for i in range(len(strain_names)):
                # Get genes from current subset of strains (0 to i+1)
                current_strains = strain_names[:i+1]
                
                # Calculate pan-genome (union of all genes in current strains)
                pan_genes = set()
                for strain in current_strains:
                    pan_genes.update(dic[strain])
                
                # Calculate core-genome (intersection of all genes in current strains)
                if len(current_strains) == 1:
                    core_genes = set(dic[current_strains[0]])
                else:
                    core_genes = set(dic[current_strains[0]])
                    for strain in current_strains[1:]:
                        core_genes = core_genes.intersection(set(dic[strain]))
                
                # Store results
                pan_results.append({
                    'strain': strain_names[i],
                    'core': len(core_genes),
                    'pan': len(pan_genes),
                    'genome_number': i + 1
                })
                
                # Write to file
                panomic.write(f"{strain_names[i]};{len(core_genes)};{len(pan_genes)}\n")
        
        # Generate pan-genome plot using the new method
        Visualization.generate_lineplot(t3, t4, l1, l2, t5, fileType, outputs)
        
        # Pan-distribution analysis
        if db_param == "-card":
            self._process_card_distribution(t1, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, fileType, outputs)
        elif db_param == "-vfdb":
            self._process_vfdb_distribution(t1, t6, t7, t10, t12, t14, fileType, outputs)
        elif db_param == "-bacmet":
            self._process_bacmet_distribution(t1, t6, t7, t8, t10, t12, t14, fileType, outputs)
        elif db_param == "-megares":
            self._process_megares_distribution(t1, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, fileType, outputs)
        
        return outputs

    def _setup_output_files(self, db_param, fileType, aligner_suffix=""):
        """Setup output file names based on database type with enhanced structure and validation"""
        outputs = []
        db_name = db_param[1:]  # Remove the '-' from parameter name
        
        # Validate inputs
        if not db_param.startswith('-'):
            raise ValueError(f"Invalid database parameter: {db_param}")
        
        if fileType not in ['pdf', 'png']:
            fileType = 'pdf'  # Default fallback
        
        suffix = f"_{aligner_suffix}" if aligner_suffix else ""
        
        # Database configuration mapping
        db_configs = {
            "-card": {
                "title": "Pan-resistome development",
                "pan_label": "Pan-resistome",
                "core_label": "Core-resistome",
                "files": {
                    "gene_count": f"card_gene_count{suffix}.csv",
                    "strain_count": f"card_strain_count{suffix}.csv",
                    "pan_analysis": f"card_pan{suffix}.csv",
                    "mechanisms": f"card_mechanisms{suffix}.csv",
                    "drug_classes": f"card_drug_classes{suffix}.csv",
                    "mechanisms_plot": f"card_mechanisms_barplot{suffix}.{fileType}",
                    "drug_classes_plot": f"card_drug_classes_barplot{suffix}.{fileType}",
                    "mechanisms_scatter": f"card_mechanisms_scatterplot{suffix}.{fileType}",
                    "drug_classes_scatter": f"card_drug_classes_scatterplot{suffix}.{fileType}",
                    "mechanisms_bubble": f"card_mechanisms_bubble{suffix}.{fileType}",
                    "drug_classes_bubble": f"card_drug_classes_bubble{suffix}.{fileType}",
                    "mechanisms_strip": f"card_mechanisms_strip{suffix}.{fileType}",
                    "drug_classes_strip": f"card_drug_classes_strip{suffix}.{fileType}"
                }
            },
            "-vfdb": {
                "title": "Pan-virulome development",
                "pan_label": "Pan-virulome",
                "core_label": "Core-virulome",
                "files": {
                    "gene_count": f"vfdb_gene_count{suffix}.csv",
                    "strain_count": f"vfdb_strain_count{suffix}.csv",
                    "pan_analysis": f"vfdb_pan{suffix}.csv",
                    "mechanisms": f"vfdb_mechanisms{suffix}.csv",
                    "mechanisms_plot": f"vfdb_mechanisms_barplot{suffix}.{fileType}",
                    "mechanisms_scatter": f"vfdb_mechanisms_scatterplot{suffix}.{fileType}",
                    "mechanisms_bubble": f"vfdb_mechanisms_bubble{suffix}.{fileType}",
                    "mechanisms_strip": f"vfdb_mechanisms_strip{suffix}.{fileType}"
                }
            },
            "-bacmet": {
                "title": "Pan-resistome development",
                "pan_label": "Pan-resistome",
                "core_label": "Core-resistome",
                "files": {
                    "gene_count": f"bacmet_gene_count{suffix}.csv",
                    "strain_count": f"bacmet_strain_count{suffix}.csv",
                    "pan_analysis": f"bacmet_pan{suffix}.csv",
                    "heavy_metals": f"bacmet_heavy_metals{suffix}.csv",
                    "all_compounds": f"bacmet_all_compounds{suffix}.csv",
                    "heavy_metals_plot": f"bacmet_heavy_metals_barplot{suffix}.{fileType}",
                    "heavy_metals_scatter": f"bacmet_heavy_metals_scatterplot{suffix}.{fileType}",
                    "heavy_metals_bubble": f"bacmet_heavy_metals_bubble{suffix}.{fileType}",
                    "heavy_metals_strip": f"bacmet_heavy_metals_strip{suffix}.{fileType}"
                }
            },
            "-megares": {
                "title": "Pan-resistome development",
                "pan_label": "Pan-resistome",
                "core_label": "Core-resistome",
                "files": {
                    "gene_count": f"megares_gene_count{suffix}.csv",
                    "strain_count": f"megares_strain_count{suffix}.csv",
                    "pan_analysis": f"megares_pan{suffix}.csv",
                    "mechanisms": f"megares_mechanisms{suffix}.csv",
                    "drug_classes": f"megares_drug_classes{suffix}.csv",
                    "mechanisms_plot": f"megares_mechanisms_barplot{suffix}.{fileType}",
                    "drug_classes_plot": f"megares_drug_classes_barplot{suffix}.{fileType}",
                    "mechanisms_scatter": f"megares_mechanisms_scatterplot{suffix}.{fileType}",
                    "drug_classes_scatter": f"megares_drug_classes_scatterplot{suffix}.{fileType}",
                    "mechanisms_bubble": f"megares_mechanisms_bubble{suffix}.{fileType}",
                    "drug_classes_bubble": f"megares_drug_classes_bubble{suffix}.{fileType}",
                    "mechanisms_strip": f"megares_mechanisms_strip{suffix}.{fileType}",
                    "drug_classes_strip": f"megares_drug_classes_strip{suffix}.{fileType}"
                }
            }
        }
        
        # Get configuration for the specified database
        if db_param not in db_configs:
            raise ValueError(f"Unsupported database parameter: {db_param}")
        
        config = db_configs[db_param]
        
        # Add core files to outputs (all databases have these)
        core_files = ["gene_count", "strain_count", "pan_analysis"]
        for file_key in core_files:
            if file_key in config["files"]:
                outputs.append(config["files"][file_key])
        
        # Add database-specific files to outputs
        for file_key, file_path in config["files"].items():
            if file_key not in core_files:
                outputs.append(file_path)
        
        # Create return tuple based on database type
        base_return = [
            outputs,
            config["files"]["gene_count"],           # t1
            config["files"]["strain_count"],         # t2
            config["files"]["pan_analysis"],         # t3
            config["title"],                         # t4
            config["pan_label"],                     # l1
            config["core_label"]                     # l2
        ]
        
        # Add database-specific files with proper None handling
        if db_param == "-card":
            return base_return + [
                config["files"]["mechanisms"],           # t6
                config["files"]["drug_classes"],         # t7
                config["files"]["mechanisms_plot"],      # t8
                config["files"]["drug_classes_plot"],    # t9
                config["files"]["mechanisms_scatter"],   # t10
                config["files"]["drug_classes_scatter"], # t11
                config["files"]["mechanisms_bubble"],    # t12
                config["files"]["drug_classes_bubble"],  # t13
                config["files"]["mechanisms_strip"],     # t14
                config["files"]["drug_classes_strip"]    # t15
            ]
        elif db_param == "-vfdb":
            return base_return + [
                config["files"]["mechanisms"],           # t6
                config["files"]["mechanisms_plot"],      # t7
                None,                                     # t8 (not used for VFDB)
                None,                                     # t9 (not used for VFDB)
                config["files"]["mechanisms_scatter"],   # t10
                None,                                     # t11 (not used for VFDB)
                config["files"]["mechanisms_bubble"],    # t12
                None,                                     # t13 (not used for VFDB)
                config["files"]["mechanisms_strip"],     # t14
                None                                      # t15 (not used for VFDB)
            ]
        elif db_param == "-bacmet":
            return base_return + [
                config["files"]["heavy_metals"],         # t6
                config["files"]["all_compounds"],        # t7
                config["files"]["heavy_metals_plot"],    # t8
                None,                                     # t9 (not used for BacMet)
                config["files"]["heavy_metals_scatter"], # t10
                None,                                     # t11 (not used for BacMet)
                config["files"]["heavy_metals_bubble"],  # t12
                None,                                     # t13 (not used for BacMet)
                config["files"]["heavy_metals_strip"],   # t14
                None                                      # t15 (not used for BacMet)
            ]
        elif db_param == "-megares":
            return base_return + [
                config["files"]["mechanisms"],           # t6
                config["files"]["drug_classes"],         # t7
                config["files"]["mechanisms_plot"],      # t8
                config["files"]["drug_classes_plot"],    # t9
                config["files"]["mechanisms_scatter"],   # t10
                config["files"]["drug_classes_scatter"], # t11
                config["files"]["mechanisms_bubble"],    # t12
                config["files"]["drug_classes_bubble"],  # t13
                config["files"]["mechanisms_strip"],     # t14
                config["files"]["drug_classes_strip"]    # t15
            ]
        
        # Fallback (should not reach here due to validation above)
        return base_return + [None, None, None, None, None, None, None, None, None, None]

    def _process_card_distribution(self, t1, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, fileType, outputs):
        """Process CARD database distribution analysis"""
        print("\nMaking the pan-distribution...")
        aro = pd.read_csv(os.path.join(self.dbpath, "aro_index.tsv"), sep="\t")
        aro_genes = aro["ARO Name"].tolist()
        aro_drug = aro["Drug Class"].tolist()
        aro_mech = aro["Resistance Mechanism"].tolist()
        aro_dict = {}
        
        for i in range(0, len(aro_genes)):
            aro_dict[aro_genes[i]] = (aro_drug[i], aro_mech[i])

        mech = []
        drug = []
        for i in aro_dict.keys():
            if ";" in str(aro_dict[i][1]):
                temp = str(aro_dict[i][1]).split(";")
                for j in temp:
                    if j not in mech:
                        mech.append(j)
            else:
                temp = aro_dict[i][1]
                if temp not in mech:
                    mech.append(temp)
            if ";" in str(aro_dict[i][0]):
                temp = str(aro_dict[i][0]).split(";")
                for j in temp:
                    if j not in drug:
                        drug.append(j)
            else:
                temp = aro_dict[i][0]
                if temp not in drug:
                    drug.append(temp)

        genes = pd.read_csv(t1, sep=";")
        core = []
        acce = []
        exclusive = []
        g = genes["Genes"].tolist()
        n = genes["Presence Number"].tolist()
        
        for i in range(0, len(g)):
            if n[i] == len(self.strains):
                core.append(g[i])
            elif (n[i] > 1) and (n[i] < len(self.strains)):
                acce.append(g[i])
            elif n[i] == 1:
                exclusive.append(g[i])

        # Resistance mechanisms
        with open(t6, "w") as out:
            out.write("Resistance Mechanism;Core;Accessory;Exclusive\n")
            for k in mech:
                coreM = accessoryM = exclusiveM = 0
                for i in core:
                    try:
                        if str(k) in str(aro_dict[i][1]):
                            coreM += 1
                    except KeyError:
                        for j in aro_dict.keys():
                            if i in j and str(k) in str(aro_dict[j][1]):
                                coreM += 1
                
                for i in acce:
                    try:
                        if str(k) in str(aro_dict[i][1]):
                            accessoryM += 1
                    except KeyError:
                        for j in aro_dict.keys():
                            if i in j and str(k) in str(aro_dict[j][1]):
                                accessoryM += 1
                
                for i in exclusive:
                    try:
                        if str(k) in str(aro_dict[i][1]):
                            exclusiveM += 1
                    except KeyError:
                        for j in aro_dict.keys():
                            if i in j and str(k) in str(aro_dict[j][1]):
                                exclusiveM += 1
                
                if (coreM != 0) or (accessoryM != 0) or (exclusiveM != 0):
                    out.write(str(k).capitalize() + ";" + str(coreM) + ";" + str(accessoryM) + ";" + str(exclusiveM) + "\n")

        # Drug classes
        with open(t7, "w") as out2:
            out2.write("Drug Class;Core;Accessory;Exclusive\n")
            for k in drug:
                if str(k).capitalize() == "Nan":
                    continue
                coreM = accessoryM = exclusiveM = 0
                
                for i in core:
                    try:
                        if str(k) in str(aro_dict[i][0]):
                            coreM += 1
                    except KeyError:
                        for j in aro_dict.keys():
                            if i in j and str(k) in str(aro_dict[j][0]):
                                coreM += 1
                
                for i in acce:
                    try:
                        if str(k) in str(aro_dict[i][0]):
                            accessoryM += 1
                    except KeyError:
                        for j in aro_dict.keys():
                            if i in j and str(k) in str(aro_dict[j][0]):
                                accessoryM += 1
                
                for i in exclusive:
                    try:
                        if str(k) in str(aro_dict[i][0]):
                            exclusiveM += 1
                    except KeyError:
                        for j in aro_dict.keys():
                            if i in j and str(k) in str(aro_dict[j][0]):
                                exclusiveM += 1
                
                if (coreM != 0) or (accessoryM != 0) or (exclusiveM != 0):
                    out2.write(str(k).capitalize() + ";" + str(coreM) + ";" + str(accessoryM) + ";" + str(exclusiveM) + "\n")

        # Generate barplots and scatterplots with separate file names
        try:
            # Mechanisms
            if t8 is not None:
                Visualization.generate_barplot(t6, "Resistance Mechanism", t8, fileType, outputs)
            if t10 is not None:
                Visualization.generate_scatterplot(t6, "Resistance Mechanism", t10, fileType, outputs)
            if t12 is not None:
                Visualization.generate_scatterplot_with_continuous_hues_and_sizes(t6, "Resistance Mechanism", t12, fileType, outputs)
            if t14 is not None:
                Visualization.generate_regression_fit_over_strip_plot(t6, "Resistance Mechanism", t14, fileType, outputs)
            
            # Drug classes
            if t9 is not None:
                Visualization.generate_barplot(t7, "Drug Class", t9, fileType, outputs)
            if t11 is not None:
                Visualization.generate_scatterplot(t7, "Drug Class", t11, fileType, outputs)
            if t13 is not None:
                Visualization.generate_scatterplot_with_continuous_hues_and_sizes(t7, "Drug Class", t13, fileType, outputs)
            if t15 is not None:
                Visualization.generate_regression_fit_over_strip_plot(t7, "Drug Class", t15, fileType, outputs)
        except Exception as e:
            print(f"Error generating plots: {e}")
            import traceback
            traceback.print_exc()

    def _process_vfdb_distribution(self, t1, t6, t7, t10, t12, t14, fileType, outputs):
        """Process VFDB database distribution analysis"""
        print("\nMaking the pan-distribution...")
        
        # Extrair genes_comp do DatabaseManager ou de onde estiver definido
        # Se genes_comp foi definido em outro lugar, você precisa acessá-lo corretamente
        # Aqui estou assumindo que você pode obtê-lo chamando DataProcessor.extract_keys novamente
        comp, genes_comp = DataProcessor.extract_keys("-vfdb", self.dbpath)
        
        genes = pd.read_csv(t1, sep=";")
        core = []
        acce = []
        exclusive = []
        g = genes["Genes"].tolist()
        n = genes["Presence Number"].tolist()
        
        for i in range(0, len(g)):
            if n[i] == len(self.strains):
                core.append(g[i])
            elif (n[i] > 1) and (n[i] < len(self.strains)):
                acce.append(g[i])
            elif n[i] == 1:
                exclusive.append(g[i])

        with open(t6, "w") as out:
            out.write("Virulence Mechanism;Core;Accessory;Exclusive\n")
            mech = []
            for k in genes_comp:
                if genes_comp[k] not in mech:
                    mech.append(genes_comp[k])
            
            for mechanism in mech:
                core_number = accessory_number = exclusive_number = 0
                
                for gene in core:
                    if gene in genes_comp and genes_comp[gene] == mechanism:
                        core_number += 1
                for gene in acce:
                    if gene in genes_comp and genes_comp[gene] == mechanism:
                        accessory_number += 1
                for gene in exclusive:
                    if gene in genes_comp and genes_comp[gene] == mechanism:
                        exclusive_number += 1
                
                if (core_number != 0) or (accessory_number != 0) or (exclusive_number != 0):
                    out.write(str(mechanism).capitalize() + ";" + str(core_number) + ";" + str(accessory_number) + ";" + str(exclusive_number) + "\n")

        try:
            # Generate barplot and scatterplot with separate file names
            if t7 is not None:
                Visualization.generate_barplot(t6, "Virulence Mechanism", t7, fileType, outputs)
            if t10 is not None:
                Visualization.generate_scatterplot(t6, "Virulence Mechanism", t10, fileType, outputs)
            if t12 is not None:
                Visualization.generate_scatterplot_with_continuous_hues_and_sizes(t6, "Virulence Mechanism", t12, fileType, outputs)
            if t14 is not None:
                Visualization.generate_regression_fit_over_strip_plot(t6, "Virulence Mechanism", t14, fileType, outputs)
        except Exception as e:
            print(f"Error generating plots: {e}")

    def _process_bacmet_distribution(self, t1, t6, t7, t8, t10, t12, t14, fileType, outputs):
        """Process BacMet database distribution analysis"""
        db = pd.read_csv(os.path.join(self.dbpath, "bacmet_2.txt"), sep="\t")
        genes_list = db["Gene_name"].tolist()
        compostos = db["Compound"].tolist()
        comp = []
        
        for i in compostos:
            if "," in i:
                temp = i.split(",")
                for j in temp:
                    if j.strip() not in comp:
                        comp.append(j.strip())
            else:
                if i.strip() not in comp:
                    comp.append(i.strip())
        
        dic = {}
        for i in range(0, len(genes_list)):
            if "," not in compostos[i]:
                dic[genes_list[i]] = compostos[i]
            else:
                temp = compostos[i].split(', ')
                for j in range(0, len(temp)):
                    temp[j] = temp[j].strip()
                dic[genes_list[i]] = temp
        
        matriz = pd.read_csv(t1, sep=";")
        my_genes = {}
        for i in range(0, len(matriz["Genes"].tolist())):
            my_genes[matriz["Genes"][i]] = matriz["Presence Number"][i]
        
        core_ome = []
        accessory_ome = []
        exclusive_ome = []
        for i in my_genes.keys():
            if my_genes[i] == len(self.strains):
                core_ome.append(i)
            elif my_genes[i] > 1:
                accessory_ome.append(i)
            else:
                exclusive_ome.append(i)
        
        # Heavy metals file
        with open(t6, 'w') as outa:
            outa.write("Compound;Core;Accessory;Exclusive\n")
            # All compounds file
            with open(t7, 'w') as outb:
                outb.write("Compound;Core;Accessory;Exclusive\n")
                
                for k in comp:
                    core = accessory = exclusive = 0
                    
                    for i in core_ome:
                        try:
                            if isinstance(dic[i], list) and k in dic[i]:
                                core += 1
                            elif isinstance(dic[i], str) and k == dic[i]:
                                core += 1
                        except KeyError:
                            for j in dic.keys():
                                if i in j:
                                    if isinstance(dic[j], list) and k in dic[j]:
                                        core += 1
                                    elif isinstance(dic[j], str) and k == dic[j]:
                                        core += 1
                    
                    for i in accessory_ome:
                        try:
                            if isinstance(dic[i], list) and k in dic[i]:
                                accessory += 1
                            elif isinstance(dic[i], str) and k == dic[i]:
                                accessory += 1
                        except KeyError:
                            for j in dic.keys():
                                if i in j:
                                    if isinstance(dic[j], list) and k in dic[j]:
                                        accessory += 1
                                    elif isinstance(dic[j], str) and k == dic[j]:
                                        accessory += 1
                    
                    for i in exclusive_ome:
                        try:
                            if isinstance(dic[i], list) and k in dic[i]:
                                exclusive += 1
                            elif isinstance(dic[i], str) and k == dic[i]:
                                exclusive += 1
                        except KeyError:
                            for j in dic.keys():
                                if i in j:
                                    if isinstance(dic[j], list) and k in dic[j]:
                                        exclusive += 1
                                    elif isinstance(dic[j], str) and k == dic[j]:
                                        exclusive += 1
                    
                    if (core != 0) or (accessory != 0) or (exclusive != 0):
                        if ("(" in k) and ("[" not in k):
                            outa.write(k + ";" + str(core) + ";" + str(accessory) + ";" + str(exclusive) + "\n")
                        outb.write(k + ";" + str(core) + ";" + str(accessory) + ";" + str(exclusive) + "\n")

        try:
            # Generate barplot and scatterplot with separate file names
            if t8 is not None:
                Visualization.generate_barplot(t6, "Compound", t8, fileType, outputs)
            if t10 is not None:
                Visualization.generate_scatterplot(t6, "Compound", t10, fileType, outputs)
            if t12 is not None:
                Visualization.generate_scatterplot_with_continuous_hues_and_sizes(t6, "Compound", t12, fileType, outputs)
            if t14 is not None:
                Visualization.generate_regression_fit_over_strip_plot(t6, "Compound", t14, fileType, outputs)
        except Exception as e:
            print(f"Error generating plots: {e}")

    def _process_megares_distribution(self, t1, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, fileType, outputs):
        """Process MEGARes database distribution analysis"""
        print("\nMaking the MEGARes pan-distribution...")
        
        # Use the instance variables that were set in _run_analysis_workflow
        genes_comp = self.genes_comp  # Maps gene -> drug_class
        mechanisms_comp = self.mechanisms_comp  # Maps gene -> mechanism
        
        # Extract unique mechanisms and drug classes
        mechanisms = list(set(mechanisms_comp.values()))  # Unique mechanisms
        drug_classes = list(set(genes_comp.values()))     # Unique drug classes
        
        print(f"Found {len(mechanisms)} unique mechanisms")
        print(f"Found {len(drug_classes)} unique drug classes")
        
        genes = pd.read_csv(t1, sep=";")
        core = []
        acce = []
        exclusive = []
        g = genes["Genes"].tolist()
        n = genes["Presence Number"].tolist()
        
        for i in range(0, len(g)):
            if n[i] == len(self.strains):
                core.append(g[i])
            elif (n[i] > 1) and (n[i] < len(self.strains)):
                acce.append(g[i])
            elif n[i] == 1:
                exclusive.append(g[i])

        # Resistance mechanisms
        with open(t6, "w") as out:
            out.write("Resistance Mechanism;Core;Accessory;Exclusive\n")
            for mechanism in mechanisms:
                core_count = accessory_count = exclusive_count = 0
                
                for gene in core:
                    if gene in mechanisms_comp and mechanisms_comp[gene] == mechanism:
                        core_count += 1
                
                for gene in acce:
                    if gene in mechanisms_comp and mechanisms_comp[gene] == mechanism:
                        accessory_count += 1
                
                for gene in exclusive:
                    if gene in mechanisms_comp and mechanisms_comp[gene] == mechanism:
                        exclusive_count += 1
                
                if (core_count != 0) or (accessory_count != 0) or (exclusive_count != 0):
                    out.write(f"{mechanism};{core_count};{accessory_count};{exclusive_count}\n")

        # Drug classes (similar to mechanisms for MEGARes)
        with open(t7, "w") as out2:
            out2.write("Drug Class;Core;Accessory;Exclusive\n")
            for drug_class in drug_classes:
                core_count = accessory_count = exclusive_count = 0
                
                for gene in core:
                    if gene in genes_comp and genes_comp[gene] == drug_class:
                        core_count += 1
                
                for gene in acce:
                    if gene in genes_comp and genes_comp[gene] == drug_class:
                        accessory_count += 1
                
                for gene in exclusive:
                    if gene in genes_comp and genes_comp[gene] == drug_class:
                        exclusive_count += 1
                
                if (core_count != 0) or (accessory_count != 0) or (exclusive_count != 0):
                    out2.write(f"{drug_class};{core_count};{accessory_count};{exclusive_count}\n")

        try:
            # Generate barplots and scatterplots with separate file names
            # Mechanisms
            if t8 is not None:
                Visualization.generate_barplot(t6, "Resistance Mechanism", t8, fileType, outputs)
            if t10 is not None:
                Visualization.generate_scatterplot(t6, "Resistance Mechanism", t10, fileType, outputs)
            if t12 is not None:
                Visualization.generate_scatterplot_with_continuous_hues_and_sizes(t6, "Resistance Mechanism", t12, fileType, outputs)
            if t14 is not None:
                Visualization.generate_regression_fit_over_strip_plot(t6, "Resistance Mechanism", t14, fileType, outputs)
            
            # Drug classes
            if t9 is not None:
                Visualization.generate_barplot(t7, "Drug Class", t9, fileType, outputs)
            if t11 is not None:
                Visualization.generate_scatterplot(t7, "Drug Class", t11, fileType, outputs)
            if t13 is not None:
                Visualization.generate_scatterplot_with_continuous_hues_and_sizes(t7, "Drug Class", t13, fileType, outputs)
            if t15 is not None:
                Visualization.generate_regression_fit_over_strip_plot(t7, "Drug Class", t15, fileType, outputs)
        except Exception as e:
            print(f"Error generating plots: {e}")

    def _organize_results(self, outputs, db_param, aligner_suffix=""):
        """Organize results into output directory"""
        print(f"\nGrouping the results{f' ({aligner_suffix})' if aligner_suffix else ''}...\n")
        
        if aligner_suffix:
            atual = f"Results_{db_param[1:]}_{aligner_suffix}_{dt.now().strftime('%d-%m-%Y_%H-%M-%S')}"
        else:
            atual = "Results_" + db_param[1:] + "_" + dt.now().strftime("%d-%m-%Y_%H-%M-%S")
        
        os.mkdir(atual)
        
        # Add the database-specific Tabular directories to outputs
        db_name = db_param[1:]  # Remove the '-' from parameter name
        
        if aligner_suffix:
            tabular1_dir = f"Tabular_1_{db_name}_{aligner_suffix}"
            tabular2_dir = f"Tabular_2_{db_name}_{aligner_suffix}"
        else:
            tabular1_dir = f"Tabular_1_{db_name}"
            tabular2_dir = f"Tabular_2_{db_name}"
        
        # Add Tabular directories to outputs if they exist
        if os.path.exists(tabular1_dir):
            outputs.append(tabular1_dir)
        if os.path.exists(tabular2_dir):
            outputs.append(tabular2_dir)
        
        for i in outputs:
            try:
                if os.path.exists(i):
                    shutil.move(i, atual)
                    print(f"Moved {i} to {atual}")
                else:
                    print(f"Warning: {i} not found, skipping...")
            except BaseException as e:
                erro_string = f"It was not possible to move the file {str(i)} to the final directory.\nError: {str(e)}\nPlease, check the output path.\n"
                print(erro_string)

    def _remove_intermediate_files(self):
        """Remove intermediate files if not keeping them"""
        if ("-keep" not in sys.argv) and ("-k" not in sys.argv):
            try:
                shutil.rmtree("Positions_1")
            except (PermissionError, FileNotFoundError):
                pass
            try:
                shutil.rmtree("faa")
            except (PermissionError, FileNotFoundError):
                pass

    def _write_error_file(self):
        """Write error messages to a file"""
        erro_file = "panvita_error_" + dt.now().strftime("%d-%m-%Y_%H-%M-%S") + ".err"
        with open(erro_file, "w") as erro_out:
            string = "PanViTa " + str(dt.now().strftime("%d-%m-%Y_%H-%M-%S")) + "\n"
            erro_out.write(string)
            erro_out.write(
                "The following lines contains the errors from the last runing.\nPlease, check them carefully.\n")
            for i in self.erro:
                erro_out.write(i)
            erro_out.write(
                "\nIf the lines appear empty, no error has been computed for the current run.\n")
        return erro_file

    def _print_final_messages(self):
        """Print final messages and citations"""
        if len(self.erro) > 0:
            final_erro = self._write_error_file()
            print("\nNumber of errors reported: " + str(len(self.erro)))
            print("Please check the " + str(final_erro) + " file.\n")
        else:
            print("\nNo error reported!")

        self._print_citation()

    def _print_citation(self):
        """Print citation information"""
        print('''That's all, folks!
Thank you for using this script.
If you're going to use results from PanViTa, please cite us:

PanViTa\thttps://doi.org/10.3389/fbinf.2023.1070406\t2023

Do not forget to quote the databases used.\n''')
        if "-bacmet" in sys.argv:
            print("BacMet\thttps://doi.org/10.1093/nar/gkt1252\t2014")
        if "-card" in sys.argv:
            print("CARD\thttps://doi.org/10.1093/nar/gkz935\t2020")
        if "-megares" in sys.argv:
            print("MEGARes\thttps://doi.org/10.1093/nar/gkac1047\t2022")
        if "-vfdb" in sys.argv:
            print("VFDB\thttps://doi.org/10.1093/nar/gky1080\t2019")
        print("\nDon't forget to mention the optional software too, if you already used them.")
        if "-m" in sys.argv:
            print("mlst\thttps://doi.org/10.1186/1471-2105-11-595\t2010")
            print("mlst\thttps://github.com/tseemann/mlst")
        if "-a" in sys.argv:
            print("prokka\thttps://doi.org/10.1093/bioinformatics/btu153\t2014")
        print('')
