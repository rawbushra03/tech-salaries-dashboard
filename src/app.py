"""Interactive Streamlit dashboard for global tech salaries."""

from pathlib import Path
from typing import Iterable, Optional, Sequence

import pandas as pd
import plotly.express as px
import streamlit as st

try:  # Works both with package imports and Streamlit's script runner.
    from .data_loader import clean_data
except ImportError:  # pragma: no cover - depends on how Streamlit executes the file
    try:
        from src.data_loader import clean_data
    except ImportError:
        from data_loader import clean_data


DATA_URL = "https://raw.githubusercontent.com/foorilla/ai-jobs-net-salaries/main/salaries.csv"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_CLEANED_PATH = PROJECT_ROOT / "data" / "salaries_cleaned.csv"
LOCAL_RAW_PATH = PROJECT_ROOT / "data" / "salaries_raw.csv"

REMOTE_ORDER = ("Remote", "Hybrid", "On-site")
EXPERIENCE_ORDER = (
    "Entry-level",
    "Mid-level",
    "Senior-level",
    "Executive-level",
    "Unknown",
)


@st.cache_data(ttl=3600)
def load_data(
    data_url: str = DATA_URL,
    local_cleaned_path: str = str(LOCAL_CLEANED_PATH),
    local_raw_path: str = str(LOCAL_RAW_PATH),
) -> pd.DataFrame:
    """Load the remote dataset, falling back to the local CSV when necessary.

    Streamlit caches this function for one hour.  The source is recorded in
    ``DataFrame.attrs`` so the sidebar can tell the user whether the current
    view came from GitHub or the local fallback without emitting UI elements
    from inside a cached function.
    """
    remote_error: Optional[Exception] = None

    try:
        remote_df = pd.read_csv(data_url)
        cleaned = clean_data(remote_df)
        cleaned.attrs["data_source"] = "GitHub"
        cleaned.attrs["source_url"] = data_url
        return cleaned
    except Exception as error:  # A network error must not break the dashboard.
        remote_error = error

    fallback_errors = []
    fallback_candidates = (
        (Path(local_cleaned_path), "Local cleaned CSV"),
        (Path(local_raw_path), "Local raw CSV"),
    )

    for path, source_name in fallback_candidates:
        if not path.exists():
            continue
        try:
            local_df = clean_data(pd.read_csv(path))
            local_df.attrs["data_source"] = source_name
            local_df.attrs["source_path"] = str(path)
            return local_df
        except Exception as error:
            fallback_errors.append(f"{path}: {error}")

    details = "; ".join(fallback_errors) or "no local CSV was found"
    raise FileNotFoundError(
        "Unable to load salary data from GitHub or the local fallback "
        f"({details})."
    ) from remote_error


def filter_data(
    data: pd.DataFrame,
    years: Optional[Iterable[int]] = None,
    regions: Optional[Iterable[str]] = None,
    roles: Optional[Iterable[str]] = None,
    remote_statuses: Optional[Iterable[str]] = None,
    experience_levels: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Return the rows matching the currently selected dashboard filters."""
    filtered = data

    if years is not None:
        filtered = filtered[filtered["work_year"].isin(list(years))]
    if regions is not None:
        filtered = filtered[filtered["region"].isin(list(regions))]
    if roles is not None:
        filtered = filtered[filtered["job_title"].isin(list(roles))]
    if remote_statuses is not None:
        filtered = filtered[filtered["remote_status"].isin(list(remote_statuses))]
    if experience_levels is not None:
        filtered = filtered[
            filtered["experience_level_name"].isin(list(experience_levels))
        ]

    return filtered.copy()


def calculate_kpis(data: pd.DataFrame) -> dict:
    """Calculate KPI values safely, including the empty-filter case."""
    if data.empty:
        return {
            "average_salary": None,
            "total_roles": 0,
            "remote_percentage": None,
            "top_paying_region": "—",
        }

    region_averages = data.groupby("region")["salary_in_usd"].mean()
    top_region = region_averages.idxmax() if not region_averages.empty else "—"

    return {
        "average_salary": float(data["salary_in_usd"].mean()),
        "total_roles": int(len(data)),
        "remote_percentage": float(data["remote_status"].eq("Remote").mean() * 100),
        "top_paying_region": str(top_region),
    }


def format_currency(value: Optional[float]) -> str:
    """Format a dollar amount for a KPI while handling missing values."""
    if value is None or pd.isna(value):
        return "—"
    return f"${value:,.0f}"


def format_percentage(value: Optional[float]) -> str:
    """Format a percentage for a KPI while handling missing values."""
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.1f}%"


def format_year_scope(years: Sequence[int]) -> str:
    """Create a compact, dynamic label for the selected years."""
    selected_years = sorted({int(year) for year in years})
    if not selected_years:
        return "No years selected"
    if len(selected_years) == 1:
        return str(selected_years[0])
    return f"{selected_years[0]}–{selected_years[-1]}"


def ordered_options(values: Iterable[str], preferred_order: Sequence[str]) -> list:
    """Keep familiar status labels first and append any new labels."""
    available = {str(value) for value in values}
    ordered = [value for value in preferred_order if value in available]
    ordered.extend(sorted(available.difference(ordered)))
    return ordered


def render_kpis(data: pd.DataFrame) -> dict:
    """Render the reactive KPI row and return its values for later insights."""
    kpis = calculate_kpis(data)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Avg Salary (USD)", format_currency(kpis["average_salary"]))
    with col2:
        st.metric("Total Roles Analyzed", f"{kpis['total_roles']:,}")
    with col3:
        st.metric("% Fully Remote", format_percentage(kpis["remote_percentage"]))
    with col4:
        st.metric("Top Paying Region", kpis["top_paying_region"])

    return kpis


def render_latam_spotlight(context_data: pd.DataFrame, year_scope: str) -> None:
    """Render a responsive LATAM salary benchmark and remote-work snapshot.

    ``context_data`` applies year, role, experience and modality filters but
    intentionally does not apply the region filter.  This keeps LATAM visible
    as a benchmark even when a user is exploring only US or EU records.
    """
    st.header("🌎 LATAM Spotlight")

    latam_data = context_data[context_data["region"].eq("LATAM")]
    if latam_data.empty:
        st.info(
            "No LATAM records match the selected years, roles, experience "
            "levels, and work modalities."
        )
        return

    latam_average = float(latam_data["salary_in_usd"].mean())
    global_average = float(context_data["salary_in_usd"].mean())
    us_data = context_data[context_data["region"].eq("US")]
    us_average = float(us_data["salary_in_usd"].mean()) if not us_data.empty else None
    latam_remote_percentage = float(
        latam_data["remote_status"].eq("Remote").mean() * 100
    )

    latam_vs_us = None
    if us_average and us_average != 0:
        latam_vs_us = (latam_average - us_average) / us_average * 100

    metric1, metric2, metric3, metric4 = st.columns(4)
    with metric1:
        st.metric("LATAM Avg Salary", format_currency(latam_average))
    with metric2:
        st.metric(
            "LATAM vs US",
            f"{latam_vs_us:+.1f}%" if latam_vs_us is not None else "—",
            help="Difference in average salary relative to US-based roles.",
        )
    with metric3:
        st.metric("LATAM Fully Remote", format_percentage(latam_remote_percentage))
    with metric4:
        st.metric("LATAM Roles", f"{len(latam_data):,}")

    benchmark_rows = [
        {"Segment": "LATAM", "Average salary": latam_average},
        {"Segment": "Global", "Average salary": global_average},
    ]
    if us_average is not None:
        benchmark_rows.insert(1, {"Segment": "US", "Average salary": us_average})

    benchmark = pd.DataFrame(benchmark_rows)
    fig = px.bar(
        benchmark,
        x="Segment",
        y="Average salary",
        color="Segment",
        title=f"Average Salary Benchmark · {year_scope}",
        labels={"Average salary": "Average salary (USD)"},
        color_discrete_map={"LATAM": "#f97316", "US": "#2563eb", "Global": "#64748b"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Benchmark uses the selected year, role, experience, and modality filters; "
        "the region filter is intentionally excluded so LATAM remains a useful comparison."
    )


def main() -> None:
    """Build the Streamlit application."""
    st.set_page_config(
        page_title="Tech Salaries | Global Insights",
        page_icon="💰",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .main { background-color: #f5f7f9; }
        .stMetric {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    try:
        data = load_data()
    except Exception as error:
        st.error(
            "Salary data could not be loaded. Check the GitHub URL or add "
            "data/salaries_cleaned.csv to the project."
        )
        st.exception(error)
        st.stop()

    source = data.attrs.get("data_source", "Unknown source")
    st.sidebar.header("Filter Options")
    if source == "GitHub":
        st.sidebar.success("Live GitHub data · refreshed every hour")
    else:
        st.sidebar.info(f"Using {source.lower()} fallback")
    st.sidebar.caption("Source: foorilla/ai-jobs-net-salaries")

    year_options = sorted(int(year) for year in data["work_year"].unique())
    region_options = sorted(str(region) for region in data["region"].unique())
    role_options = sorted(str(role) for role in data["job_title"].unique())
    remote_options = ordered_options(data["remote_status"].unique(), REMOTE_ORDER)
    experience_options = ordered_options(
        data["experience_level_name"].unique(), EXPERIENCE_ORDER
    )

    years = st.sidebar.multiselect(
        "Select Year",
        options=year_options,
        default=year_options,
    )
    regions = st.sidebar.multiselect(
        "Select Region",
        options=region_options,
        default=region_options,
    )
    roles = st.sidebar.multiselect(
        "Select Job Role (optional)",
        options=role_options,
        default=[],
    )
    remote_statuses = st.sidebar.multiselect(
        "Work Modality",
        options=remote_options,
        default=remote_options,
    )
    experience_levels = st.sidebar.multiselect(
        "Experience Level",
        options=experience_options,
        default=experience_options,
    )

    # The main view respects every filter.  The comparison context leaves out
    # region so LATAM can act as a benchmark regardless of the region selected.
    filtered_data = filter_data(
        data,
        years=years,
        regions=regions,
        roles=roles or None,
        remote_statuses=remote_statuses,
        experience_levels=experience_levels,
    )
    comparison_context = filter_data(
        data,
        years=years,
        roles=roles or None,
        remote_statuses=remote_statuses,
        experience_levels=experience_levels,
    )

    year_scope = format_year_scope(years)
    if roles and len(roles) == 1:
        role_scope = roles[0]
    elif roles:
        role_scope = f"{len(roles)} selected roles"
    else:
        role_scope = "all roles"
    region_scope = ", ".join(regions) if regions else "no regions selected"

    st.title(f"🚀 Tech Salaries Dashboard · {year_scope}")
    st.caption(
        f"Data & AI compensation · {role_scope} · {region_scope} · "
        f"{len(filtered_data):,} records in view"
    )

    if filtered_data.empty:
        st.warning(
            "No records match the current filters. Select at least one value in "
            "each required filter to repopulate the charts."
        )

    kpis = render_kpis(filtered_data)
    st.markdown("---")

    # Visualisations row 1: role ranking and time evolution.
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.subheader(f"Top 10 Roles by Average Salary · {year_scope}")
        if filtered_data.empty:
            st.info("No role data for the current selection.")
        else:
            top_roles = (
                filtered_data.groupby("job_title")["salary_in_usd"]
                .mean()
                .sort_values(ascending=False)
                .head(10)
                .rename("Average salary")
                .reset_index()
            )
            fig_bar = px.bar(
                top_roles,
                x="Average salary",
                y="job_title",
                orientation="h",
                color="Average salary",
                color_continuous_scale="Viridis",
                labels={"Average salary": "Average salary (USD)", "job_title": "Role"},
            )
            fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_bar, use_container_width=True)

    with row1_col2:
        st.subheader(f"Salary Evolution · {year_scope}")
        evolution = (
            filtered_data.groupby("work_year", as_index=False)["salary_in_usd"].mean()
            if not filtered_data.empty
            else pd.DataFrame(columns=["work_year", "salary_in_usd"])
        )
        if evolution.empty:
            st.info("No time-series data for the current selection.")
        else:
            fig_line = px.line(
                evolution,
                x="work_year",
                y="salary_in_usd",
                markers=True,
                labels={"salary_in_usd": "Average salary (USD)", "work_year": "Year"},
            )
            st.plotly_chart(fig_line, use_container_width=True)

    # Visualisations row 2: distribution views.
    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        st.subheader(f"Salary Distribution by Region · {year_scope}")
        if filtered_data.empty:
            st.info("No regional data for the current selection.")
        else:
            fig_box = px.box(
                filtered_data,
                x="region",
                y="salary_in_usd",
                color="region",
                labels={"salary_in_usd": "Salary (USD)", "region": "Region"},
            )
            st.plotly_chart(fig_box, use_container_width=True)

    with row2_col2:
        st.subheader(f"Global Salary Distribution · {year_scope}")
        if filtered_data.empty:
            st.info("No salary data for the current selection.")
        else:
            fig_hist = px.histogram(
                filtered_data,
                x="salary_in_usd",
                nbins=50,
                marginal="rug",
                color_discrete_sequence=["#636EFA"],
                labels={"salary_in_usd": "Salary (USD)"},
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader(f"Salary Heatmap: Role vs Region · {year_scope}")
    if filtered_data.empty:
        st.info("No heatmap data for the current selection.")
    else:
        top_15_roles = filtered_data["job_title"].value_counts().head(15).index
        heatmap_data = filtered_data[
            filtered_data["job_title"].isin(top_15_roles)
        ].pivot_table(
            index="job_title",
            columns="region",
            values="salary_in_usd",
            aggfunc="mean",
        )
        if heatmap_data.empty:
            st.info("No role-by-region combinations are available.")
        else:
            fig_heat = px.imshow(
                heatmap_data,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="RdBu_r",
                labels={"x": "Region", "y": "Job Role", "color": "Avg Salary"},
            )
            st.plotly_chart(fig_heat, use_container_width=True)

    # Keep the LATAM benchmark separate from the region-filtered overview.
    render_latam_spotlight(comparison_context, year_scope)

    st.subheader(f"Average Salary by Selected Region · {year_scope}")
    if filtered_data.empty:
        st.info("No regional comparison for the current selection.")
    else:
        comparison = (
            filtered_data.groupby("region", as_index=False)["salary_in_usd"]
            .mean()
            .rename(columns={"salary_in_usd": "Average salary"})
            .sort_values("Average salary", ascending=False)
        )
        fig_comparison = px.bar(
            comparison,
            x="region",
            y="Average salary",
            color="region",
            labels={"Average salary": "Average salary (USD)", "region": "Region"},
        )
        st.plotly_chart(fig_comparison, use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Download filtered data",
        data=filtered_data.to_csv(index=False).encode("utf-8"),
        file_name="tech_salaries_filtered.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.header("💡 Key Insights")
    if filtered_data.empty:
        st.info("Key insights will appear once the filters return at least one role.")
    else:
        highest_salary = float(filtered_data["salary_in_usd"].max())
        most_common_role = str(filtered_data["job_title"].mode().iloc[0])
        if len(evolution) > 1:
            first_salary = float(evolution["salary_in_usd"].iloc[0])
            last_salary = float(evolution["salary_in_usd"].iloc[-1])
            trend = "growing" if last_salary > first_salary else "shifting"
        else:
            trend = "stable"

        remote_average = filtered_data.loc[
            filtered_data["remote_status"].eq("Remote"), "salary_in_usd"
        ].mean()
        onsite_average = filtered_data.loc[
            filtered_data["remote_status"].eq("On-site"), "salary_in_usd"
        ].mean()
        if pd.notna(remote_average) and pd.notna(onsite_average) and onsite_average:
            remote_gap = (remote_average - onsite_average) / onsite_average * 100
            remote_insight = (
                f"Remote roles earn **{abs(remote_gap):.1f}% "
                f"{'more' if remote_gap >= 0 else 'less'}** than on-site roles."
            )
        else:
            remote_insight = "There are not enough remote and on-site roles to compare a premium."

        st.markdown(
            f"""
            - **Highest Salary Found:** {format_currency(highest_salary)} USD
            - **Most Common Role:** {most_common_role}
            - **Market Trend:** Average salaries show a **{trend}** trend across the selected years.
            """
        )
        st.markdown(
            f"""
            - **Remote Premium:** {remote_insight}
            - **Regional Leader:** **{kpis['top_paying_region']}** has the highest average salary in the current view.
            - **Scope:** These insights update with every sidebar selection.
            """
        )

    st.markdown(
        "**Author:** Bushra Rawat | "
        "[LinkedIn](https://www.linkedin.com/in/bushra-rawat/) | "
        "[GitHub](https://github.com/rawbushra03)"
    )


if __name__ == "__main__":
    main()
