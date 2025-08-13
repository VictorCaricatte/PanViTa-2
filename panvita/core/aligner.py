import os
import sys

from .config import PanViTaConfig


class Aligner:
    def __init__(self, dppath):
        self.dppath = dppath
        self.diamond_exe = os.path.join(dppath, "diamond.exe" if PanViTaConfig.is_windows() else "diamond")
        self.blastp_exe = os.path.join(dppath, "blastp.exe" if PanViTaConfig.is_windows() else "blastp")
        self.tblastn_exe = os.path.join(dppath, "tblastn.exe" if PanViTaConfig.is_windows() else "tblastn")

    def choose_aligner(self):
        """Determine which aligner(s) to use based on availability and user choice"""
        diamond_available = os.path.exists(self.diamond_exe)
        blast_available = os.path.exists(self.blastp_exe)
        tblastn_available = os.path.exists(self.tblastn_exe)
        
        if not diamond_available and not blast_available:
            print("ERROR: Neither DIAMOND nor BLAST were found!")
            return None, None, None
        
        # Check if MEGARes is being used (requires tblastn for nucleotide sequences)
        megares_used = "-megares" in sys.argv
        
        if not diamond_available:
            print("DIAMOND not found. Using BLAST only.")
            return ["blast"], [self.blastp_exe], ["BLAST"]
        
        if not blast_available:
            if megares_used:
                print("WARNING: MEGARes analysis requires BLAST (tblastn), but BLAST was not found!")
                print("MEGARes will be skipped. Using DIAMOND for other databases.")
            else:
                print("BLAST not found. Using DIAMOND only.")
            return ["diamond"], [self.diamond_exe], ["DIAMOND"]
        
        # Both are available, ask user
        print("\nBoth DIAMOND and BLAST are available.")
        if megares_used:
            print("Note: MEGARes analysis will use BLAST (tblastn) for nucleotide sequences.")
        print("Which aligner would you like to use?")
        print("1. DIAMOND only (faster)" + (" - Note: MEGARes will be skipped with DIAMOND" if megares_used else ""))
        print("2. BLAST only (more sensitive)")
        print("3. Both DIAMOND and BLAST")
        
        while True:
            try:
                choice = input("Enter your choice (1, 2, or 3): ").strip()
                if choice == "1":
                    if megares_used:
                        print("Warning: DIAMOND cannot analyze MEGARes (nucleotide database). MEGARes will be skipped.")
                    return ["diamond"], [self.diamond_exe], ["DIAMOND"]
                elif choice == "2":
                    return ["blast"], [self.blastp_exe], ["BLAST"]
                elif choice == "3":
                    return ["diamond", "blast"], [self.diamond_exe, self.blastp_exe], ["DIAMOND", "BLAST"]
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")
            except (EOFError, KeyboardInterrupt):
                print("\nUsing BLAST by default (required for MEGARes)." if megares_used else "\nUsing DIAMOND by default.")
                return (["blast"], [self.blastp_exe], ["BLAST"]) if megares_used else (["diamond"], [self.diamond_exe], ["DIAMOND"])

    def align(self, input_file, db_path, output_file, aligner_type="diamond", db_type="protein"):
        """Perform alignment using the specified aligner"""
        if aligner_type == "diamond":
            if db_type == "nucleotide":
                # DIAMOND doesn't support tblastn, so skip MEGARes for DIAMOND
                print("Warning: DIAMOND cannot be used with nucleotide databases (MEGARes). Skipping MEGARes alignment...")
                # Create empty output file
                with open(output_file, 'w') as f:
                    pass
                return
            else:
                # Use blastp for protein databases (protein query vs protein db)
                cmd = (f"{self.diamond_exe} blastp -q {input_file} -d {db_path}.dmnd -o {output_file} "
                       "--quiet -k 1 -e 5e-6 -f 6 qseqid sseqid pident qcovhsp mismatch gapopen qstart qend sstart send evalue bitscore")
        elif aligner_type == "blast":
            if db_type == "nucleotide":
                # Use tblastn for nucleotide databases (protein query vs translated nucleotide db)
                cmd = (f"{self.tblastn_exe} -query {input_file} -db {db_path} -out {output_file} "
                       '-max_target_seqs 1 -evalue 5e-6 -outfmt "6 qseqid sseqid pident qcovhsp mismatch gapopen qstart qend sstart send evalue bitscore"')
            else:
                # Use blastp for protein databases
                cmd = (f"{self.blastp_exe} -query {input_file} -db {db_path} -out {output_file} "
                       '-max_target_seqs 1 -evalue 5e-6 -outfmt "6 qseqid sseqid pident qcovhsp mismatch gapopen qstart qend sstart send evalue bitscore"')
                
        print(f"Aligning {input_file}...\n")
        os.system(cmd)

