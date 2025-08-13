import os
import sys
import math

from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns

class Visualization:
    @staticmethod
    def generate_matrix(db_param, outputs, comp, aligner_suffix=""):
        """Generate presence/absence matrix from alignment results"""
        db_name = db_param[1:]  # Remove the '-' from parameter name
        
        if aligner_suffix:
            titulo = f"matriz_{db_name}_{aligner_suffix}.csv"
            tabular_dir = f"Tabular_2_{db_name}_{aligner_suffix}"
        else:
            titulo = f"matriz_{db_name}.csv"
            tabular_dir = f"Tabular_2_{db_name}"
        
        outputs.append(titulo)

        print(f"\nGenerating the presence and identity matrix for {db_param}{f' ({aligner_suffix})' if aligner_suffix else ''}...")

        dicl = {}
        totalgenes = set()  # Use set for better performance
        found_genes_per_strain = {}  # Track found genes per strain for save-genes functionality
        
        # Check if directory exists and has files
        if not os.path.exists(tabular_dir):
            print(f"Warning: Directory {tabular_dir} not found!")
            return titulo, dicl, [], found_genes_per_strain
            
        files_in_dir = os.listdir(tabular_dir)
        if not files_in_dir:
            print(f"Warning: No files found in {tabular_dir}!")
            return titulo, dicl, [], found_genes_per_strain
        
        print(f"Processing {len(files_in_dir)} strain files...")
        
        # Debug: Print sample of comp dictionary for MEGARes.
        if db_param == "-megares" and comp:
            print(f"Sample comp mappings for MEGARes:")
            sample_keys = list(comp.keys())[:5]  # Show first 5 mappings
            for k in sample_keys:
                print(f"  {k} -> {comp[k]}")
        
        for i in files_in_dir:
            if not i.endswith('.tab'):
                continue
                
            linhagem = i[:-4]  # Remove .tab extension
            file_path = os.path.join(tabular_dir, i)
            
            try:
                with open(file_path, 'rt') as file:
                    linhas = file.readlines()
            except Exception as e:
                print(f"Warning: Could not read file {file_path}: {e}")
                continue
            
            genes = {}
            genes_found = 0
            debug_sample_count = 0
            strain_found_genes = {}  # Track locus_tags and genes for this strain
            
            for j in linhas:
                linha = j.strip()
                if not linha:  # Skip empty lines
                    continue
                    
                linha = linha.split('\t')
                if len(linha) < 3:  # Need at least query, subject, identity
                    continue
                
                # Debug: Print first few subject IDs for MEGARes to understand format
                if db_param == "-megares" and debug_sample_count < 3:
                    print(f"  Debug - Subject ID: {linha[1]}")
                    debug_sample_count += 1
                    
                gene = None
                original_gene = None  # For debugging
                locus_tag = linha[0]  # First column is the locus_tag
                
                # Special handling for MEGARes first - extract exact MEG_ID
                if 'MEG_' in linha[1] and '|' in linha[1]:
                    # Subject ID format: MEG_7303|Drugs|Elfamycins|EF-Tu_inhibition|TUFAB|RequiresSNPConfirmation
                    parts = linha[1].split('|')
                    if len(parts) >= 5:
                        meg_id = parts[0]  # Get MEG_7303 (exact match)
                        actual_gene = parts[4]  # Get TUFAB (the real gene name)
                        
                        # Check if we have this exact MEG_ID in our comp dictionary
                        if meg_id in comp:
                            gene = comp[meg_id]
                            original_gene = "exact_comp_match:" + meg_id
                        # If not found, use the actual gene from the header
                        elif actual_gene.strip():
                            gene = actual_gene.strip().replace('\n', '').replace('\r', '')  # Clean newlines
                            original_gene = "header_gene:" + actual_gene.strip()
                            # Debug print for this case
                            if db_param == "-megares" and debug_sample_count <= 10:
                                print(f"    Using gene from header: {meg_id} -> {gene}")
                
                # If no MEGARes match, try regular substring matching for other databases
                if gene is None:
                    for k in comp.keys():
                        if k in linha[1]:  # linha[1] is the subject sequence ID
                            gene = comp[k]
                            original_gene = "substring_match:" + k
                            break
                
                # Debug print for MEGARes
                if db_param == "-megares" and gene and debug_sample_count <= 10:
                    print(f"    Matched gene: {gene} (from {original_gene})")
                
                if gene:
                    try:
                        identidade = float(linha[2])  # Convert identity to float
                        genes[gene] = identidade
                        totalgenes.add(gene)
                        genes_found += 1
                        
                        # Store locus_tag for save-genes functionality
                        if gene not in strain_found_genes:
                            strain_found_genes[gene] = []
                        strain_found_genes[gene].append(locus_tag)
                        
                    except (ValueError, IndexError):
                        print(f"Warning: Invalid identity value in {file_path}: {linha}")
                        continue
            
            dicl[str(linhagem)] = genes
            found_genes_per_strain[str(linhagem)] = strain_found_genes
            print(f"  - {linhagem}: {genes_found} genes found")
        
        # Convert set back to sorted list for consistent output
        totalgenes = sorted(list(totalgenes))
        
        print(f"Total unique genes found: {len(totalgenes)}")
        print(f"Total strains processed: {len(dicl)}")
        
        # Generate the matrix file
        if not totalgenes:  # If no genes were found, create empty matrix
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
        """Generate clustermap visualization from matrix"""
        fileType = "pdf"
        if "-pdf" in sys.argv:
            fileType = "pdf"
        elif "-png" in sys.argv:
            fileType = "png"
        
        db_name = db_param[1:]  # Remove the '-' from parameter name
        
        if aligner_suffix:
            out = f"heatmap_{db_name}_{aligner_suffix}.{fileType}"
        else:
            out = f"heatmap_{db_name}.{fileType}"
        
        outputs.append(out)
        
        if db_param == "-card":
            color = "Blues"
        elif db_param == "-vfdb":
            color = "Reds"
        elif db_param == "-bacmet":
            color = "Greens"
        elif db_param == "-megares":
            color = "Oranges"

        df = pd.read_csv(data_file, sep=';')
        df = df.set_index('Strains')
        headers = list(df.columns.values)
        lines = list(df.index.values)
        for i in headers:
            if "Unnamed:" in i:
                df = df.drop(columns=[i])


        x = math.ceil(len(headers) * 0.65)
        y = math.ceil(len(lines) * 0.65)


        print(f"\nPlotting final heatmap{f' ({aligner_suffix})' if aligner_suffix else ''}...")
        try:

            plt.figure(figsize=(x, y))
            p2 = sns.heatmap(df, cmap=color, annot=True, fmt='.0f', cbar_kws={'label': 'Identity (%)'})
            p2.figure.savefig(out, format=fileType, dpi=300, bbox_inches="tight")

            plt.close()

        except BaseException:
            erro_string = f"\nIt was not possible to plot the {out} figure...\nPlease verify the GenBank files and the matrix_x.csv output."
            erro.append(erro_string)
            print(erro_string)

    @staticmethod
    def generate_barplot(data_file, index_col, output_file, fileType, outputs):
        """Generate barplot from a semicolon-separated data file with dynamic sizing"""
        try:
            data = pd.read_csv(data_file, sep=";", index_col=index_col)

            if data is not None and not data.empty:

                # Prepare data for seaborn barplot
                data_melted = data.reset_index().melt(id_vars=index_col, var_name='Category', value_name='Count')
                
                # Calculate dynamic figure size based on data dimensions
                num_categories = len(data.index)
                num_series = len(data.columns)
                
                # Base dimensions
                base_width = 10
                base_height = 6
                
                # Dynamic width calculation - scale with number of categories
                width = max(base_width, min(20, base_width + num_categories * 0.8))
                
                # Dynamic height calculation - scale with number of series and max values
                max_value = data.values.max()
                height = max(base_height, min(15, base_height + num_series * 0.5 + max_value * 0.01))
                
                plt.figure(figsize=(width, height))
                ax = sns.barplot(data=data_melted, x=index_col, y='Count', hue='Category', errorbar=None)
                
                # Add value labels on top of bars - format as integers
                for container in ax.containers:
                    ax.bar_label(container, fontsize=max(8, min(12, 10 - num_categories * 0.1)), fmt='%.0f')
                
                ax.set_xlabel(index_col, fontsize=12)
                ax.set_ylabel('Number of Genes', fontsize=12)
                ax.set_title(f'{index_col} Distribution', fontsize=14, fontweight='bold')
                
                # Force integer ticks on y-axis
                ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
                
                # Dynamic rotation based on category name length
                max_label_length = max(len(str(label)) for label in data.index)
                rotation_angle = 45 if max_label_length > 10 or num_categories > 8 else 0
                
                plt.xticks(rotation=rotation_angle, ha='right' if rotation_angle > 0 else 'center')
                
                # Adjust layout based on rotation
                if rotation_angle > 0:
                    plt.subplots_adjust(bottom=0.2)
                
                plt.tight_layout()
                
                # Ensure output_file is a string and has proper extension
                if not isinstance(output_file, str):
                    output_file = str(output_file)
                if not output_file.endswith(f'.{fileType}'):
                    output_file = f"{output_file}.{fileType}"
                
                ax.figure.savefig(output_file, format=fileType, dpi=300, bbox_inches="tight")
                plt.close()
                outputs.append(output_file)
                print(f"Barplot saved as: {output_file} (size: {width:.1f}x{height:.1f})")
            else:
                print(f"No data to plot for {output_file}")
        except Exception as e:
            print(f"Error generating barplot {output_file}: {e}")

    @staticmethod
    def generate_scatterplot(data_file, index_col, output_file, fileType, outputs):
        """Generate scatterplot from a semicolon-separated data file with dynamic sizing"""
        try:
            data = pd.read_csv(data_file, sep=";", index_col=index_col)

            if data is not None and not data.empty:
                # Prepare data for scatterplot - we need at least 2 columns
                if len(data.columns) < 2:
                    print(f"Error: Need at least 2 columns for scatterplot, found {len(data.columns)}")
                    return
                
                # Use first two columns for x and y
                x_column = data.columns[0]
                y_column = data.columns[1]
                hue_column = data.columns[2] if len(data.columns) > 2 else None
                
                # Reset index to make it a regular column for plotting
                data_reset = data.reset_index()
                
                # Calculate dynamic figure size based on data dimensions
                num_points = len(data)
                num_categories = len(data.columns)
                
                # Base dimensions
                base_width = 10
                base_height = 8
                
                # Dynamic sizing based on data
                width = max(base_width, min(16, base_width + num_points * 0.01))
                height = max(base_height, min(12, base_height + num_categories * 0.5))
                
                plt.figure(figsize=(width, height))
                
                # Create scatterplot using the first two numeric columns
                if hue_column is not None:
                    # Use third column as hue if available
                    ax = sns.scatterplot(data=data_reset, x=x_column, y=y_column, hue=hue_column,
                                        s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
                else:
                    # Simple scatterplot without hue
                    ax = sns.scatterplot(data=data_reset, x=x_column, y=y_column,
                                        s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
                
                # Set labels and title
                ax.set_xlabel(x_column.replace('_', ' ').title(), fontsize=12, fontweight='bold')
                ax.set_ylabel(y_column.replace('_', ' ').title(), fontsize=12, fontweight='bold')
                ax.set_title(f'{x_column} vs {y_column} Distribution', fontsize=14, fontweight='bold', pad=20)
                
                # Force integer ticks on both axes
                ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
                ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
                
                # Add grid for better readability
                plt.grid(True, alpha=0.3, linestyle='--')
                
                # Adjust legend if hue is used
                if hue_column is not None:
                    legend = ax.legend(title=hue_column.replace('_', ' ').title(), 
                                        bbox_to_anchor=(1.05, 1), loc='upper left',
                                        frameon=True, shadow=True)
                    legend.get_frame().set_facecolor('white')
                    legend.get_frame().set_alpha(0.9)
                
                # Add correlation coefficient if both columns are numeric
                try:
                    if pd.api.types.is_numeric_dtype(data[x_column]) and pd.api.types.is_numeric_dtype(data[y_column]):
                        correlation = data[x_column].corr(data[y_column])
                        plt.text(0.05, 0.95, f'r = {correlation:.3f}', transform=ax.transAxes,
                                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.8),
                                fontsize=11, verticalalignment='top')
                except Exception:
                    pass  # Skip correlation if calculation fails
                
                plt.tight_layout()
                
                # Ensure output_file is a string and has proper extension
                if not isinstance(output_file, str):
                    output_file = str(output_file)
                if not output_file.endswith(f'.{fileType}'):
                    output_file = f"{output_file}.{fileType}"
                
                ax.figure.savefig(output_file, format=fileType, dpi=300, bbox_inches="tight")
                plt.close()
                outputs.append(output_file)
                print(f"Scatterplot saved as: {output_file} (size: {width:.1f}x{height:.1f})")
            else:
                print(f"No data to plot for {output_file}")
        except Exception as e:
            print(f"Error generating scatterplot {output_file}: {e}")

    @staticmethod
    def generate_joint_and_marginal_distributions(data_file, db_param, outputs, erro, aligner_suffix=""):
        """Hexbin joint plot with marginal distributions using seaborn"""
        try:
            fileType = "pdf" if "-pdf" in sys.argv or "-png" not in sys.argv else "png"
            if "-png" in sys.argv:
                fileType = "png"
            db_name = db_param[1:]
            out = f"joint_hexbin_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
            outputs.append(out)

            # Database-specific color palettes (matching other generate methods)
            if db_param == "-card":
                color_palette = "Blues"
                main_color = "#2171b5"  # Blue
            elif db_param == "-vfdb":
                color_palette = "Reds"
                main_color = "#cb181d"  # Red
            elif db_param == "-bacmet":
                color_palette = "Greens"
                main_color = "#238b45"  # Green
            elif db_param == "-megares":
                color_palette = "Oranges"
                main_color = "#d94801"  # Orange
            else:
                color_palette = "viridis"
                main_color = "#4CB391"  # Default

            df = pd.read_csv(data_file, sep=';').set_index('Strains')
            for col in list(df.columns):
                if "Unnamed:" in col:
                    df = df.drop(columns=[col])

            # Metrics
            genes_present = (df > 0).sum(axis=1).astype(int)
            df_numeric = df.apply(pd.to_numeric, errors='coerce')
            # Calculate mean identity, replacing 0 with NaN for calculation, then fill NaN with 0
            mean_identity_temp = df_numeric.replace(0, pd.NA).mean(axis=1, skipna=True)
            mean_identity = pd.to_numeric(mean_identity_temp.fillna(0), errors='coerce')
            metrics = pd.DataFrame({"GenesPresent": genes_present, "MeanIdentity": mean_identity})

            if metrics.empty:
                print(f"Warning: No data to plot for hexbin jointplot ({db_param})")
                return

            # Check if we have enough data points for a meaningful hexbin plot
            if len(metrics) < 2:
                print(f"Warning: Not enough data points ({len(metrics)}) for hexbin jointplot ({db_param}). Need at least 2 strains.")
                return
            
            # Check for valid numeric ranges to avoid division by zero
            x_range = metrics["GenesPresent"].max() - metrics["GenesPresent"].min()
            y_range = metrics["MeanIdentity"].max() - metrics["MeanIdentity"].min()
            
            if x_range == 0 and y_range == 0:
                print(f"Warning: No variation in data for hexbin jointplot ({db_param}). All values are identical.")
                return
            elif x_range == 0:
                print(f"Warning: No variation in genes present for hexbin jointplot ({db_param})")
                return
            elif y_range == 0:
                print(f"Warning: No variation in mean identity for hexbin jointplot ({db_param})")
                return

            # Calculate dynamic figure size based on data range
            data_span_x = x_range if x_range > 0 else 10
            data_span_y = y_range if y_range > 0 else 10
            
            # Base size with scaling factor
            base_size = 6
            scale_factor = min(1.5, max(0.8, (data_span_x + data_span_y) / 100))
            fig_size = base_size * scale_factor
            
            # Set the correct theme
            sns.set_theme(style="ticks")
            
            try:
                x = metrics["GenesPresent"].to_numpy()
                y = metrics["MeanIdentity"].to_numpy()

                # Create hexbin plot with consistent colors and appropriate scaling
                g = sns.jointplot(
                    x=x, y=y, 
                    kind="hex", 
                    color=main_color,
                    height=fig_size,
                    joint_kws={
                        'gridsize': 15,  # Moderate hexagon size
                        'cmap': color_palette,
                        'alpha': 0.8,  # Full opacity for hexagons
                        'edgecolors': 'white'  # White edges for better definition
                    },
                    marginal_kws={
                        'color': main_color,
                        'alpha': 0.8,
                        'bins': 15
                    }
                )
                
                # Set labels and title
                g.set_axis_labels("Genes Present", "Mean Identity (%)", fontsize=12, fontweight='bold')
                g.figure.suptitle(f"Hexbin plot with marginal distributions - {db_name.upper()}", 
                                y=1.02, fontsize=14, fontweight="bold")
                
                # Improve axis appearance
                g.ax_joint.tick_params(labelsize=10)
                
                # Add some padding to the axes
                x_padding = x_range * 0.05 if x_range > 0 else 1
                y_padding = y_range * 0.05 if y_range > 0 else 1
                
                g.ax_joint.set_xlim(
                    metrics["GenesPresent"].min() - x_padding,
                    metrics["GenesPresent"].max() + x_padding
                )
                g.ax_joint.set_ylim(
                    metrics["MeanIdentity"].min() - y_padding,
                    metrics["MeanIdentity"].max() + y_padding
                )

                g.figure.savefig(out, format=fileType, dpi=300, bbox_inches="tight")
                plt.close(g.figure)
                print(f"Hexbin jointplot saved as: {out}")
                
            finally:
                # Reset theme to default after plotting
                sns.reset_defaults()
                
        except Exception as e:
            erro_string = f"\nFailed to plot hexbin jointplot ({db_param}): {e}"
            erro.append(erro_string)
            print(erro_string)

    @staticmethod
    def generate_scatterplot_heatmap(data_file, db_param, outputs, erro, aligner_suffix=""):
        
        fileType = "pdf"
        if "-pdf" in sys.argv:
            fileType = "pdf"
        elif "-png" in sys.argv:
            fileType = "png"

        db_name = db_param[1:]
        out = f"scatter_heatmap_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
        outputs.append(out)

        # Tema semelhante ao exemplo solicitado
        try:
            
            # Aplicar tema temporariamente apenas para este gráfico
            with sns.axes_style("whitegrid"):
                # Leitura e preparo
                df = pd.read_csv(data_file, sep=';').set_index('Strains')
                # Remover colunas não nomeadas
                for col in list(df.columns):
                    if "Unnamed:" in col:
                        df = df.drop(columns=[col])

                # Long-form: Strains, Gene, Identity
                long_df = df.reset_index().melt(id_vars='Strains', var_name='Gene', value_name='Identity')
                # Garantir tipo numérico para Identity e filtrar zeros/NaN
                long_df['Identity'] = pd.to_numeric(long_df['Identity'], errors='coerce')
                long_df = long_df[long_df['Identity'] > 0]
                if long_df.empty:
                    print(f"Warning: No data to plot for scatter heatmap {out}")
                    return

                # Limites para normalização de tamanho/cor
                id_min = float(long_df['Identity'].min())
                id_max = float(long_df['Identity'].max())
                if id_max <= id_min:
                    id_max = id_min + 1.0

                # Paleta contínua dependente do db_param (seguindo generate_heatmap)
                if db_param == "-card":
                    palette = "Blues"
                elif db_param == "-vfdb":
                    palette = "Reds"
                elif db_param == "-bacmet":
                    palette = "Greens"
                elif db_param == "-megares":
                    palette = "Oranges"
                else:
                    palette = "viridis"

                # Dimensionamento dinâmico: altura baseada em strains e largura proporcional a genes
                n_genes = long_df['Gene'].nunique()
                n_strains = long_df['Strains'].nunique()
                # Altura: escala suavemente com o número de strains
                height = max(5, min(22, 2 + 0.28 * n_strains))
                # Aspecto (largura/altura): proporcional à razão genes/strains (com limites mais largos para mais espaço no X)
                aspect_ratio = max(15.0, min(15.0, n_genes / max(n_strains, 1)))

                print(f"\nPlotting scatter heatmap{f' ({aligner_suffix})' if aligner_suffix else ''}...")

                g = sns.relplot(
                    data=long_df,
                    x="Gene", y="Strains",
                    hue="Identity", size="Identity",
                    palette=palette, legend=True,
                    hue_norm=(id_min, id_max),
                    edgecolor=".7",
                    height=height,
                    sizes=(id_min * 10, id_max * 10),  # Tamanho proporcional ao Identity
                    size_norm=(id_min, id_max),
                    aspect=aspect_ratio
                )

                # Ajustes de estilo no espírito do exemplo
                g.set(xlabel="Genes", ylabel="Strains")
                g.despine(left=True, bottom=True)
                # Reduzir espaçamento vertical entre categorias e margens extras
                try:
                    g.ax.set_ylim(-0.5, n_strains - 0.5)
                except Exception:
                    pass
                # Aumentar espaço no X e reduzir ao máximo no Y
                g.ax.margins(x=.08, y=0.0)
                # Reduzir padding entre ticks/labels no Y e aumentar no X
                try:
                    # Tamanho de fonte dinâmico para Y para compactar visualmente
                    y_labelsize = max(7, min(11, 12 - int(n_strains * 0.15)))
                    g.ax.tick_params(axis='y', pad=0, labelsize=y_labelsize)
                    g.ax.tick_params(axis='x', pad=10)
                except Exception:
                    pass
                for label in g.ax.get_xticklabels():
                    label.set_rotation(90)

                g.figure.suptitle(f"Scatter Heatmap - {db_name.upper()}", y=1.02, fontweight="bold")

                # Salvar
                g.figure.savefig(out, format=fileType, dpi=300, bbox_inches="tight")
                plt.close(g.figure)
                print(f"Scatter heatmap saved as: {out}")

        except BaseException as e:
            erro_string = (
                f"\nIt was not possible to plot the scatter heatmap {out}...\n"
                f"Error: {e}\nPlease verify the GenBank files and the matrix_x.csv output."
            )
            erro.append(erro_string)
            print(erro_string)

    @staticmethod
    def generate_scatterplot_with_continuous_hues_and_sizes(data_file, index_col, output_file, fileType, outputs):
        """Bubble scatter: x=index_col (categorical), y=Category, hue/size by Count (continuous) using seaborn"""
        try:
            data = pd.read_csv(data_file, sep=';', index_col=index_col)
            if data is None or data.empty:
                print(f"No data to plot for {output_file}")
                return

            long_df = data.reset_index().melt(id_vars=index_col, var_name="Category", value_name="Count")

            num_x = long_df[index_col].nunique()
            num_y = long_df["Category"].nunique()

            base_w, base_h = 10, 6
            width = max(base_w, min(24, base_w + num_x * 0.7))
            height = max(base_h, min(16, base_h + num_y * 0.7))

            plt.figure(figsize=(width, height))
            ax = sns.scatterplot(
                data=long_df, x=index_col, y="Category",
                hue="Count", size="Count", sizes=(40, 600),
                palette="viridis", alpha=0.8, edgecolor="black", linewidth=0.4
            )
            ax.set_title(f"Counts by {index_col} and Category", fontweight="bold")
            ax.set_xlabel(index_col, fontweight="bold")
            ax.set_ylabel("Category", fontweight="bold")
            plt.xticks(rotation=45, ha="right")
            ax.grid(True, linestyle="--", alpha=0.3)  # Use ax.grid() instead of plt.grid()

            if not isinstance(output_file, str):
                output_file = str(output_file)
            if not output_file.endswith(f".{fileType}"):
                output_file = f"{output_file}.{fileType}"

            plt.tight_layout()
            plt.savefig(output_file, format=fileType, dpi=300, bbox_inches="tight")
            plt.close()
            outputs.append(output_file)
            print(f"Bubble scatter saved as: {output_file} (size: {width:.1f}x{height:.1f})")
        except Exception as e:
            print(f"Error generating bubble scatter {output_file}: {e}")

    @staticmethod
    def generate_regression_fit_over_strip_plot(data_file, index_col, output_file, fileType, outputs):
        """Strip plot with regression fit (trend over ordered categories) using seaborn"""
        try:
            data = pd.read_csv(data_file, sep=';', index_col=index_col)
            if data is None or data.empty:
                print(f"No data to plot for {output_file}")
                return

            long_df = data.reset_index().melt(id_vars=index_col, var_name="Category", value_name="Count")
            # Map categories to numeric positions
            x_levels = list(long_df[index_col].unique())
            x_pos_map = {cat: idx for idx, cat in enumerate(x_levels)}
            long_df["x_pos"] = long_df[index_col].map(x_pos_map)

            base_w = 10
            width = max(base_w, min(24, base_w + len(x_levels) * 0.6))
            height = 8

            plt.figure(figsize=(width, height))
            # Strip plot (categorical)
            sns.stripplot(data=long_df, x=index_col, y="Count", hue="Category", jitter=0.25, dodge=True, alpha=0.6)
            # Regression over numeric x positions (trend across index_col order)
            sns.regplot(data=long_df, x="x_pos", y="Count", scatter=False, color="black", line_kws={"lw": 2})

            plt.xticks(ticks=range(len(x_levels)), labels=x_levels, rotation=45, ha="right")
            plt.xlabel(index_col, fontweight="bold")
            plt.ylabel("Count", fontweight="bold")
            plt.title(f"Regression Fit over {index_col}", fontweight="bold")
            plt.grid(True, linestyle="--", alpha=0.3)
            plt.tight_layout()

            if not isinstance(output_file, str):
                output_file = str(output_file)
            if not output_file.endswith(f".{fileType}"):
                output_file = f"{output_file}.{fileType}"

            plt.savefig(output_file, format=fileType, dpi=300, bbox_inches="tight")
            plt.close()
            outputs.append(output_file)
            print(f"Regression over strip plot saved as: {output_file} (size: {width:.1f}x{height:.1f})")
        except Exception as e:
            print(f"Error generating regression over strip plot {output_file}: {e}")

    @staticmethod
    def generate_clustermap(data_file, db_param, outputs, erro, aligner_suffix=""):
        """Hierarchical clustermap using seaborn.clustermap"""
        fileType = "pdf"
        if "-pdf" in sys.argv:
            fileType = "pdf"
        elif "-png" in sys.argv:
            fileType = "png"

        db_name = db_param[1:]
        out = f"clustermap_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
        outputs.append(out)

        if db_param == "-card":
            cmap = "Blues"
        elif db_param == "-vfdb":
            cmap = "Reds"
        elif db_param == "-bacmet":
            cmap = "Greens"
        elif db_param == "-megares":
            cmap = "Oranges"
        else:
            cmap = "viridis"

        try:
            df = pd.read_csv(data_file, sep=';').set_index('Strains')
            for col in list(df.columns):
                if "Unnamed:" in col:
                    df = df.drop(columns=[col])

            if df.empty or df.shape[1] == 0:
                print(f"Warning: Empty data for clustermap: {data_file}")
                return
            
            # Check if we have enough data for clustering
            num_rows = len(df.index)
            num_cols = len(df.columns)
            
            if num_rows < 2:
                print(f"Warning: Cannot create clustermap with only {num_rows} sample(s). At least 2 samples are required for hierarchical clustering.")
                print(f"Skipping clustermap generation for {db_param}. Consider adding more genomes to your analysis.")
                return
            
            if num_cols < 2:
                print(f"Warning: Cannot create clustermap with only {num_cols} gene(s). At least 2 genes are required for hierarchical clustering.")
                print(f"Skipping clustermap generation for {db_param}.")
                return

            # Create clustermap
            g = sns.clustermap(
                df, cmap=cmap, method="average", metric="euclidean",
                z_score=None, standard_scale=None, cbar_kws={'label': 'Identity (%)'},
                figsize=(12, max(6, min(18, 0.4 * len(df.index) + 4)))
            )
            g.fig.suptitle(f"Hierarchical Clustermap - {db_name.upper()}", y=1.02, fontweight="bold")

            g.savefig(out, format=fileType, dpi=300, bbox_inches="tight")
            plt.close(g.fig)
            print(f"Hierarchical clustermap saved as: {out}")
        except Exception as e:
            erro_string = f"\nIt was not possible to plot the clustermap {out}: {e}"
            erro.append(erro_string)
            print(erro_string)

    @staticmethod
    def generate_lineplot(data_file, title, pan_label, core_label, output_file, fileType, outputs):
        """Generate pan-genome lineplot with proper parameter handling"""
        try:
            # Generate pan-genome plot with validation
            df_pan = pd.read_csv(data_file, sep=";")
            
            # Validate data before plotting
            if len(df_pan) == 0:
                print("Warning: No data found for pan-genome analysis!")
                return outputs
            
            df_pan["Number of Genomes"] = list(range(1, len(df_pan["Strains"]) + 1))
            df_pan = df_pan.rename(columns={'Core': 'Core Genes'})
            
            # Validate that core never exceeds pan
            invalid_rows = df_pan[df_pan["Core Genes"] > df_pan["Pan"]]
            if len(invalid_rows) > 0:
                print("Warning: Found rows where core > pan, correcting...")
                df_pan.loc[df_pan["Core Genes"] > df_pan["Pan"], "Core Genes"] = df_pan["Pan"]
            
            # Obter valores únicos dos dados para ajustar o tamanho da figura
            unique_values = sorted(set(df_pan["Pan"].tolist() + df_pan["Core Genes"].tolist()))
            # Adicionar 0 se não estiver presente
            if 0 not in unique_values and min(unique_values) > 0:
                unique_values = [0] + unique_values
            # Usar apenas valores inteiros
            unique_values = [int(val) for val in unique_values if val == int(val)]
            
            # Ajustar a altura com base no número de valores únicos
            num_unique_values = len(unique_values)
            # Garantir espaçamento adequado entre os valores do eixo Y
            y_size = max(8, min(10, 4 + num_unique_values * 0.8))
            
            plt.figure(figsize=(12, y_size))
            plt.subplot(1, 1, 1)
            
            # Create line plots with better styling
            sns.lineplot(x=df_pan["Number of Genomes"], y=df_pan["Pan"], 
                         marker='o', linewidth=2.5, markersize=8, color='#1f77b4', alpha=0.8, label=pan_label)
            sns.lineplot(x=df_pan["Number of Genomes"], y=df_pan["Core Genes"], 
                         marker='s', linewidth=2.5, markersize=8, color='#ff7f0e', alpha=0.8, label=core_label)
            
            plt.xlabel('Number of Genomes', fontsize=14, fontweight='bold')
            plt.ylabel('Number of Genes', fontsize=14, fontweight='bold')
            plt.title(title, fontsize=16, fontweight='bold', pad=20)
            plt.legend(fontsize=12, frameon=True, shadow=True, loc='upper left')
            plt.grid(True, alpha=0.3, linestyle='--')
            
            # Set integer ticks for x-axis
            plt.xticks(range(1, len(df_pan) + 1))
            
            # Garantir que o eixo Y mostre valores exatos correspondentes aos dados
            from matplotlib.ticker import FixedLocator
            # Definir os ticks exatamente nos valores dos dados
            plt.gca().yaxis.set_major_locator(FixedLocator(unique_values))
            
            # Add annotations for first and last points
            if len(df_pan) > 1:
                plt.annotate(f'Final Pan: {df_pan["Pan"].iloc[-1]}', 
                            xy=(len(df_pan), df_pan["Pan"].iloc[-1]), 
                            xytext=(10, 10), textcoords='offset points',
                            bbox=dict(boxstyle='round,pad=0.3', fc='lightblue', alpha=0.7),
                            fontsize=10)
                plt.annotate(f'Final Core: {df_pan["Core Genes"].iloc[-1]}', 
                            xy=(len(df_pan), df_pan["Core Genes"].iloc[-1]), 
                            xytext=(10, -15), textcoords='offset points',
                            bbox=dict(boxstyle='round,pad=0.3', fc='orange', alpha=0.7),
                            fontsize=10)
            
            plt.tight_layout()
            
            # Ensure output_file is a string and has proper extension
            if not isinstance(output_file, str):
                output_file = str(output_file)
            if not output_file.endswith(f'.{fileType}'):
                output_file = f"{output_file}.{fileType}"
            
            plt.savefig(output_file, format=fileType, dpi=300, bbox_inches="tight")
            plt.close()
            outputs.append(output_file)
            
            print(f"Pan-genome analysis completed:")
            print(f"  - Total genomes analyzed: {len(df_pan)}")
            print(f"  - Final pan-genome size: {df_pan['Pan'].iloc[-1]} genes")
            print(f"  - Final core-genome size: {df_pan['Core Genes'].iloc[-1]} genes")
            print(f"  - Pan-genome plot saved as: {output_file}")
            
            # Additional statistics
            if len(df_pan) > 1:
                pan_growth = df_pan['Pan'].iloc[-1] - df_pan['Pan'].iloc[0]
                core_reduction = df_pan['Core Genes'].iloc[0] - df_pan['Core Genes'].iloc[-1]
                print(f"  - Pan-genome growth: +{pan_growth} genes")
                print(f"  - Core-genome reduction: -{core_reduction} genes")
                
        except Exception as e:
            print(f"Error generating lineplot {output_file}: {e}")

