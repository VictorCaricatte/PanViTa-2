# PanVITA 2.0 - Pan Virulence and resisTance Analysis

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://python.org)
<!-- [![License - OUTDATED FOR NOW ](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![DOI - OUTDATED FOR NOW](https://img.shields.io/badge/DOI-10.3389%2Ffbinf.2023.1070406-blue.svg)](https://doi.org/10.3389/fbinf.2023.1070406)-->

## 📖 About PanVITA 2.0

**PanVITA 2.0** (Pan Virulence and resisTance Analysis) is a bioinformatics tool developed for comparative analysis of multiple genomes against specialized databases for antimicrobial resistance and virulence factors.

This tool allows identification and comparison of resistance genes to antibiotics, heavy metals, biocides, and virulence factors in prokaryotic genomes, generating intuitive visualizations and presence/absence matrices for epidemiological and evolutionary analyses.

## 🎯 What is it for?

- **Resistance Analysis**: Identification of resistance genes to antibiotics, metals, and biocides
- **Virulence Factors**: Detection of pathogenicity-related genes
- **Comparative Analysis**: Comparison of multiple genomes simultaneously
- **Molecular Epidemiology**: Studies of resistance and virulence dissemination
- **Genomic Surveillance**: Monitoring of pathogens and their resistance profiles

## ⚡ Main Features

### 🗄️ Supported Databases

| Database | Description | Focus |
|----------|-------------|-------|
| **CARD** | Comprehensive Antibiotic Resistance Database | Antibiotic resistance |
| **BacMet** | Antibacterial Biocide and Metal Resistance Genes | Metal and biocide resistance |
| **MEGARes** | MEGARes Antimicrobial Resistance Database | Antimicrobial resistance |
| **VFDB** | Virulence Factor Database | Virulence factors |

### 🔧 Alignment Tools

- **DIAMOND**: Fast protein alignment (recommended for large datasets)
- **BLAST**: Traditional high-precision alignment
- **Hybrid Mode**: Combination of both tools for cross-validation

### 📊 Generated Visualizations

- **Heatmaps**: Visualization of gene presence/absence
- **Clustermaps**: Hierarchical clustering of genomes
- **Bar Charts**: Distribution of resistance classes
- **Matrices**: Tabular data for further analyses

### 🌐 Advanced Features

- **Automatic download** of genomes from NCBI
- **Automatic annotation** using PROKKA
- **Metadata extraction** from BioSample
- **Cross-platform support** (Windows/Linux)
- **Customizable filters** for identity and coverage

## 🚀 How to Use

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/ViniiSalles/PanVITA-2.0.git
cd PanVITA-2.0

# Install Python dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Complete analysis against all databases
python panvita.py -card -vfdb -bacmet -megares file1.gbk file2.gbk

# Specific analysis against CARD and VFDB
python panvita.py -card -vfdb *.gbk

# Using DIAMOND only
python panvita.py -diamond -card file.gbk

# Using BLAST only
python panvita.py -blast -vfdb file.gbk

# Using both aligners
python panvita.py -both -card -vfdb file.gbk
```

### Main Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-i` | Minimum identity (%) | 70 |
| `-c` | Minimum coverage (%) | 70 |
| `-keep` | Keep temporary files | False |
| `-pdf` | Save figures as PDF | True |
| `-png` | Save figures as PNG | False |

### NCBI Features

```bash
# Download genomes in FASTA
python panvita.py -g ncbi_table.csv

# Download and annotate genomes
python panvita.py -a ncbi_table.csv

# Download GenBank files
python panvita.py -b ncbi_table.csv

# Extract metadata
python panvita.py -m ncbi_table.csv
```

### Database Update

```bash
# Update all databases and dependencies
python panvita.py -update
# or
python panvita.py -u
```

## 📋 Dependencies and Requirements

### 📦 Python Dependencies

```bash
pandas>=1.3.0      # Data manipulation
matplotlib>=3.3.0  # Visualizations
seaborn>=0.11.0    # Statistical graphics
basemap>=1.3.0     # Geographic maps
wget>=3.2          # File downloads
```

### 🖥️ System Dependencies

#### Windows
- **Microsoft Visual C++ Redistributable** (2015-2022)
  - [Download x64](https://aka.ms/vs/17/release/vc_redist.x64.exe)
  - [Download x86](https://aka.ms/vs/17/release/vc_redist.x86.exe)

#### Linux
- **build-essential**
```bash
sudo apt update
sudo apt install build-essential
```

### 🔍 Dependencies Comparison

| Windows | Linux | Function |
|---------|-------|----------|
| `msvcp140.dll` | `libstdc++.so.6` | C++ standard library |
| `vcruntime140.dll` | `libgcc_s.so.1` | Compiler runtime |
| `msvcrt.dll` | `libc.so.6` | Standard C library |
| `vcomp140.dll` | `libgomp.so.1` | OpenMP support |

## 📁 File Structure

```
PanVITA-2.0/
├── panvita.py              # Main script
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── DB/                    # Databases
│   ├── aro_index.tsv
│   ├── bacmet_2.*
│   ├── card_protein_homolog_model.*
│   ├── megares_v3.*
│   └── vfdb_core.*
├── Dependences/           # BLAST/DIAMOND executables
├── Positions/             # CDS position files
└── Results_*/             # Analysis results
```

## 🔧 Common Troubleshooting

### Error: mdb_env_open
```bash
# Solution 1: Set environment variable
export BLASTDB_LMDB_MAP_SIZE=1000000

# Solution 2: Re-download databases
rm -rf DB/ Dependences/
python panvita.py -update
```

### DIAMOND/BLAST won't run
1. Check if system dependencies are installed
2. Run update: `python panvita.py -update`
3. On Windows, install Visual C++ Redistributable

### SSL/Download Issues
PanVITA 2.0 includes automatic handling of common SSL issues in corporate environments.

## 📚 Supported Input Formats

- **GBK/GBF**: GenBank files from PROKKA or NCBI
- **GBFF**: GenBank files from NCBI (mandatory extension)
- **CSV**: NCBI metadata tables for downloads

## 📊 Output Formats

- **CSV**: Presence/absence matrices and metadata
- **PDF/PNG**: Visualizations and graphs
- **FASTA**: Protein sequences (optional)
- **TAB**: CDS position files (optional)

## 📖 Citation - OUTDATED FOR NOW

If you use PanVITA in your work, please cite:

```
PanVITA - Pan Virulence and resisTance Analysis
DOI: 10.3389/fbinf.2023.1070406
```

## 👥 Contact and Support

- **Email**: dlnrodrigues@ufmg.br - victorsc@ufmg.br - vinicius.oliveira.1444802@sga.pucminas.br
- **GitHub**: [Issues](https://github.com/ViniiSalles/PanVITA-2.0/issues)

## 📄 License - OUTDATED FOR NOW

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Version**: 2.0.0  
**Last updated**: August 2025
