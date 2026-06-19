import os
import ast


def analyze_repository_architecture(
    repo_path,
    repo_files
):

    findings = []

    if len(repo_files) > 100:

        findings.append(
            {
                "type": "Large Repository",
                "severity": "Medium",
                "message":
                f"Repository contains {len(repo_files)} files."
            }
        )

    for file in repo_files:

        path = os.path.join(
            repo_path,
            file
        )

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                code = f.read()

            line_count = len(
                code.splitlines()
            )

            if line_count > 300:

                findings.append(
                    {
                        "type": "Large Module",
                        "severity": "Medium",
                        "message":
                        f"{file} has {line_count} lines."
                    }
                )

            tree = ast.parse(
                code
            )

            function_count = sum(
                isinstance(
                    node,
                    ast.FunctionDef
                )
                for node in ast.walk(tree)
            )

            class_count = sum(
                isinstance(
                    node,
                    ast.ClassDef
                )
                for node in ast.walk(tree)
            )

            if (
                line_count > 500
                or function_count > 20
                or class_count > 10
            ):

                findings.append(
                    {
                        "type": "God Module",
                        "severity": "High",
                        "message":
                        f"{file} has "
                        f"{line_count} lines, "
                        f"{function_count} functions, "
                        f"{class_count} classes."
                    }
                )

        except Exception:

            pass

    return findings
