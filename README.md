[README.md](https://github.com/user-attachments/files/25460929/README.md)
# PanViTa 2 — Pan Virulence and resisTance Analysis

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Version](https://img.shields.io/badge/Version-2.0.4-red.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey.svg)]()
[![DOI](https://img.shields.io/badge/DOI-10.3389%2Ffbinf.2023.1070406-blue.svg)](https://doi.org/10.3389/fbinf.2023.1070406)

##  About PanViTa 2

**PanViTa 2** (Pan Virulence and resisTance Analysis) is a bioinformatics pipeline for large-scale comparative genomics of prokaryotes. It automatically screens multiple annotated genomes against curated databases of antimicrobial resistance genes and virulence factors, classifies genes into Core, Accessory, and Exclusive categories, and produces publication-ready visualizations and tabular reports — all from a single command.

PanViTa 2 is a complete rewrite of the original PanViTa ([Rodrigues *et al.*, 2023](https://doi.org/10.3389/fbinf.2023.1070406)), featuring a fully modular architecture, parallel alignment execution, seven supported databases, advanced visualizations (UpSet plots, PCoA, co-occurrence networks), and cross-platform support.

##  What is it for?

- **Resistance Analysis**: Identification of resistance genes to antibiotics, heavy metals, and biocides
- **Virulence Factors**: Detection of pathogenicity and virulence-related genes
- **Comparative Genomics**: Simultaneous comparison of any number of genomes
- **Molecular Epidemiology**: Studies of resistance and virulence dissemination across strains
- **Genomic Surveillance**: Monitoring of pathogen resistance profiles at the population level
- **Pan-genome Studies**: Classification of the resistome/virulome into core, accessory, and strain-exclusive components

---

##  Main Features

###  Supported Databases

| Flag | Database | Focus |
|------|----------|-------|
| `-card` | **CARD** — Comprehensive Antibiotic Resistance Database | Antibiotic resistance |
| `-bacmet` | **BacMet** — Antibacterial Biocide and Metal Resistance Genes (Experimentally Confirmed) | Metal and biocide resistance |
| `-megares` | **MEGARes v3** — MEGARes Antimicrobial Resistance Database | Antimicrobial resistance |
| `-vfdb` | **VFDB** — Virulence Factor Database (core set A) | Virulence factors |
| `-resfinder` | **ResFinder** — Resistance gene identification | Antibiotic resistance |
| `-argannot` | **ARG-ANNOT** — Antibiotic Resistance Gene Annotation v6 | Antibiotic resistance |
| `-victors` | **Victors** — Victors Virulence Factors Database | Virulence factors |
| `-custom [path]` | **Custom** — User-provided FASTA database | Any |

All databases are **downloaded and indexed automatically** on first use and can be updated at any time with `-update`.

###  Alignment Tools

| Tool | Flag | Description |
|------|------|-------------|
| **DIAMOND** | `-diamond` | Fast protein aligner — recommended for large datasets |
| **BLAST** | `-blast` | Traditional high-precision protein alignment |
| **Both** | `-both` | Runs DIAMOND and BLAST independently, generating separate result sets for cross-validation |

Both tools are downloaded and managed automatically.

###  Generated Visualizations

| Output | Description |
|--------|-------------|
| **Heatmap / Clustermap** | Hierarchically clustered presence/absence matrix coloured by identity (%) |
| **Pan-genome Rarefaction Curves** | Permutation-based pan-genome and core-genome curves as genomes accumulate |
| **UpSet Plot** | Intersection structure of gene sets across all genomes |
| **PCoA** | Principal Coordinates Analysis projecting genomes by gene-content dissimilarity |
| **Co-occurrence Network** | Pearson correlation network of gene co-occurrence (r > 0.75) coloured by category |
| **Distribution Bar Charts** | Core/Accessory/Exclusive breakdown per drug class, resistance mechanism, or virulence category |
| **Detailed Reports** | Long-format CSV and Excel reports per genome per gene with metadata |

###  Advanced Features

- **Automatic download** of genomes from NCBI (GenBank and FASTA formats)
- **Automatic genome annotation** via PROKKA integration
- **BioSample metadata extraction** including MLST typing
- **Parallel alignment execution** — genomes are aligned concurrently for speed
- **Gene classification** into Core / Accessory / Exclusive categories
- **Save-genes mode** — exports found gene sequences in `.faa` files per genome
- **Cross-platform support** (Windows and Linux)
- **Customizable thresholds** for identity and coverage
- **Automatic error logging** with timestamped `.err` files

---

##  Installation

### Clone the Repository

```bash
git clone https://github.com/VictorCaricatte/PanViTa-2.git
cd PanVITA-2.0
```

### Python Dependencies

```bash
pip install pandas numpy matplotlib seaborn networkx scikit-learn scipy upsetplot wget openpyxl
```

Or install from the requirements file:

```bash
pip install -r requirements.txt
```

### System Dependencies

#### Linux (Ubuntu / Debian)
```bash
sudo apt update
sudo apt install build-essential libstdc++6 libgomp1
```

#### Linux (CentOS / RHEL)
```bash
sudo yum groupinstall 'Development Tools'
sudo yum install libstdc++-devel libgomp
```

#### Windows
Install the **Microsoft Visual C++ Redistributable** before running PanViTa 2:
- [Download x64](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- [Download x86](https://aka.ms/vs/17/release/vc_redist.x86.exe)

### System Libraries Reference

| Function | Windows | Linux |
|----------|---------|-------|
| C++ standard library | `msvcp140.dll` | `libstdc++.so.6` |
| Compiler runtime | `vcruntime140.dll` | `libgcc_s.so.1` |
| Standard C library | `msvcrt.dll` | `libc.so.6` |
| OpenMP support | `vcomp140.dll` | `libgomp.so.1` |

### Optional Tools

The following tools must be installed separately by the user if needed:

| Tool | Purpose | Installation |
|------|---------|-------------|
| [PROKKA](https://github.com/tseemann/prokka) | Prokaryotic genome annotation | `conda install -c bioconda prokka` |
| [mlst](https://github.com/tseemann/mlst) | Multi-locus sequence typing | `conda install -c bioconda mlst` |

> **Note:** If using conda, you may need to deactivate it before running PanViTa 2 to avoid conflicts with auto-downloaded executables: `conda deactivate`

---

##  Supported Input Formats

- **GBK / GBF**: GenBank files from PROKKA annotation or NCBI
- **GBFF**: GenBank files downloaded from NCBI (**must** have `.gbf` or `.gbff` extension)
- **CSV**: NCBI Assembly metadata tables for the download modes (`-g`, `-a`, `-b`, `-m`)

> All input files should be in the working directory or referenced by path. GenBank files must contain `CDS` feature blocks with `/locus_tag` and `/translation` qualifiers.

---

##  How to Use

###  Running PanViTa 2

There are **two ways** to run PanViTa 2:

---

#### 1.  Graphical Interface (Recommended for new users)

PanViTa 2 now includes a graphical user interface (GUI) built with Tkinter. To launch it, simply run:

```bash
python3 interface.py
```

The interface allows you to configure databases, alignment tools, thresholds, and input files through a user-friendly window — no need to memorize command-line flags.

> ⚠️ **Note:** The graphical interface is currently under active development. Some features may not yet be available. Feedback and bug reports are welcome via [GitHub Issues](https://github.com/VictorCaricatte/PanViTa-2/issues).

---

#### 2.  Command Line (Recommended for advanced users and pipelines)

For scripting, automation, or HPC environments, PanViTa 2 can be run directly from the terminal:

```bash
python3 panvita.py [DATABASES] [PARAMETERS] file1.gbk file2.gbk ...
```

---

#### 3.  Standalone Executable (Coming Soon)

A standalone executable version of PanViTa 2 is currently **in development**. It will allow users to run the tool without installing Python or any dependencies. Stay tuned for updates on the [GitHub repository](https://github.com/VictorCaricatte/PanViTa-2).

---

### Basic Syntax

```bash
python3 panvita.py [DATABASES] [PARAMETERS] file1.gbk file2.gbk ...
```

### Usage Examples

```bash
# Screen genomes against CARD and VFDB
python3 panvita.py -card -vfdb strain1.gbk strain2.gbk strain3.gbk

# Use all databases at once
python3 panvita.py -card -vfdb -bacmet -megares -resfinder -argannot -victors *.gbk

# Use DIAMOND only with custom thresholds
python3 panvita.py -diamond -card -i 80 -c 80 *.gbk

# Use BLAST only
python3 panvita.py -blast -vfdb *.gbk

# Run both aligners and generate independent result sets
python3 panvita.py -both -card -vfdb *.gbk

# Use a custom protein FASTA database
python3 panvita.py -custom /path/to/mydb.fasta *.gbk

# Keep intermediate files and save found gene sequences
python3 panvita.py -card -keep -save-genes *.gbk

# Update all databases and tools
python3 panvita.py -update
```

### Main Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-i [value]` | Minimum identity (%) to consider a gene present | `70` |
| `-c [value]` | Minimum coverage (%) to consider a gene present | `70` |
| `-diamond` | Force DIAMOND only | — |
| `-blast` | Force BLAST only | — |
| `-both` | Run both aligners independently | — |
| `-d` | Use system-installed DIAMOND | — |
| `-keep` / `-k` | Keep intermediate protein and position files | `False` |
| `-pdf` | Save figures as PDF | `True` |
| `-png` | Save figures as PNG (high memory) | `False` |
| `-save-genes` | Save found gene sequences per genome (`.faa`) | `False` |
| `-update` / `-u` | Update databases and dependencies | — |
| `-h` / `-help` | Print help and exit | — |
| `-v` / `-version` | Print version and exit | — |

### NCBI Download and Annotation Modes

>  **These features are currently in testing.**

```bash
# Download FASTA genome assemblies from NCBI
python3 panvita.py -g ncbi_assembly_table.csv

# Download and annotate genomes with PROKKA
python3 panvita.py -a ncbi_assembly_table.csv

# Download GenBank (.gbff) files
python3 panvita.py -b ncbi_assembly_table.csv

# Extract BioSample metadata (includes MLST)
python3 panvita.py -m ncbi_assembly_table.csv

# Use strain name as locus_tag prefix (requires -b)
python3 panvita.py -b -s ncbi_assembly_table.csv
```

---

##  Workflow Description

```
Input GBK/GBF files
        │
        ▼
┌───────────────────────────────┐
│  1. Dependency Check          │  DIAMOND and BLAST downloaded if missing
│  2. Database Check            │  Selected databases downloaded and indexed
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  3. GBK Parsing               │  CDS features extracted → protein FASTA per genome
│  4. Position Extraction       │  Genomic coordinates stored for each CDS
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  5. Parallel Alignment        │  Each genome aligned concurrently against each database
│     (DIAMOND / BLAST / Both)  │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  6. Result Mining             │  Hits filtered by identity (-i) and coverage (-c)
│                               │  Best-hit selection per query–subject pair
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  7. Presence/Absence Matrix   │  Genes × Strains matrix with identity values
│  8. Gene Classification       │  Core / Accessory / Exclusive
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  9. Visualizations            │  Heatmap, Rarefaction, UpSet, PCoA, Network, Barplots
│ 10. Tabular Reports           │  CSV and Excel detailed reports
└───────────────────────────────┘
        │
        ▼
   Results_[DB]_[DD-MM-YYYY_HH-MM-SS]/
```

### Gene Classification Criteria

| Class | Criterion |
|-------|-----------|
| **Core** | Present in **all** analysed genomes |
| **Accessory** | Present in **more than one** but **not all** genomes |
| **Exclusive** | Present in **exactly one** genome |

---

##  File Structure

```
PanVITA-2/
├── panvita.py              # Main script and execution orchestrator
├── config.py               # System checks, SSL configuration, platform detection
├── dependences.py          # DIAMOND and BLAST download and management
├── bank.py                 # Database download, indexing, and updates
├── ncbi.py                 # NCBI FTP downloads; PROKKA integration
├── functions.py            # GBK parsing, protein extraction, alignment, result mining
├── visualization.py        # All figure generation and tabular report production
├── utils.py                # File download, extraction, and cleanup utilities
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── DB/                     # Databases (auto-created)
│   ├── bacmet_2.*
│   ├── card_protein_homolog_model.*
│   ├── aro_index.tsv
│   ├── megares_v3.*
│   ├── vfdb_core.*
│   ├── resfinder.*
│   ├── argannot.*
│   └── victors*.*
├── Dependences/            # DIAMOND and BLAST executables (auto-created)
└── Results_*/              # Analysis results (timestamped)
```

---

##  Output Formats

| Format | Description |
|--------|-------------|
| **CSV** | Presence/absence matrices, gene tables, detailed reports |
| **XLSX** | Detailed reports in Excel format |
| **PDF / PNG** | All visualizations and figures |
| **FASTA** | Protein sequences of found genes (optional, `-save-genes`) |
| **TAB** | Raw alignment tabular outputs (optional, `-keep`) |

### Output Files Reference

| File / Directory | Description |
|-----------------|-------------|
| `matriz_[db].csv` | Presence/absence matrix with identity values (genes × strains) |
| `[db]_genes.csv` | Gene count table with Core/Accessory/Exclusive classification |
| `[db]_heatmap.[pdf/png]` | Hierarchically clustered heatmap |
| `[db]_pan_rarefaction.[pdf/png]` | Pan-genome and core-genome rarefaction curves |
| `[db]_upset.[pdf/png]` | UpSet plot of shared gene sets across strains |
| `[db]_pcoa.[pdf/png]` | PCoA of genomes by gene-content dissimilarity |
| `[db]_network.[pdf/png]` | Gene co-occurrence network (Pearson r > 0.75) |
| `[db]_distribution_mechanism.[pdf/png]` | Breakdown by resistance mechanism or VF class |
| `[db]_distribution_class.[pdf/png]` | Breakdown by drug class or compound |
| `[db]_detailed_report.csv` | Long-format report: genome × gene × identity × metadata |
| `[db]_detailed_report.xlsx` | Same as above in Excel format |
| `Tabular_1_[db]/` | Raw alignment output files per genome |
| `Tabular_2_[db]/` | Filtered alignment results per genome |
| `panvita_error_[timestamp].err` | Error log (only generated when errors occur) |
| `PROKKA.sh` | Shell script with all PROKKA commands (generated with `-g` or `-a`) |

---

##  Common Troubleshooting

### DIAMOND or BLAST won't run
1. Verify system dependencies are installed
2. Re-download tools: `python3 panvita.py -update`
3. On Windows, install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Error: `mdb_env_open` (BLAST LMDB)
```bash
# Set the environment variable before running
export BLASTDB_LMDB_MAP_SIZE=1000000

# Or re-download databases entirely
rm -rf DB/ Dependences/
python3 panvita.py -update
```

### SSL / Download Failures
PanViTa 2 includes automatic SSL certificate handling for corporate or restricted environments. If downloads still fail, check your network connection and proxy settings.

### No genes found in output
- Check the `.err` log file for errors
- Identity/coverage thresholds may be too stringent — try lowering with `-i 60 -c 60`
- Ensure input GenBank files contain `/translation` qualifiers (use PROKKA-annotated files)
- Re-run database download with `-update`

### Conda conflicts
```bash
conda deactivate
python3 panvita.py -card *.gbk
```

---

##  References and Citations

If you use PanViTa 2 in your research, **please cite all relevant tools and databases**. PanViTa 2 automatically prints the relevant citations at the end of each run.

### PanViTa

> Rodrigues DN, Oliveira V *et al.* **PanViTa: Pan Virulence and resisTance Analysis.** *Frontiers in Bioinformatics*, 2023.  
> 🔗 https://doi.org/10.3389/fbinf.2023.1070406

### Databases

| Database | Reference | DOI |
|----------|-----------|-----|
| **CARD** | Alcock BP *et al.* CARD 2020: antibiotic resistome surveillance with the comprehensive antibiotic resistance database. *Nucleic Acids Research*, 2020. | https://doi.org/10.1093/nar/gkz935 |
| **BacMet** | Pal C *et al.* BacMet: antibacterial biocide and metal resistance genes database. *Nucleic Acids Research*, 2014. | https://doi.org/10.1093/nar/gkt1252 |
| **VFDB** | Liu B *et al.* VFDB 2019: a comparative pathogenomic platform with an interactive web interface. *Nucleic Acids Research*, 2019. | https://doi.org/10.1093/nar/gky1080 |
| **MEGARes v3** | Doster E *et al.* MEGARes and AMR++, v3.0: an updated comprehensive database of antimicrobial resistance determinants. *Nucleic Acids Research*, 2022. | https://doi.org/10.1093/nar/gkac1047 |
| **ResFinder** | Zankari E *et al.* Identification of acquired antimicrobial resistance genes. *Journal of Antimicrobial Chemotherapy*, 2012. | https://doi.org/10.1093/jac/dks261 |
| **ARG-ANNOT** | Gupta SK *et al.* ARG-ANNOT: a new bioinformatic tool to discover antibiotic resistance genes in bacterial genomes. *Antimicrobial Agents and Chemotherapy*, 2014. | https://doi.org/10.1128/AAC.01310-13 |
| **Victors** | Sayers S *et al.* Victors: a web-based knowledge base of virulence factors in human and animal pathogens. *Nucleic Acids Research*, 2018. | https://doi.org/10.1093/nar/gkx1038 |

### Alignment Tools

| Tool | Reference | DOI |
|------|-----------|-----|
| **DIAMOND** | Buchfink B, Xie C, Huson DH. Fast and sensitive protein alignment using DIAMOND. *Nature Methods*, 2015. | https://doi.org/10.1038/nmeth.3176 |
| **BLAST** | Altschul SF *et al.* Basic local alignment search tool. *Journal of Molecular Biology*, 1990. | https://doi.org/10.1016/S0022-2836(05)80360-2 |

### Optional Tools (cite if used)

| Tool | Reference | DOI |
|------|-----------|-----|
| **PROKKA** | Seemann T. Prokka: rapid prokaryotic genome annotation. *Bioinformatics*, 2014. | https://doi.org/10.1093/bioinformatics/btu153 |
| **mlst** | Maiden MCJ *et al.* MLST revisited: the gene-by-gene approach to bacterial genomics. *Nature Reviews Microbiology*, 2013. | https://doi.org/10.1038/nrmicro3093 |

---

##  Contact and Support

- **Email**: victorsc@ufmg.br | dlnrodrigues@ufmg.br | vinicius.oliveira.1444802@sga.pucminas.br
- **Institution**: Universidade Federal de Minas Gerais (UFMG) / PUC Minas
- **GitHub Issues**: [Report a bug or request a feature](https://github.com/VictorCaricatte/PanViTa-2/issues)

##  License

This project is licensed under the GPL-3.0 License and have a Brasilian registration — see the [LICENSE](LICENSE) file for details.

---

**Version**: 2.0.4 | **Last updated**: February 2026
