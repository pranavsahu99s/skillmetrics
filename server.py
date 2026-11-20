"""
SkillMetrics - Lightweight Standalone Python Web Dashboard Server
Runs with 100% standard Python 3 (zero external dependencies required!).
Provides JSON REST APIs and serves an interactive dashboard with Chart.js and Live Job Openings.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import db
import job_fetcher

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkillMetrics: Tech Job Market & Salary Insights</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --accent-purple: #818cf8;
            --border: #334155;
            --success: #34d399;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
        body { background-color: var(--bg-primary); color: var(--text-primary); display: flex; min-height: 100vh; }
        
        /* Sidebar */
        aside {
            width: 280px;
            background-color: var(--bg-secondary);
            border-right: 1px solid var(--border);
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .logo { font-size: 1.4rem; font-weight: 700; color: var(--accent); display: flex; align-items: center; gap: 10px; }
        .filter-group { display: flex; flex-direction: column; gap: 8px; }
        label { font-size: 0.85rem; color: var(--text-secondary); font-weight: 600; text-transform: uppercase; }
        select {
            background-color: #0f172a;
            color: var(--text-primary);
            border: 1px solid var(--border);
            padding: 10px 12px;
            border-radius: 8px;
            font-size: 0.9rem;
            outline: none;
        }
        select:focus { border-color: var(--accent); }

        /* Main Content */
        main { flex: 1; padding: 32px; overflow-y: auto; }
        header { margin-bottom: 24px; }
        header h1 { font-size: 2rem; font-weight: 800; margin-bottom: 6px; }
        header p { color: var(--text-secondary); font-size: 1rem; max-width: 800px; line-height: 1.5; }

        /* KPI Cards */
        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 28px; }
        .kpi-card {
            background: linear-gradient(145deg, #1e293b, #172033);
            border: 1px solid var(--border);
            padding: 20px;
            border-radius: 12px;
        }
        .kpi-title { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; }
        .kpi-value { font-size: 1.8rem; font-weight: 800; color: var(--accent); margin-top: 6px; }
        .kpi-sub { font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; }

        /* Nav Tabs */
        .tabs { display: flex; gap: 12px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }
        .tab-btn {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1rem;
            font-weight: 600;
            padding: 12px 16px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
        }
        .tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }

        /* Charts */
        .chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
        .chart-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            padding: 20px;
            border-radius: 12px;
        }
        .chart-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 16px; color: var(--text-primary); }
        .chart-container { position: relative; height: 320px; width: 100%; }

        /* Live Job Cards */
        .job-card {
            background-color: #1e293b;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 16px;
        }
        .job-card:hover { border-color: var(--accent); }
        .job-title { font-size: 1.15rem; font-weight: 700; color: var(--text-primary); }
        .job-company { color: var(--accent); font-weight: 600; font-size: 0.9rem; margin-top: 4px; }
        .badge-fit {
            background-color: #065f46;
            color: #34d399;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
        }
        .tag-pill {
            display: inline-block;
            background-color: #0f172a;
            color: #94a3b8;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 2px 10px;
            font-size: 0.75rem;
            margin-right: 6px;
            margin-top: 6px;
        }
        .tag-matched {
            background-color: #1e3a5f;
            color: var(--accent);
            border-color: var(--accent);
            font-weight: 600;
        }
        .btn-apply {
            background-color: var(--accent);
            color: #0f172a;
            font-weight: 700;
            padding: 6px 14px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.85rem;
            display: inline-block;
        }
        .portal-btn {
            background-color: #0f172a;
            color: var(--accent);
            border: 1px solid var(--border);
            padding: 8px 14px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
            margin-right: 8px;
            margin-top: 8px;
        }
        .portal-btn:hover { border-color: var(--accent); }

        /* SQL Explorer */
        textarea {
            width: 100%;
            height: 120px;
            background-color: #0f172a;
            color: #38bdf8;
            font-family: monospace;
            padding: 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 12px;
            resize: vertical;
        }
        button.btn-primary {
            background-color: var(--accent);
            color: #0f172a;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 700;
            cursor: pointer;
        }
        table { width: 100%; border-collapse: collapse; margin-top: 16px; }
        th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); font-size: 0.9rem; }
        th { background-color: #172033; color: var(--text-secondary); }
    </style>
</head>
<body>
    <aside>
        <div class="logo">💼 SkillMetrics</div>
        <p style="font-size: 0.85rem; color: var(--text-secondary);">Direct SQLite Analytics & Salary Explorer</p>
        
        <div class="filter-group">
            <label for="roleFilter">Role Category</label>
            <select id="roleFilter" onchange="loadDashboard()">
                <option value="All">All Roles</option>
            </select>
        </div>

        <div class="filter-group">
            <label for="expFilter">Experience Level</label>
            <select id="expFilter" onchange="loadDashboard()">
                <option value="All">All Levels</option>
            </select>
        </div>

        <div class="filter-group">
            <label for="remoteFilter">Workplace Policy</label>
            <select id="remoteFilter" onchange="loadDashboard()">
                <option value="All">All Workplaces</option>
            </select>
        </div>

        <div style="margin-top: auto; font-size: 0.8rem; color: var(--text-secondary);">
            ⚡ Powered by Pure Python & SQLite Normalization
        </div>
    </aside>

    <main>
        <header>
            <h1>Tech Job Market & Salary Insights Explorer</h1>
            <p>Analyzes tech job postings cleaned and normalized into SQLite tables. Real-time SQL aggregations uncover salary benchmarks, high-paying skills, and live online job openings.</p>
        </header>

        <!-- KPI Cards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-title">Total Postings</div>
                <div class="kpi-value" id="kpi-jobs">-</div>
                <div class="kpi-sub">Normalized DB Records</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Average Salary</div>
                <div class="kpi-value" id="kpi-salary">-</div>
                <div class="kpi-sub">Annual Base USD</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Top In-Demand Skill</div>
                <div class="kpi-value" id="kpi-skill">-</div>
                <div class="kpi-sub" id="kpi-skill-count">0 mentions</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Avg Years Experience</div>
                <div class="kpi-value" id="kpi-exp">-</div>
                <div class="kpi-sub">Industry requirement</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Top Hiring Company</div>
                <div class="kpi-value" style="font-size: 1.3rem;" id="kpi-company">-</div>
                <div class="kpi-sub">Most active openings</div>
            </div>
        </div>

        <!-- Tabs -->
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('tab-benchmarks')">💰 Salary Benchmarks</button>
            <button class="tab-btn" onclick="switchTab('tab-skills')">🚀 In-Demand Skills</button>
            <button class="tab-btn" onclick="switchTab('tab-livejobs')">🔥 Live Openings & JD Matcher</button>
            <button class="tab-btn" onclick="switchTab('tab-sql')">🔍 SQL Query Engine</button>
        </div>

        <!-- Tab 1: Salary Benchmarks -->
        <div id="tab-benchmarks">
            <div class="chart-row">
                <div class="chart-card">
                    <div class="chart-title">Average Salary by Tech Role Category</div>
                    <div class="chart-container"><canvas id="chartRoleSalary"></canvas></div>
                </div>
                <div class="chart-card">
                    <div class="chart-title">Salary Progression Across Experience Levels</div>
                    <div class="chart-container"><canvas id="chartExpSalary"></canvas></div>
                </div>
            </div>
            <div class="chart-row">
                <div class="chart-card">
                    <div class="chart-title">Workplace Distribution (Remote vs Hybrid vs On-site)</div>
                    <div class="chart-container"><canvas id="chartRemoteDist"></canvas></div>
                </div>
                <div class="chart-card">
                    <div class="chart-title">Average Salary by Workplace Policy</div>
                    <div class="chart-container"><canvas id="chartRemoteSalary"></canvas></div>
                </div>
            </div>
        </div>

        <!-- Tab 2: Skills -->
        <div id="tab-skills" style="display:none;">
            <div class="chart-row">
                <div class="chart-card">
                    <div class="chart-title">Top 12 Most Demanded Technical Skills</div>
                    <div class="chart-container"><canvas id="chartTopSkills"></canvas></div>
                </div>
                <div class="chart-card">
                    <div class="chart-title">Average Salary Payoff per Skill</div>
                    <div class="chart-container"><canvas id="chartSkillSalary"></canvas></div>
                </div>
            </div>
        </div>

        <!-- Tab 3: Live Jobs -->
        <div id="tab-livejobs" style="display:none;">
            <div class="chart-card" style="margin-bottom: 20px;">
                <div class="chart-title">🎯 Live Current Openings Online</div>
                <p style="color: var(--text-secondary); margin-bottom: 12px; font-size: 0.9rem;">
                    Active tech positions fetched online directly from public job boards for your selected role and experience. Check requirements, JD fit, and apply directly.
                </p>
                <div id="portalLinks" style="margin-bottom: 16px;"></div>
                <div id="liveJobsList">
                    <p style="color: var(--text-secondary);">Loading live job postings...</p>
                </div>
            </div>
        </div>

        <!-- Tab 4: SQL Explorer -->
        <div id="tab-sql" style="display:none;">
            <div class="chart-card">
                <div class="chart-title">Live SQLite Query Explorer</div>
                <p style="color: var(--text-secondary); margin-bottom: 12px; font-size: 0.9rem;">
                    Test direct SQL queries against normalized tables: <code>companies</code>, <code>job_postings</code>, <code>skills</code>, and <code>job_skills</code>.
                </p>
                <textarea id="sqlInput">SELECT jp.role_category, jp.experience_level, c.name as company, jp.location, jp.avg_salary
FROM job_postings jp
JOIN companies c ON jp.company_id = c.id
ORDER BY jp.avg_salary DESC
LIMIT 8;</textarea>
                <br>
                <button class="btn-primary" onclick="runCustomSql()">▶️ Execute SQL</button>
                <div id="sqlOutput"></div>
            </div>
        </div>
    </main>

    <script>
        let charts = {};

        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-benchmarks').style.display = tabId === 'tab-benchmarks' ? 'block' : 'none';
            document.getElementById('tab-skills').style.display = tabId === 'tab-skills' ? 'block' : 'none';
            document.getElementById('tab-livejobs').style.display = tabId === 'tab-livejobs' ? 'block' : 'none';
            document.getElementById('tab-sql').style.display = tabId === 'tab-sql' ? 'block' : 'none';
            
            if (tabId === 'tab-livejobs') {
                loadLiveJobs();
            }
        }

        async function initFilters() {
            const res = await fetch('/api/filters');
            const data = await res.json();
            
            const roleSelect = document.getElementById('roleFilter');
            data.roles.forEach(r => {
                const opt = document.createElement('option');
                opt.value = r; opt.textContent = r;
                roleSelect.appendChild(opt);
            });

            const expSelect = document.getElementById('expFilter');
            data.experience_levels.forEach(e => {
                const opt = document.createElement('option');
                opt.value = e; opt.textContent = e;
                expSelect.appendChild(opt);
            });

            const remoteSelect = document.getElementById('remoteFilter');
            data.remote_types.forEach(rt => {
                const opt = document.createElement('option');
                opt.value = rt; opt.textContent = rt;
                remoteSelect.appendChild(opt);
            });
        }

        async function loadDashboard() {
            const role = document.getElementById('roleFilter').value;
            const exp = document.getElementById('expFilter').value;
            const remote = document.getElementById('remoteFilter').value;

            const params = new URLSearchParams({ role, exp, remote });

            // 1. Fetch KPIs
            const kpiRes = await fetch('/api/kpis?' + params);
            const kpis = await kpiRes.json();
            document.getElementById('kpi-jobs').innerText = kpis.total_jobs ? kpis.total_jobs.toLocaleString() : '0';
            document.getElementById('kpi-salary').innerText = kpis.avg_salary ? '$' + Math.round(kpis.avg_salary).toLocaleString() : '$0';
            document.getElementById('kpi-skill').innerText = kpis.top_skill || 'N/A';
            document.getElementById('kpi-skill-count').innerText = (kpis.top_skill_count || 0) + ' mentions';
            document.getElementById('kpi-exp').innerText = (kpis.avg_years_exp || 0) + ' yrs';
            document.getElementById('kpi-company').innerText = kpis.top_company || 'N/A';

            // 2. Fetch Salary By Role
            const roleRes = await fetch('/api/salary_by_role?' + params);
            const roleData = await roleRes.json();
            renderRoleChart(roleData);

            // 3. Fetch Salary By Experience
            const expRes = await fetch('/api/salary_by_exp?' + params);
            const expData = await expRes.json();
            renderExpChart(expData);

            // 4. Fetch Remote stats
            const remRes = await fetch('/api/remote_stats?' + params);
            const remData = await remRes.json();
            renderRemoteCharts(remData);

            // 5. Fetch Skills
            const skillRes = await fetch('/api/skills?' + params);
            const skillData = await skillRes.json();
            renderSkillCharts(skillData);

            // 6. Reload live jobs if tab is active
            if (document.getElementById('tab-livejobs').style.display === 'block') {
                loadLiveJobs();
            }
        }

        async function loadLiveJobs() {
            const role = document.getElementById('roleFilter').value;
            const exp = document.getElementById('expFilter').value;
            const params = new URLSearchParams({ role, exp });

            const container = document.getElementById('liveJobsList');
            container.innerHTML = '<p style="color: var(--text-secondary);">Fetching latest openings online...</p>';

            const res = await fetch('/api/live_jobs?' + params);
            const data = await res.json();

            // Render direct 1-click links
            const portalDiv = document.getElementById('portalLinks');
            let portalHtml = '<strong style="color: var(--text-secondary); font-size: 0.85rem;">1-CLICK SEARCH ON TOP PORTALS:</strong><br>';
            for (const [site, url] of Object.entries(data.search_links)) {
                portalHtml += `<a href="${url}" target="_blank" class="portal-btn">🔎 ${site} ↗</a>`;
            }
            portalDiv.innerHTML = portalHtml;

            // Render jobs
            if (!data.jobs || data.jobs.length === 0) {
                container.innerHTML = '<p style="color: var(--text-secondary);">No openings returned right now. Please use the 1-click search portals above.</p>';
                return;
            }

            let html = '';
            data.jobs.forEach(j => {
                const matchedTags = (j.matched_skills || []).map(m => `<span class="tag-pill tag-matched">✓ ${m}</span>`).join('');
                const regularTags = (j.tags || []).slice(0, 4).filter(t => !(j.matched_skills || []).includes(t)).map(t => `<span class="tag-pill">${t}</span>`).join('');

                html += `
                <div class="job-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <div class="job-title">${j.title}</div>
                            <div class="job-company">🏢 ${j.company} &nbsp;•&nbsp; 📍 ${j.location} &nbsp;•&nbsp; 💵 ${j.salary}</div>
                        </div>
                        <div>
                            <span class="badge-fit">🎯 ${j.fit_score}% Fit</span>
                            <span style="font-size:0.75rem; color:#94a3b8; margin-left:6px;">${j.source}</span>
                        </div>
                    </div>
                    <div style="margin-top: 10px; color: #cbd5e1; font-size: 0.85rem; line-height: 1.4;">
                        ${j.description || 'Full JD available on application page.'}
                    </div>
                    <div style="margin-top: 10px; display:flex; justify-content:space-between; align-items:center;">
                        <div>${matchedTags}${regularTags}</div>
                        <a href="${j.url}" target="_blank" class="btn-apply">Apply Direct ↗</a>
                    </div>
                </div>`;
            });
            container.innerHTML = html;
        }

        function renderRoleChart(data) {
            const ctx = document.getElementById('chartRoleSalary').getContext('2d');
            if (charts.role) charts.role.destroy();
            charts.role = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(d => d.role_category),
                    datasets: [{
                        label: 'Avg Salary ($)',
                        data: data.map(d => d.average_salary),
                        backgroundColor: '#38bdf8',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                        y: { ticks: { color: '#f8fafc' }, grid: { display: false } }
                    }
                }
            });
        }

        function renderExpChart(data) {
            const ctx = document.getElementById('chartExpSalary').getContext('2d');
            if (charts.exp) charts.exp.destroy();
            charts.exp = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(d => d.experience_level),
                    datasets: [
                        { label: 'Min Salary', data: data.map(d => d.avg_min_salary), backgroundColor: '#38bdf8', borderRadius: 4 },
                        { label: 'Avg Salary', data: data.map(d => d.average_salary), backgroundColor: '#818cf8', borderRadius: 4 },
                        { label: 'Max Salary', data: data.map(d => d.avg_max_salary), backgroundColor: '#c084fc', borderRadius: 4 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94a3b8' } } },
                    scales: {
                        x: { ticks: { color: '#f8fafc' }, grid: { display: false } },
                        y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
                    }
                }
            });
        }

        function renderRemoteCharts(data) {
            const ctxDist = document.getElementById('chartRemoteDist').getContext('2d');
            if (charts.remoteDist) charts.remoteDist.destroy();
            charts.remoteDist = new Chart(ctxDist, {
                type: 'doughnut',
                data: {
                    labels: data.map(d => d.remote_type),
                    datasets: [{
                        data: data.map(d => d.job_count),
                        backgroundColor: ['#38bdf8', '#818cf8', '#34d399']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#f8fafc' } } }
                }
            });

            const ctxSal = document.getElementById('chartRemoteSalary').getContext('2d');
            if (charts.remoteSal) charts.remoteSal.destroy();
            charts.remoteSal = new Chart(ctxSal, {
                type: 'bar',
                data: {
                    labels: data.map(d => d.remote_type),
                    datasets: [{
                        label: 'Average Salary ($)',
                        data: data.map(d => d.avg_salary),
                        backgroundColor: ['#38bdf8', '#818cf8', '#34d399'],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: '#f8fafc' }, grid: { display: false } },
                        y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
                    }
                }
            });
        }

        function renderSkillCharts(data) {
            const top12 = data.slice(0, 12);
            const ctxSkills = document.getElementById('chartTopSkills').getContext('2d');
            if (charts.skills) charts.skills.destroy();
            charts.skills = new Chart(ctxSkills, {
                type: 'bar',
                data: {
                    labels: top12.map(d => d.skill_name),
                    datasets: [{
                        label: 'Job Demand Count',
                        data: top12.map(d => d.demand_count),
                        backgroundColor: '#818cf8',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                        y: { ticks: { color: '#f8fafc' }, grid: { display: false } }
                    }
                }
            });

            const ctxPay = document.getElementById('chartSkillSalary').getContext('2d');
            if (charts.skillPay) charts.skillPay.destroy();
            charts.skillPay = new Chart(ctxPay, {
                type: 'bar',
                data: {
                    labels: top12.map(d => d.skill_name),
                    datasets: [{
                        label: 'Avg Salary ($)',
                        data: top12.map(d => d.avg_salary_with_skill),
                        backgroundColor: '#34d399',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: '#f8fafc', maxRotation: 45 }, grid: { display: false } },
                        y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
                    }
                }
            });
        }

        async function runCustomSql() {
            const query = document.getElementById('sqlInput').value;
            const res = await fetch('/api/custom_sql', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            const data = await res.json();
            const out = document.getElementById('sqlOutput');
            if (data.error) {
                out.innerHTML = `<div style="color: #ef4444; margin-top: 12px; font-weight: 600;">Error: ${data.error}</div>`;
                return;
            }
            if (!data.rows || data.rows.length === 0) {
                out.innerHTML = '<p style="color: #94a3b8; margin-top: 12px;">Query executed successfully (0 rows returned).</p>';
                return;
            }

            let html = '<table><thead><tr>';
            data.columns.forEach(c => html += `<th>${c}</th>`);
            html += '</tr></thead><tbody>';
            data.rows.forEach(r => {
                html += '<tr>';
                r.forEach(val => html += `<td>${val}</td>`);
                html += '</tr>';
            });
            html += '</tbody></table>';
            out.innerHTML = html;
        }

        window.addEventListener('DOMContentLoaded', async () => {
            await initFilters();
            await loadDashboard();
        });
    </script>
</body>
</html>
"""

class DashboardHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        role = params.get("role", [None])[0]
        exp = params.get("exp", [None])[0]
        remote = params.get("remote", [None])[0]

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))

        elif path == "/api/filters":
            self._send_json(db.get_filter_options())

        elif path == "/api/kpis":
            self._send_json(db.get_summary_kpis(role=role, exp_level=exp, remote_type=remote))

        elif path == "/api/salary_by_role":
            data, _ = db.get_salary_by_role(exp_level=exp, remote_type=remote)
            self._send_json(data)

        elif path == "/api/salary_by_exp":
            data, _ = db.get_salary_by_experience(role=role, remote_type=remote)
            self._send_json(data)

        elif path == "/api/remote_stats":
            data, _ = db.get_remote_distribution(role=role, exp_level=exp)
            self._send_json(data)

        elif path == "/api/skills":
            data, _ = db.get_in_demand_skills(role=role, exp_level=exp, limit=15)
            self._send_json(data)

        elif path == "/api/live_jobs":
            jobs = job_fetcher.get_live_job_openings(role=role or "All", exp_level=exp or "All", limit=12)
            links = job_fetcher.get_direct_search_links(role or "All", exp or "All")
            self._send_json({"jobs": jobs, "search_links": links})

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/custom_sql":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            req = json.loads(body)
            query = req.get("query", "")
            cols, rows, error = db.execute_custom_sql(query)
            self._send_json({"columns": cols, "rows": rows, "error": error})
        else:
            self.send_response(404)
            self.end_headers()


def run(port=8050):
    server_address = ("", port)
    httpd = HTTPServer(server_address, DashboardHandler)
    print(f"🚀 SkillMetrics Web Dashboard running at http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    run()
