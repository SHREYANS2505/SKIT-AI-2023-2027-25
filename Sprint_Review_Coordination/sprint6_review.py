#!/usr/bin/env python3
"""Sprint 6 static quality review for the OZONE Smart Agriculture project.

Usage:
    python sprint6_review.py /path/to/SKIT-AI-2023-2027-25
    python sprint6_review.py /path/to/SKIT-AI-2023-2027-25 --json
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from dataclasses import asdict, dataclass

REQUIRED_FILES = (
    "app.py", "README.md", "loan_tracker.py", "mandi_service.py",
    "templates/index.html", "templates/home.html",
    "templates/register.html", "templates/farmer_profile.html",
    "static/js/main.js", "static/CSS/style.css",
    "static/CSS/home.css", "static/CSS/register.css",
)
EXPECTED_ROUTES = (
    "/", "/register", "/api/login", "/api/user", "/home",
    "/api/weather", "/api/mandi-prices", "/farmer-profile",
    "/profile", "/api/loan-tracker/update", "/login", "/logout",
)

@dataclass
class Check:
    name: str
    status: str
    details: str

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def audit_project(project: Path) -> list[Check]:
    checks: list[Check] = []
    if not project.exists() or not project.is_dir():
        return [Check("project_path", "FAIL", f"Project directory not found: {project}")]

    for rel in REQUIRED_FILES:
        exists = (project / rel).is_file()
        checks.append(Check(f"file:{rel}", "PASS" if exists else "FAIL",
                            "Required file exists" if exists else "Required file is missing"))

    app_source = read_text(project / "app.py")
    route_matches = set(re.findall(r"@app\.route\(\s*['\"]([^'\"]+)['\"]", app_source))
    for route in EXPECTED_ROUTES:
        present = route in route_matches
        checks.append(Check(f"route:{route}", "PASS" if present else "WARN",
                            "Route declaration found" if present else
                            "Route not found in app.py; confirm whether it was renamed or removed"))

    # Check that route decorators point to functions and that obvious duplicate route declarations
    route_lines = re.findall(r"@app\.route\(\s*['\"]([^'\"]+)['\"][^\n]*\)\s*\n\s*def\s+([A-Za-z_]\w*)", app_source)
    checks.append(Check("route_handlers", "PASS" if route_lines else "WARN",
                        f"Found {len(route_lines)} route decorator/handler pairs"))
    duplicates = sorted({r for r in route_matches if len(re.findall(
        r"@app\.route\(\s*['\"]" + re.escape(r) + r"['\"]", app_source)) > 1})
    checks.append(Check("duplicate_routes", "WARN" if duplicates else "PASS",
                        "Duplicate route declarations: " + ", ".join(duplicates) if duplicates
                        else "No duplicate route declarations detected"))

    # UI assets: report empties and template links to local assets that do not exist.
    templates = list((project / "templates").glob("*.html")) if (project / "templates").is_dir() else []
    linked_assets: set[str] = set()
    for template in templates:
        content = read_text(template)
        for match in re.findall(r"""url_for\(\s*['"]static['"]\s*,\s*filename\s*=\s*['"]([^'"]+)['"]""", content):
            linked_assets.add(match)
    missing_assets = sorted(a for a in linked_assets if not (project / "static" / a).is_file())
    checks.append(Check("template_static_assets", "FAIL" if missing_assets else "PASS",
                        "Missing assets: " + ", ".join(missing_assets) if missing_assets
                        else f"Checked {len(linked_assets)} referenced static assets; all exist"))

    for rel in ("static/js/main.js", "static/CSS/style.css",
                "static/CSS/home.css", "static/CSS/register.css"):
        path = project / rel
        if path.is_file():
            content = read_text(path)
            checks.append(Check(f"nonempty:{rel}", "PASS" if content.strip() else "FAIL",
                                f"{len(content.splitlines())} lines" if content.strip() else "File is empty"))

    # Static checks for common Flask startup risks; findings are warnings for human review.
    if re.search(r"\bdatabase\.init_db\s*\(", app_source) and not re.search(
            r"^\s*import\s+database\b|^\s*from\s+database\s+import", app_source, re.M):
        checks.append(Check("startup_database_import", "WARN",
                            "app.py calls database.init_db() but no database import was detected"))
    if "app = Flask(" not in app_source:
        checks.append(Check("flask_app_initialization", "FAIL",
                            "Could not find app = Flask(...); verify application initialization"))
    else:
        checks.append(Check("flask_app_initialization", "PASS", "Flask app initialization found"))

    # Secret-key fallback is flagged so production configuration can be checked.
    if re.search(r"secret_key\s*=\s*.*['\"][^'\"]{8,}['\"]", app_source):
        checks.append(Check("secret_key_fallback", "WARN",
                            "A literal secret-key fallback may be present; use an environment variable in deployment"))
    else:
        checks.append(Check("secret_key_fallback", "PASS",
                            "No obvious literal secret-key fallback detected"))
    return checks

def main() -> int:
    parser = argparse.ArgumentParser(description="Run Sprint 6 static project quality checks.")
    parser.add_argument("project", type=Path, help="Path to the extracted OZONE project")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()
    results = audit_project(args.project.resolve())
    if args.json:
        print(json.dumps([asdict(c) for c in results], indent=2))
    else:
        print("=" * 72)
        print("SPRINT 6 — UI MODULE REVIEW & STATIC QUALITY AUDIT")
        print(f"Project: {args.project.resolve()}")
        print("=" * 72)
        for item in results:
            print(f"[{item.status:4}] {item.name}: {item.details}")
        counts = {status: sum(c.status == status for c in results) for status in ("PASS", "WARN", "FAIL")}
        print("-" * 72)
        print(f"Summary: {counts['PASS']} passed | {counts['WARN']} warnings | {counts['FAIL']} failed")
        print("Note: static checks do not replace browser-based or live API testing.")
    return 1 if any(c.status == "FAIL" for c in results) else 0

if __name__ == "__main__":
    raise SystemExit(main())
