"""
SkillMetrics - Live Job Fetcher Module
Fetches real, current job openings online for any selected role and experience level.
Uses Python's built-in urllib.request (100% simple, standard library, zero external dependencies).
"""

import urllib.request
import json
import urllib.parse
import re
from typing import List, Dict, Any, Tuple

# Mapping role categories to effective search keywords
ROLE_KEYWORDS = {
    "Software Engineer": ["software engineer", "developer", "backend", "full stack", "software developer", "engineer"],
    "Data Engineer": ["data engineer", "etl", "big data", "data platform", "analytics engineer", "pipeline", "spark", "sql"],
    "Machine Learning Engineer": ["machine learning", "ml engineer", "ai engineer", "applied ai", "data scientist", "deep learning", "llm"],
    "DevOps / Cloud Engineer": ["devops", "cloud engineer", "sre", "platform engineer", "infrastructure", "kubernetes", "aws"],
    "Frontend Engineer": ["frontend", "front end", "react", "vue", "ui developer", "javascript", "typescript", "web developer"],
    "Backend Engineer": ["backend", "back end", "python", "golang", "api engineer", "node", "java", "django", "fastapi"],
    "Cybersecurity Analyst": ["security", "cybersecurity", "infosec", "soc", "penetration testing", "threat", "vulnerability"],
    "Data Scientist": ["data scientist", "data science", "machine learning", "statistician", "analytics"]
}

EXP_KEYWORDS = {
    "Entry-level": ["junior", "jr", "entry", "associate", "intern", "graduate", "0-2"],
    "Mid-level": ["mid", "intermediate", "engineer", "developer", "2-5"],
    "Senior": ["senior", "sr", "lead", "staff", "principal", "5+"],
    "Lead / Staff": ["lead", "staff", "principal", "director", "head", "architect", "manager"]
}


def clean_html(raw_html: str) -> str:
    """Removes HTML tags from JD descriptions for clean preview."""
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', raw_html)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:280] + ("..." if len(clean) > 280 else "")


def fetch_from_remoteok() -> List[Dict[str, Any]]:
    """Fetches live tech jobs from RemoteOK public API."""
    jobs = []
    try:
        url = "https://remoteok.com/api"
        req = urllib.request.Request(url, headers={"User-Agent": "SkillMetrics-JobExplorer/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            # Skip the first element which is an API notice
            for item in data[1:]:
                position = item.get("position", "")
                tags = item.get("tags", [])
                company = item.get("company", "")
                link = item.get("url", "")
                description = item.get("description", "")
                
                min_sal = item.get("salary_min", 0)
                max_sal = item.get("salary_max", 0)
                salary_str = f"${min_sal:,} - ${max_sal:,} USD" if min_sal and max_sal else "Market Competitive"

                jobs.append({
                    "title": position,
                    "company": company,
                    "location": item.get("location") or "Remote",
                    "salary": salary_str,
                    "tags": [t for t in tags if isinstance(t, str)],
                    "url": link,
                    "description": clean_html(description),
                    "source": "RemoteOK"
                })
    except Exception as e:
        print(f"RemoteOK fetch notice: {e}")
    return jobs


def fetch_from_arbeitnow() -> List[Dict[str, Any]]:
    """Fetches live tech jobs from Arbeitnow public API."""
    jobs = []
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        req = urllib.request.Request(url, headers={"User-Agent": "SkillMetrics-JobExplorer/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            items = data.get("data", [])
            for item in items:
                title = item.get("title", "")
                company = item.get("company_name", "")
                link = item.get("url", "")
                loc = "Remote" if item.get("remote") else (item.get("location") or "Remote")
                description = item.get("description", "")
                tags = item.get("tags", [])

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": loc,
                    "salary": "Market Competitive",
                    "tags": [t for t in tags if isinstance(t, str)],
                    "url": link,
                    "description": clean_html(description),
                    "source": "Arbeitnow"
                })
    except Exception as e:
        print(f"Arbeitnow fetch notice: {e}")
    return jobs


def is_tech_job(job: Dict[str, Any]) -> bool:
    """Ensures the job is within the tech / engineering / data domain."""
    text = f"{job['title']} {' '.join(job.get('tags', []))}".lower()
    tech_indicators = [
        "engineer", "developer", "software", "data", "cloud", "devops", "frontend",
        "backend", "fullstack", "full stack", "python", "javascript", "golang",
        "react", "ai", "machine learning", "security", "analyst", "architect", "tech"
    ]
    return any(ind in text for ind in tech_indicators)


def matches_role_and_experience(job: Dict[str, Any], role: str, exp_level: str) -> bool:
    """Checks if a job matches the specific role category and experience seniority."""
    if not is_tech_job(job):
        return False

    title_lower = job["title"].lower()
    tags_lower = [t.lower() for t in job.get("tags", [])]
    desc_lower = job.get("description", "").lower()
    combined_text = f"{title_lower} {' '.join(tags_lower)} {desc_lower}"

    # 1. Role filter
    if role and role != "All":
        keywords = ROLE_KEYWORDS.get(role, [role.lower()])
        # Check title and tags first (high confidence)
        matches_title_or_tags = any(kw in title_lower or any(kw in t for t in tags_lower) for kw in keywords)
        matches_desc = any(kw in desc_lower for kw in keywords)
        if not (matches_title_or_tags or matches_desc):
            return False

    # 2. Experience filter
    if exp_level and exp_level != "All":
        if exp_level == "Entry-level":
            # Exclude explicit senior/lead in title unless entry keywords present
            has_junior = any(w in title_lower or w in desc_lower for w in ["junior", "jr", "entry", "associate", "intern", "graduate"])
            has_senior = any(w in title_lower for w in ["senior", "sr", "lead", "staff", "principal", "director", "head"])
            if has_senior and not has_junior:
                return False
        elif exp_level in ["Senior", "Lead / Staff"]:
            has_senior = any(w in combined_text for w in ["senior", "sr", "lead", "staff", "principal", "architect"])
            if not has_senior:
                return False

    return True


def evaluate_jd_fit(job: Dict[str, Any], target_skills: List[str]) -> Tuple[int, List[str]]:
    """Calculates JD match percentage and lists matched skills for the candidate."""
    if not target_skills:
        # Default skills baseline for general tech roles
        target_skills = ["Python", "SQL", "Git", "Docker", "API", "Cloud"]

    corpus = f"{job['title']} {' '.join(job.get('tags', []))} {job.get('description', '')}".lower()
    matched = [s for s in target_skills if s.lower() in corpus]

    # Calculate match percentage
    base = 60
    bonus = int((len(matched) / max(len(target_skills[:4]), 1)) * 40)
    score = min(100, base + bonus)
    return score, matched


def get_live_job_openings(role: str = "All", exp_level: str = "All", target_skills: List[str] = None, limit: int = 12) -> List[Dict[str, Any]]:
    """
    Fetches, filters, evaluates JD fit, and returns top active job openings online.
    """
    all_raw = []
    all_raw.extend(fetch_from_arbeitnow())
    all_raw.extend(fetch_from_remoteok())

    filtered = []
    for job in all_raw:
        if matches_role_and_experience(job, role, exp_level):
            score, matched = evaluate_jd_fit(job, target_skills or [])
            job["fit_score"] = score
            job["matched_skills"] = matched
            filtered.append(job)

    # Sort by fit score descending
    filtered.sort(key=lambda x: x["fit_score"], reverse=True)

    # Fallback to tech jobs if specific criteria returned very few
    if len(filtered) < 3:
        for job in all_raw:
            if is_tech_job(job) and job not in filtered:
                score, matched = evaluate_jd_fit(job, target_skills or [])
                job["fit_score"] = score
                job["matched_skills"] = matched
                filtered.append(job)
            if len(filtered) >= limit:
                break

    return filtered[:limit]


def get_direct_search_links(role: str, exp_level: str) -> Dict[str, str]:
    """Generates 1-click filtered search URLs for top job boards."""
    role_term = "" if role == "All" else role
    exp_term = "" if exp_level == "All" else exp_level
    query = f"{exp_term} {role_term} software engineer developer".strip()
    encoded = urllib.parse.quote_plus(query)

    return {
        "LinkedIn Jobs": f"https://www.linkedin.com/jobs/search/?keywords={encoded}&f_TPR=r604800",
        "Indeed": f"https://www.indeed.com/jobs?q={encoded}&fromage=7",
        "Google Jobs": f"https://www.google.com/search?q={encoded}+jobs+hiring",
        "Wellfound (AngelList)": f"https://wellfound.com/jobs?q={encoded}",
        "WeWorkRemotely": f"https://weworkremotely.com/remote-jobs/search?term={encoded}"
    }
