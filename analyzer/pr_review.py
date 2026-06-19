from analyzer.secret_detector import (
    detect_secrets
)

from analyzer.unused_import_detector import (
    detect_unused_imports
)


def review_pull_request(
    diff_text
):

    added_lines = []

    for line in diff_text.splitlines():

        if (
            line.startswith("+")
            and not line.startswith("+++")
        ):

            added_lines.append(
                line[1:]
            )

    code = "\n".join(
        added_lines
    )

    findings = []

    findings.extend(
        detect_secrets(
            code
        )
    )

    findings.extend(
        detect_unused_imports(
            code
        )
    )

    return findings
