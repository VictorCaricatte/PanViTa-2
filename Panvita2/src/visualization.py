# File: visualization.py
# Description: Plotting and matrix generation 

import os
import sys
import math
import textwrap
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import cm
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms
import warnings

try:
    import networkx as nx
except ImportError:
    nx = None

try:
    from sklearn.manifold import MDS
    from sklearn.cluster import KMeans
    from scipy.spatial.distance import pdist, squareform
except ImportError:
    MDS = None

try:
    from upsetplot import from_contents, UpSet
except ImportError:
    from_contents = None

# New dependency for interactive 3D plots
try:
    import plotly.graph_objects as go
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

class Visualization:
    @staticmethod
    def generate_matrix(db_param, outputs, comp, aligner_suffix=""):
        """Generate presence/absence matrix from alignment results"""
        db_name = db_param[1:]
        
        if aligner_suffix:
            titulo = f"matriz_{db_name}_{aligner_suffix}.csv"
            tabular_dir = f"Tabular_2_{db_name}_{aligner_suffix}"
        else:
            titulo = f"matriz_{db_name}.csv"
            tabular_dir = f"Tabular_2_{db_name}"
        
        outputs.append(titulo)

        print(f"\nGenerating the presence and identity matrix for {db_param}{f' ({aligner_suffix})' if aligner_suffix else ''}...")

        dicl = {}
        totalgenes = set()
        found_genes_per_strain = {}
        
        if not os.path.exists(tabular_dir):
            print(f"Warning: Directory {tabular_dir} not found!")
            return titulo, dicl, [], found_genes_per_strain
            
        files_in_dir = os.listdir(tabular_dir)
        if not files_in_dir:
            print(f"Warning: No files found in {tabular_dir}!")
            return titulo, dicl, [], found_genes_per_strain
        
        print(f"Processing {len(files_in_dir)} strain files...")
        
        for i in files_in_dir:
            if not i.endswith('.tab'):
                continue
                
            linhagem = i[:-4]
            file_path = os.path.join(tabular_dir, i)
            
            try:
                with open(file_path, 'rt') as file:
                    linhas = file.readlines()
            except Exception as e:
                print(f"Warning: Could not read file {file_path}: {e}")
                continue
            
            genes = {}
            genes_found = 0
            strain_found_genes = {}
            
            for j in linhas:
                linha = j.strip()
                if not linha:
                    continue
                    
                linha = linha.split('\t')
                if len(linha) < 3:
                    continue
                
                gene = None
                locus_tag = linha[0]
                
                # Special handling for MEGARes
                if 'MEG_' in linha[1] and '|' in linha[1]:
                    parts = linha[1].split('|')
                    if len(parts) >= 5:
                        meg_id = parts[0]
                        actual_gene = parts[4]
                        if meg_id in comp:
                            gene = comp[meg_id]
                        elif actual_gene.strip():
                            gene = actual_gene.strip().replace('\n', '').replace('\r', '')
                
                if gene is None:
                    subject_id = linha[1].split()[0]
                    if subject_id in comp:
                         gene = comp[subject_id]
                    else:
                        for k in comp.keys():
                            if k in linha[1]:
                                gene = comp[k]
                                break
                
                if gene:
                    try:
                        identidade = float(linha[2])
                        genes[gene] = identidade
                        totalgenes.add(gene)
                        genes_found += 1
                        
                        if gene not in strain_found_genes:
                            strain_found_genes[gene] = []
                        strain_found_genes[gene].append(locus_tag)
                        
                    except (ValueError, IndexError):
                        continue
            
            dicl[str(linhagem)] = genes
            found_genes_per_strain[str(linhagem)] = strain_found_genes
        
        totalgenes = sorted(list(totalgenes))
        
        print(f"Total unique genes found: {len(totalgenes)}")
        print(f"Total strains processed: {len(dicl)}")
        
        if not totalgenes:
            print(f"Warning: No genes found for {db_param}. Creating empty matrix.")
            with open(titulo, 'w') as saida:
                saida.write('Strains\n')
                for strain in dicl.keys():
                    saida.write(strain + '\n')
            return titulo, dicl, [], found_genes_per_strain
        
        with open(titulo, 'w') as saida:
            saida.write('Strains')
            for gene in totalgenes:
                saida.write(f';{gene}')
            saida.write('\n')
            
            for strain in dicl.keys():
                saida.write(strain)
                for gene in totalgenes:
                    if gene in dicl[strain]:
                        saida.write(f';{dicl[strain][gene]}')
                    else:
                        saida.write(';0')
                saida.write('\n')
        
        print(f"Matrix saved as: {titulo}")
        return titulo, dicl, totalgenes, found_genes_per_strain

    @staticmethod
    def generate_heatmap(data_file, db_param, outputs, erro, aligner_suffix=""):
        """Generate refined heatmap visualization from matrix"""
        fileType = "pdf"
        if "-pdf" in sys.argv:
            fileType = "pdf"
        elif "-png" in sys.argv:
            fileType = "png"
        
        db_name = db_param[1:]  
        
        if aligner_suffix:
            out = f"heatmap_{db_name}_{aligner_suffix}.{fileType}"
        else:
            out = f"heatmap_{db_name}.{fileType}"
        
        outputs.append(out)
        
        # Updated Colors: Victors now matches VFDB (Reds)
        if db_param == "-card": color = "Blues"
        elif db_param == "-vfdb": color = "Reds"
        elif db_param == "-bacmet": color = "Greens"
        elif db_param == "-megares": color = "Oranges"
        elif db_param == "-resfinder": color = "PuBu"
        elif db_param == "-argannot": color = "RdPu"
        elif db_param == "-victors": color = "Reds" 
        else: color = "Greys"

        try:
            df = pd.read_csv(data_file, sep=';')
            df = df.set_index('Strains')
            
            headers = list(df.columns.values)
            for i in headers:
                if "Unnamed:" in i:
                    df = df.drop(columns=[i])

            df = df.T 

            max_len = 40
            new_index = [str(x)[:max_len] + '...' if len(str(x)) > max_len else str(x) for x in df.index]
            df.index = new_index

            num_genes = df.shape[0]
            num_strains = df.shape[1]
            
            fig_height = max(8, num_genes * 0.25) 
            fig_width = max(10, num_strains * 0.8)

            fig_height = min(fig_height, 200)
            fig_width = min(fig_width, 50)

            print(f"\nPlotting final heatmap{f' ({aligner_suffix})' if aligner_suffix else ''}...")
            
            plt.figure(figsize=(fig_width, fig_height))
            
            font_size = 12
            if num_genes > 100: font_size = 10
            
            sns.set(font_scale=1.0)
            sns.set_style("white")

            # Create annotation matrix to show only hits (values > 0)
            def format_hit(val):
                try:
                    if float(val) > 0:
                        return f"{float(val):.0f}"
                except ValueError:
                    pass
                return ""
                
            try:
                annot_matrix = df.map(format_hit)
            except AttributeError:
                # Fallback for older pandas versions
                annot_matrix = df.applymap(format_hit)

            ax = sns.heatmap(
                df, 
                cmap=color, 
                annot=annot_matrix,
                fmt='', 
                cbar_kws={'label': 'Identity (%)', 'shrink': 0.5},
                linewidths=0.5 if num_genes < 100 else 0,
                linecolor='lightgray',
                square=False,
                annot_kws={"size": font_size - 2}
            )
            
            ax.set_title(f"Heatmap - {db_name.upper()}", fontsize=16, fontweight='bold', pad=20)
            ax.set_ylabel("Genes / Factors", fontsize=14, fontweight='bold')
            ax.set_xlabel("Strains", fontsize=14, fontweight='bold')
            
            ax.tick_params(axis='y', labelsize=font_size, rotation=0)
            ax.tick_params(axis='x', labelsize=font_size, rotation=45)

            plt.tight_layout()
            plt.savefig(out, format=fileType, dpi=300, bbox_inches="tight")
            plt.close()
            sns.reset_orig()

        except BaseException as e:
            erro_string = f"\nIt was not possible to plot the {out} figure...\nError: {e}"
            erro.append(erro_string)
            print(erro_string)

    @staticmethod
    def generate_barplot(data_file, index_col, output_file, fileType, outputs):
        """Generates a bar chart from a data file."""
        try:
            data = pd.read_csv(data_file, sep=";", index_col=index_col)
            if data.empty:
                print(f"Warning: No data to plot in {output_file}")
                return

            data['Total'] = data.sum(axis=1)
            data_sorted = data.sort_values('Total', ascending=False).drop(columns='Total')
            data_melted = data_sorted.reset_index().melt(id_vars=index_col, var_name='Category', value_name='Count')

            num_categories = len(data_sorted.index)
            width = max(12, min(30, 8 + num_categories * 0.8))
            height = 8

            plt.figure(figsize=(width, height))
            ax = sns.barplot(data=data_melted, x=index_col, y='Count', hue='Category',
                             palette={"Core": "#1f77b4", "Accessory": "#ff7f0e", "Exclusive": "#2ca02c"})

            ax.set_xlabel(index_col.replace('_', ' ').title(), fontsize=12, fontweight='bold')
            ax.set_ylabel('Number of Genes', fontsize=12, fontweight='bold')
            ax.set_title(f'Distribution of Genes by {index_col.replace("_", " ").title()}', fontsize=16, fontweight='bold')

            plt.xticks(rotation=45, ha='right')
            ax.grid(axis='y', linestyle='--', alpha=0.7)

            ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
            plt.tight_layout()

            plt.savefig(output_file, format=fileType, dpi=300)
            plt.close()
            
            outputs.append(output_file)
            print(f"Bar chart saved as: {output_file}")
        
        except Exception as e:
            print(f"Error generating bar chart {output_file}: {e}")

    @staticmethod
    def generate_joint_and_marginal_distributions(data_file, db_param, outputs, erro, aligner_suffix=""):
        """Hexbin joint plot with marginal distributions"""
        try:
            fileType = "pdf" if "-pdf" in sys.argv or "-png" not in sys.argv else "png"
            if "-png" in sys.argv:
                fileType = "png"
            db_name = db_param[1:]
            out = f"joint_hexbin_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
            outputs.append(out)

            # Updated Colors: Victors matches VFDB
            if db_param == "-card": color_palette, main_color = "Blues", "#2171b5"
            elif db_param == "-vfdb": color_palette, main_color = "Reds", "#cb181d"
            elif db_param == "-bacmet": color_palette, main_color = "Greens", "#238b45"
            elif db_param == "-megares": color_palette, main_color = "Oranges", "#d94801"
            elif db_param == "-resfinder": color_palette, main_color = "PuBu", "#0570b0"
            elif db_param == "-argannot": color_palette, main_color = "RdPu", "#ae017e"
            elif db_param == "-victors": color_palette, main_color = "Reds", "#cb181d"
            else: color_palette, main_color = "Greys", "#525252"

            df = pd.read_csv(data_file, sep=';').set_index('Strains')
            for col in list(df.columns):
                if "Unnamed:" in col:
                    df = df.drop(columns=[col])

            genes_present = (df > 0).sum(axis=1).astype(int)
            df_numeric = df.apply(pd.to_numeric, errors='coerce')
            mean_identity_temp = df_numeric.replace(0, pd.NA).mean(axis=1, skipna=True)
            mean_identity = pd.to_numeric(mean_identity_temp.fillna(0), errors='coerce')
            metrics = pd.DataFrame({"GenesPresent": genes_present, "MeanIdentity": mean_identity})

            if len(metrics) < 2:
                return
            
            x_range = metrics["GenesPresent"].max() - metrics["GenesPresent"].min()
            y_range = metrics["MeanIdentity"].max() - metrics["MeanIdentity"].min()
            
            if x_range == 0 and y_range == 0:
                return

            base_size = 6
            sns.set_theme(style="ticks")
            
            g = sns.jointplot(
                x=metrics["GenesPresent"], y=metrics["MeanIdentity"], 
                kind="hex", color=main_color, height=base_size,
                joint_kws={'gridsize': 15, 'cmap': color_palette, 'alpha': 0.8, 'edgecolors': 'white'},
                marginal_kws={'color': main_color, 'alpha': 0.8, 'bins': 15}
            )
            
            g.set_axis_labels("Genes Present", "Mean Identity (%)", fontsize=12, fontweight='bold')
            g.figure.suptitle(f"Hexbin plot - {db_name.upper()}", y=1.02, fontsize=14, fontweight="bold")
            g.figure.savefig(out, format=fileType, dpi=300, bbox_inches="tight")
            plt.close(g.figure)
            print(f"Hexbin jointplot saved as: {out}")
            sns.reset_defaults()
                
        except Exception as e:
            erro.append(f"Failed to plot hexbin jointplot: {e}")

    @staticmethod
    def generate_scatterplot_heatmap(data_file, db_param, outputs, erro, aligner_suffix=""):
        """Dynamic scatterplot-based heatmap"""
        fileType = "pdf"
        if "-pdf" in sys.argv:
            fileType = "pdf"
        elif "-png" in sys.argv:
            fileType = "png"

        db_name = db_param[1:]
        out = f"scatter_heatmap_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
        outputs.append(out)

        try:
            with sns.axes_style("whitegrid"):
                df = pd.read_csv(data_file, sep=';').set_index('Strains')
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                long_df = df.reset_index().melt(id_vars='Strains', var_name='Gene', value_name='Identity')
                long_df['Identity'] = pd.to_numeric(long_df['Identity'], errors='coerce')
                long_df = long_df[long_df['Identity'] > 0]

                if long_df.empty: return

                long_df['Gene'] = long_df['Gene'].apply(lambda x: str(x)[:40] + '...' if len(str(x)) > 40 else str(x))

                id_min = float(long_df['Identity'].min())
                id_max = float(long_df['Identity'].max())
                if id_max <= id_min: id_max = id_min + 1.0

                # Updated Colors: Victors matches VFDB
                palette_map = {
                    "-card": "Blues", "-vfdb": "Reds", "-bacmet": "Greens", "-megares": "Oranges",
                    "-resfinder": "PuBu", "-argannot": "RdPu", "-victors": "Reds", "-custom": "Greys"
                }
                palette = palette_map.get(db_param, "viridis")

                n_genes = long_df['Gene'].nunique()
                n_strains = long_df['Strains'].nunique()
                height = max(10, n_genes * 0.25) 
                width = max(8, n_strains * 0.5)
                aspect_ratio = width / height

                g = sns.relplot(
                    data=long_df, x="Strains", y="Gene", hue="Identity", size="Identity",
                    palette=palette, legend="brief", hue_norm=(id_min, id_max),
                    edgecolor=".5", linewidth=0.5, height=height, sizes=(20, 200),
                    size_norm=(id_min, id_max), aspect=aspect_ratio, kind='scatter'
                )

                g.set(xlabel="Strains", ylabel="Genes / Factors")
                g.despine(left=True, bottom=True)
                g.ax.tick_params(axis='x', rotation=45)
                g.figure.suptitle(f"Gene Presence Scatter Heatmap - {db_name.upper()}", y=1.002, fontweight="bold")
                g.figure.savefig(out, format=fileType, dpi=300, bbox_inches="tight")
                plt.close(g.figure)
                print(f"Dynamic scatter heatmap saved as: {out}")

        except Exception as e:
            erro.append(f"Error plotting scatter heatmap: {e}")

    @staticmethod
    def generate_clustermap(data_file, db_param, outputs, erro, aligner_suffix=""):
        """Hierarchical Clustermap"""
        fileType = "pdf"
        if "-pdf" in sys.argv:
            fileType = "pdf"
        elif "-png" in sys.argv:
            fileType = "png"

        db_name = db_param[1:]
        out = f"clustermap_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
        outputs.append(out)

        # Colors: Victors matches VFDB
        cmap_map = {
            "-card": "Blues", "-vfdb": "Reds", "-bacmet": "Greens", "-megares": "Oranges",
            "-resfinder": "PuBu", "-argannot": "RdPu", "-victors": "Reds", "-custom": "Greys"
        }
        cmap = cmap_map.get(db_param, "viridis")

        try:
            df = pd.read_csv(data_file, sep=';').set_index('Strains')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            if df.empty or df.shape[1] < 2 or df.shape[0] < 2: return

            df_T = df.T 
            df_T.index = [str(x)[:40] + '...' if len(str(x)) > 40 else str(x) for x in df_T.index]
            
            fig_height = max(10, df_T.shape[0] * 0.25)
            fig_width = max(8, df_T.shape[1] * 0.8) + 4
            fig_height, fig_width = min(fig_height, 200), min(fig_width, 60)
            
            sns.set(font_scale=1.0)
            g = sns.clustermap(
                df_T, cmap=cmap, method="average", metric="euclidean",
                linewidths=0.5, linecolor='lightgray', figsize=(fig_width, fig_height),
                xticklabels=True, yticklabels=True, dendrogram_ratio=(0.2, 0.2)
            )
            
            plt.setp(g.ax_heatmap.get_xticklabels(), rotation=45, ha='right')
            g.savefig(out, format=fileType, dpi=300, bbox_inches="tight")
            plt.close(g.fig)
            sns.reset_orig()
            print(f"Hierarchical clustermap saved as: {out}")
            
        except Exception as e:
            erro.append(f"Error plotting clustermap: {e}")

    @staticmethod
    def generate_rarefaction_permutations(data_file, title, output_file, fileType, outputs):
        """Generates a Pangenome Rarefaction Curve with Permutations"""
        try:
            df = pd.read_csv(data_file, sep=";", index_col="Strains")
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            binary_matrix = (df > 0).astype(int).values
            n_strains, n_genes = binary_matrix.shape
            
            if n_strains < 2:
                print("Warning: Not enough strains for rarefaction curve.")
                return

            permutations = 50 if n_strains < 50 else 20
            
            pan_matrix = np.zeros((permutations, n_strains))
            core_matrix = np.zeros((permutations, n_strains))
            
            print(f"\nCalculating rarefaction curve with {permutations} permutations...")
            
            strain_indices = np.arange(n_strains)
            
            for p in range(permutations):
                np.random.shuffle(strain_indices)
                shuffled_matrix = binary_matrix[strain_indices, :]
                
                current_pan = np.zeros(n_genes)
                current_core = np.ones(n_genes)
                
                for s in range(n_strains):
                    row = shuffled_matrix[s, :]
                    current_pan = np.logical_or(current_pan, row)
                    pan_matrix[p, s] = np.sum(current_pan)
                    
                    if s == 0:
                        current_core = row
                    else:
                        current_core = np.logical_and(current_core, row)
                    core_matrix[p, s] = np.sum(current_core)

            x_axis = np.arange(1, n_strains + 1)
            pan_mean = np.mean(pan_matrix, axis=0)
            pan_std = np.std(pan_matrix, axis=0)
            core_mean = np.mean(core_matrix, axis=0)
            core_std = np.std(core_matrix, axis=0)
            
            plt.figure(figsize=(12, 8))
            sns.set_style("whitegrid")
            
            plt.plot(x_axis, pan_mean, '-', color='#1f77b4', label='Pan-Genome', linewidth=2.5)
            plt.fill_between(x_axis, pan_mean - pan_std, pan_mean + pan_std, color='#1f77b4', alpha=0.2)
            
            plt.plot(x_axis, core_mean, '-', color='#ff7f0e', label='Core-Genome', linewidth=2.5)
            plt.fill_between(x_axis, core_mean - core_std, core_mean + core_std, color='#ff7f0e', alpha=0.2)
            
            if n_strains > 4:
                try:
                    from scipy.optimize import curve_fit
                    def heaps_law(N, k, gamma): return k * (N ** gamma)
                    popt, _ = curve_fit(heaps_law, x_axis, pan_mean)
                    gamma = popt[1]
                    status = "Open" if gamma > 0 else "Closed"
                    plt.annotate(rf"Heaps' Law $\gamma={gamma:.2f}$ ({status})", xy=(0.05, 0.95), xycoords='axes fraction',
                                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.8))
                except: pass

            plt.title(f"{title} (Rarefaction with Shuffling)", fontsize=16, fontweight='bold', pad=20)
            plt.xlabel("Number of Genomes", fontsize=14, fontweight='bold')
            plt.ylabel("Number of Genes", fontsize=14, fontweight='bold')
            plt.legend(fontsize=12, loc='center right')
            
            plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True))
            plt.xlim(left=1, right=n_strains)
            plt.tight_layout()
            
            final_out = f"{output_file}_rarefaction.{fileType}"
            plt.savefig(final_out, format=fileType, dpi=300)
            plt.close()
            
            outputs.append(final_out)
            print(f"Rarefaction curve saved as: {final_out}")
            
        except Exception as e:
            print(f"Error generating rarefaction curve: {e}")

    @staticmethod
    def generate_pcoa_jaccard(data_file, db_param, outputs, meta1, aligner_suffix=""):
        """
        Generates a PCoA (Principal Coordinates Analysis) plot using Jaccard Distance.
        UPDATED: Added check for Stress calculation.
        """
        if MDS is None:
            print("Warning: Scikit-learn or Scipy not installed. Skipping PCoA.")
            return

        db_name = db_param[1:]
        fileType = "pdf" if "-pdf" in sys.argv or "-png" not in sys.argv else "png"
        out = f"pcoa_jaccard_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
        
        try:
            print(f"\nCalculating Scientific PCoA (Jaccard Distance) for {db_name.upper()}...")
            
            df = pd.read_csv(data_file, sep=";", index_col="Strains")
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df_binary = (df > 0).astype(int)
            
            if df_binary.shape[0] < 3:
                print("Not enough strains for PCoA (requires >= 3).")
                return
            
            dist_matrix = pdist(df_binary.values, metric='jaccard')
            
            # Using MDS for PCoA
            # Note: normalized_stress is only available in scikit-learn >= 1.0. 
            # We wrap it in try-except to handle older versions gracefully.
            try:
                mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42, normalized_stress='auto')
                coords = mds.fit_transform(squareform(dist_matrix))
            except TypeError:
                # Fallback for older sklearn versions that don't support normalized_stress
                mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
                coords = mds.fit_transform(squareform(dist_matrix))
            
            plot_df = pd.DataFrame(coords, columns=['PCoA1', 'PCoA2'], index=df_binary.index)
            
            # K-Means for Coloring
            n_clusters = min(3, len(plot_df)) 
            kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(plot_df)
            plot_df['Cluster'] = kmeans.labels_.astype(str)
            
            stress = mds.stress_
            print(f"  PCoA Stress Value: {stress:.6f}")
            if stress < 0.001:
                print("  Note: A stress value of 0.000 indicates a perfect fit (common in small datasets).")
            
            # Setup Plot Style - Scientific
            plt.figure(figsize=(10, 8))
            
            # Define colors
            colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"] # Scientific standard
            cluster_ids = sorted(plot_df['Cluster'].unique())
            
            ax = plt.gca()
            
            # Plot function with manual ellipses
            def confidence_ellipse(x, y, ax, n_std=2.0, facecolor='none', **kwargs):
                if x.size < 2 or y.size < 2: return
                cov = np.cov(x, y)
                pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
                ell_radius_x = np.sqrt(1 + pearson)
                ell_radius_y = np.sqrt(1 - pearson)
                
                ellipse = Ellipse((0, 0), width=ell_radius_x * 2, height=ell_radius_y * 2,
                                  facecolor=facecolor, **kwargs)
                
                scale_x = np.sqrt(cov[0, 0]) * n_std
                mean_x = np.mean(x)
                scale_y = np.sqrt(cov[1, 1]) * n_std
                mean_y = np.mean(y)
                
                transf = transforms.Affine2D() \
                    .rotate_deg(45) \
                    .scale(scale_x, scale_y) \
                    .translate(mean_x, mean_y)
                
                ellipse.set_transform(transf + ax.transData)
                return ax.add_patch(ellipse)

            # Draw Points and Ellipses
            for i, cluster in enumerate(cluster_ids):
                subset = plot_df[plot_df['Cluster'] == cluster]
                color = colors[i % len(colors)]
                
                # Draw Points
                ax.scatter(subset['PCoA1'], subset['PCoA2'], c=color, label=f"Cluster {i+1}", 
                           s=100, alpha=0.9, edgecolors='k', linewidth=0.5)
                
                # Draw Ellipse (Confidence Interval)
                if len(subset) > 2:
                    confidence_ellipse(subset['PCoA1'], subset['PCoA2'], ax, n_std=2.0,
                                      edgecolor=color, facecolor=color, alpha=0.2, linestyle='-.')

            # Add labels if few points
            if len(plot_df) <= 30:
                from adjustText import adjust_text 
                texts = []
                for i, txt in enumerate(plot_df.index):
                    texts.append(plt.text(plot_df.PCoA1[i], plot_df.PCoA2[i], txt, fontsize=9))
                try:
                    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='gray', alpha=0.5))
                except: pass
            
            # Aesthetics matching the image provided
            plt.axhline(0, color='grey', linestyle='-', linewidth=0.8)
            plt.axvline(0, color='grey', linestyle='-', linewidth=0.8)
            plt.title(f"PCoA (Jaccard) - {db_name.upper()} | Stress: {stress:.3f}", fontsize=14, fontweight='bold')
            plt.xlabel("PCoA 1", fontsize=12, fontweight='bold')
            plt.ylabel("PCoA 2", fontsize=12, fontweight='bold')
            plt.legend(fontsize=10, loc='best', frameon=True, shadow=True)
            plt.grid(True, linestyle=':', alpha=0.6)
            
            plt.tight_layout()
            plt.savefig(out, format=fileType, dpi=300)
            plt.close()
            
            outputs.append(out)
            print(f"PCoA plot saved as: {out}")
            
        except Exception as e:
            print(f"Error generating PCoA: {e}")

    @staticmethod
    def generate_upsetplot(data_file, db_param, outputs, aligner_suffix=""):
        """Generates an UpSet Plot to visualize gene set intersections."""
        if from_contents is None:
            print("Warning: 'upsetplot' library not installed. Skipping UpSet Plot.")
            return

        db_name = db_param[1:]
        fileType = "pdf" if "-pdf" in sys.argv or "-png" not in sys.argv else "png"
        out = f"upsetplot_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
        
        try:
            print(f"\nGenerating UpSet Plot for {db_name.upper()}...")
            
            # Load data and ensure proper indexing
            df = pd.read_csv(data_file, sep=";", index_col="Strains")
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df_binary = (df > 0).astype(int)
            
            # Optimization: If dataset is huge, pick top 20 distinct intersection patterns or top 30 strains
            if df_binary.shape[0] > 30:
                print("  Dataset too large for clear UpSet plot. Selecting top 30 strains by gene count.")
                gene_counts = df_binary.sum(axis=1)
                top_strains = gene_counts.sort_values(ascending=False).head(30).index
                df_binary = df_binary.loc[top_strains]
            
            # Build dictionary {Strain_Name: [list of genes]}
            # This shows how Strains overlap based on gene content
            upset_data_dict = {}
            for strain in df_binary.index:
                present_genes = df_binary.loc[strain][df_binary.loc[strain] == 1].index.tolist()
                # Only add if not empty to avoid errors
                if present_genes:
                    upset_data_dict[strain] = present_genes
            
            if not upset_data_dict:
                print("  No intersection data found to plot.")
                return

            # Convert to UpSet format
            upset_data = from_contents(upset_data_dict)
            
            # Plotting
            fig = plt.figure(figsize=(12, 8))
            
            # Calculate dynamic min_subset_size to avoid clutter
            total_intersections = len(upset_data)
            min_size = max(2, int(total_intersections * 0.01))
            
            upset = UpSet(upset_data, subset_size='count', show_counts=True, 
                          sort_by='cardinality', sort_categories_by='cardinality',
                          min_subset_size=min_size)
            
            # Styling
            try:
                upset.style_subsets(present=list(upset_data_dict.keys())[:5], edgecolor='white', linewidth=1)
            except:
                pass # Fail gracefully if styling subset doesn't work
                
            upset.plot()
            plt.suptitle(f"UpSet Plot - Gene Intersections (Top Strains)", fontsize=16, fontweight='bold', y=1.02)
            
            plt.savefig(out, format=fileType, dpi=300, bbox_inches="tight")
            plt.close()
            
            outputs.append(out)
            print(f"UpSet plot saved as: {out}")
            
        except Exception as e:
            print(f"Error generating UpSet Plot: {e}")

    @staticmethod
    def generate_interactive_network_3d(data_file, db_param, outputs, meta1, aligner_suffix=""):
        """
        Generates an INTERACTIVE 3D Network using Plotly.
        UPDATED: Added background grid.
        """
        if not PLOTLY_AVAILABLE or MDS is None:
            return
        
        db_name = db_param[1:]
        out_html = f"network_3d_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.html"
        
        try:
            print(f"\nGenerating 3D Interactive Network for {db_name.upper()}...")
            df = pd.read_csv(data_file, sep=";", index_col="Strains")
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df_filtered = df.T
            df_binary = (df_filtered > 0).astype(int)
            
            n_strains = df.shape[0]
            if n_strains > 5:
                gene_counts = df_binary.sum(axis=1)
                mask = (gene_counts > (n_strains * 0.05)) & (gene_counts < (n_strains * 0.95))
                df_filtered = df_binary[mask]
            
            if df_filtered.shape[0] < 5: return

            dist_matrix = pdist(df_filtered.values, metric='jaccard')
            sim_matrix = 1 - squareform(dist_matrix)
            
            threshold = 0.75
            adj = np.where(sim_matrix > threshold, 1, 0)
            np.fill_diagonal(adj, 0)
            
            G = nx.from_numpy_array(adj)
            mapping = {i: name for i, name in enumerate(df_filtered.index)}
            G = nx.relabel_nodes(G, mapping)
            G.remove_nodes_from(list(nx.isolates(G)))
            
            if G.number_of_nodes() == 0: return

            pos = nx.spring_layout(G, dim=3, seed=42)
            
            x_nodes = [pos[n][0] for n in G.nodes()]
            y_nodes = [pos[n][1] for n in G.nodes()]
            z_nodes = [pos[n][2] for n in G.nodes()]
            
            categories = [meta1.get(n, "Unknown") for n in G.nodes()]
            unique_cats = sorted(list(set(categories)))
            
            # Create color palette using seaborn to match 2D logic
            palette = sns.color_palette("husl", len(unique_cats))
            # Convert RGB tuples to Hex for Plotly
            palette_hex = [f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}" for r,g,b in palette]
            cat_color_map = dict(zip(unique_cats, palette_hex))
            
            # Edges Trace (Background)
            edge_x, edge_y, edge_z = [], [], []
            for edge in G.edges():
                x0, y0, z0 = pos[edge[0]]
                x1, y1, z1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_z.extend([z0, z1, None])

            edge_trace = go.Scatter3d(
                x=edge_x, y=edge_y, z=edge_z,
                mode='lines',
                line=dict(color='#888', width=1),
                hoverinfo='none',
                showlegend=False
            )

            # Create Figure and add Edges
            fig = go.Figure()
            fig.add_trace(edge_trace)

            # Add a separate Trace for EACH category to create the Legend
            for cat in unique_cats:
                # Find indices of nodes belonging to this category
                node_indices = [i for i, x in enumerate(categories) if x == cat]
                
                # Filter coordinates and names
                x_c = [x_nodes[i] for i in node_indices]
                y_c = [y_nodes[i] for i in node_indices]
                z_c = [z_nodes[i] for i in node_indices]
                node_names = [list(G.nodes())[i] for i in node_indices]
                
                fig.add_trace(go.Scatter3d(
                    x=x_c, y=y_c, z=z_c,
                    mode='markers',
                    name=cat, # This name appears in the legend
                    marker=dict(
                        size=6,
                        color=cat_color_map[cat], # Single color for this group
                    ),
                    text=[f"Gene: {n}<br>Cat: {cat}" for n in node_names],
                    hoverinfo='text'
                ))

            fig.update_layout(
                title=f"3D Gene Interaction Network - {db_name.upper()}",
                legend=dict(
                    title="Gene Category",
                    itemsizing='constant'
                ),
                scene=dict(
                    # Show Cartesian grid
                    xaxis=dict(showbackground=True, showgrid=True, title='X'),
                    yaxis=dict(showbackground=True, showgrid=True, title='Y'),
                    zaxis=dict(showbackground=True, showgrid=True, title='Z')
                ),
                margin=dict(l=0, r=0, b=0, t=40)
            )
            
            pio.write_html(fig, file=out_html, auto_open=False)
            outputs.append(out_html)
            print(f"3D Interactive Network saved: {out_html}")
            
        except Exception as e:
            print(f"Error 3D Network: {e}")

    @staticmethod
    def generate_interactive_strain_network_3d(data_file, db_param, outputs, aligner_suffix=""):
        """
        Generates an INTERACTIVE 3D Network for STRAINS (Linhagens) using Plotly.
        Nodes = Strains, Edges = Similarity based on gene content.
        """
        if not PLOTLY_AVAILABLE or MDS is None:
            return
        
        db_name = db_param[1:]
        out_html = f"network_3d_strains_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.html"
        
        try:
            print(f"\nGenerating 3D Interactive Strain Network for {db_name.upper()}...")
            df = pd.read_csv(data_file, sep=";", index_col="Strains")
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Use original dataframe (Rows=Strains, Cols=Genes)
            df_binary = (df > 0).astype(int)
            
            if df_binary.shape[0] < 3:
                print("  Not enough strains for network.")
                return

            # Calculate Similarity between STRAINS (rows)
            dist_matrix = pdist(df_binary.values, metric='jaccard')
            sim_matrix = 1 - squareform(dist_matrix)
            
            threshold = 0.75 # Similarity threshold
            adj = np.where(sim_matrix > threshold, 1, 0)
            np.fill_diagonal(adj, 0)
            
            G = nx.from_numpy_array(adj)
            mapping = {i: name for i, name in enumerate(df_binary.index)}
            G = nx.relabel_nodes(G, mapping)
            G.remove_nodes_from(list(nx.isolates(G)))
            
            if G.number_of_nodes() == 0: 
                print("  No significant strain connections found.")
                return

            pos = nx.spring_layout(G, dim=3, seed=42)
            
            x_nodes = [pos[n][0] for n in G.nodes()]
            y_nodes = [pos[n][1] for n in G.nodes()]
            z_nodes = [pos[n][2] for n in G.nodes()]
            
            node_names = list(G.nodes())

            # Edges Trace
            edge_x, edge_y, edge_z = [], [], []
            for edge in G.edges():
                x0, y0, z0 = pos[edge[0]]
                x1, y1, z1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_z.extend([z0, z1, None])

            edge_trace = go.Scatter3d(
                x=edge_x, y=edge_y, z=edge_z,
                mode='lines',
                line=dict(color='#888', width=1),
                hoverinfo='none'
            )

            # Nodes Trace (Strains)
            node_trace = go.Scatter3d(
                x=x_nodes, y=y_nodes, z=z_nodes,
                mode='markers+text',
                marker=dict(
                    size=8,
                    color='#1f77b4', # Unified color for strains
                    opacity=0.8
                ),
                text=node_names,
                hoverinfo='text'
            )

            fig = go.Figure(data=[edge_trace, node_trace])
            fig.update_layout(
                title=f"3D Strain Similarity Network - {db_name.upper()}",
                showlegend=False,
                scene=dict(
                    xaxis=dict(showbackground=True, showgrid=True, title='X'),
                    yaxis=dict(showbackground=True, showgrid=True, title='Y'),
                    zaxis=dict(showbackground=True, showgrid=True, title='Z')
                ),
                margin=dict(l=0, r=0, b=0, t=40)
            )
            
            pio.write_html(fig, file=out_html, auto_open=False)
            outputs.append(out_html)
            print(f"3D Strain Network saved: {out_html}")
            
        except Exception as e:
            print(f"Error 3D Strain Network: {e}")

    @staticmethod
    def generate_radar_plot(data_file, db_param, outputs, aligner_suffix=""):
        """
        Generates a Radar/Spider Plot mapping individual Strains (Linhagens).
        Uses aliases for Strains to keep the plot neat, and creates an extra image serving as the legend.
        """
        db_name = db_param[1:]
        fileType = "pdf" if "-pdf" in sys.argv or "-png" not in sys.argv else "png"
        out = f"radar_plot_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
        
        try:
            print(f"\nGenerating Optimized Radar Plot for {db_name.upper()}...")
            df = pd.read_csv(data_file, sep=";", index_col="Strains")
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # 1. Clean data: Remove columns with all zeros
            df = df.loc[:, (df != 0).any(axis=0)]
            if df.empty:
                print("  No data available for radar plot.")
                return

            # 2. Strict Limit on Genes (Axes) to prevent pollution
            if df.shape[1] > 20:
                print("  Limiting Radar Plot to top 20 most variable genes for clarity.")
                variance = df.var()
                top_genes = variance.sort_values(ascending=False).head(20).index
                df = df[top_genes]
            
            categories = list(df.columns)
            N = len(categories)
            
            # 3. Abbreviation Helper for axes
            def abbreviate(name, max_len=10):
                s = str(name).strip()
                if len(s) > max_len:
                    return s[:max_len-2] + ".."
                return s

            categories_abbr = [abbreviate(c) for c in categories]
            
            # 4. Create Aliases for Strains (L1, L2...)
            original_strains = df.index.tolist()
            strain_aliases = {strain: f"L{idx+1}" for idx, strain in enumerate(original_strains)}
            df = df.rename(index=strain_aliases)
            
            # Setup Angles
            angles = [n / float(N) * 2 * math.pi for n in range(N)]
            angles += angles[:1] # Close the loop
            
            plt.figure(figsize=(10, 10))
            ax = plt.subplot(111, polar=True)
            
            # Set Labels
            plt.xticks(angles[:-1], categories_abbr, color='black', size=9)
            ax.set_rlabel_position(0)
            plt.yticks([25, 50, 75, 100], ["25", "50", "75", "100"], color="grey", size=7)
            plt.ylim(0, 100)
            
            num_strains = len(df.index)
            
            # Plot individual lines for each strain
            colors = cm.get_cmap("tab10", num_strains)
            for idx, (alias, row) in enumerate(df.iterrows()):
                values = row.tolist()
                values += values[:1]
                color = colors(idx % 10)
                ax.plot(angles, values, linewidth=1.5, linestyle='solid', label=alias, color=color)
                ax.fill(angles, values, color=color, alpha=0.05)
            
            plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), title="Strains")
            plt.title(f"Radar Identity Map - {db_name.upper()}", size=16, y=1.08, fontweight='bold')
            
            plt.savefig(out, dpi=300, bbox_inches="tight")
            plt.close()
            outputs.append(out)
            print(f"Radar Plot saved: {out}")
            
            # 5. Generate Separate Legend Image that ties the Genomes back to the Strain Alias shown
            legend_out = f"radar_plot_legend_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
            
            # Calculate dynamic height for the legend table
            leg_height = max(4, num_strains * 0.4)
            fig_leg, ax_leg = plt.subplots(figsize=(8, leg_height))
            ax_leg.axis('tight')
            ax_leg.axis('off')
            
            table_data = [[alias, orig] for orig, alias in strain_aliases.items()]
            table = ax_leg.table(cellText=table_data, colLabels=["Strain Alias", "Genome/Original Name"], loc='center', cellLoc='left')
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1, 1.5)
            
            plt.title(f"Radar Plot Legend Map - {db_name.upper()}", size=14, fontweight='bold', pad=20)
            plt.savefig(legend_out, format=fileType, dpi=300, bbox_inches="tight")
            plt.close(fig_leg)
            
            outputs.append(legend_out)
            print(f"Radar Plot Legend Image saved: {legend_out}")
            
        except Exception as e:
            print(f"Error Radar Plot: {e}")

    @staticmethod
    def generate_detailed_report(matrix_file, gene_count_file, db_param, meta1, meta2, outputs, aligner_suffix=""):
        """Generates a comprehensive Excel and CSV report with robust Category Calculation"""
        db_name = db_param[1:]
        suffix = f"_{aligner_suffix}" if aligner_suffix else ""
        
        csv_filename = f"{db_name}_detailed_report{suffix}.csv"
        xlsx_filename = f"{db_name}_detailed_report{suffix}.xlsx"
        
        print(f"\nGenerating detailed comprehensive reports for {db_name.upper()}...")
        
        try:
            # Load the main matrix
            df_matrix = pd.read_csv(matrix_file, sep=';', index_col='Strains')
            df_matrix = df_matrix.loc[:, ~df_matrix.columns.str.contains('^Unnamed')]
            
            # Robust: Remove spaces from column names (genes) to match metadata keys
            df_matrix.columns = df_matrix.columns.str.strip()
            
            total_genomes = len(df_matrix.index)
            if total_genomes == 0:
                print("Error: No genomes found in matrix for report.")
                return

            # Calculate Pan-Genome Categories Internally (More Robust)
            # Renamed to 'Pan_Class' to avoid collision with biological 'Category'
            binary_matrix = (df_matrix > 0).astype(int)
            gene_sums = binary_matrix.sum(axis=0) # Sum columns (Genes)
            
            pan_categories = {}
            core_count = 0
            accessory_count = 0
            exclusive_count = 0

            for gene, count in gene_sums.items():
                gene_key = str(gene).strip()
                if count >= total_genomes:
                    pan_categories[gene_key] = 'Core'
                    core_count += 1
                elif count == 1:
                    pan_categories[gene_key] = 'Exclusive'
                    exclusive_count += 1
                else:
                    pan_categories[gene_key] = 'Accessory'
                    accessory_count += 1
            
            print(f"  Classification Stats: Core={core_count}, Accessory={accessory_count}, Exclusive={exclusive_count}")

            # Flatten matrix for report
            df_long = df_matrix.melt(ignore_index=False, var_name='Gene', value_name='Identity').reset_index()
            
            # Rename 'Strains' to 'Genome' if necessary
            if 'Strains' in df_long.columns:
                df_long.rename(columns={'Strains': 'Genome'}, inplace=True)
            elif 'index' in df_long.columns:
                 df_long.rename(columns={'index': 'Genome'}, inplace=True)
            
            # Clean gene names in long dataframe too
            df_long['Gene'] = df_long['Gene'].astype(str).str.strip()
                
            # Filter only present genes
            df_present = df_long[df_long['Identity'] > 0].copy()
            
            if df_present.empty:
                print("  No genes present to report.")
                return

            # Define Labels based on DB
            label_1, label_2 = "Classification_1", "Classification_2"
            
            if db_param == "-card": label_1, label_2 = "Drug_Class", "Resistance_Mechanism"
            elif db_param == "-bacmet": label_1, label_2 = "Compound", "Resistance_Type"
            elif db_param == "-vfdb": label_1, label_2 = "Virulence_Factor", "VF_Category"
            elif db_param == "-megares": label_1, label_2 = "Drug_Class", "Mechanism"
            elif db_param == "-victors": label_1, label_2 = "Product", "Category"
            elif db_param == "-argannot": label_1, label_2 = "Antibiotic_Class", "Category"
            elif db_param == "-resfinder": label_1, label_2 = "Resistance_Type", "Phenotype"

            # Clean metadata keys: strip whitespace and handle potential mismatches
            meta1_clean = {str(k).strip(): v for k, v in meta1.items()}
            meta2_clean = {str(k).strip(): v for k, v in meta2.items()}

            # Map Data
            # 1. Pan-Genome Classification (Core/Accessory/Exclusive)
            df_present['Pan_Class'] = df_present['Gene'].map(pan_categories).fillna('Unknown')
            
            # 2. Biological Classification (Mechanism/Category/Product)
            df_present[label_1] = df_present['Gene'].map(meta1_clean).fillna('Unknown')
            df_present[label_2] = df_present['Gene'].map(meta2_clean).fillna('Unknown')
            
            # Select and Order Columns
            # Ensure we include both the Pan_Class AND the DB specific labels
            final_df = df_present[['Genome', 'Gene', 'Identity', 'Pan_Class', label_1, label_2]].sort_values(by=['Genome', 'Gene'])
            
            # Save Outputs
            final_df.to_csv(csv_filename, index=False)
            outputs.append(csv_filename)
            
            try:
                final_df.to_excel(xlsx_filename, index=False, sheet_name=f'{db_name.upper()} Report')
                outputs.append(xlsx_filename)
                print(f"Detailed reports saved:\n  - {csv_filename}\n  - {xlsx_filename}")
            except:
                print(f"Note: Saved CSV only: {csv_filename}")

        except Exception as e:
            print(f"Error generating detailed report: {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def generate_lineplot(data_file, title, pan_label, core_label, output_file, fileType, outputs):
        """Standard cumulative lineplot"""
        try:
            df_pan = pd.read_csv(data_file, sep=";")
            if len(df_pan) == 0: return
            
            df_pan["Number of Genomes"] = list(range(1, len(df_pan["Strains"]) + 1))
            df_pan = df_pan.rename(columns={'Core': 'Core Genes'})
            
            if "Core Genes" in df_pan.columns and "Pan" in df_pan.columns:
                df_pan.loc[df_pan["Core Genes"] > df_pan["Pan"], "Core Genes"] = df_pan["Pan"]
            
            plt.figure(figsize=(12, 8))
            sns.lineplot(x="Number of Genomes", y="Pan", data=df_pan, marker='o', linewidth=2.5, color='#1f77b4', label=pan_label)
            sns.lineplot(x="Number of Genomes", y="Core Genes", data=df_pan, marker='s', linewidth=2.5, color='#ff7f0e', label=core_label)
            
            plt.xlabel('Number of Genomes', fontsize=14, fontweight='bold')
            plt.ylabel('Number of Genes', fontsize=14, fontweight='bold')
            plt.title(title, fontsize=16, fontweight='bold', pad=20)
            plt.legend(fontsize=12)
            plt.grid(True, alpha=0.4, linestyle='--')
            
            from matplotlib.ticker import MaxNLocator
            plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
            plt.tight_layout()
            
            if not str(output_file).endswith(f'.{fileType}'):
                output_file = f"{output_file}.{fileType}"
            
            plt.savefig(output_file, format=fileType, dpi=300)
            plt.close()
            outputs.append(output_file)
            print(f"Simple pan-genome plot saved as: {output_file}")
                
        except Exception as e:

            print(f"Error generating lineplot: {e}")
