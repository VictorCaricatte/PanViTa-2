# File: functions.py
# Description: Core processing logic (GBK parsing, Alignment, Data mining, Metadata Extraction)

import os
import sys
import re
from config import PanViTaConfig
import pandas as pd # Required for reading tsv/csv metadata files

class GBKProcessor:
    @staticmethod
    def extract_faa(gbk_file):
        """Extract protein sequences from GenBank file"""
        with open(gbk_file, 'rt') as gbk:
            cds = gbk.readlines()
            
        final = []
        for i in range(0, len(cds)):
            if "   CDS   " in cds[i]:
                locus_tag = ""
                product = ""
                sequence = []
                
                for j in range(i, len(cds)):
                    if ("/locus_tag=" in cds[j]) and (cds[j].count('"') == 2):
                        locus_tag = cds[j].replace("/locus_tag=", "")
                        locus_tag = locus_tag.strip()
                        locus_tag = locus_tag.replace("\"", "")
                        locus_tag = locus_tag.replace("\n", "")
                        
                    if ("/locus_tag=" in cds[j]) and (cds[j].count('"') == 1):
                        locus_tag = cds[j].replace("/locus_tag=", "")
                        locus_tag = locus_tag.strip()
                        locus_tag = locus_tag.replace("\"", "")
                        locus_tag = locus_tag.replace("\n", "")
                        locus_tag2 = cds[j + 1].strip()
                        locus_tag2 = locus_tag2.replace("\"", "")
                        locus_tag2 = locus_tag2.replace("\n", "")
                        locus_tag = f"{locus_tag}{locus_tag2}"
                        
                    elif "/product=" in cds[j]:
                        product = cds[j].replace("/product=", "")
                        product = product.strip()
                        product = product.replace("\"", "")
                        product = product.replace("\n", '')
                        
                    elif "/translation=" in cds[j]:
                        if cds[j].count("\"") == 2:
                            seq = cds[j].replace("/translation=", "")
                            seq = seq.replace("\"", "")
                            seq = seq.strip() + "\n"
                            header = ">" + locus_tag + " " + product + "\n"
                            final.append(header)
                            final.append(seq)
                            break
                        else:
                            seq = cds[j].replace("/translation=", "")
                            seq = seq.replace("\"", "")
                            seq = seq.strip() + "\n"
                            sequence.append(seq)
                            k = j + 1
                            if "\"" in cds[k]:
                                seq = cds[k].replace(" ", "")
                                seq = seq.replace("\"", "")
                                sequence.append(seq)
                            else:
                                while ("\"" not in cds[k]):
                                    seq = cds[k].replace(" ", "")
                                    seq = seq.replace("\"", "")
                                    sequence.append(seq)
                                    k = k + 1
                                seq = cds[k].replace(" ", "")
                                seq = seq.replace("\"", "")
                                sequence.append(seq)
                            header = ">" + locus_tag + " " + product + "\n"
                            final.append(header)
                            for l in sequence:
                                final.append(l)
                            break
        return final

    @staticmethod
    def extract_positions(gbk_file):
        """Extract CDS positions from GenBank file"""
        with open(gbk_file, 'rt') as gbk:
            cds = gbk.readlines()
            
        positions = {}
        lenght = 0
        totalcds = 0
        
        for i in range(0, len(cds)):
            if ("   CDS   " in cds[i]) and ("   ::" not in cds[i]):
                locus_tag = ""
                position = ""
                
                for j in range(i, len(cds)):
                    if "   CDS   " in cds[j]:
                        totalcds = totalcds + 1
                        position = cds[j].replace('\n', '')
                        position = position.replace("CDS", "")
                        position = position.strip()
                        
                        if (">" in position) or ("<" in position):
                            position = position.replace(">", "").replace("<", "")
                            
                        if "complement(join(" in position:
                            position = position.replace("complement(join(", "")
                            position = position.replace(")", "").strip()
                            position = position.split("..")
                            if "," in position[0]:
                                temp = position[0].split(",")
                                position[0] = temp[0]
                            if totalcds == 1:
                                try:
                                    position = [int(position[0]) + lenght, int(position[1]) + lenght]
                                except BaseException:
                                    position = [int(position[0]) + lenght, int(position[2]) + lenght]
                                    
                        elif "complement(" in position:
                            position = position.replace("complement(", "")
                            position = position.replace(")", "").strip()
                            position = position.split("..")
                            position = [int(position[0]) + lenght, int(position[1]) + lenght]
                            
                        elif "join(" in position:
                            position = position.replace("join(", "")
                            position = position.replace(")", "").strip()
                            position = position.split("..")
                            if "," in position[0]:
                                temp = position[0].split(",")
                                position[0] = temp[0]
                            if totalcds == 1:
                                try:
                                    position = [int(position[0]) + lenght, int(position[1]) + lenght]
                                except BaseException:
                                    position = [int(position[0]) + lenght, int(position[2]) + lenght]
                        else:
                            position = position.replace("<", "").replace(">", "").strip()
                            position = position.split("..")
                            position = [int(position[0]) + lenght, int(position[1]) + lenght]
                            
                    if ("/locus_tag=" in cds[j]) and (cds[j].count('"') == 2):
                        locus_tag = cds[j].replace("/locus_tag=", "")
                        locus_tag = locus_tag.strip()
                        locus_tag = locus_tag.replace("\"", "")
                        locus_tag = locus_tag.replace("\n", "")
                        positions[locus_tag] = str(position[0]) + "\t" + str(position[1])
                        break
                        
                    elif ("/locus_tag=" in cds[j]) and (cds[j].count('"') == 1):
                        locus_tag = cds[j].replace("/locus_tag=", "")
                        locus_tag = locus_tag.strip()
                        locus_tag = locus_tag.replace("\"", "")
                        locus_tag = locus_tag.replace("\n", "")
                        locus_tag2 = cds[j + 1].strip()
                        locus_tag2 = locus_tag2.replace("\"", "")
                        locus_tag2 = locus_tag2.replace("\n", "")
                        locus_tag = f"{locus_tag}{locus_tag2}"
                        positions[locus_tag] = str(position[0]) + "\t" + str(position[1])
                        break
                        
            if "CONTIG " in cds[i]:
                lenght = lenght + int(cds[i].strip().replace(")", "").split("..")[-1])
                
        return positions

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
        
        nucl_db_used = any(db in sys.argv for db in ["-megares", "-resfinder", "-victors-nucl"])
        
        if not diamond_available:
            print("DIAMOND not found. Using BLAST only.")
            return ["blast"], [self.blastp_exe], ["BLAST"]
        
        if not blast_available:
            if nucl_db_used:
                print("WARNING: Nucleotide database analysis requires BLAST (tblastn), but BLAST was not found!")
                print("Nucleotide databases will be skipped. Using DIAMOND for other databases.")
            else:
                print("BLAST not found. Using DIAMOND only.")
            return ["diamond"], [self.diamond_exe], ["DIAMOND"]
        
        # Both are available, ask user
        print("\nBoth DIAMOND and BLAST are available.")
        if nucl_db_used:
            print("Note: Nucleotide database analysis will use BLAST (tblastn).")
        print("Which aligner would you like to use?")
        print("1. DIAMOND only (faster)" + (" - Note: Nucleotide DBs will be skipped with DIAMOND" if nucl_db_used else ""))
        print("2. BLAST only (more sensitive)")
        print("3. Both DIAMOND and BLAST")
        
        while True:
            try:
                choice = input("Enter your choice (1, 2, or 3): ").strip()
                if choice == "1":
                    if nucl_db_used:
                        print("Warning: DIAMOND cannot analyze nucleotide databases. They will be skipped.")
                    return ["diamond"], [self.diamond_exe], ["DIAMOND"]
                elif choice == "2":
                    return ["blast"], [self.blastp_exe], ["BLAST"]
                elif choice == "3":
                    return ["diamond", "blast"], [self.diamond_exe, self.blastp_exe], ["DIAMOND", "BLAST"]
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")
            except (EOFError, KeyboardInterrupt):
                print("\nUsing BLAST by default (required for Nucleotide DBs)." if nucl_db_used else "\nUsing DIAMOND by default.")
                return (["blast"], [self.blastp_exe], ["BLAST"]) if nucl_db_used else (["diamond"], [self.diamond_exe], ["DIAMOND"])

    def align(self, input_file, db_path, output_file, aligner_type="diamond", db_type="protein", threads=1):
        """Perform alignment using the specified aligner and threads"""
        if aligner_type == "diamond":
            if db_type == "nucleotide":
                print(f"Warning: DIAMOND cannot be used with nucleotide databases. Skipping alignment for {os.path.basename(input_file)}...")
                with open(output_file, 'w') as f:
                    pass
                return f"Skipped {os.path.basename(input_file)} for DIAMOND (nucleotide db)"
            else:
                cmd = (f"{self.diamond_exe} blastp --threads {threads} -q {input_file} -d {db_path}.dmnd -o {output_file} "
                       "--quiet -k 1 -e 5e-6 -f 6 qseqid sseqid pident qcovhsp mismatch gapopen qstart qend sstart send evalue bitscore")
        elif aligner_type == "blast":
            if db_type == "nucleotide":
                cmd = (f"{self.tblastn_exe} -num_threads {threads} -query {input_file} -db {db_path} -out {output_file} "
                       '-max_target_seqs 1 -evalue 5e-6 -outfmt "6 qseqid sseqid pident qcovhsp mismatch gapopen qstart qend sstart send evalue bitscore"')
            else:
                cmd = (f"{self.blastp_exe} -num_threads {threads} -query {input_file} -db {db_path} -out {output_file} "
                       '-max_target_seqs 1 -evalue 5e-6 -outfmt "6 qseqid sseqid pident qcovhsp mismatch gapopen qstart qend sstart send evalue bitscore"')
        
        os.system(cmd)
        return f"Aligned {os.path.basename(input_file)}"

class DataProcessor:
    @staticmethod
    def extract_short_gene_name(product_desc, raw_id):
        """
        Generates or extracts a very readable short gene name from the product description. 
        """
        # Take the final part of the ID to ensure uniqueness in case we need a fallback (e.g., NP_269682).
        if '|' in raw_id:
            parts = [p for p in raw_id.split('|') if p]
            short_id = parts[-1] if parts else raw_id
        else:
            short_id = raw_id.split()[0]
            
        short_id = short_id.split('.')[0] 
        
        desc = product_desc.strip()
        stopwords = {'putative', 'probable', 'hypothetical', 'protein', 'precursor', 'type', 'the', 'a', 'an', 'family', 'domain', 'containing'}
        tokens = [t for t in desc.split() if t.lower() not in stopwords]
        
        if not tokens:
            return short_id
            
        for token in reversed(tokens):
            clean_token = re.sub(r'[^\w\s-]', '', token)
            if re.match(r'^[A-Za-z][a-zA-Z0-9_-]{1,7}$', clean_token):
                if any(c.isupper() for c in clean_token) or any(c.isdigit() for c in clean_token):
                    if len(clean_token) > 1 and clean_token.lower() not in ["atp", "abc", "dna", "rna"]:
                        return clean_token

        short_name = ""
        for w in tokens[:2]:
            clean_w = re.sub(r'[^\w\s]', '', w)
            if len(clean_w) > 4:
                short_name += clean_w[:4].capitalize()
            else:
                short_name += clean_w.capitalize()
                
        if short_name:
            id_suffix = short_id.split('_')[-1] if '_' in short_id else short_id[-4:]
            return f"{short_name}_{id_suffix}"
            
        return short_id

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
    def classify_virulence_factor(product_name):
        """
        Library for Victors categorization.
        Infers Virulence Category based on keywords in the product description.
        Refinado sem substrings curtas que causam overlaps.
        """
        prod_lower = product_name.lower()
        
        categories = {
            # Adherence
            "adhesin": "Adherence",
            "adhesion": "Adherence",
            "pili": "Adherence",
            "pilus": "Adherence",
            "fimbria": "Adherence",
            "agglutinin": "Adherence",
            "attachment": "Adherence",
            "intimin": "Adherence",
            "fibronectin": "Adherence",
            "collagen": "Adherence",
            "biofilm": "Biofilm Formation",
            "exopolysaccharide": "Biofilm Formation",
            
            # Invasion
            "invasin": "Invasion",
            "invasion": "Invasion",
            "internalin": "Invasion",
            "penetration": "Invasion",
            
            # Toxins
            "toxin": "Toxin",
            "hemolysin": "Toxin",
            "cytolysin": "Toxin",
            "exotoxin": "Toxin",
            "enterotoxin": "Toxin",
            "shiga": "Toxin",
            "cholera": "Toxin",
            "pertussis": "Toxin",
            "tetanus": "Toxin",
            "botulinum": "Toxin",
            "anthrax": "Toxin",
            "streptolysin": "Toxin",
            "leukocidin": "Toxin",
            "superantigen": "Toxin",
            "aerolysin": "Toxin",
            
            # Enzymes / Hydrolytic
            "protease": "Enzyme",
            "peptidase": "Enzyme",
            "lipase": "Enzyme",
            "phospholipase": "Enzyme",
            "urease": "Enzyme",
            "coagulase": "Enzyme",
            "kinase": "Enzyme",
            "hyaluronidase": "Enzyme",
            "nuclease": "Enzyme",
            "elastase": "Enzyme",
            "collagenase": "Enzyme",
            "neuraminidase": "Enzyme",
            "transferase": "Enzyme",
            "synthetase": "Enzyme",
            "synthase": "Enzyme",
            "lysozyme": "Enzyme",
            "isomerase": "Enzyme",
            "reductase": "Enzyme",
            "ligase": "Enzyme",
            "helicase": "Enzyme",
            "mutase": "Enzyme",
            "oxidase": "Enzyme",
            
            # Iron / Nutrient Uptake
            "siderophore": "Iron Uptake",
            "iron": "Iron Uptake",
            "heme": "Iron Uptake",
            "ferric": "Iron Uptake",
            "ferrous": "Iron Uptake",
            "transferrin": "Iron Uptake",
            "lactoferrin": "Iron Uptake",
            "enterobactin": "Iron Uptake",
            "aerobactin": "Iron Uptake",
            "zinc": "Nutrient Uptake",
            "manganese": "Nutrient Uptake",
            "magnesium": "Nutrient Uptake",
            
            # Immune Evasion
            "capsul": "Immune Evasion",
            "alginate": "Immune Evasion",
            "lipopolysaccharide": "Immune Evasion",
            "surface protein": "Immune Evasion",
            "complement": "Immune Evasion",
            "macrophage": "Immune Evasion",
            "phagocytosis": "Immune Evasion",
            "evasion": "Immune Evasion",
            "serum resistance": "Immune Evasion",
            "o-antigen": "Immune Evasion",
            "k-antigen": "Immune Evasion",
            
            # Secretion System
            "secretion system": "Secretion System",
            "t1ss": "Secretion System",
            "t2ss": "Secretion System",
            "t3ss": "Secretion System",
            "t4ss": "Secretion System",
            "t5ss": "Secretion System",
            "t6ss": "Secretion System",
            "t7ss": "Secretion System",
            "effector": "Secretion System",
            "translocator": "Secretion System",
            "export": "Secretion System",
            "needle": "Secretion System",
            "chaperone": "Secretion System",
            
            # Motility
            "flagell": "Motility",
            "chemotaxis": "Motility",
            "motility": "Motility",
            "motor": "Motility",
            "swarming": "Motility",
            "swimming": "Motility",
            
            # Regulation
            "regulator": "Regulation",
            "sensor": "Regulation",
            "quorum": "Regulation",
            "transcription factor": "Regulation",
            "activator": "Regulation",
            "repressor": "Regulation",
            "two-component": "Regulation",
            "sigma factor": "Regulation",
            
            # Outer Membrane / Surface
            "porin": "Outer Membrane",
            "outer membrane": "Outer Membrane",
            "surface antigen": "Outer Membrane",
            "lipoprotein": "Outer Membrane",
            "peptidoglycan": "Outer Membrane",
            "teichoic": "Outer Membrane",
            
            # Efflux / Resistance
            "efflux": "Efflux Pump / Resistance",
            "pump": "Efflux Pump / Resistance",
            "resistance": "Efflux Pump / Resistance",
            "multidrug": "Efflux Pump / Resistance",
            "transporter": "Efflux Pump / Resistance",
            "abc transporter": "Efflux Pump / Resistance",
            
            # Stress Survival
            "stress": "Stress Survival",
            "survival": "Stress Survival",
            "heat shock": "Stress Survival",
            "cold shock": "Stress Survival",
            "detoxification": "Stress Survival",
            "catalase": "Stress Survival",
            "superoxide": "Stress Survival",
            
            # Mobile Elements
            "plasmid": "Mobile Element",
            "transposon": "Mobile Element",
            "integrase": "Mobile Element",
            "phage": "Mobile Element",
            "prophage": "Mobile Element",
            "island": "Mobile Element"
        }
        
        for key, category in categories.items():
            if key in prod_lower:
                return category
                
        return "Other Virulence Factor"

    @staticmethod
    def extract_keys(db_param, dbpath):
        """
        Extract gene keys and annotations from database files.
        Returns 3 dictionaries to support comprehensive reporting for all databases.
        """
        comp = {}
        meta1 = {} 
        meta2 = {} 
        
        print(f"Extracting gene keys and metadata for {db_param}...")
        
        def load_metadata_csv(csv_path):
            if os.path.exists(csv_path):
                print(f"  - Loading existing metadata library: {os.path.basename(csv_path)}")
                try:
                    df = pd.read_csv(csv_path)
                    for _, row in df.iterrows():
                        ident = str(row['ID'])
                        gene = str(row['Gene'])
                        c1 = str(row['Category1'])
                        c2 = str(row['Category2'])
                        
                        comp[ident] = gene
                        meta1[gene] = c1
                        meta2[gene] = c2
                    return True
                except Exception as e:
                    print(f"  - Error loading metadata CSV: {e}. Rebuilding...")
            return False

        if "-bacmet" == db_param:
            try:
                with open(os.path.join(dbpath, 'bacmet_2.fasta'), 'rt') as bacmetFile:
                    bacmet = bacmetFile.readlines()
                
                for i in bacmet:
                    if '>' in i:
                        parts = i.split('|')
                        if len(parts) >= 2:
                            ident = parts[0][1:]
                            gene = parts[1]
                            comp[str(ident)] = str(gene)

                bacmet_txt = os.path.join(dbpath, 'bacmet_2.txt')
                
                if os.path.exists(bacmet_txt):
                    try:
                        df = pd.read_csv(bacmet_txt, sep='\t', encoding='latin-1', on_bad_lines='skip')
                        df.columns = [c.strip() for c in df.columns]
                        
                        for _, row in df.iterrows():
                            gene_name = str(row.get('Gene_name', 'Unknown')).strip()
                            compound = str(row.get('Compound', 'Unknown')).strip()
                            description = str(row.get('Description', 'Biocide/Metal Resistance')).strip()
                            
                            meta1[gene_name] = compound
                            meta2[gene_name] = description
                    except Exception as e:
                         print(f"Warning: Failed to parse BacMet annotation file structure: {e}")

                print(f"  - BacMet: {len(comp)} gene mappings extracted")
                
            except Exception as e:
                print(f"Warning: Error reading BacMet database: {e}")
        
        elif "-card" == db_param:
            try:
                with open(os.path.join(dbpath, 'card_protein_homolog_model.fasta'), 'rt') as cardFile:
                    card = cardFile.readlines()
                
                for i in card:
                    if '>' in i:
                        parts = i.split("|")
                        if len(parts) >= 4:
                            ident = parts[1]
                            gene = parts[3].split()[0]
                            comp[str(ident)] = str(gene)
                
                aro_path = os.path.join(dbpath, 'aro_index.tsv')
                if os.path.exists(aro_path):
                    try:
                        df_aro = pd.read_csv(aro_path, sep='\t')
                        df_aro['Resistance Mechanism'] = df_aro['Resistance Mechanism'].fillna('Unknown')
                        df_aro['Drug Class'] = df_aro['Drug Class'].fillna('Unknown')
                        
                        for _, row in df_aro.iterrows():
                            gene_key = str(row['ARO Name'])
                            meta1[gene_key] = str(row['Drug Class'])
                            meta2[gene_key] = str(row['Resistance Mechanism'])
                            
                    except Exception as e:
                        print(f"Warning: Failed to parse CARD annotation file: {e}")

                print(f"  - CARD: {len(comp)} gene mappings extracted")
                
            except Exception as e:
                print(f"Warning: Error reading CARD database: {e}")
        
        elif "-vfdb" == db_param:
            try:
                with open(os.path.join(dbpath, 'vfdb_core.fasta'), 'rt') as vfdbFile:
                    vfdb = vfdbFile.readlines()
                
                for i in vfdb:
                    if '>' in i:
                        mech = "Unknown"
                        category = "Unknown"
                        
                        bracket_content = re.findall(r"\[(.*?)\]", i)
                        for content in bracket_content:
                            if " - " in content and "VF" in content:
                                parts = content.split(" - ")
                                if len(parts) == 2:
                                    mech = parts[0].split(' (')[0]
                                    category = parts[1].split(' (')[0]
                        
                        if '(' in i and ')' in i:
                            start = i.find('(') + 1
                            end = i.find(')', start)
                            if start < end:
                                gene_part = i[start:end]
                                if '|' in gene_part:
                                    parts = gene_part.split('|')
                                    ident = parts[-1] 
                                else:
                                    ident = gene_part
                            else:
                                continue
                            
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
                            meta1[str(gene)] = str(mech)
                            meta2[str(gene)] = str(category)
                
                print(f"  - VFDB: {len(comp)} gene mappings extracted")
                
            except Exception as e:
                print(f"Warning: Error reading VFDB database: {e}")
        
        elif "-megares" == db_param:
            try:
                with open(os.path.join(dbpath, 'megares_v3.fasta'), 'rt') as megaresFile:
                    megares = megaresFile.readlines()
                
                for i in megares:
                    if '>' in i:
                        parts = i.split('|')
                        if len(parts) >= 5:
                            ident = parts[0][1:] 
                            drug_class = parts[2]
                            mechanism = parts[3] 
                            gene = parts[4]      
                            
                            gene_clean = str(gene).strip()
                            comp[str(ident)] = gene_clean
                            meta1[gene_clean] = str(drug_class).strip()
                            meta2[gene_clean] = str(mechanism).strip()
                
                print(f"  - MEGARes: {len(comp)} gene mappings extracted")
                
            except Exception as e:
                print(f"Warning: Error reading MEGARes database: {e}")

        elif "-resfinder" == db_param:
            csv_path = os.path.join(dbpath, "resfinder_metadata_library_.csv")
            if not load_metadata_csv(csv_path):
                try:
                    library_data = []
                    with open(os.path.join(dbpath, 'resfinder.fasta'), 'rt') as f:
                        for i in f:
                            if '>' in i:
                                # Captura a linha completa
                                full_header = i.strip().replace('>', '')
                                # Divide pelo primeiro termo caso tenha espaços e depois por '_'
                                parts = full_header.split()[0].split('_')
                                gene = parts[0]
                                
                                rest_of_header = parts[1:] if len(parts) > 1 else []
                                
                                variant_acc = "Unknown"
                                resistance = "Unknown"
                                
                                # Extrai Variante, Accession e Resistência/Fenótipo
                                if len(rest_of_header) >= 2:
                                    variant_acc = f"{rest_of_header[0]} {rest_of_header[1]}"
                                    if len(rest_of_header) > 2:
                                        resistance = " ".join(rest_of_header[2:])
                                elif len(rest_of_header) == 1:
                                    variant_acc = rest_of_header[0]
                                
                                # Fallback: se a resistência não foi encontrada separada por '_', busca no restante da string
                                full_line_parts = i.strip().replace('>', '').split()
                                if resistance == "Unknown" and len(full_line_parts) > 1:
                                    resistance = " ".join(full_line_parts[1:])
                                    
                                if resistance == "Unknown":
                                    resistance = "Unspecified Resistance"
                                
                                comp[full_header.split()[0]] = gene
                                meta1[gene] = resistance
                                meta2[gene] = variant_acc
                                
                                library_data.append({"ID": full_header.split()[0], "Gene": gene, "Category1": resistance, "Category2": variant_acc})
                    
                    if library_data: pd.DataFrame(library_data).to_csv(csv_path, index=False)
                except Exception as e: print(f"Error ResFinder: {e}")

        elif "-argannot" == db_param:
            csv_path = os.path.join(dbpath, "argannot_metadata_library_.csv")
            if not load_metadata_csv(csv_path):
                try:
                    library_data = []
                    with open(os.path.join(dbpath, 'argannot.fasta'), 'rt') as f:
                        for i in f:
                            if '>' in i:
                                full_id = i.strip().split()[0].replace('>', '')
                                
                                match = re.match(r"\((.*?)\)(.*)", full_id)
                                if match:
                                    ab_class = match.group(1)
                                    rest = match.group(2)
                                    gene = rest.split(':')[0]
                                else:
                                    gene = full_id.split(':')[0]
                                    ab_class = "Unknown"

                                comp[full_id] = gene
                                
                                meta1[gene] = ab_class
                                map_mech = {'Bla': 'Beta-Lactam', 'Tet': 'Tetracycline', 'AGly': 'Aminoglycoside', 
                                            'MLS': 'Macrolide', 'Phe': 'Phenicol', 'Sul': 'Sulfonamide', 
                                            'Dfr': 'Trimethoprim', 'Qui': 'Quinolone', 'Gly': 'Glycopeptide'}
                                meta2[gene] = map_mech.get(ab_class, f"{ab_class} Resistance")
                                
                                library_data.append({"ID": full_id, "Gene": gene, "Category1": ab_class, "Category2": meta2[gene]})
                    
                    if library_data: pd.DataFrame(library_data).to_csv(csv_path, index=False)
                except Exception as e: print(f"Error ARG-ANNOT: {e}")

        elif db_param in ["-victors", "-victors-nucl"]:
            csv_name = "victors_metadata_library_.csv" if db_param == "-victors" else "victors_nucl_metadata_library_.csv"
            csv_path = os.path.join(dbpath, csv_name)
            target_fasta = 'victorsprotein.fasta' if db_param == "-victors" else 'victorsgene.fasta'
            
            if not load_metadata_csv(csv_path):
                try:
                    library_data = []
                    with open(os.path.join(dbpath, target_fasta), 'rt', encoding='utf-8', errors='replace') as f:
                        for i in f:
                            if '>' in i:
                                full_id = i.strip().split()[0].replace('>', '')
                                parts = i.replace('>','').split('|')
                                
                                ids_to_map = [full_id]
                                if len(parts) > 1:
                                    ids_to_map.append(parts[1]) 
                                    if len(parts) > 3: ids_to_map.append(parts[3]) 
                                
                                # 1. Extração do Produto Real
                                product = "Unknown"
                                prod_match = re.search(r'\[protein=(.*?)\]', i) or re.search(r'\[product=(.*?)\]', i)
                                if prod_match:
                                    product = prod_match.group(1).strip()
                                elif 'product=' in i:
                                    product = i.split('product=')[1].split(']')[0]
                                elif len(parts) >= 5:
                                    desc = parts[4].strip()
                                    product = desc.rsplit('[', 1)[0].strip() if '[' in desc else desc
                                elif len(parts) >= 3:
                                    product = parts[-1].strip()
                                
                                product_clean = product.replace('putative ', '').replace('probable ', '').strip()
                                
                                # 2. Extração de um nome de Gene Curto, Legível e Eficiente para gráficos
                                gene_name = "Unknown"
                                gene_match = re.search(r'\[gene=(.*?)\]', i)
                                if gene_match:
                                    gene_name = gene_match.group(1).strip()
                                else:
                                    # Fallback inovador: Chama a nova função que cria nomes limpos!
                                    gene_name = DataProcessor.extract_short_gene_name(product_clean, full_id)
                                
                                cat = DataProcessor.classify_virulence_factor(product_clean)
                                
                                for ident in ids_to_map:
                                    comp[ident] = gene_name
                                
                                meta1[gene_name] = product_clean
                                meta2[gene_name] = cat
                                
                                library_data.append({"ID": full_id, "Gene": gene_name, "Category1": product_clean, "Category2": cat})
                    
                    if library_data: pd.DataFrame(library_data).to_csv(csv_path, index=False)
                except Exception as e: print(f"Error Victors: {e}")

        elif "-custom" == db_param:
            try:
                with open(os.path.join(dbpath, 'custom.fasta'), 'rt') as customFile:
                    lines = customFile.readlines()
                
                for i in lines:
                    if '>' in i:
                        header = i.strip().replace('>', '')
                        ident = header.split()[0]
                        gene = ident 
                        comp[ident] = gene
                        meta1[gene] = "Custom Database"
                        meta2[gene] = "Custom Mechanism"
                        
                print(f"  - Custom DB: {len(comp)} gene mappings extracted")
            except Exception as e:
                print(f"Warning: Error reading Custom database: {e}")
        
        if len(comp) == 0:
            print(f"Warning: No gene mappings found for {db_param}! This may cause issues with analysis.")
        
        return comp, meta1, meta2

    @staticmethod
    def process_tabular_output(tabular_dir, comp, meta1, meta2, outputs, db_param, strains):
        """Process BLAST/DIAMOND output into tabular reports (CSV/Excel)"""
        
        if db_param == "-bacmet":
            label_1 = "Compound"
            label_2 = "Description"
        elif db_param == "-megares":
            label_1 = "Drug_Class"
            label_2 = "Mechanism"
        elif db_param in ["-victors", "-victors-nucl"]:
            label_1 = "Product"
            label_2 = "Function_Category"
        elif db_param == "-argannot":
            label_1 = "Antibiotic_Class"
            label_2 = "Mechanism"
        elif db_param == "-resfinder":
            label_1 = "Resistance_Type"
            label_2 = "Phenotype_Mechanism"
        else:
            label_1 = "Product"
            label_2 = "Category"

        print(f"Processing tabular outputs for {db_param}...")
        
        if not comp:
            print("  Skipping detailed report generation due to missing gene mappings.")
            return

        all_results = []
        
        if not os.path.exists(tabular_dir):
            print(f"Warning: Tabular directory {tabular_dir} not found.")
            return

        files = [f for f in os.listdir(tabular_dir) if f.endswith(".txt") or f.endswith(".tsv")]
        
        for file in files:
            strain = file.replace(".txt", "").replace(".tsv", "")
            filepath = os.path.join(tabular_dir, file)
            
            if os.stat(filepath).st_size == 0:
                continue
                
            try:
                df = pd.read_csv(filepath, sep='\t', header=None)
                
                for _, row in df.iterrows():
                    sseqid = str(row[1]) 
                    pident = row[2]      
                    
                    gene_key = sseqid
                    if gene_key not in comp:
                        if "|" in gene_key:
                             parts = gene_key.split("|")
                             if len(parts) > 1 and parts[1] in comp: 
                                 gene_key = parts[1]
                             elif parts[0] in comp: 
                                 gene_key = parts[0]
                    
                    gene_name = comp.get(gene_key, sseqid)
                    
                    val_meta1 = meta1.get(gene_name, "Unknown")
                    val_meta2 = meta2.get(gene_name, "Unknown")
                    
                    all_results.append({
                        'Genome': strain,
                        'Gene': gene_name,
                        'Identity': pident,
                        label_1: val_meta1,
                        label_2: val_meta2,
                    })
                    
            except Exception as e:
                print(f"  Error processing file {file}: {e}")

        if all_results:
            result_df = pd.DataFrame(all_results)
            
            cols = ['Genome', 'Gene', 'Identity', label_1, label_2]
            existing_cols = [c for c in cols if c in result_df.columns]
            result_df = result_df[existing_cols]
            
            output_csv = f"{db_param.replace('-', '')}_detailed_report.csv"
            output_xlsx = f"{db_param.replace('-', '')}_detailed_report.xlsx"
            
            result_df.to_csv(output_csv, index=False)
            outputs.append(output_csv)
            
            try:
                result_df.to_excel(output_xlsx, index=False)
                outputs.append(output_xlsx)
            except:
                pass
                
            print(f"  Detailed report generated: {output_csv}")