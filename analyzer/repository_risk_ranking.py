import os

from analyzer.static_analysis import (
    run_static_analysis
)

from analyzer.file_risk_score import (
    calculate_file_risk
)


def rank_repository_files(
    repo_path,
    repo_files
):

    results = []

    for file in repo_files:

        if not file.endswith(".py"):

            continue

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

            findings = run_static_analysis(
                code
            )

            risk_score = calculate_file_risk(
                findings
            )

            results.append(
                {
                    "file": file,
                    "risk_score": risk_score,
                    "issues": len(findings)
                }
            )

        except Exception:

            continue

    results.sort(
        key=lambda x: x["risk_score"],
        reverse=True
    )

    return results
