import os

from analyzer.static_analysis import (
    run_static_analysis
)


def analyze_repository_static(
    repo_path,
    repo_files
):

    findings = []

    for file in repo_files:

        full_path = os.path.join(
            repo_path,
            file
        )

        try:

            with open(
                full_path,
                "r",
                encoding="utf-8"
            ) as f:

                code = f.read()

            if file.endswith(".py"):

                file_findings = run_static_analysis(
                    code
                )

            else:

                file_findings = []

            for finding in file_findings:

                finding["file"] = file

            findings.extend(
                file_findings
            )

        except Exception:

            continue

    return findings
