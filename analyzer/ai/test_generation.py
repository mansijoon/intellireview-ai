from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GeneratedTest:
    file_path: str
    test_code: str
    target: str


def generate_test(
    *,
    file_path: str,
    source: str,
    target: str,
) -> GeneratedTest:
    if not file_path.strip():
        raise ValueError("file_path must not be empty")

    if not source.strip():
        raise ValueError("source must not be empty")

    if not target.strip():
        raise ValueError("target must not be empty")

    tree = ast.parse(source)

    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    }

    if target not in functions:
        raise ValueError(
            f"Target '{target}' not found in source"
        )

    function = functions[target]

    argument_names = [
        arg.arg
        for arg in function.args.args
    ]

    if len(argument_names) == 0:
        invocation = f"{target}()"
    else:
        arguments = ", ".join(
            "None"
            for _ in argument_names
        )
        invocation = f"{target}({arguments})"

    test_code = f"""def test_{target}_generated():
    result = {invocation}
    assert result is not None
"""

    ast.parse(test_code)

    return GeneratedTest(
        file_path=file_path,
        test_code=test_code,
        target=target,
    )
