"""
SkillMetrics - ETL Pipeline: Data Cleaning, Normalization & Loading
Generates/cleans tech job market records and loads them into a normalized SQLite database.
Schema:
  1. companies (id, name, industry, company_size, headquarters)
  2. job_postings (id, company_id, title, role_category, experience_level, min_salary, max_salary, avg_salary, currency, location, remote_type, posted_date, min_years_exp, education_level)
  3. skills (id, skill_name, category)
  4. job_skills (job_id, skill_id, is_required)
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "skillmetrics.db")

COMPANIES_DATA = [
    ("CloudScale Tech", "Cloud Computing", "1000-5000", "San Francisco, CA"),
    ("DataFlow Labs", "Artificial Intelligence", "200-500", "New York, NY"),
    ("Apex Fintech Systems", "Financial Tech", "500-1000", "Chicago, IL"),
    ("CyberShield Global", "Cybersecurity", "1000-5000", "Austin, TX"),
    ("HealthBridge AI", "Healthcare Tech", "50-200", "Boston, MA"),
    ("NextWave Mobile", "Consumer Tech", "50-200", "Seattle, WA"),
    ("Hyperion Robotics", "Robotics & IoT", "500-1000", "San Jose, CA"),
    ("QuantumCore Networks", "Enterprise Software", "5000+", "Denver, CO"),
    ("OmniRetail Digital", "E-Commerce", "5000+", "Atlanta, GA"),
    ("GreenGrid Technologies", "CleanTech", "50-200", "Portland, OR"),
    ("Starlight Media Tech", "Media & Entertainment", "200-500", "Los Angeles, CA"),
    ("Vanguard Crypto Labs", "Blockchain / Web3", "50-200", "Miami, FL"),
    ("InsightEdge Analytics", "Big Data", "200-500", "Dallas, TX"),
    ("Synapse NeuroTech", "AI Research", "50-200", "San Diego, CA"),
    ("Horizon Aerospace Software", "Aerospace & Defense", "5000+", "Washington, DC"),
]

SKILLS_BY_CATEGORY = {
    "Languages": ["Python", "JavaScript", "TypeScript", "Java", "Go", "C++", "Rust", "SQL", "C#", "Kotlin", "Swift"],
    "Frameworks & Web": ["React", "Node.js", "Django", "FastAPI", "Next.js", "Vue.js", "Flask", "Spring Boot", "Express.js", "Angular"],
    "Cloud & DevOps": ["AWS", "Docker", "Kubernetes", "Azure", "GCP", "Terraform", "CI/CD", "Linux", "Ansible", "GitLab CI"],
    "Databases & Storage": ["PostgreSQL", "MongoDB", "Redis", "MySQL", "Snowflake", "Elasticsearch", "DynamoDB", "Kafka"],
    "Data Science & AI": ["PyTorch", "TensorFlow", "Pandas", "Scikit-Learn", "LLMs & GenAI", "Spark", "Hugging Face", "LangChain", "Computer Vision"],
    "Security & Systems": ["Network Security", "Cryptography", "Penetration Testing", "OAuth/SAML", "SIEM", "Zero Trust Architecture"]
}

ROLES_CATALOG = {
    "Software Engineer": {
        "titles": ["Software Engineer", "Backend Software Engineer", "Full Stack Software Engineer", "Software Systems Engineer"],
        "base_salary_range": (85000, 160000),
        "primary_skills": ["Python", "Java", "JavaScript", "SQL", "Docker", "GitLab CI", "PostgreSQL", "React", "Linux"],
    },
    "Data Engineer": {
        "titles": ["Data Engineer", "Senior Data Platform Engineer", "Big Data Pipeline Engineer", "Analytics Engineer"],
        "base_salary_range": (95000, 175000),
        "primary_skills": ["Python", "SQL", "Spark", "Kafka", "PostgreSQL", "Snowflake", "AWS", "Docker", "Terraform"],
    },
    "Machine Learning Engineer": {
        "titles": ["Machine Learning Engineer", "AI/ML Systems Engineer", "Applied AI Scientist", "LLM Engineer"],
        "base_salary_range": (115000, 210000),
        "primary_skills": ["Python", "PyTorch", "TensorFlow", "Scikit-Learn", "Docker", "LLMs & GenAI", "AWS", "FastAPI", "SQL"],
    },
    "DevOps / Cloud Engineer": {
        "titles": ["DevOps Engineer", "Cloud Infrastructure Engineer", "Site Reliability Engineer (SRE)", "Platform Engineer"],
        "base_salary_range": (100000, 180000),
        "primary_skills": ["AWS", "Docker", "Kubernetes", "Terraform", "Linux", "CI/CD", "Go", "Python", "Ansible"],
    },
    "Frontend Engineer": {
        "titles": ["Frontend Developer", "UI/UX Frontend Engineer", "Senior React Engineer", "Web Applications Engineer"],
        "base_salary_range": (80000, 150000),
        "primary_skills": ["JavaScript", "TypeScript", "React", "Next.js", "Vue.js", "HTML5/CSS3", "Node.js", "GitLab CI"],
    },
    "Backend Engineer": {
        "titles": ["Backend Developer", "API & Microservices Engineer", "Distributed Systems Engineer", "Core Backend Architect"],
        "base_salary_range": (90000, 165000),
        "primary_skills": ["Go", "Python", "Java", "FastAPI", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS"],
    },
    "Cybersecurity Analyst": {
        "titles": ["Cybersecurity Analyst", "Security Engineer", "InfoSec Specialist", "SOC Detection Engineer"],
        "base_salary_range": (85000, 155000),
        "primary_skills": ["Network Security", "Linux", "Python", "SIEM", "Penetration Testing", "OAuth/SAML", "AWS", "Cryptography"],
    },
    "Data Scientist": {
        "titles": ["Data Scientist", "Decision Scientist", "Quantitative Research Analyst", "Statistical Modeler"],
        "base_salary_range": (95000, 170000),
        "primary_skills": ["Python", "SQL", "Pandas", "Scikit-Learn", "Statistics", "PyTorch", "Snowflake", "Tableau"],
    }
}

EXPERIENCE_LEVELS = [
    ("Entry-level", 0.75, (0, 2), "Bachelor's Degree", 0.20),
    ("Mid-level", 1.00, (2, 5), "Bachelor's Degree", 0.45),
    ("Senior", 1.35, (5, 8), "Bachelor's / Master's", 0.25),
    ("Lead / Staff", 1.65, (8, 12), "Master's or equivalent experience", 0.10)
]

LOCATIONS = [
    ("San Francisco, CA", 1.25),
    ("New York, NY", 1.20),
    ("Seattle, WA", 1.15),
    ("Austin, TX", 1.05),
    ("Boston, MA", 1.10),
    ("Chicago, IL", 1.00),
    ("Denver, CO", 0.98),
    ("Remote - US", 1.05),
    ("Remote - Global", 0.95),
]

REMOTE_TYPES = ["Remote", "Hybrid", "On-site"]


def init_database(conn):
    """Creates the normalized schema tables in SQLite."""
    cursor = conn.cursor()
    
    # 1. Companies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        industry TEXT NOT NULL,
        company_size TEXT NOT NULL,
        headquarters TEXT NOT NULL
    )
    """)

    # 2. Skills Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL
    )
    """)

    # 3. Job Postings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_postings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        role_category TEXT NOT NULL,
        experience_level TEXT NOT NULL,
        min_salary INTEGER NOT NULL,
        max_salary INTEGER NOT NULL,
        avg_salary INTEGER NOT NULL,
        currency TEXT DEFAULT 'USD',
        location TEXT NOT NULL,
        remote_type TEXT NOT NULL,
        posted_date TEXT NOT NULL,
        min_years_exp INTEGER NOT NULL,
        education_level TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    )
    """)

    # 4. Job Skills Junction Table (Many-to-Many normalized relationship)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_skills (
        job_id INTEGER NOT NULL,
        skill_id INTEGER NOT NULL,
        is_required INTEGER DEFAULT 1,
        PRIMARY KEY (job_id, skill_id),
        FOREIGN KEY (job_id) REFERENCES job_postings(id) ON DELETE CASCADE,
        FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
    )
    """)

    # Create Indexes for fast querying & joins
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_role ON job_postings(role_category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_exp ON job_postings(experience_level);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON job_postings(company_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_skills_job ON job_skills(job_id);")
    conn.commit()


def seed_data(conn, num_jobs=1200):
    """Generates and normalizes realistic tech market data."""
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM job_skills")
    cursor.execute("DELETE FROM job_postings")
    cursor.execute("DELETE FROM skills")
    cursor.execute("DELETE FROM companies")

    # Seed Companies
    company_ids = []
    for name, ind, size, hq in COMPANIES_DATA:
        cursor.execute(
            "INSERT INTO companies (name, industry, company_size, headquarters) VALUES (?, ?, ?, ?)",
            (name, ind, size, hq)
        )
        company_ids.append(cursor.lastrowid)

    # Seed Skills
    skill_name_to_id = {}
    for cat, skills_list in SKILLS_BY_CATEGORY.items():
        for skill in skills_list:
            cursor.execute(
                "INSERT INTO skills (skill_name, category) VALUES (?, ?)",
                (skill, cat)
            )
            skill_name_to_id[skill] = cursor.lastrowid

    # Seed Job Postings and Job_Skills junction
    base_date = datetime.now()
    exp_weights = [exp[4] for exp in EXPERIENCE_LEVELS]

    for i in range(num_jobs):
        company_id = random.choice(company_ids)
        role_category = random.choice(list(ROLES_CATALOG.keys()))
        role_info = ROLES_CATALOG[role_category]

        title = random.choice(role_info["titles"])
        exp_choice = random.choices(EXPERIENCE_LEVELS, weights=exp_weights, k=1)[0]
        exp_name, exp_multiplier, exp_years_range, edu_level, _ = exp_choice
        
        years_exp = random.randint(exp_years_range[0], exp_years_range[1])
        location, loc_multiplier = random.choice(LOCATIONS)
        remote_type = random.choices(REMOTE_TYPES, weights=[0.45, 0.35, 0.20], k=1)[0]
        if "Remote" in location:
            remote_type = "Remote"

        # Calculate normalized salary
        min_base, max_base = role_info["base_salary_range"]
        # Add slight random market variance (+/- 10%)
        variance = random.uniform(0.92, 1.08)
        min_sal = int(min_base * exp_multiplier * loc_multiplier * variance / 1000) * 1000
        max_sal = int(max_base * exp_multiplier * loc_multiplier * variance / 1000) * 1000
        # Ensure minimum salary spread
        if max_sal <= min_sal:
            max_sal = min_sal + 15000
        avg_sal = int((min_sal + max_sal) / 2)

        days_ago = random.randint(0, 90)
        posted_date = (base_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO job_postings 
            (company_id, title, role_category, experience_level, min_salary, max_salary, avg_salary, 
             currency, location, remote_type, posted_date, min_years_exp, education_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_id, title, role_category, exp_name, min_sal, max_sal, avg_sal,
            "USD", location, remote_type, posted_date, years_exp, edu_level
        ))
        job_id = cursor.lastrowid

        # Associate Skills for this Job
        # Choose 3-6 primary skills for this role, plus 1-3 general skills
        primary_pool = [s for s in role_info["primary_skills"] if s in skill_name_to_id]
        num_primary = min(len(primary_pool), random.randint(3, 5))
        selected_skills = random.sample(primary_pool, num_primary)

        all_skills_pool = list(skill_name_to_id.keys())
        extra_skills = random.sample([s for s in all_skills_pool if s not in selected_skills], random.randint(1, 3))
        
        for idx, skill in enumerate(selected_skills + extra_skills):
            is_req = 1 if idx < num_primary else 0
            cursor.execute(
                "INSERT OR IGNORE INTO job_skills (job_id, skill_id, is_required) VALUES (?, ?, ?)",
                (job_id, skill_name_to_id[skill], is_req)
            )

    conn.commit()
    print(f"ETL completed successfully! Loaded {num_jobs} normalized job postings across {len(company_ids)} companies and {len(skill_name_to_id)} skills.")


def run_etl():
    """Initializes the database schema and loads clean normalized datasets."""
    conn = sqlite3.connect(DB_PATH)
    init_database(conn)
    seed_data(conn, num_jobs=1200)
    conn.close()


if __name__ == "__main__":
    run_etl()
