import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_visualizations(data_path='data/salaries_cleaned.csv', output_dir='screenshots'):
    """
    Generates statistical analysis and saves plots as images.
    """
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    df = pd.read_csv(data_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # Set visual style
    sns.set_theme(style="whitegrid")
    plt.rcParams['figure.figsize'] = (12, 6)

    # 1. Top 10 roles mejor pagados (Average)
    top_roles = df.groupby('job_title')['salary_in_usd'].mean().sort_values(ascending=False).head(10)
    plt.figure()
    sns.barplot(x=top_roles.values, y=top_roles.index, palette='viridis')
    plt.title('Top 10 Highest Paying Roles (Average USD)')
    plt.xlabel('Average Salary (USD)')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/top_10_roles.png')
    plt.close()

    # 2. Salarios por región
    plt.figure()
    sns.boxplot(data=df, x='region', y='salary_in_usd', palette='Set2')
    plt.title('Salary Distribution by Region')
    plt.ylabel('Salary (USD)')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/salary_by_region.png')
    plt.close()

    # 3. Evolución de salarios 2021-2025
    plt.figure()
    sns.lineplot(data=df, x='work_year', y='salary_in_usd', estimator='mean', marker='o')
    plt.title('Salary Evolution (2021-2025)')
    plt.ylabel('Average Salary (USD)')
    plt.xticks([2021, 2022, 2023, 2024, 2025])
    plt.tight_layout()
    plt.savefig(f'{output_dir}/salary_evolution.png')
    plt.close()

    # 4. Comparación Remote vs On-site
    plt.figure()
    sns.violinplot(data=df, x='remote_status', y='salary_in_usd', palette='pastel')
    plt.title('Remote vs On-site Salary Comparison')
    plt.ylabel('Salary (USD)')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/remote_vs_onsite.png')
    plt.close()

    # 5. Salario por nivel de experiencia
    plt.figure()
    order = ['Entry-level', 'Mid-level', 'Senior-level', 'Executive-level']
    sns.barplot(data=df, x='experience_level_name', y='salary_in_usd', order=order, palette='magma')
    plt.title('Average Salary by Experience Level')
    plt.ylabel('Average Salary (USD)')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/salary_by_level.png')
    plt.close()

    print(f"Visualizations saved to {output_dir}")

if __name__ == "__main__":
    generate_visualizations()
