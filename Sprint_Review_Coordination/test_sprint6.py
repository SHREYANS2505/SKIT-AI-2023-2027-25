"""Unit tests for the Sprint 6 static review tool."""
import tempfile
import unittest
from pathlib import Path
from sprint6_review import audit_project

class Sprint6AuditTests(unittest.TestCase):
    def make_project(self, root: Path):
        for rel in (
            "app.py", "README.md", "loan_tracker.py", "mandi_service.py",
            "templates/index.html", "templates/home.html",
            "templates/register.html", "templates/farmer_profile.html",
            "static/js/main.js", "static/CSS/style.css",
            "static/CSS/home.css", "static/CSS/register.css",
        ):
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("", encoding="utf-8")
        (root / "app.py").write_text(
            "from flask import Flask\\napp = Flask(__name__)\\n"
            "@app.route('/')\\ndef index():\\n    return 'ok'\\n",
            encoding="utf-8"
        )
        (root / "templates/index.html").write_text(
            "<script src=\"{{ url_for('static', filename='js/main.js') }}\"></script>",
            encoding="utf-8"
        )

    def test_required_files_and_flask_initialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            results = audit_project(root)
            statuses = {item.name: item.status for item in results}
            self.assertEqual(statuses["file:app.py"], "PASS")
            self.assertEqual(statuses["flask_app_initialization"], "PASS")
            self.assertEqual(statuses["template_static_assets"], "PASS")

    def test_missing_project_directory_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = audit_project(Path(tmp) / "not-a-project")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, "FAIL")

    def test_missing_required_file_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            (root / "loan_tracker.py").unlink()
            results = audit_project(root)
            statuses = {item.name: item.status for item in results}
            self.assertEqual(statuses["file:loan_tracker.py"], "FAIL")

if __name__ == "__main__":
    unittest.main(verbosity=2)
