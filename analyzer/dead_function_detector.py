import ast


def detect_dead_functions(code):

    findings = []

    try:

        tree = ast.parse(code)

    except Exception:

        return findings

    defined = set()
    called = set()

    for node in ast.walk(tree):

        if isinstance(
            node,
            ast.FunctionDef
        ):

            defined.add(
                node.name
            )

        elif isinstance(
            node,
            ast.Call
        ):

            if isinstance(
                node.func,
                ast.Name
            ):

                called.add(
                    node.func.id
                )

    dead = defined - called

    for function in dead:

        if function == "main":

            continue

        findings.append(
            {
                "type": "Dead Function",
                "severity": "Medium",
                "message":
                f"{function} defined but never called."
            }
        )

    return findings
