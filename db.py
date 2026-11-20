"""
SkillMetrics - Database Access & SQL Analytics Engine
Executes SQL joins, aggregations, and window-like queries directly on the SQLite database.
"""

import sqlite3
import os
from typing import Dict, Any, List, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "skillmetrics.db")


def get_connection():
    """Returns a SQLite connection with row dictionary factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_filter_options():
    """Retrieves dynamic filter lists for UI dropdowns."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT role_category FROM job_postings ORDER BY role_category ASC")
        roles = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT experience_level FROM job_postings ORDER BY min_years_exp ASC")
        exp_levels = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT remote_type FROM job_postings ORDER BY remote_type ASC")
        remote_types = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT category FROM skills ORDER BY category ASC")
        skill_categories = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT MIN(min_salary), MAX(max_salary) FROM job_postings")
        min_sal, max_sal = cursor.fetchone()

        return {
            "roles": roles,
            "experience_levels": exp_levels,
            "remote_types": remote_types,
            "skill_categories": skill_categories,
            "salary_range": (int(min_sal or 50000), int(max_sal or 300000))
        }


def get_summary_kpis(role=None, exp_level=None, remote_type=None) -> Dict[str, Any]:
    """Computes headline KPIs (total postings, median/avg salary, top hiring company, top skill)."""
    where_clauses = []
    params = []

    if role and role != "All":
        where_clauses.append("jp.role_category = ?")
        params.append(role)
    if exp_level and exp_level != "All":
        where_clauses.append("jp.experience_level = ?")
        params.append(exp_level)
    if remote_type and remote_type != "All":
        where_clauses.append("jp.remote_type = ?")
        params.append(remote_type)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with get_connection() as conn:
        cursor = conn.cursor()

        # Job Count & Salary stats
        query = f"""
            SELECT 
                COUNT(*) as total_jobs,
                ROUND(AVG(avg_salary), 0) as avg_salary,
                MIN(min_salary) as min_salary,
                MAX(max_salary) as max_salary,
                ROUND(AVG(min_years_exp), 1) as avg_years_exp
            FROM job_postings jp
            {where_sql}
        """
        cursor.execute(query, params)
        kpi_row = dict(cursor.fetchone())

        # Top Skill (SQL JOIN)
        skill_query = f"""
            SELECT s.skill_name, COUNT(*) as skill_count
            FROM job_skills js
            JOIN skills s ON js.skill_id = s.id
            JOIN job_postings jp ON js.job_id = jp.id
            {where_sql}
            GROUP BY s.skill_name
            ORDER BY skill_count DESC
            LIMIT 1
        """
        cursor.execute(skill_query, params)
        top_skill_row = cursor.fetchone()
        kpi_row["top_skill"] = top_skill_row["skill_name"] if top_skill_row else "N/A"
        kpi_row["top_skill_count"] = top_skill_row["skill_count"] if top_skill_row else 0

        # Top Hiring Company (SQL JOIN)
        comp_query = f"""
            SELECT c.name, COUNT(*) as post_count
            FROM job_postings jp
            JOIN companies c ON jp.company_id = c.id
            {where_sql}
            GROUP BY c.name
            ORDER BY post_count DESC
            LIMIT 1
        """
        cursor.execute(comp_query, params)
        top_comp_row = cursor.fetchone()
        kpi_row["top_company"] = top_comp_row["name"] if top_comp_row else "N/A"

        return kpi_row


def get_salary_by_experience(role=None, remote_type=None) -> Tuple[List[Dict[str, Any]], str]:
    """SQL aggregation: average, min, and max salary grouped by experience level."""
    where_clauses = []
    params = []

    if role and role != "All":
        where_clauses.append("role_category = ?")
        params.append(role)
    if remote_type and remote_type != "All":
        where_clauses.append("remote_type = ?")
        params.append(remote_type)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    sql_query = f"""
    SELECT 
        experience_level,
        COUNT(*) as job_count,
        ROUND(AVG(min_salary), 0) as avg_min_salary,
        ROUND(AVG(avg_salary), 0) as average_salary,
        ROUND(AVG(max_salary), 0) as avg_max_salary,
        ROUND(AVG(min_years_exp), 1) as avg_req_years
    FROM job_postings
    {where_sql}
    GROUP BY experience_level
    ORDER BY avg_req_years ASC
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql_query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        return rows, sql_query.strip()


def get_salary_by_role(exp_level=None, remote_type=None) -> Tuple[List[Dict[str, Any]], str]:
    """SQL aggregation: benchmark salary by role category."""
    where_clauses = []
    params = []

    if exp_level and exp_level != "All":
        where_clauses.append("experience_level = ?")
        params.append(exp_level)
    if remote_type and remote_type != "All":
        where_clauses.append("remote_type = ?")
        params.append(remote_type)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    sql_query = f"""
    SELECT 
        role_category,
        COUNT(*) as total_postings,
        ROUND(AVG(min_salary), 0) as avg_min_salary,
        ROUND(AVG(avg_salary), 0) as average_salary,
        ROUND(AVG(max_salary), 0) as avg_max_salary,
        MIN(min_salary) as lowest_salary,
        MAX(max_salary) as highest_salary
    FROM job_postings
    {where_sql}
    GROUP BY role_category
    ORDER BY average_salary DESC
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql_query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        return rows, sql_query.strip()


def get_in_demand_skills(role=None, exp_level=None, skill_category=None, limit=15) -> Tuple[List[Dict[str, Any]], str]:
    """SQL multi-table JOIN: in-demand technical skills & average salary payoff."""
    where_clauses = []
    params = []

    if role and role != "All":
        where_clauses.append("jp.role_category = ?")
        params.append(role)
    if exp_level and exp_level != "All":
        where_clauses.append("jp.experience_level = ?")
        params.append(exp_level)
    if skill_category and skill_category != "All":
        where_clauses.append("s.category = ?")
        params.append(skill_category)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    sql_query = f"""
    SELECT 
        s.skill_name,
        s.category as skill_category,
        COUNT(js.job_id) as demand_count,
        ROUND(AVG(jp.avg_salary), 0) as avg_salary_with_skill,
        SUM(CASE WHEN js.is_required = 1 THEN 1 ELSE 0 END) as strictly_required_count
    FROM job_skills js
    JOIN skills s ON js.skill_id = s.id
    JOIN job_postings jp ON js.job_id = jp.id
    {where_sql}
    GROUP BY s.id, s.skill_name, s.category
    ORDER BY demand_count DESC, avg_salary_with_skill DESC
    LIMIT {limit}
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql_query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        return rows, sql_query.strip()


def get_role_requirements_matrix(role=None) -> Tuple[List[Dict[str, Any]], str]:
    """SQL aggregation: education & experience requirements across experience levels."""
    where_sql = "WHERE role_category = ?" if (role and role != "All") else ""
    params = [role] if (role and role != "All") else []

    sql_query = f"""
    SELECT 
        experience_level,
        education_level,
        COUNT(*) as count,
        ROUND(AVG(min_years_exp), 1) as avg_years_exp,
        ROUND(AVG(avg_salary), 0) as avg_salary
    FROM job_postings
    {where_sql}
    GROUP BY experience_level, education_level
    ORDER BY avg_years_exp ASC, count DESC
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql_query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        return rows, sql_query.strip()


def get_remote_distribution(role=None, exp_level=None) -> Tuple[List[Dict[str, Any]], str]:
    """SQL aggregation: remote vs hybrid vs on-site breakdown."""
    where_clauses = []
    params = []
    if role and role != "All":
        where_clauses.append("role_category = ?")
        params.append(role)
    if exp_level and exp_level != "All":
        where_clauses.append("experience_level = ?")
        params.append(exp_level)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    sql_query = f"""
    SELECT 
        remote_type,
        COUNT(*) as job_count,
        ROUND(AVG(avg_salary), 0) as avg_salary
    FROM job_postings
    {where_sql}
    GROUP BY remote_type
    ORDER BY job_count DESC
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql_query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        return rows, sql_query.strip()


def execute_custom_sql(sql_query: str) -> Tuple[List[str], List[List[Any]], str]:
    """Executes a custom user-defined SELECT query safely."""
    clean_query = sql_query.strip()
    if not clean_query.lower().startswith("select"):
        return [], [], "Only SELECT queries are allowed for data exploration."

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(clean_query)
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            row_data = [list(r) for r in rows[:100]]  # Limit 100 rows for display safety
            return col_names, row_data, ""
    except Exception as e:
        return [], [], str(e)
