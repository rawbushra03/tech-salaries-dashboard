# 🚀 Tech Salaries Dashboard

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0+-green.svg)](https://pandas.pydata.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.20+-red.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.10+-orange.svg)](https://plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An interactive dashboard for exploring global tech salaries, with a focus on Data, AI, and remote-work trends from 2021 onwards.

---

## 🔗 Live Demo

[**Open the dashboard on Streamlit Cloud →**](https://tech-salaries-dashboard-bushra-rawat.streamlit.app/)

The dashboard refreshes its GitHub data cache every hour and falls back to the local processed CSV when the remote source is unavailable.

---

## 📊 Project Overview

This project explores how compensation varies by location, role, experience level, and work modality. It answers questions about geographic salary differences, the remote premium, and the way seniority affects compensation in the modern tech market.

### Key Features

- **Global Insights:** Compare US, LATAM, EU, ASIA, Africa, and Oceania.
- **LATAM Spotlight:** Benchmark LATAM salaries against US and global averages, with a reactive fully-remote metric.
- **Remote Work Analysis:** Compare Remote, Hybrid, and On-site roles.
- **Interactive Filters:** Filter by year, role, region, experience level, and work modality.
- **Reactive KPIs:** Recalculate average salary, sample size, remote share, and the highest-paying region for every filter selection.
- **Dynamic Narrative:** Chart titles and dashboard context update to reflect the selected scope.
- **Visual Analytics:** Explore interactive Plotly charts, including heatmaps, box plots, distributions, and time trends.
- **Downloadable Data:** Export the currently filtered records as a CSV from the sidebar.

---

## 🔄 How It Works

The dashboard uses a small, reproducible data pipeline:

1. **Fetch:** `src/app.py` reads the public [salary CSV on GitHub](https://raw.githubusercontent.com/foorilla/ai-jobs-net-salaries/main/salaries.csv) with `pandas.read_csv`.
2. **Cache:** Streamlit caches the loaded and cleaned dataframe for **one hour** (`ttl=3600`) so the app stays responsive without requesting the source on every interaction.
3. **Fallback:** If GitHub cannot be reached, the app tries `data/salaries_cleaned.csv` and then `data/salaries_raw.csv` from the repository.
4. **Clean:** `src/data_loader.py` exposes the independent `clean_data(df)` function. It removes duplicates, handles missing required values, keeps records from 2021 onwards, normalises numeric fields, and adds:
   - `region` from the company-location country code;
   - `experience_level_name` from the source experience code; and
   - `remote_status` from the remote-work ratio.
5. **Filter:** Sidebar selections create the main filtered dataframe. The LATAM benchmark applies the year, role, experience, and modality selections while keeping all regions available for comparison.
6. **Analyse:** KPIs, charts, the LATAM Spotlight, insights, and the download button are all recomputed from the current selection on each Streamlit rerun.

This separation keeps data preparation independent from the user interface and makes the same cleaning function reusable in notebooks or scripts.

---

## 📸 Screenshots

| Salary Evolution | Top Roles |
|---|---|
| ![Evolution](screenshots/salary_evolution.png) | ![Top Roles](screenshots/top_10_roles.png) |

| Regional Distribution | Remote vs On-site |
|---|---|
| ![Region](screenshots/salary_by_region.png) | ![Remote](screenshots/remote_vs_onsite.png) |

---

## 🛠️ Tech Stack

- **Data Processing:** Python, Pandas, NumPy
- **Visualizations:** Plotly Express, Matplotlib, Seaborn
- **Dashboard Framework:** Streamlit
- **Environment:** Jupyter Notebooks for exploratory analysis
- **Data Source:** [foorilla/ai-jobs-net-salaries](https://github.com/foorilla/ai-jobs-net-salaries), published under CC0

---

## 🚀 Installation & Usage

### 1. Clone the repository

```bash
git clone https://github.com/rawbushra03/tech-salaries-dashboard.git
cd tech-salaries-dashboard
```

### 2. Set up a virtual environment (recommended)

```bash
# macOS / Linux
python -m venv .venv
source .venv/bin/activate

# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the dashboard

```bash
streamlit run src/app.py
```

---

## 📁 Project Structure

```text
tech-salaries-dashboard/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── data_loader.py    # Reusable cleaning and local-loading helpers
│   ├── analyzer.py       # Statistical analysis and static plots
│   └── app.py            # Streamlit dashboard and interactive pipeline
├── data/
│   ├── salaries_raw.csv      # Optional raw dataset for local fallback
│   └── salaries_cleaned.csv  # Processed local fallback
├── notebooks/
│   └── exploratory_analysis.ipynb
└── screenshots/          # Exported visualisations
```

---

## 💡 Key Insights

- **Remote Advantage:** Remote roles can command competitive salaries comparable to on-site roles in major tech hubs.
- **US Leadership:** US-based roles remain the highest-paying market in the current sample, while LATAM provides a useful lower-cost comparison for distributed teams.
- **Specialisation Pays:** AI and Machine Learning roles are among the top earners globally.
- **Experience Matters:** Compensation generally rises from entry-level to senior and executive roles, reflecting the value of specialised experience.

---

## 🤝 Contact

**Bushra Rawat**  
- [LinkedIn](https://www.linkedin.com/in/bushra-rawat/)  
- [GitHub](https://github.com/rawbushra03)  
- Email: rawatbush2003@gmail.com

---

*License: MIT*
