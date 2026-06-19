import re


def calculate_metrics(code: str):

    lines = len(code.splitlines())

    functions = len(
        re.findall(r"def\s+\w+\(", code)
    )

    classes = len(
        re.findall(r"class\s+\w+", code)
    )

    imports = len(
        re.findall(r"^\s*(import|from)\s+", code, re.MULTILINE)
    )

    loops = len(
        re.findall(r"\b(for|while)\b", code)
    )

    conditionals = len(
        re.findall(r"\b(if|elif|else)\b", code)
    )

    complexity_score = (
        loops +
        conditionals +
        functions
    )

    if complexity_score < 5:
        risk = "Low"

    elif complexity_score < 15:
        risk = "Medium"

    else:
        risk = "High"

    return {
        "lines": lines,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "loops": loops,
        "conditionals": conditionals,
        "complexity_score": complexity_score,
        "risk": risk
    }
