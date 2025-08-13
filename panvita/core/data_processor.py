import os
import re
import sys


class DataProcessor:
    @staticmethod
    def blastmining_specific(input_file, input_dir, output_dir):
        """Filter alignment results based on thresholds"""
        _in = os.path.join(input_dir, input_file)
        _out = os.path.join(output_dir, input_file)
        evalue = 5e-06
        identidade = 70
        cobertura = 70
        
        if "-i" in sys.argv:
            try:
                identidade = float(sys.argv[sys.argv.index("-i") + 1])
            except BaseException:
                identidade = 70
                
        if "-c" in sys.argv:
            try:
                cobertura = float(sys.argv[sys.argv.index("-c") + 1])
            except BaseException:
                cobertura = 70
                
        print(_out)
        try:
            with open(_in, 'rt') as fileO:
                file = fileO.readlines()
                
            with open(_out, 'w') as saida:
                for j in file:
                    linha = j.split('\t')
                    if float(linha[10]) <= evalue:
                        if float(linha[2]) >= identidade:
                            if float(linha[3]) >= cobertura:
                                saida.write(j)
        except BaseException:
            print(f"Warning: mining file not found - {_in}")

    @staticmethod
    def extract_keys(db_param, dbpath):
        """Extract gene keys and annotations from database files"""
        comp = {}
        genes_comp = {}
        
        print(f"Extracting gene keys for {db_param}...")
        
        # BACMET
        if "-bacmet" == db_param:
            try:
                with open(os.path.join(dbpath, 'bacmet_2.fasta'), 'rt') as bacmetFile:
                    bacmet = bacmetFile.readlines()
                
                for i in bacmet:
                    if '>' in i:
                        # Format: >BAC0001|abeM|tr|Q5FAM9|Q5FAM9_ACIBA
                        parts = i.split('|')
                        if len(parts) >= 2:
                            ident = parts[0][1:]  # Remove '>' and get BAC0001
                            gene = parts[1]       # Get abeM
                            comp[str(ident)] = str(gene)
                
                print(f"  - BacMet: {len(comp)} gene mappings extracted")
                
            except Exception as e:
                print(f"Warning: Error reading BacMet database: {e}")
        
        # CARD
        elif "-card" == db_param:
            try:
                with open(os.path.join(dbpath, 'card_protein_homolog_model.fasta'), 'rt') as cardFile:
                    card = cardFile.readlines()
                
                for i in card:
                    if '>' in i:
                        # Format: >gb|ACT97415.1|ARO:3002999|CblA-1 [mixed culture bacterium AX_gF3SD01_15]
                        parts = i.split("|")
                        if len(parts) >= 4:
                            ident = parts[1]     # Get ACT97415.1
                            gene = parts[3].split()[0]  # Get CblA-1 (before space)
                            comp[str(ident)] = str(gene)
                
                print(f"  - CARD: {len(comp)} gene mappings extracted")
                
            except Exception as e:
                print(f"Warning: Error reading CARD database: {e}")
        
        # VFDB
        elif "-vfdb" == db_param:
            try:
                with open(os.path.join(dbpath, 'vfdb_core.fasta'), 'rt') as vfdbFile:
                    vfdb = vfdbFile.readlines()
                
                for i in vfdb:
                    if '>' in i:
                        # Format: >VFG037176(gb|WP_001081735) (plc1) phospholipase C [Phospholipase C (VF0470) - Exotoxin (VFC0235)] [Acinetobacter baumannii ACICU]
                        # Extract mechanism using regex
                        mech = re.findall(r"(?<=\)\s-\s)[A-z\/\-\s]*(?=\s\()", i, flags=0)
                        if len(mech) == 1:
                            mech = mech[0]
                        else:
                            mech = "Unknown"
                        
                        # Extract identifier and gene name
                        if '(' in i and ')' in i:
                            # Get the part between first ( and first )
                            start = i.find('(') + 1
                            end = i.find(')', start)
                            if start < end:
                                gene_part = i[start:end]
                                # Handle different formats like (gb|WP_001081735) or (plc1)
                                if '|' in gene_part:
                                    parts = gene_part.split('|')
                                    ident = parts[-1]  # Get the last part after |
                                else:
                                    ident = gene_part
                            else:
                                continue
                            
                            # Get gene name from the second parentheses if exists
                            second_paren = i.find('(', end)
                            if second_paren != -1:
                                gene_end = i.find(')', second_paren)
                                if gene_end != -1:
                                    gene = i[second_paren + 1:gene_end]
                                else:
                                    gene = ident
                            else:
                                gene = ident
                            
                            comp[str(ident)] = str(gene)
                            genes_comp[str(gene)] = str(mech)
                
                print(f"  - VFDB: {len(comp)} gene mappings extracted")
                print(f"  - VFDB mechanisms: {len(genes_comp)} mechanisms extracted")
                
            except Exception as e:
                print(f"Warning: Error reading VFDB database: {e}")
        
        # MEGARes
        elif "-megares" == db_param:
            try:
                with open(os.path.join(dbpath, 'megares_v3.fasta'), 'rt') as megaresFile:
                    megares = megaresFile.readlines()
                
                unique_genes = set()  # Track unique gene names for debugging
                mechanisms_comp = {}  # Additional mapping for mechanisms
                
                for i in megares:
                    if '>' in i:
                        # Format: >MEG_1|Drugs|Aminoglycosides|Aminoglycoside-resistant_16S_ribosomal_subunit_protein|A16S|RequiresSNPConfirmation
                        parts = i.split('|')
                        if len(parts) >= 5:
                            ident = parts[0][1:]  # Remove '>' and get MEG_1
                            drug_type = parts[1]  # Get Drugs
                            drug_class = parts[2] # Get Aminoglycosides  
                            mechanism = parts[3]  # Get Aminoglycoside-resistant_16S_ribosomal_subunit_protein
                            gene = parts[4]       # Get A16S
                            
                            gene_clean = str(gene).strip()
                            comp[str(ident)] = gene_clean  # Clean whitespace/newlines
                            genes_comp[gene_clean] = str(drug_class).strip()  # Map gene to drug class
                            mechanisms_comp[gene_clean] = str(mechanism).strip()  # Map gene to mechanism
                            unique_genes.add(gene_clean)
                
                print(f"  - MEGARes: {len(comp)} gene mappings extracted")
                print(f"  - MEGARes drug classes: {len(set(genes_comp.values()))} unique drug classes")
                print(f"  - MEGARes mechanisms: {len(set(mechanisms_comp.values()))} unique mechanisms")
                print(f"  - MEGARes unique genes found: {len(unique_genes)}")
                
                # Debug: Print first few unique genes
                if unique_genes:
                    sample_genes = sorted(list(unique_genes))[:10]
                    print(f"  - Sample genes: {', '.join(sample_genes)}")
                
                # Return the mechanisms mapping for MEGARes as third element
                return comp, genes_comp, mechanisms_comp
                
            except Exception as e:
                print(f"Warning: Error reading MEGARes database: {e}")
        
        if len(comp) == 0:
            print(f"Warning: No gene mappings found for {db_param}! This may cause issues with analysis.")
        
        return comp, genes_comp

