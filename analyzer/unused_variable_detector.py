import ast


def detect_unused_variables(code):

    findings = []

    try:

        tree = ast.parse(code)

    except Exception:

        return findings

    assigned = set()
    used = set()

    for node in ast.walk(tree):

        if isinstance(
            node,
            ast.Assign
        ):

            for target in node.targets:

                if isinstance(
                    target,
                    ast.Name
                ):

                    assigned.add(
                        target.id
                    )

        elif isinstance(
            node,
            ast.Name
        ):

            if isinstance(
                node.ctx,
                ast.Load
            ):

                used.add(
                    node.id
                )

    unused = assigned - used

    for variable in unused:

        findings.append(
            {
                "type": "Unused Variable",
                "severity": "Low",
                "message":
                f"{variable} assigned but never used."
            }
        )

    return findings
