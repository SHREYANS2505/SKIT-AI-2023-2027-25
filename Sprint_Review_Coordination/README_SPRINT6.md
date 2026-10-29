# Sprint 6 Module — OZONE Smart Agriculture Project

**Sprint dates:** 26 October 2026 – 30 November 2026  
**Sprint focus:** Sprint review coordination, UI module checks, and quality review.

This is a flat, standalone folder: every deliverable is directly in this directory, with no nested folders. It contains a small static-review tool and its unit tests; it does not copy or overwrite the main project.

## Files

- `sprint6_review.py` — scans the existing OZONE project for expected modules, Flask route declarations, UI assets, duplicate routes, and a few common startup/configuration risks.
- `test_sprint6.py` — unit tests for the review tool using temporary sample projects.
- `SPRINT6_REVIEW_NOTES.md` — review checklist and execution notes.
- `requirements_sprint6.txt` — no third-party dependencies are required by these review scripts.

## Run the unit tests

Use Python 3.10 or later:

```bash
python3 -m unittest -v test_sprint6.py
```

## Run the project audit

First extract the supplied `SKIT-AI-2023-2027-25.zip`. Then run the tool with the path to the extracted project folder:

```bash
python3 sprint6_review.py "/path/to/SKIT-AI-2023-2027-25"
```

For machine-readable output:

```bash
python3 sprint6_review.py "/path/to/SKIT-AI-2023-2027-25" --json
```

The audit is deliberately read-only. It does not change the project, database, or Git history. `WARN` means a human should verify the finding; static inspection cannot prove that the application works in a browser or that external APIs are available.

## Sprint 6 completion evidence

1. Check expected UI templates, CSS, and JavaScript files.
2. Check that expected route declarations are present.
3. Find template references to missing static assets.
4. Flag duplicate route declarations and likely Flask startup configuration issues.
5. Run unit tests and record results during the sprint review.
