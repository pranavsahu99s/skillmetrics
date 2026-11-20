"""
SkillMetrics - Tech Job Market & Salary Insights Explorer
Interactive Dashboard built with Streamlit, Plotly, Pandas, Python SQLite, and Live Online Job Fetcher.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db
import etl
import job_fetcher

# Set page config
st.set_page_config(
    page_title="SkillMetrics | Tech Job Market Insights",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished dashboard UI
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-title {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38bdf8;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #cbd5e1;
        margin-top: 2px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        padding-left: 18px;
        padding-right: 18px;
        border-radius: 6px;
        font-weight: 600;
    }
    .job-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .job-card:hover {
        border-color: #38bdf8;
    }
    .job-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 4px;
    }
    .job-company {
        color: #38bdf8;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .badge-fit {
        background-color: #065f46;
        color: #34d399;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-source {
        background-color: #312e81;
        color: #a5b4fc;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 8px;
    }
    .tag-pill {
        display: inline-block;
        background-color: #0f172a;
        color: #94a3b8;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.75rem;
        margin-right: 6px;
        margin-top: 6px;
    }
    .tag-matched {
        background-color: #1e3a5f;
        color: #38bdf8;
        border-color: #38bdf8;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR FILTERS -----------------
st.sidebar.image("https://img.icons8.com/fluency/96/combo-chart.png", width=64)
st.sidebar.title("SkillMetrics")
st.sidebar.caption("Tech Job Market & Salary Insights Explorer")

# Get dynamic filter options from SQLite
filter_options = db.get_filter_options()

st.sidebar.markdown("### 🎛️ Market Filters")

selected_role = st.sidebar.selectbox(
    "Role Category",
    options=["All"] + filter_options["roles"],
    index=0
)

selected_exp = st.sidebar.selectbox(
    "Experience Level",
    options=["All"] + filter_options["experience_levels"],
    index=0
)

selected_remote = st.sidebar.selectbox(
    "Workplace Type",
    options=["All"] + filter_options["remote_types"],
    index=0
)

selected_skill_cat = st.sidebar.selectbox(
    "Skill Category",
    options=["All"] + filter_options["skill_categories"],
    index=0
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh / Re-seed Data (ETL)"):
    with st.spinner("Executing ETL pipeline & loading normalized tables..."):
        etl.run_etl()
    st.sidebar.success("Database successfully re-seeded!")
    st.rerun()

st.sidebar.markdown("""
**Database Details:**
- **Engine:** Python SQLite 3
- **Schema:** 3NF Normalized Relational
- **Live Feed:** Online Tech Job APIs
""")

# ----------------- MAIN CONTENT & METRIC CARDS -----------------
st.title("💼 SkillMetrics: Tech Job Market & Salary Insights")
st.markdown(
    "A clean data analytics dashboard powered by **Python, normalized SQLite tables, and live job feeds**. "
    "Executes SQL aggregations to benchmark salaries, discover in-demand skills, and directly fetch current job openings online."
)

# Fetch KPIs
kpi = db.get_summary_kpis(
    role=selected_role,
    exp_level=selected_exp,
    remote_type=selected_remote
)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total Postings</div>
        <div class="metric-value">{kpi['total_jobs']:,}</div>
        <div class="metric-sub">Normalized DB Records</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    avg_salary_val = f"${int(kpi['avg_salary']):,}" if kpi['avg_salary'] else "$0"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Average Salary</div>
        <div class="metric-value">{avg_salary_val}</div>
        <div class="metric-sub">Annual Base (USD)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Top In-Demand Skill</div>
        <div class="metric-value">{kpi['top_skill']}</div>
        <div class="metric-sub">{kpi['top_skill_count']} job mentions</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Avg Exp. Required</div>
        <div class="metric-value">{kpi['avg_years_exp'] or 0} yrs</div>
        <div class="metric-sub">Industry baseline</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Top Hiring Company</div>
        <div class="metric-value" style="font-size:1.2rem; margin-top:10px;">{kpi['top_company']}</div>
        <div class="metric-sub">Most active employer</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- DASHBOARD TABS -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💰 Salary Benchmarks",
    "🚀 In-Demand Technical Skills",
    "🎓 Role & Experience Requirements",
    "🔥 Live Job Openings & JD Matcher",
    "🔍 SQL Engine & Query Explorer"
])

# ----------------- TAB 1: SALARY BENCHMARKS -----------------
with tab1:
    st.subheader("Salary Benchmarks & Compensation Analysis")
    st.caption("Visualizing salary spreads across experience levels, tech specializations, and remote workplace formats.")

    c1, c2 = st.columns([1.1, 0.9])

    with c1:
        role_salaries, role_sql = db.get_salary_by_role(
            exp_level=selected_exp,
            remote_type=selected_remote
        )
        if role_salaries:
            df_role = pd.DataFrame(role_salaries)
            fig_role = px.bar(
                df_role,
                x="average_salary",
                y="role_category",
                orientation="h",
                color="average_salary",
                color_continuous_scale="Viridis",
                labels={"average_salary": "Average Salary (USD)", "role_category": "Role Category"},
                title="Average Salary by Role Category",
                text="average_salary"
            )
            fig_role.update_traces(texttemplate='$%{text:,.0f}', textposition='inside')
            fig_role.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=20, t=40, b=20))
            st.plotly_chart(fig_role, width="stretch")

    with c2:
        exp_salaries, exp_sql = db.get_salary_by_experience(
            role=selected_role,
            remote_type=selected_remote
        )
        if exp_salaries:
            df_exp = pd.DataFrame(exp_salaries)
            fig_exp = go.Figure()
            fig_exp.add_trace(go.Bar(
                name="Avg Minimum",
                x=df_exp["experience_level"],
                y=df_exp["avg_min_salary"],
                marker_color="#38bdf8"
            ))
            fig_exp.add_trace(go.Bar(
                name="Average Salary",
                x=df_exp["experience_level"],
                y=df_exp["average_salary"],
                marker_color="#6366f1"
            ))
            fig_exp.add_trace(go.Bar(
                name="Avg Maximum",
                x=df_exp["experience_level"],
                y=df_exp["avg_max_salary"],
                marker_color="#a855f7"
            ))
            fig_exp.update_layout(
                barmode='group',
                title="Salary Spread by Experience Level",
                yaxis_title="Salary (USD)",
                margin=dict(l=0, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_exp, width="stretch")

    st.markdown("#### Workplace Type Distribution & Pay Comparison")
    remote_data, remote_sql = db.get_remote_distribution(role=selected_role, exp_level=selected_exp)
    if remote_data:
        df_remote = pd.DataFrame(remote_data)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            fig_donut = px.pie(
                df_remote,
                names="remote_type",
                values="job_count",
                hole=0.45,
                title="Postings by Workplace Policy (Remote / Hybrid / On-site)",
                color_discrete_sequence=px.colors.sequential.Teal
            )
            st.plotly_chart(fig_donut, width="stretch")
        with col_r2:
            fig_rem_sal = px.bar(
                df_remote,
                x="remote_type",
                y="avg_salary",
                color="remote_type",
                text="avg_salary",
                title="Average Compensation by Workplace Policy",
                labels={"avg_salary": "Average Salary (USD)", "remote_type": "Workplace Format"}
            )
            fig_rem_sal.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_rem_sal, width="stretch")

    with st.expander("🔍 View Executed SQL Query for Salary Benchmarks"):
        st.code(role_sql, language="sql")

# ----------------- TAB 2: IN-DEMAND SKILLS -----------------
with tab2:
    st.subheader("In-Demand Technical Skills & Market Payoff")
    st.caption("Relational SQL multi-table JOINs between job postings, junction mapping, and normalized skills catalog.")

    skills_data, skills_sql = db.get_in_demand_skills(
        role=selected_role,
        exp_level=selected_exp,
        skill_category=selected_skill_cat,
        limit=16
    )

    if skills_data:
        df_skills = pd.DataFrame(skills_data)

        col_s1, col_s2 = st.columns([1, 1])

        with col_s1:
            fig_skill_count = px.bar(
                df_skills,
                x="demand_count",
                y="skill_name",
                orientation="h",
                color="skill_category",
                title="Top In-Demand Technical Skills (Frequency in Postings)",
                labels={"demand_count": "Number of Job Postings", "skill_name": "Skill Name"},
                text="demand_count"
            )
            fig_skill_count.update_traces(textposition='outside')
            fig_skill_count.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_skill_count, width="stretch")

        with col_s2:
            fig_skill_pay = px.scatter(
                df_skills,
                x="demand_count",
                y="avg_salary_with_skill",
                size="demand_count",
                color="skill_category",
                hover_name="skill_name",
                text="skill_name",
                title="Skill Demand vs Average Salary Correlation",
                labels={
                    "demand_count": "Job Postings Demand",
                    "avg_salary_with_skill": "Average Salary ($ USD)"
                }
            )
            fig_skill_pay.update_traces(textposition='top center')
            st.plotly_chart(fig_skill_pay, width="stretch")

        st.markdown("#### Detailed Skill Demand & Requirements Table")
        df_skills_display = df_skills.rename(columns={
            "skill_name": "Skill",
            "skill_category": "Category",
            "demand_count": "Job Postings Mentioning Skill",
            "strictly_required_count": "Must-Have Requirement",
            "avg_salary_with_skill": "Average Market Salary (USD)"
        })
        df_skills_display["Average Market Salary (USD)"] = df_skills_display["Average Market Salary (USD)"].apply(lambda x: f"${int(x):,}")
        st.dataframe(df_skills_display, width="stretch", hide_index=True)

    with st.expander("🔍 View Executed SQL Query for In-Demand Skills"):
        st.code(skills_sql, language="sql")

# ----------------- TAB 3: ROLE & EXPERIENCE REQUIREMENTS -----------------
with tab3:
    st.subheader("Role Requirements & Experience Matrix")
    st.caption("How education level and minimum years of experience factor into hiring qualifications across seniority levels.")

    req_data, req_sql = db.get_role_requirements_matrix(role=selected_role)
    if req_data:
        df_req = pd.DataFrame(req_data)

        col_req1, col_req2 = st.columns([1, 1])

        with col_req1:
            fig_edu = px.bar(
                df_req,
                x="experience_level",
                y="count",
                color="education_level",
                barmode="stack",
                title="Education Level Distribution by Seniority",
                labels={"count": "Postings Count", "experience_level": "Experience Level"}
            )
            st.plotly_chart(fig_edu, width="stretch")

        with col_req2:
            fig_exp_years = px.scatter(
                df_req,
                x="avg_years_exp",
                y="avg_salary",
                size="count",
                color="experience_level",
                hover_name="education_level",
                title="Minimum Years of Experience vs Average Salary",
                labels={"avg_years_exp": "Average Years Required", "avg_salary": "Average Salary ($ USD)"}
            )
            st.plotly_chart(fig_exp_years, width="stretch")

        st.markdown("#### Experience Level Matrix")
        st.dataframe(df_req, width="stretch", hide_index=True)

    with st.expander("🔍 View Executed SQL Query for Requirements Matrix"):
        st.code(req_sql, language="sql")

# ----------------- TAB 4: LIVE ONLINE JOB OPENINGS & JD MATCHER -----------------
with tab4:
    st.subheader("🔥 Live Online Job Openings & Candidate JD Matcher")
    st.markdown(
        f"Fetches real-time, currently open tech positions online matching **Role:** `{selected_role}` and **Experience:** `{selected_exp}`. "
        "Allows a candidate to directly check current vacancies, review JD requirements, and apply immediately."
    )

    # 1. Candidate JD Fit Skills Selector
    st.markdown("#### 🎯 Check Candidate Fit Against Live Job Openings")
    default_skills = ["Python", "SQL", "Docker", "AWS", "Git"]
    if selected_role == "Machine Learning Engineer":
        default_skills = ["Python", "PyTorch", "TensorFlow", "Docker", "AWS"]
    elif selected_role == "Frontend Engineer":
        default_skills = ["JavaScript", "TypeScript", "React", "Next.js", "Git"]
    elif selected_role == "DevOps / Cloud Engineer":
        default_skills = ["AWS", "Docker", "Kubernetes", "Terraform", "Linux"]
    elif selected_role == "Data Engineer":
        default_skills = ["Python", "SQL", "Spark", "AWS", "PostgreSQL"]

    candidate_skills = st.multiselect(
        "Select / customize candidate technical skills for JD match calculation:",
        options=["Python", "SQL", "Java", "Go", "JavaScript", "TypeScript", "React", "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform", "PostgreSQL", "Spark", "PyTorch", "Linux", "Git"],
        default=default_skills
    )

    # 2. Fetch Live Openings Button / Cache
    @st.cache_data(ttl=120)
    def fetch_cached_jobs(role, exp, skills_tuple):
        return job_fetcher.get_live_job_openings(role=role, exp_level=exp, target_skills=list(skills_tuple), limit=15)

    with st.spinner("Fetching live current openings online..."):
        live_jobs = fetch_cached_jobs(selected_role, selected_exp, tuple(candidate_skills))

    st.markdown(f"**Found {len(live_jobs)} Active Job Openings Online:**")

    if live_jobs:
        for job in live_jobs:
            fit_score = job.get("fit_score", 70)
            fit_label = "🌟 Excellent Match" if fit_score >= 85 else ("👍 Good Match" if fit_score >= 70 else "📝 Potential Fit")
            matched_pills = "".join([f'<span class="tag-pill tag-matched">✓ {m}</span>' for m in job.get("matched_skills", [])])
            other_tags = "".join([f'<span class="tag-pill">{t}</span>' for t in job.get("tags", [])[:5] if t not in job.get("matched_skills", [])])

            st.markdown(f"""
            <div class="job-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                    <div>
                        <div class="job-title">{job['title']}</div>
                        <div class="job-company">🏢 {job['company']} &nbsp;•&nbsp; 📍 {job['location']} &nbsp;•&nbsp; 💵 {job['salary']}</div>
                    </div>
                    <div style="margin-top: 4px;">
                        <span class="badge-fit">🎯 {fit_score}% Fit ({fit_label})</span>
                        <span class="badge-source">{job['source']}</span>
                    </div>
                </div>
                <div style="margin-top: 10px; color: #cbd5e1; font-size: 0.88rem; line-height: 1.4;">
                    <strong>JD Summary:</strong> {job['description'] or 'See full job description on site.'}
                </div>
                <div style="margin-top: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <div>
                        {matched_pills}
                        {other_tags}
                    </div>
                    <div>
                        <a href="{job['url']}" target="_blank" style="text-decoration: none;">
                            <button style="background-color: #38bdf8; color: #0f172a; border: none; font-weight: 700; padding: 7px 16px; border-radius: 6px; cursor: pointer;">
                                Apply / View Opening ↗
                            </button>
                        </a>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No live jobs found matching the exact filter at this moment. Use the 1-click search portals below.")

    # 3. Direct 1-Click Search Links on Major Platforms
    st.markdown("---")
    st.markdown("#### 🌐 1-Click Direct Search on Top Platforms")
    st.caption("Instantly open verified, live postings directly on top job sites filtered for your selected role and experience:")

    links = job_fetcher.get_direct_search_links(selected_role, selected_exp)
    btn_cols = st.columns(len(links))
    for col, (platform, url) in zip(btn_cols, links.items()):
        with col:
            st.link_button(f"🔎 {platform}", url, width="stretch")

# ----------------- TAB 5: SQL ENGINE & QUERY EXPLORER -----------------
with tab5:
    st.subheader("Interactive SQL Engine & Query Explorer")
    st.markdown("""
    Under the hood, SkillMetrics directly connects Python to a **normalized relational database**.
    
    ### Relational Schema (3NF):
    1. **`companies`**: `(id, name, industry, company_size, headquarters)`
    2. **`job_postings`**: `(id, company_id, title, role_category, experience_level, min_salary, max_salary, avg_salary, location, remote_type, min_years_exp, education_level)`
    3. **`skills`**: `(id, skill_name, category)`
    4. **`job_skills`**: Junction table `(job_id, skill_id, is_required)`
    """)

    st.markdown("#### Test Custom SQL Queries Live")
    default_query = """SELECT 
    jp.role_category,
    jp.experience_level,
    c.name as company_name,
    jp.location,
    jp.avg_salary
FROM job_postings jp
JOIN companies c ON jp.company_id = c.id
ORDER BY jp.avg_salary DESC
LIMIT 10;"""

    user_sql = st.text_area("Write SQL Query:", value=default_query, height=160)

    if st.button("▶️ Execute SQL Query"):
        cols, rows, error = db.execute_custom_sql(user_sql)
        if error:
            st.error(f"SQL Execution Error: {error}")
        else:
            if cols and rows:
                df_custom = pd.DataFrame(rows, columns=cols)
                st.success(f"Returned {len(rows)} rows successfully.")
                st.dataframe(df_custom, width="stretch")
            else:
                st.info("Query returned 0 rows.")

st.markdown("---")
st.caption("SkillMetrics Explorer • Pure Python, Normalized SQLite, Streamlit & Live Job Fetcher")
