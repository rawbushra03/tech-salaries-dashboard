import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Page Config
st.set_page_config(page_title="Tech Salaries Dashboard", page_icon="💰", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# Data Loading with Fallback
@st.cache_data
def load_data():
    path = 'data/salaries_cleaned.csv'
    if not os.path.exists(path):
        # Fallback to creating it if possible
        if os.path.exists('data/salaries_raw.csv'):
            from data_loader import load_and_clean_data
            return load_and_clean_data()
        else:
            return None
    return pd.read_csv(path)

df = load_data()

if df is None:
    st.error("Data not found! Please make sure 'data/salaries_cleaned.csv' exists.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Options")

years = st.sidebar.multiselect("Select Year", options=sorted(df['work_year'].unique()), default=sorted(df['work_year'].unique()))
regions = st.sidebar.multiselect("Select Region", options=sorted(df['region'].unique()), default=sorted(df['region'].unique()))
roles = st.sidebar.multiselect("Select Job Role", options=sorted(df['job_title'].unique()))
remote_status = st.sidebar.multiselect("Work Modality", options=df['remote_status'].unique(), default=df['remote_status'].unique())
exp_levels = st.sidebar.multiselect("Experience Level", options=df['experience_level_name'].unique(), default=df['experience_level_name'].unique())

# Filter data
filtered_df = df[
    (df['work_year'].isin(years)) &
    (df['region'].isin(regions)) &
    (df['remote_status'].isin(remote_status)) &
    (df['experience_level_name'].isin(exp_levels))
]

if roles:
    filtered_df = filtered_df[filtered_df['job_title'].isin(roles)]

# --- MAIN DASHBOARD ---
st.title("🚀 Tech Salaries Global Dashboard")
st.markdown("Analyzing the landscape of Data & AI salaries (2021-2025)")

# KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    avg_salary = filtered_df['salary_in_usd'].mean()
    st.metric("Avg Salary (USD)", f"${avg_salary:,.0f}")
with col2:
    total_jobs = len(filtered_df)
    st.metric("Total Roles Analyzed", f"{total_jobs:,}")
with col3:
    remote_pct = (filtered_df['remote_status'] == 'Remote').mean() * 100
    st.metric("% Remote Jobs", f"{remote_pct:.1f}%")
with col4:
    top_paying_region = filtered_df.groupby('region')['salary_in_usd'].mean().idxmax()
    st.metric("Top Paying Region", top_paying_region)

st.markdown("---")

# Visualizations Row 1
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    # Bar Chart: Top Salaries by Role
    st.subheader("Top 10 Roles by Average Salary")
    top_roles = filtered_df.groupby('job_title')['salary_in_usd'].mean().sort_values(ascending=False).head(10).reset_index()
    fig_bar = px.bar(top_roles, x='salary_in_usd', y='job_title', orientation='h', 
                     color='salary_in_usd', color_continuous_scale='Viridis',
                     labels={'salary_in_usd': 'Avg Salary (USD)', 'job_title': 'Role'})
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

with row1_col2:
    # Line Chart: Evolution
    st.subheader("Salary Evolution Over Time")
    evolution = filtered_df.groupby('work_year')['salary_in_usd'].mean().reset_index()
    fig_line = px.line(evolution, x='work_year', y='salary_in_usd', markers=True,
                       labels={'salary_in_usd': 'Avg Salary (USD)', 'work_year': 'Year'})
    st.plotly_chart(fig_line, use_container_width=True)

# Visualizations Row 2
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    # Box Plot: Distribution by Region
    st.subheader("Salary Distribution by Region")
    fig_box = px.box(filtered_df, x='region', y='salary_in_usd', color='region',
                     labels={'salary_in_usd': 'Salary (USD)', 'region': 'Region'})
    st.plotly_chart(fig_box, use_container_width=True)

with row2_col2:
    # Histogram: General Distribution
    st.subheader("Global Salary Distribution")
    fig_hist = px.histogram(filtered_df, x='salary_in_usd', nbins=50, 
                            marginal="rug", color_discrete_sequence=['#636EFA'],
                            labels={'salary_in_usd': 'Salary (USD)'})
    st.plotly_chart(fig_hist, use_container_width=True)

# Heatmap Row
st.subheader("Salary Heatmap: Role vs Region")
# Only for top 15 roles to keep it readable
top_15_roles = filtered_df['job_title'].value_counts().head(15).index
heatmap_data = filtered_df[filtered_df['job_title'].isin(top_15_roles)].pivot_table(
    index='job_title', columns='region', values='salary_in_usd', aggfunc='mean'
)
fig_heat = px.imshow(heatmap_data, text_auto=True, aspect="auto", 
                      color_continuous_scale='RdBu_r',
                      labels=dict(x="Region", y="Job Role", color="Avg Salary"))
st.plotly_chart(fig_heat, use_container_width=True)

# Visualizations Row 3: LATAM vs US Comparison
st.subheader("🌎 LATAM vs US vs Global Comparison")
comparison_df = filtered_df.groupby('region')['salary_in_usd'].mean().sort_values(ascending=False).reset_index()
fig_comp = px.bar(comparison_df, x='region', y='salary_in_usd', 
                  color='region', title="Average Salary by Region (USD)",
                  labels={'salary_in_usd': 'Avg Salary (USD)', 'region': 'Region'})
st.plotly_chart(fig_comp, use_container_width=True)

# Download Button
st.sidebar.markdown("---")
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="📥 Download filtered data",
    data=csv,
    file_name='tech_salaries_filtered.csv',
    mime='text/csv',
)

# Key Insights
st.markdown("---")
st.header("💡 Key Insights")
col_ins1, col_ins2 = st.columns(2)

with col_ins1:
    highest_salary = filtered_df['salary_in_usd'].max()
    most_common_role = filtered_df['job_title'].mode()[0]
    st.markdown(f"""
    - **Highest Salary Found:** ${highest_salary:,.0f} USD
    - **Most Common Role:** {most_common_role}
    - **Market Trend:** Average salaries have shown a {'growing' if evolution['salary_in_usd'].iloc[-1] > evolution['salary_in_usd'].iloc[0] else 'shifting'} trend since 2021.
    """)

with col_ins2:
    remote_avg = filtered_df[filtered_df['remote_status'] == 'Remote']['salary_in_usd'].mean()
    onsite_avg = filtered_df[filtered_df['remote_status'] == 'On-site']['salary_in_usd'].mean()
    diff = ((remote_avg - onsite_avg) / onsite_avg) * 100
    st.markdown(f"""
    - **Remote Premium:** Remote roles earn on average **{abs(diff):.1f}% {'more' if diff > 0 else 'less'}** than on-site roles.
    - **Experience Gap:** Senior-level roles earn significantly more than entry-level, reflecting high demand for expertise.
    - **Regional Leader:** {top_paying_region} continues to lead in compensation packages.
    """)

st.markdown(f"**Author:** Bushra Rawat | [LinkedIn](https://www.linkedin.com/in/bushra-rawat/) | [GitHub](https://github.com/rawbushra03)")
