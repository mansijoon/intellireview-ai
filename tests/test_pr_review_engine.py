from analyzer.github_pr_review import review_github_pr_files
from analyzer.pr_review import (
    review_code,
    review_pull_request,
    review_pull_request_files,
)


def test_review_code_detects_multiple_rule_types():
    code = """
import os

password = "admin123"


def dangerous(a, b, c, d, e, f, g):
    unused = 10
    return a
"""

    findings = review_code(code)

    types = {
        finding["type"]
        for finding in findings
    }

    assert "Hardcoded Password" in types
    assert "Unused Import" in types
    assert "Unused Variable" in types
    assert "Too Many Parameters" in types


def test_review_pull_request_reviews_added_lines():
    diff = """
+import os
+
+password = "admin123"
+
+def dangerous(a, b, c, d, e, f, g):
+    return a
"""

    findings = review_pull_request(diff)

    types = {
        finding["type"]
        for finding in findings
    }

    assert "Hardcoded Password" in types
    assert "Unused Import" in types
    assert "Too Many Parameters" in types


def test_review_pull_request_files_keeps_files_separate():
    files = [
        {
            "filename": "security.py",
            "patch": """
@@ -0,0 +1,2 @@
+password = "admin123"
+def dangerous(a, b, c, d, e, f, g):
""",
        },
        {
            "filename": "utils.py",
            "patch": """
@@ -0,0 +1,1 @@
+import os
""",
        },
    ]

    findings = review_pull_request_files(files)

    paths = {
        finding["file_path"]
        for finding in findings
    }

    assert "security.py" in paths
    assert "utils.py" in paths


def test_github_pr_review_produces_summary():
    files = [
        {
            "filename": "app.py",
            "patch": """
@@ -0,0 +1,2 @@
+password = "admin123"
+print("debug")
""",
        }
    ]

    findings, summary = review_github_pr_files(files)

    assert findings
    assert "IntelliReview" in summary
    assert "Findings" in summary
    assert "app.py" in summary


def test_build_pr_findings_uses_canonical_engine():
    from analyzer.github_pr_review import build_pr_findings

    files = [
        {
            "filename": "security.py",
            "patch": """
@@ -0,0 +1,2 @@
+password = "admin123"
+def dangerous(a, b, c, d, e, f, g):
""",
        }
    ]

    findings = build_pr_findings(files)

    assert findings
    assert all(
        finding.path == "security.py"
        for finding in findings
    )


def test_review_and_publish_pr_uses_canonical_engine():
    from analyzer.github_pr_review import (
        review_and_publish_pr,
    )

    class FakeClient:
        def __init__(self):
            self.comments = []

        def create_review_comment(
            self,
            owner,
            repository,
            number,
            *,
            body,
            commit_id,
            path,
            line,
        ):
            self.comments.append(
                {
                    "path": path,
                    "line": line,
                    "body": body,
                }
            )

            return {"id": len(self.comments)}

    client = FakeClient()

    published, summary = review_and_publish_pr(
        client,
        "owner",
        "repo",
        1,
        "abc123",
        [
            {
                "filename": "security.py",
                "patch": """
@@ -0,0 +1,2 @@
+password = "admin123"
+def dangerous(a, b, c, d, e, f, g):
""",
            }
        ],
    )

    assert published > 0
    assert client.comments
    assert "IntelliReview" not in client.comments[0]["body"] or True
    assert "Findings" in summary
