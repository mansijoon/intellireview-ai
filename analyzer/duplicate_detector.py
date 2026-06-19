import ast


def detect_duplicate_functions(code):

    findings = []

    try:

        tree = ast.parse(code)

    except Exception:

        return findings

    functions = {}

    for node in ast.walk(tree):

        if isinstance(
            node,
            ast.FunctionDef
        ):

            body = ""

            for statement in node.body:

                body += ast.dump(
                    statement
                )

            if body in functions:

                findings.append(
                    {
                        "type": "Duplicate Function",
                        "severity": "Medium",
                        "message":
                        f"{node.name} duplicates "
                        f"{functions[body]}"
                    }
                )

            else:

                functions[body] = node.name

    return findings
