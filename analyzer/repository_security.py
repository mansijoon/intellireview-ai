import os

from analyzer.secret_detector import detect_secrets
from analyzer.static_analysis import run_static_analysis


SUPPORTED_EXTENSIONS = (
    ".py",
    ".js",
    ".ts",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
)


def analyze_repository_security(repo_path):
    """
    Analyze repository for security vulnerabilities.
    """

    findings = []

    for root, _, files in os.walk(repo_path):

        for file in files:

            if not file.endswith(SUPPORTED_EXTENSIONS):
                continue

            path = os.path.join(root, file)

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    code = f.read()

                secrets = detect_secrets(code)
                static_findings = run_static_analysis(code)

                security_findings = []

                for item in static_findings:
                    issue = item.get(
                        "issue",
                        ""
                    ).lower()

                    if any(
                        keyword in issue
                        for keyword in (
                            "security",
                            "secret",
                            "password",
                            "token",
                            "credential",
                            "sql injection",
                            "xss",
                            "command injection",
                        )
                    ):
                        security_findings.append(item)

                findings.append(
                    {
                        "file": os.path.relpath(
                            path,
                            repo_path
                        ),
                        "secrets": secrets,
                        "issues": security_findings,
                    }
                )

            except Exception:
                continue

    return findings
