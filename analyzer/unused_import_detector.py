import ast


def detect_unused_imports(code):

    findings = []

    try:

        tree = ast.parse(code)

    except Exception:

        return findings

    imports = set()
    used = set()

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:

                imports.add(
                    alias.asname
                    or
                    alias.name
                )

        elif isinstance(
            node,
            ast.ImportFrom
        ):

            for alias in node.names:

                imports.add(
                    alias.asname
                    or
                    alias.name
                )

        elif isinstance(
            node,
            ast.Name
        ):

            used.add(
                node.id
            )

    unused = imports - used

    for name in unused:

        findings.append(
            {
                "type": "Unused Import",
                "severity": "Low",
                "message":
                f"{name} imported but never used."
            }
        )

    return findings
