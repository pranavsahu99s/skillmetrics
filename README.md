# SkillMetrics: Tech Job Market & Salary Insights Explorer

**SkillMetrics** is an interactive, Python-powered data analytics web application that explores tech job market compensation, in-demand technical skills, and hiring requirements across seniority levels — with **real-time live online job fetching & candidate JD matching**.

---

## 💡 Project Analysis in Simpler Terms

### The Problem It Solves
When developers and data analysts look at the tech job market, they often wonder:
- *"What is the real market salary for a Machine Learning Engineer vs. a Backend Engineer?"*
- *"Does learning AWS or Kubernetes give me a measurable salary bump?"*
- *"How do requirements change as I advance from Entry-level to Senior or Lead?"*
- *"What real-world openings exist online right now for my role, and how well does my skill set fit the job description?"*

Instead of guessing or reading static blog posts, **SkillMetrics** turns job market postings into actionable, data-driven answers using clean SQL queries, and connects directly to live job feeds online.

### Core Components (Built as Simple as Possible)
1. **ETL Pipeline (`etl.py`)**:
   - Takes raw tech job postings and normalizes them into relational database tables (Third Normal Form - 3NF).
   - Eliminates duplicate company and skill names by creating clean junction tables.
2. **Direct Python Database Engine (`db.py`)**:
   - Uses Python's native `sqlite3` module (zero external database servers to configure or pay for).
   - Runs multi-table `JOIN`s, `GROUP BY` aggregations, and filtering queries with microsecond performance.
3. **Live Job Fetcher & JD Matcher (`job_fetcher.py`)**:
   - Uses Python's built-in `urllib.request` (zero complex scrapers/selenium/tokens).
   - Queries public online job feeds (RemoteOK & Arbeitnow) in real time.
   - Filters by selected **Role Category** and **Experience Seniority**.
   - Computes candidate **JD Fit Score (%)** against required technical skills.
   - Provides direct **1-click apply links** + pre-filtered links to **LinkedIn Jobs**, **Indeed**, **Google Jobs**, **Wellfound**, and **WeWorkRemotely**.
4. **Interactive Dashboards**:
   - **Streamlit Dashboard (`app.py`)**: Full-featured interactive analytics dashboard with Plotly charts, KPI metrics, dynamic filters, candidate skill customization, and live SQL Query Inspector.
   - **Standalone Web Server (`server.py`)**: Ultra-lightweight native Python web server with Chart.js, running with zero external dependencies.

---

## 🗄️ Normalized Database Schema (SQLite)

The database schema is structured into 4 normalized relational tables:

```
[companies] (1) <────── (N) [job_postings] (N) <─── (1) [job_skills] (N) ───> (1) [skills]
```

1. **`companies`**: Stores unique employers (`id`, `name`, `industry`, `company_size`, `headquarters`).
2. **`job_postings`**: Stores core job openings (`id`, `company_id`, `title`, `role_category`, `experience_level`, `min_salary`, `max_salary`, `avg_salary`, `location`, `remote_type`, `posted_date`, `min_years_exp`, `education_level`).
3. **`skills`**: Catalog of standardized technical skills (`id`, `skill_name`, `category`).
4. **`job_skills`**: Junction table mapping many-to-many relationships (`job_id`, `skill_id`, `is_required`).

---

## ⚡ Direct SQL Joins & Aggregations Executed in Python

### 1. In-Demand Skills & Salary Correlation
```sql
SELECT 
    s.skill_name,
    s.category,
    COUNT(js.job_id) AS demand_count,
    ROUND(AVG(jp.avg_salary), 0) AS avg_salary_with_skill
FROM job_skills js
JOIN skills s ON js.skill_id = s.id
JOIN job_postings jp ON js.job_id = jp.id
GROUP BY s.id, s.skill_name
ORDER BY demand_count DESC
LIMIT 15;
```

### 2. Salary Spread by Experience Level
```sql
SELECT 
    experience_level,
    COUNT(*) AS job_count,
    ROUND(AVG(min_salary), 0) AS avg_min,
    ROUND(AVG(avg_salary), 0) AS average_salary,
    ROUND(AVG(max_salary), 0) AS avg_max
FROM job_postings
GROUP BY experience_level
ORDER BY avg_req_years ASC;
```

---

## 🚀 How to Run the Project

### Environment Setup (Single Shared Virtual Environment via `uv`)
The project utilizes `uv` to manage all Python packages in a single virtual environment:

```bash
# 1. Initialize and install dependencies using uv
uv venv
uv pip install streamlit pandas plotly

# 2. Run ETL pipeline (Cleans and loads 1,200+ normalized records into skillmetrics.db)
uv run python etl.py
```

### Option A: Run the Interactive Streamlit Dashboard
```bash
uv run streamlit run app.py
```
*Access in browser at:* `http://localhost:8501`
*Navigate to the **🔥 Live Job Openings & JD Matcher** tab to see real-time current openings.*

### Option B: Run the Lightweight Native Python Server (Zero External Setup)
```bash
python3 server.py
```
*Access in browser at:* `http://localhost:8050`
*Click on the **🔥 Live Openings & JD Matcher** tab for current vacancies.*

---

## 📁 Project Directory Structure
```
pythonProject/
├── app.py           # Streamlit interactive dashboard (Plotly, Filters, Live Openings, JD Matcher)
├── server.py        # Standalone Python HTTP web server & Chart.js dashboard
├── db.py            # Direct SQL query execution layer (SQLite + Python)
├── etl.py           # Data generation, cleaning, and 3NF normalization pipeline
├── job_fetcher.py   # Live online job fetcher & candidate JD fit evaluator (pure Python)
├── skillmetrics.db  # Normalized SQLite database file
├── README.md        # Architecture & documentation
└── .venv/           # Unified virtual environment managed with uv
```
