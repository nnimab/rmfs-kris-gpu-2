import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def plot_nerl_evolution(log_dir, output_dir):
    """
    Plots the evolution of fitness scores for a NERL training run,
    showing the cumulative best fitness and per-generation average.
    """
    fitness_data = []
    
    # Extract experiment name from log_dir path
    experiment_name = os.path.basename(os.path.normpath(log_dir))

    for gen_folder in sorted(os.listdir(log_dir)):
        if gen_folder.startswith('gen'):
            fitness_file = os.path.join(log_dir, gen_folder, 'fitness_scores.json')
            if os.path.exists(fitness_file):
                with open(fitness_file, 'r') as f:
                    data = json.load(f)
                    generation = data['generation']
                    best_fitness = data['best_fitness']
                    # Handle potential extreme negative values from penalties
                    all_fitness_no_extreme = [f for f in data['all_fitness'] if f > -1e9]
                    avg_fitness = sum(all_fitness_no_extreme) / len(all_fitness_no_extreme) if all_fitness_no_extreme else 0
                    
                    fitness_data.append({
                        'Generation': generation,
                        'Best Fitness': best_fitness,
                        'Average Fitness': avg_fitness
                    })

    if not fitness_data:
        print(f"No fitness data found in {log_dir}")
        return

    df = pd.DataFrame(fitness_data)
    # Calculate Cumulative Best Fitness
    df['Cumulative Best Fitness'] = df['Best Fitness'].cummax()

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))

    sns.lineplot(data=df, x='Generation', y='Cumulative Best Fitness', ax=ax, marker='o', label='Cumulative Best Fitness')
    sns.lineplot(data=df, x='Generation', y='Average Fitness', ax=ax, marker='x', linestyle='--', label='Average Fitness (per generation)')

    ax.set_title(f'NERL Training Evolution: {experiment_name}', fontsize=16)
    ax.set_xlabel('Generation', fontsize=12)
    ax.set_ylabel('Fitness Score', fontsize=12)
    ax.legend(fontsize=10)
    ax.tick_params(axis='both', which='major', labelsize=10)
    plt.tight_layout()

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, f"{experiment_name}_evolution.png")
    plt.savefig(output_path, dpi=300)
    print(f"SUCCESS: Plot for {experiment_name} saved to {output_path}")
    plt.close(fig)

def plot_comparison_evolution(experiment_dirs, title, output_dir, smoothing_window=3):
    """
    Plots a smoothed comparison of normalized fitness evolution for multiple NERL runs.

    Args:
        experiment_dirs (list): A list of directories for the experiments to compare.
        title (str): The title for the plot.
        output_dir (str): The directory to save the generated plot.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 8))

    for log_dir in experiment_dirs:
        experiment_name = os.path.basename(os.path.normpath(log_dir))
        fitness_data = []
        gen_folders = [d for d in os.listdir(log_dir) if d.startswith('gen')]
        
        for gen_folder in sorted(gen_folders):
            fitness_file = os.path.join(log_dir, gen_folder, 'fitness_scores.json')
            if os.path.exists(fitness_file):
                with open(fitness_file, 'r') as f:
                    data = json.load(f)
                    fitness_data.append({
                        'Generation': data['generation'],
                        'Best Fitness': data['best_fitness']
                    })
        
        if not fitness_data:
            continue

        df = pd.DataFrame(fitness_data)
        
        # Min-Max Normalization
        min_fitness = df['Best Fitness'].min()
        max_fitness = df['Best Fitness'].max()
        
        if (max_fitness - min_fitness) > 0:
            df['Normalized Fitness'] = (df['Best Fitness'] - min_fitness) / (max_fitness - min_fitness)
        else:
            df['Normalized Fitness'] = 0.5

        # Apply moving average for smoothing
        df['Smoothed Fitness'] = df['Normalized Fitness'].rolling(window=smoothing_window, center=True, min_periods=1).mean()

        sns.lineplot(data=df, x='Generation', y='Smoothed Fitness', ax=ax, label=experiment_name)

    ax.set_title(title, fontsize=18, weight='bold')
    ax.set_xlabel('Generation', fontsize=14)
    ax.set_ylabel('Smoothed Normalized Fitness Score', fontsize=14)
    ax.legend(title='Experiment', fontsize=10)
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_filename = title.replace(' ', '_') + ".png"
    output_path = os.path.join(output_dir, output_filename)
    plt.savefig(output_path, dpi=300)
    print(f"SUCCESS: Comparison plot saved to {output_path}")
    plt.close(fig)

def generate_summary_table(log_dir, output_dir):
    """
    Generates a markdown table summarizing the results from all experiments.

    Args:
        log_dir (str): The directory containing all experiment logs.
        output_dir (str): The directory to save the generated markdown table.
    """
    summary_data = []

    for experiment_folder in sorted(os.listdir(log_dir)):
        experiment_path = os.path.join(log_dir, experiment_folder)
        if os.path.isdir(experiment_path):
            metadata_file = os.path.join(experiment_path, 'metadata.json')
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    meta = json.load(f)
                    
                    # Safely get nested dictionary 'results'
                    results = meta.get('results', {})

                    summary_data.append({
                        'Experiment Name': experiment_folder,
                        'Controller Type': meta.get('controller_type', 'N/A'),
                        'Reward Mode': meta.get('reward_mode', 'N/A'),
                        'Best Fitness': results.get('best_fitness', 0),
                        'Final Orders Completed': results.get('completed_orders_final_eval', 0)
                    })
    
    if not summary_data:
        print("No metadata files found to generate summary table.")
        return

    df = pd.DataFrame(summary_data)
    
    # Sort by a meaningful column, e.g., Experiment Name
    df = df.sort_values(by='Experiment Name').reset_index(drop=True)

    # Convert DataFrame to Markdown
    markdown_table = df.to_markdown(index=False)

    output_path = os.path.join(output_dir, "summary_of_training_results.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Summary of All Training Results\n\n")
        f.write(markdown_table)
    
    print(f"\nSUCCESS: Summary table saved to {output_path}")


if __name__ == '__main__':
    # Define paths
    base_log_dir = 'thesis/第四章/訓練過程紀錄檔'
    output_plot_dir = 'thesis/第四章/generated_plots_and_tables'
    
    # --- Plot for a specific NERL experiment ---
    # specific_experiment = 'A_nerl_step_a3000ticks'
    # specific_log_path = os.path.join(base_log_dir, specific_experiment)
    
    # print(f"--- Starting plot generation for: {specific_experiment} ---")
    # if os.path.exists(specific_log_path):
    #     plot_nerl_evolution(specific_log_path, output_plot_dir)
    # else:
    #     print(f"ERROR: Directory not found: {specific_log_path}")

    # --- Process all NERL directories ---
    print("\n--- Starting batch processing for all NERL experiments ---")
    
    all_nerl_experiments = []
    for experiment_folder in os.listdir(base_log_dir):
        if 'nerl' in experiment_folder.lower() and os.path.isdir(os.path.join(base_log_dir, experiment_folder)):
            all_nerl_experiments.append(os.path.join(base_log_dir, experiment_folder))

    # Group experiments by reward mode
    step_experiments = [d for d in all_nerl_experiments if 'step' in os.path.basename(d)]
    global_experiments = [d for d in all_nerl_experiments if 'global' in os.path.basename(d)]

    # Generate comparison plots
    if step_experiments:
        plot_comparison_evolution(step_experiments, "NERL Performance Comparison (Step Reward)", output_plot_dir, smoothing_window=3)
    if global_experiments:
        plot_comparison_evolution(global_experiments, "NERL Performance Comparison (Global Reward)", output_plot_dir, smoothing_window=3)


    # --- Generate individual plots (optional, can be enabled if needed) ---
    # Now that comparison plots are better, individual ones might be less needed
    # but the function is kept for detailed analysis if required.
    
    # --- Generate Summary Table for All Experiments ---
    generate_summary_table(base_log_dir, output_plot_dir) 