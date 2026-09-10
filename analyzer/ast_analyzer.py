import ast


def calculate_complexity(node):

    complexity = 1

    for child in ast.walk(node):

        if isinstance(
            child,
            (
                ast.If,
                ast.For,
                ast.While,
                ast.Try,
                ast.ExceptHandler,
                ast.With
            )
        ):
            complexity += 1

    return complexity


def nesting_depth(node):
    """
    Calculate maximum control-flow nesting depth.

    AST tree depth is not equivalent to source-code nesting.
    Only control-flow constructs contribute to this metric.
    """

    control_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.With,
        ast.AsyncWith,
        ast.Match,
    )

    max_depth = 0

    def visit(current, depth):
        nonlocal max_depth

        next_depth = (
            depth + 1
            if isinstance(current, control_nodes)
            else depth
        )

        max_depth = max(
            max_depth,
            next_depth,
        )

        for child in ast.iter_child_nodes(current):
            visit(child, next_depth)

    visit(node, 0)

    return max_depth


def analyze_ast(code):

    findings = []

    try:

        tree = ast.parse(code)

    except Exception:

        return [
            {
                "type": "Parse Error",
                "severity": "High",
                "message": "Unable to parse source code."
            }
        ]

    for node in ast.walk(tree):

        if isinstance(
            node,
            ast.FunctionDef
        ):

            line_count = (
                getattr(
                    node,
                    "end_lineno",
                    node.lineno
                )
                - node.lineno
                + 1
            )

            if line_count > 50:

                findings.append(
                    {
                        "type": "Long Function",
                        "severity": "Medium",
                        "message":
                        f"{node.name} has {line_count} lines."
                    }
                )

            if len(node.args.args) > 5:

                findings.append(
                    {
                        "type": "Too Many Parameters",
                        "severity": "Medium",
                        "message":
                        f"{node.name} has "
                        f"{len(node.args.args)} parameters."
                    }
                )

            complexity = calculate_complexity(
                node
            )

            if complexity > 10:

                findings.append(
                    {
                        "type": "High Complexity",
                        "severity": "High",
                        "message":
                        f"{node.name} complexity = {complexity}"
                    }
                )

            depth = nesting_depth(
                node
            )

            if depth > 6:

                findings.append(
                    {
                        "type": "Deep Nesting",
                        "severity": "Medium",
                        "message":
                        f"{node.name} nesting depth = {depth}"
                    }
                )

    return findings
