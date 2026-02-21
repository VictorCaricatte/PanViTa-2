# ===============================================================================
# Author:       Victor S Caricatte De Araújo
# Co-author:    Diego Neres, Vinicius Oliveira
# Email:        victorsc@ufmg.br , dlnrodrigues@ufmg.br , vinicius.oliveira.1444802@sga.pucminas.br
# Intitution:   Universidade federal de Minas Gerais
# Version:      2.0.4
# Date:         February 18, 2026
# Notes: You may need deactivate conda. 
# ===============================================================================
# File: panvita.py
# Description: Main execution script for PanViTa 
# ===============================================================================

# Standard library imports
import os
import sys
import shutil
import concurrent.futures
import pandas as pd
from datetime import datetime

# Local module imports
from config import PanViTaConfig
from dependences import DependencyManager
from bank import DatabaseManager
from ncbi import NCBIDownloader
from functions import GBKProcessor, Aligner, DataProcessor
from visualization import Visualization

class PanViTa:
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
        self.custom_db_path = None # Variable to store custom database path
        self.threads = os.cpu_count() or 1 # Default thread count
        
        # Metadata storage for reporting and advanced plotting
        self.meta1_comp = {} # Classification 1 (e.g., Drug Class)
        self.meta2_comp = {} # Classification 2 (e.g., Mechanism)
        self.genes_comp = {}
        self.mechanisms_comp = {}

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
        
        # OPTIMIZATION: Align and mine in parallel 
        self._align_and_mine_parallel(aligner_types, aligner_exes, aligner_names)
        
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
            print("version 2.0.4")
            print("-----------------------------------------------")
            exit()

        # Check for new parameters in the check list
        valid_params = ["-card", "-bacmet", "-vfdb", "-megares", "-resfinder", "-argannot", "-victors", "-victors-nucl", "-custom"]
        has_param = any(p in sys.argv for p in valid_params)

        if (not has_param and ("-u" not in sys.argv) and ("-update" not in sys.argv) and
            ("-g" not in sys.argv) and ("-a" not in sys.argv) and ("-m" not in sys.argv) and 
            ("-b" not in sys.argv)) or ("-h" in sys.argv) or ("-help" in sys.argv):
            self._print_help()
            exit()

        print('''
Hello user!

This script has the function of comparing multiple genomes against previously selected databases.
The result consists of a clustermap, presence matrix, UpSet plots, Networks and PCoA.

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
-resfinder\tResFinder Resistance Database
-argannot\tARG-ANNOT Antibiotic Resistance Gene Annotation
-victors\tVictors Virulence Factors Database (Proteins)
-victors-nucl\tVictors Virulence Factors Database (Nucleotides)
-custom [path]\tUse a custom FASTA database (provide path after flag)

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
-t\tNumber of threads to use (default = all available CPUs)
-d\tForce to use DIAMOND from system
-diamond\tForce to use DIAMOND only for alignments
-blast\tForce to use BLAST only for alignments
-both\tUse both DIAMOND and BLAST for alignments
-pdf\tFigures will be saved as PDF (default)
-png\tFigures will be saved as PNG (WARNING! High memory consumption)
-save-genes\tSave found genes in individual .faa files for each genome
-g\tDownload the genomes fasta files (require CSV, TSV, or TXT table from NCBI)
-a\tDownload and annote the genomes using PROKKA pipeline (require CSV, TSV, or TXT table from NCBI)
--prokka [path]\tSpecify the path for the PROKKA executable if it's not in your system PATH
-b\tDownload the genome GenBank files (require CSV, TSV, or TXT table from NCBI)
-s\tKeep the locus_tag as same as the strain (require -b)
-m\tGet the metadata from BioSample IDs (require CSV, TSV, or TXT table from NCBI)

Note: If no aligner is specified, the program will prompt you to choose between DIAMOND, BLAST, or both.

Contact: victorsc@ufmg.br , dlnrodrigues@ufmg.br
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
        db_manager = DatabaseManager(self.dppath)
        
        # Check for custom db argument first to pass to check_databases
        custom_path = None
        if "-custom" in sys.argv:
            try:
                idx = sys.argv.index("-custom")
                if idx + 1 < len(sys.argv) and not sys.argv[idx+1].startswith("-"):
                    custom_path = sys.argv[idx+1].strip()
                    self.custom_db_path = custom_path
                else:
                    print("Error: -custom flag requires a file path argument.")
                    exit(1)
            except ValueError:
                pass

        # Perform database checks (downloading/indexing)
        # Note: We pass custom_path so it can be indexed
        self.dbpath = db_manager.check_databases(aligner_exes[0], custom_path)
        
        if "-a" in sys.argv or "-b" in sys.argv or "-g" in sys.argv or "-m" in sys.argv:
            table = None
            for i in sys.argv:
                if i.endswith((".csv", ".tsv", ".txt")):
                    table = i
                    break
            
            if table:
                if table.endswith(".csv"):
                    df = pd.read_csv(table, sep=',')
                else:
                    df = pd.read_csv(table, sep='\t')
                    
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
                 if "-a" in sys.argv or "-b" in sys.argv or "-g" in sys.argv or "-m" in sys.argv:
                     print("Error: A valid table file (.csv, .tsv, .txt) is required for download options (-a, -b, -g, -m).")
                     exit(1)
        else:
            # If no CSV operations, still need to setup databases (already done above)
            pass

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
        
        # Thread parsing
        if "-t" in sys.argv:
            try:
                idx = sys.argv.index("-t")
                self.threads = int(sys.argv[idx + 1])
            except (ValueError, IndexError):
                print("Warning: Invalid value for -t. Using default CPU count.")
        
        print("Separating files")
        self.files = []
        for i in sys.argv:
            # Avoid picking up the custom path as a file input
            if i == self.custom_db_path:
                continue
            if i.endswith(".gbk") or i.endswith(".gbf") or i.endswith(".gbff"):
                self.files.append(i)
                
        for i in sys.argv:
            if i.endswith((".csv", ".tsv", ".txt")):
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
        # List of supported database flags
        db_flags = ["-card", "-bacmet", "-vfdb", "-megares", "-resfinder", "-argannot", "-victors", "-victors-nucl"]
        
        for i in sys.argv:
            if i in db_flags:
                self.parameters.append(i)
        
        # Handle custom parameter separately
        if "-custom" in sys.argv:
            self.parameters.append("-custom")

    def _organize_downloaded_files(self):
        """Organize downloaded files if no analysis parameters"""
        if "-b" in sys.argv:
            pasta = "GenBank_" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
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
            # Try to extract strain name safely
            try:
                strain = str(i)[::-1].split('/')[0][::-1].replace(".gbk", "").replace(".gbff", "").replace(".gbf", "")
            except:
                strain = str(i).replace(".gbk", "").replace(".gbff", "").replace(".gbf", "")

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
                try:
                    tempName = j[::-1].split("/")[0][::-1].replace(".gbk", "").replace(".gbff", "").replace(".gbf", "")
                except:
                    tempName = str(j).replace(".gbk", "").replace(".gbff", "").replace(".gbf", "")
                
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
                try:
                    tempName = i[::-1].split("/")[0][::-1].replace(".gbk", "").replace(".gbff", "").replace(".gbf", "")
                except:
                    tempName = str(i).replace(".gbk", "").replace(".gbff", "").replace(".gbf", "")
                
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
    
    def _run_single_alignment(self, strain, db_path, tabular1_dir, aligner_type, db_type, threads_per_job=1):
        """Helper function to run a single alignment process for parallel execution."""
        aligner = Aligner(self.dppath)
        input_file = os.path.join("faa", f"{strain}.faa")
        output_file = os.path.join(tabular1_dir, f"{strain}.tab")
        return aligner.align(input_file, db_path, output_file, aligner_type, db_type, threads_per_job)

    def _align_and_mine_parallel(self, aligner_types, aligner_exes, aligner_names):
        """Perform alignments in parallel and then mine the results."""
        total_threads = getattr(self, 'threads', os.cpu_count() or 1)
        num_tasks = len(self.strains) if self.strains else 1
        
        # Alocação Inteligente de Threads
        max_workers = min(total_threads, num_tasks)
        if max_workers < 1: 
            max_workers = 1
        threads_per_job = max(1, total_threads // max_workers)

        print(f"\nUsing {total_threads} total threads ({max_workers} parallel jobs, {threads_per_job} threads/job).")

        for p in self.parameters:
            db_name = p[1:]  # Remove '-'

            for aligner_type, aligner_exe, aligner_name in zip(aligner_types, aligner_exes, aligner_names):
                if len(aligner_types) > 1:
                    suffix = f"_{aligner_name.lower()}"
                else:
                    suffix = ""
                
                tabular1_dir = f"Tabular_1_{db_name}{suffix}"
                tabular2_dir = f"Tabular_2_{db_name}{suffix}"
                
                # Setup directories
                for d in [tabular1_dir, tabular2_dir]:
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    os.mkdir(d)
                
                # Determine DB path and type
                db_type = "protein" # Default
                
                if p == "-card":
                    db_path = os.path.join(self.dbpath, "card_protein_homolog_model")
                elif p == "-vfdb":
                    db_path = os.path.join(self.dbpath, "vfdb_core")
                elif p == "-bacmet":
                    db_path = os.path.join(self.dbpath, "bacmet_2")
                elif p == "-megares":
                    db_path = os.path.join(self.dbpath, "megares_v3")
                    db_type = "nucleotide"
                elif p == "-resfinder":
                    db_path = os.path.join(self.dbpath, "resfinder")
                    db_type = "nucleotide"
                elif p == "-argannot":
                    db_path = os.path.join(self.dbpath, "argannot")
                elif p == "-victors":
                    db_path = os.path.join(self.dbpath, "victors")
                elif p == "-victors-nucl":
                    db_path = os.path.join(self.dbpath, "victors_nucl")
                    db_type = "nucleotide"
                elif p == "-custom":
                    db_path = os.path.join(self.dbpath, "custom")
                else:
                    continue

                print(f"\nStarting PARALLEL {aligner_name} alignments for {db_name.upper()}...")
                
                # PARALLEL EXECUTION 
                tasks = []
                with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                    for strain in self.strains:
                        tasks.append(
                            executor.submit(self._run_single_alignment, strain, db_path, tabular1_dir, aligner_type, db_type, threads_per_job)
                        )
                    
                    # Wait for all jobs to complete and print progress
                    for i, future in enumerate(concurrent.futures.as_completed(tasks)):
                        try:
                            result = future.result()
                            print(f"({i+1}/{len(self.strains)}) - {result}")
                        except Exception as exc:
                            print(f'Alignment generated an exception: {exc}')

                print(f"\nAll alignments for {db_name.upper()} complete.")
                print(f"Mining {aligner_name} alignments for {db_name.upper()}...")
                
                # Mining step (still sequential, but fast)
                for i in os.listdir(tabular1_dir):
                    DataProcessor.blastmining_specific(i, tabular1_dir, tabular2_dir)

    def _run_analysis_workflow(self, aligner_types, aligner_names):
        """Run the main analysis workflow for each database with NEW ADVANCED PLOTS"""
        for p in self.parameters:
            db_name = p[1:]  

            # Unified extraction of keys for all databases
            # comp: ID -> Gene Name
            # meta1: Gene Name -> Primary Category (e.g. Drug Class, Compound)
            # meta2: Gene Name -> Secondary Category (e.g. Mechanism, VF Category)
            comp, meta1, meta2 = DataProcessor.extract_keys(p, self.dbpath)
            
            # Store for usage in distribution functions if needed
            self.genes_comp = meta1 
            self.mechanisms_comp = meta2
            
            # Check if we have multiple aligners by looking for directories with suffixes
            aligner_dirs = []
            for dir_name in os.listdir('.'):
                if dir_name.startswith(f"Tabular_2_{db_name}_"):
                    aligner_dirs.append(dir_name.replace(f"Tabular_2_{db_name}_", ""))
            
            # If no aligner-specific directories found, check for unified directory
            if not aligner_dirs and os.path.exists(f"Tabular_2_{db_name}"):
                aligner_dirs.append("")  # Empty suffix for unified directory
            
            if not aligner_dirs:
                print(f"Warning: No analysis directories found for {p}")
                continue
                
            # Process each aligner separately
            for aligner_suffix in aligner_dirs:
                outputs = []
                
                print(f"\nProcessing analysis for {p}{f' ({aligner_suffix})' if aligner_suffix else ''}...")
                
                # Generate matrix
                titulo, dicl, totalgenes, found_genes_per_strain = Visualization.generate_matrix(p, outputs, comp, aligner_suffix)
                
                # Check if the matrix file was created and is not empty before proceeding.
                if not os.path.exists(titulo) or os.path.getsize(titulo) == 0:
                    print(f"\n❌ CRITICAL WARNING: Matrix file '{titulo}' was not generated or is empty.")
                    print("   This usually means no significant alignment results were found for this database.")
                    print(f"   Skipping the rest of the analysis for {p}{f' with {aligner_suffix}' if aligner_suffix else ''}.")
                    continue

                # Save found genes to individual .faa files if requested
                if "-save-genes" in sys.argv:
                    self._save_found_genes(found_genes_per_strain, p, aligner_suffix)
                
                # Generate positions files (only for the first aligner to avoid conflicts)
                if aligner_suffix == aligner_dirs[0]:
                    self._generate_positions_files(p, comp, aligner_suffix)
                
                # Load matrix for visualization
                df = pd.read_csv(titulo, sep=';')
                df = df.set_index('Strains')
                
                # 1. VISUALIZATIONS

                Visualization.generate_heatmap(titulo, p, outputs, self.erro, aligner_suffix)
                Visualization.generate_clustermap(titulo, p, outputs, self.erro, aligner_suffix)
                Visualization.generate_scatterplot_heatmap(titulo, p, outputs, self.erro, aligner_suffix)
                Visualization.generate_joint_and_marginal_distributions(titulo, p, outputs, self.erro, aligner_suffix)
                
                # UpSet Plot
                Visualization.generate_upsetplot(titulo, p, outputs, aligner_suffix)
                
                # PCoA (Jaccard)
                Visualization.generate_pcoa_jaccard(titulo, p, outputs, meta1, aligner_suffix)
                
                # Network (Using strictly the 3D variants, Standard 2D removed)
                Visualization.generate_interactive_network_3d(titulo, p, outputs, meta1, aligner_suffix)
                
                Visualization.generate_interactive_strain_network_3d(titulo, p, outputs, aligner_suffix)

                Visualization.generate_radar_plot(titulo, p, outputs, aligner_suffix)


                # 2. OMICS ANALYSIS & RAREFACTION

                lines = list(df.index.values)
                analysis_outputs = self._process_omics_analysis(df, lines, p, aligner_suffix)
                outputs.extend(analysis_outputs)
                
                # Generate New Rarefaction Curve (with permutations)
                # Find the 'pan' csv file generated in _process_omics_analysis
                pan_csv = None
                for out_f in analysis_outputs:
                    if "pan" in out_f and out_f.endswith(".csv"):
                        pan_csv = out_f
                        break
                
                # Title config
                pan_title = "Pan-genome analysis"
                if p in ["-card", "-megares", "-resfinder", "-argannot"]:
                    pan_title = "Pan-resistome analysis"
                elif p in ["-vfdb", "-victors", "-victors-nucl"]:
                    pan_title = "Pan-virulome analysis"
                
                fileType = "pdf" if "-pdf" in sys.argv or "-png" not in sys.argv else "png"
                if "-png" in sys.argv: fileType = "png"
                
                # Call the new rarefaction function
                # Note: generate_rarefaction_permutations uses the MATRIX file, not the summary pan file
                Visualization.generate_rarefaction_permutations(
                    titulo, 
                    pan_title, 
                    f"{p[1:]}_curve_{aligner_suffix}", 
                    fileType, 
                    outputs
                )
                
                # 3. REPORT GENERATION

                # Using the meta dictionaries extracted earlier
                gene_count_file = next((f for f in analysis_outputs if "gene_count" in f), None)
                if gene_count_file and os.path.exists(gene_count_file):
                    Visualization.generate_detailed_report(
                        titulo, 
                        gene_count_file, 
                        p, 
                        meta1, 
                        meta2, 
                        outputs, 
                        aligner_suffix
                    )

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
                    if os.path.exists(output_file):
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
            
            try:
                with open(positions, 'rt') as tab:
                    arq = tab.readlines()
            except FileNotFoundError:
                continue
            
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
                    elif "-resfinder" == db_param:
                        color = "cyan\n"
                    elif "-argannot" == db_param:
                        color = "magenta\n"
                    elif db_param in ["-victors", "-victors-nucl"]:
                        color = "red\n" # Sync with VFDB as requested
                    else: # Custom
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
        
        # Unpack based on actual length returned - Simplified for all databases
        # Outputs is always first
        outputs = output_setup[0]
        t1, t2, t3, t4, l1, l2 = output_setup[1:7]
        
        # Retrieve extra files depending on DB
        extra_files = output_setup[7:]

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
        if db_param == "-card" and len(extra_files) >= 4:
            self._process_card_distribution(t1, extra_files[0], extra_files[1], extra_files[2], extra_files[3], fileType, outputs)
        elif db_param == "-vfdb" and len(extra_files) >= 2:
            self._process_vfdb_distribution(t1, extra_files[0], extra_files[1], fileType, outputs)
        elif db_param == "-bacmet" and len(extra_files) >= 3:
            self._process_bacmet_distribution(t1, extra_files[0], extra_files[1], extra_files[2], fileType, outputs)
        elif db_param == "-megares" and len(extra_files) >= 4:
            self._process_megares_distribution(t1, extra_files[0], extra_files[1], extra_files[2], extra_files[3], fileType, outputs)
        
        return outputs

    def _setup_output_files(self, db_param, fileType, aligner_suffix=""):
        """Setup output file names based on database type with a clear, validated structure."""
        db_name = db_param[1:]
        suffix = f"_{aligner_suffix}" if aligner_suffix else ""
        
        # Base file definitions common to all databases
        base_files = {
            "gene_count": f"{db_name}_gene_count{suffix}.csv",
            "strain_count": f"{db_name}_strain_count{suffix}.csv",
            "pan_analysis": f"{db_name}_pan{suffix}.csv",
        }
        
        # Titles
        pan_title = "Pan-genome analysis"
        pan_label = "Pan-genome"
        core_label = "Core-genome"
        
        if db_param in ["-card", "-megares", "-resfinder", "-argannot"]:
            pan_title = "Pan-resistome development"
            pan_label = "Pan-resistome"
            core_label = "Core-resistome"
        elif db_param in ["-vfdb", "-victors", "-victors-nucl"]:
            pan_title = "Pan-virulome development"
            pan_label = "Pan-virulome"
            core_label = "Core-virulome"

        # Database-specific titles and additional files
        db_configs = {
            "-card": {
                "files": {
                    "mechanisms": f"card_mechanisms{suffix}.csv",
                    "drug_classes": f"card_drug_classes{suffix}.csv",
                    "mechanisms_barplot": f"card_mechanisms_barplot{suffix}.{fileType}",
                    "drug_classes_barplot": f"card_drug_classes_barplot{suffix}.{fileType}",
                }
            },
            "-vfdb": {
                "files": {
                    "mechanisms": f"vfdb_mechanisms{suffix}.csv",
                    "mechanisms_barplot": f"vfdb_mechanisms_barplot{suffix}.{fileType}",
                }
            },
            "-bacmet": {
                "files": {
                    "heavy_metals": f"bacmet_heavy_metals{suffix}.csv",
                    "all_compounds": f"bacmet_all_compounds{suffix}.csv",
                    "heavy_metals_barplot": f"bacmet_heavy_metals_barplot{suffix}.{fileType}",
                }
            },
            "-megares": {
                "files": {
                    "mechanisms": f"megares_mechanisms{suffix}.csv",
                    "drug_classes": f"megares_drug_classes{suffix}.csv",
                    "mechanisms_barplot": f"megares_mechanisms_barplot{suffix}.{fileType}",
                    "drug_classes_barplot": f"megares_drug_classes_barplot{suffix}.{fileType}",
                }
            }
        }
        
        base_return = [
            [], # Placeholder for outputs list
            base_files["gene_count"], base_files["strain_count"], base_files["pan_analysis"],
            pan_title, pan_label, core_label
        ]
        
        if db_param in db_configs:
            config = db_configs[db_param]
            all_files = {**base_files, **config['files']}
            base_return[0] = list(all_files.values()) # Fill output list
            
            if db_param in ["-card", "-megares"]:
                return base_return + [
                    all_files["mechanisms"], all_files["drug_classes"],
                    all_files["mechanisms_barplot"], all_files["drug_classes_barplot"]
                ]
            elif db_param == "-vfdb":
                return base_return + [
                    all_files["mechanisms"], all_files["mechanisms_barplot"]
                ]
            elif db_param == "-bacmet":
                return base_return + [
                    all_files["heavy_metals"], all_files["all_compounds"],
                    all_files["heavy_metals_barplot"]
                ]
        else:
            # For new simple DBs (Resfinder, Argannot, Victors, Custom)
            base_return[0] = list(base_files.values())
            return base_return

    def _process_card_distribution(self, t1, t6, t7, t8, t9, fileType, outputs):
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

        # Generate barplots 
        try:
            Visualization.generate_barplot(t6, "Resistance Mechanism", t8, fileType, outputs)
            Visualization.generate_barplot(t7, "Drug Class", t9, fileType, outputs)
        except Exception as e:
            print(f"Error generating CARD distribution plots: {e}")

    def _process_vfdb_distribution(self, t1, t6, t7, fileType, outputs):
        """Process VFDB database distribution analysis"""
        print("\nMaking the pan-distribution...")
        
        comp, genes_comp, mech_comp = DataProcessor.extract_keys("-vfdb", self.dbpath)
        
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
            Visualization.generate_barplot(t6, "Virulence Mechanism", t7, fileType, outputs)
        except Exception as e:
            print(f"Error generating VFDB distribution plots: {e}")

    def _process_bacmet_distribution(self, t1, t6, t7, t8, fileType, outputs):
        """Process BacMet database distribution analysis"""
        
        comp, meta1, meta2 = DataProcessor.extract_keys("-bacmet", self.dbpath)
        
        comp_list = []
        for c in meta1.values():
            if "," in c:
                temp = c.split(",")
                for j in temp:
                    clean_c = j.strip()
                    if clean_c not in comp_list:
                        comp_list.append(clean_c)
            else:
                clean_c = c.strip()
                if clean_c not in comp_list:
                    comp_list.append(clean_c)
        
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
                
                for k in comp_list:
                    core = accessory = exclusive = 0
                    
                    def check_compound(gene, target_compound, meta_dict):
                        val = meta_dict.get(gene, "")
                        if "," in val:
                             parts = [x.strip() for x in val.split(",")]
                             return target_compound in parts
                        else:
                             return target_compound == val.strip()

                    for i in core_ome:
                        if check_compound(i, k, meta1): core += 1
                    
                    for i in accessory_ome:
                         if check_compound(i, k, meta1): accessory += 1
                    
                    for i in exclusive_ome:
                         if check_compound(i, k, meta1): exclusive += 1
                    
                    if (core != 0) or (accessory != 0) or (exclusive != 0):
                        if ("(" in k) and ("[" not in k):
                            outa.write(k + ";" + str(core) + ";" + str(accessory) + ";" + str(exclusive) + "\n")
                        outb.write(k + ";" + str(core) + ";" + str(accessory) + ";" + str(exclusive) + "\n")

        try:
            Visualization.generate_barplot(t6, "Compound", t8, fileType, outputs)
        except Exception as e:
            print(f"Error generating BacMet distribution plots: {e}")

    def _process_megares_distribution(self, t1, t6, t7, t8, t9, fileType, outputs):
        """Process MEGARes database distribution analysis"""
        print("\nMaking the MEGARes pan-distribution...")
        
        genes_comp = self.genes_comp  
        mechanisms_comp = self.mechanisms_comp  
        
        mechanisms = list(set(mechanisms_comp.values()))  
        drug_classes = list(set(genes_comp.values()))     
        
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
            Visualization.generate_barplot(t6, "Resistance Mechanism", t8, fileType, outputs)
            Visualization.generate_barplot(t7, "Drug Class", t9, fileType, outputs)
        except Exception as e:
            print(f"Error generating MEGARes distribution plots: {e}")

    def _organize_results(self, outputs, db_param, aligner_suffix=""):
        """Organize results into output directory"""
        print(f"\nGrouping the results{f' ({aligner_suffix})' if aligner_suffix else ''}...\n")
        
        if aligner_suffix:
            atual = f"Results_{db_param[1:]}_{aligner_suffix}_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}"
        else:
            atual = "Results_" + db_param[1:] + "_" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        
        os.mkdir(atual)
        
        db_name = db_param[1:]  
        
        if aligner_suffix:
            tabular1_dir = f"Tabular_1_{db_name}_{aligner_suffix}"
            tabular2_dir = f"Tabular_2_{db_name}_{aligner_suffix}"
        else:
            tabular1_dir = f"Tabular_1_{db_name}"
            tabular2_dir = f"Tabular_2_{db_name}"
        
        if os.path.exists(tabular1_dir):
            outputs.append(tabular1_dir)
        if os.path.exists(tabular2_dir):
            outputs.append(tabular2_dir)
        
        for i in outputs:
            try:
                if isinstance(i, str) and os.path.exists(i):
                    shutil.move(i, atual)
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
        erro_file = "panvita_error_" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S") + ".err"
        with open(erro_file, "w") as erro_out:
            string = "PanViTa " + str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S")) + "\n"
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
        if "-resfinder" in sys.argv:
            print("ResFinder\thttps://doi.org/10.1093/jac/dks261\t2012")
        if "-argannot" in sys.argv:
            print("ARG-ANNOT\thttps://doi.org/10.1128/AAC.01310-13\t2014")
        if "-victors" in sys.argv or "-victors-nucl" in sys.argv:
            print("Victors\thttps://doi.org/10.1093/nar/gkx1038\t2018")

        print("\nDon't forget to mention the optional software too, if you already used them.")
        if "-m" in sys.argv:
            print("mlst\thttps://doi.org/10.1186/1471-2105-11-595\t2010")
            print("mlst\thttps://github.com/tseemann/mlst")
        if "-a" in sys.argv:
            print("prokka\thttps://doi.org/10.1093/bioinformatics/btu153\t2014")
        print('')

if __name__ == '__main__':
    panvita = PanViTa()
    panvita.run()
