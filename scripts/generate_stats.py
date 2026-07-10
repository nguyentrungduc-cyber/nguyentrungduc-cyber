#!/usr/bin/env python3
"""
Tự sinh lại assets/github-stats.svg và assets/top-langs.svg từ dữ liệu GitHub API thật.
Được chạy định kỳ bởi GitHub Actions (xem .github/workflows/update-stats.yml).

Cần biến môi trường GH_TOKEN (GitHub Actions tự cấp qua secrets.GITHUB_TOKEN) để tránh
bị rate-limit khi gọi API (60 request/giờ nếu không có token, 5000 request/giờ nếu có).
"""
import json
import os
import urllib.request

USERNAME = "nguyentrungduc-cyber"
TOKEN = os.environ.get("GH_TOKEN", "")
API = "https://api.github.com"

LANG_COLORS = {
    "C#": "#178600",
    "C++": "#f34b7d",
    "FreeMarker": "#0050b2",
    "CSS": "#563d7c",
    "JavaScript": "#f1e05a",
    "EJS": "#a91e50",
    "Shell": "#89e051",
    "HTML": "#e34c26",
    "Dockerfile": "#384d54",
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
}
DEFAULT_COLOR = "#8b949e"


def api_get(path):
    req = urllib.request.Request(f"{API}{path}")
    if TOKEN:
        req.add_header("Authorization", f"token {TOKEN}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def fetch_profile():
    return api_get(f"/users/{USERNAME}")


def fetch_repos():
    return api_get(f"/users/{USERNAME}/repos?per_page=100")


def fetch_languages(repo_name):
    try:
        return api_get(f"/repos/{USERNAME}/{repo_name}/languages")
    except Exception:
        return {}


def build_github_stats_svg(profile, repos):
    public_repos = profile.get("public_repos", len(repos))
    followers = profile.get("followers", 0)
    following = profile.get("following", 0)
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)

    svg = f"""<svg width="420" height="180" viewBox="0 0 420 180" xmlns="http://www.w3.org/2000/svg">
  <style>
    .bg {{ fill: #0d1117; stroke: #00FF9C; stroke-width: 1.5; }}
    .title {{ font: 600 15px 'Fira Code', monospace; fill: #00FF9C; }}
    .label {{ font: 400 12px 'Fira Code', monospace; fill: #c9d1d9; }}
    .value {{ font: 600 12px 'Fira Code', monospace; fill: #ffffff; }}
    .prompt {{ font: 400 12px 'Fira Code', monospace; fill: #58a6ff; }}
  </style>
  <rect class="bg" x="1" y="1" width="418" height="178" rx="10"/>
  <circle cx="20" cy="20" r="5" fill="#ff5f56"/>
  <circle cx="36" cy="20" r="5" fill="#ffbd2e"/>
  <circle cx="52" cy="20" r="5" fill="#27c93f"/>
  <text x="20" y="48" class="title">$ gh api stats --user {USERNAME}</text>

  <text x="20" y="78" class="prompt">&#10148;</text>
  <text x="35" y="78" class="label">Public repos</text>
  <text x="380" y="78" class="value" text-anchor="end">{public_repos}</text>

  <text x="20" y="100" class="prompt">&#10148;</text>
  <text x="35" y="100" class="label">Followers</text>
  <text x="380" y="100" class="value" text-anchor="end">{followers}</text>

  <text x="20" y="122" class="prompt">&#10148;</text>
  <text x="35" y="122" class="label">Following</text>
  <text x="380" y="122" class="value" text-anchor="end">{following}</text>

  <text x="20" y="144" class="prompt">&#10148;</text>
  <text x="35" y="144" class="label">Total stars</text>
  <text x="380" y="144" class="value" text-anchor="end">{total_stars}</text>

  <text x="20" y="166" class="label" fill="#8b949e">org: University of Information Technology, VNUHCM</text>
</svg>
"""
    return svg


def build_top_langs_svg(repos):
    totals = {}
    for r in repos:
        if r.get("fork"):
            continue
        for lang, size in fetch_languages(r["name"]).items():
            totals[lang] = totals.get(lang, 0) + size

    total = sum(totals.values()) or 1
    top = sorted(totals.items(), key=lambda x: -x[1])[:5]

    rows = []
    y_text = 74
    y_bar = 80
    for lang, size in top:
        pct = size / total * 100
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        bar_width = round(370 * pct / 100, 1)
        rows.append(f"""
  <text x="20" y="{y_text}" class="label">{lang}</text>
  <text x="390" y="{y_text}" class="pct" text-anchor="end">{pct:.1f}%</text>
  <rect class="track" x="20" y="{y_bar}" width="370" height="8" rx="4"/>
  <rect x="20" y="{y_bar}" width="{bar_width}" height="8" rx="4" fill="{color}"/>""")
        y_text += 30
        y_bar += 30

    height = y_text + 20
    svg = f"""<svg width="420" height="{height}" viewBox="0 0 420 {height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .bg {{ fill: #0d1117; stroke: #00FF9C; stroke-width: 1.5; }}
    .title {{ font: 600 15px 'Fira Code', monospace; fill: #00FF9C; }}
    .label {{ font: 400 12px 'Fira Code', monospace; fill: #c9d1d9; }}
    .pct {{ font: 600 12px 'Fira Code', monospace; fill: #ffffff; }}
    .track {{ fill: #21262d; }}
  </style>
  <rect class="bg" x="1" y="1" width="418" height="{height - 2}" rx="10"/>
  <circle cx="20" cy="20" r="5" fill="#ff5f56"/>
  <circle cx="36" cy="20" r="5" fill="#ffbd2e"/>
  <circle cx="52" cy="20" r="5" fill="#27c93f"/>
  <text x="20" y="48" class="title">$ cat top_languages.json</text>
{"".join(rows)}
  <text x="20" y="{y_text}" class="label" fill="#8b949e" font-size="10">Tính theo dung lượng code thật trên GitHub (bỏ qua repo fork)</text>
</svg>
"""
    return svg


def main():
    profile = fetch_profile()
    repos = fetch_repos()

    os.makedirs("assets", exist_ok=True)

    with open("assets/github-stats.svg", "w", encoding="utf-8") as f:
        f.write(build_github_stats_svg(profile, repos))

    with open("assets/top-langs.svg", "w", encoding="utf-8") as f:
        f.write(build_top_langs_svg(repos))

    print("Đã sinh lại assets/github-stats.svg và assets/top-langs.svg")


if __name__ == "__main__":
    main()
