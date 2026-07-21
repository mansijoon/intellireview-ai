import ast
import re


class ComplexityVisitor(ast.NodeVisitor):
    """
    Calculates cyclomatic complexity using Python AST.
    """

    def __init__(self):
        self.complexity = 1

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Try(self, node):
        self.complexity += len(node.handlers)
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_SetComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_DictComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_Match(self, node):
        """
        Support Python 3.10+ match/case statements.
        """
        self.complexity += len(node.cases)
        self.generic_visit(node)


def calculate_metrics(code: str):
    """
    Calculates source-code metrics.

    Returns both the legacy keys and the newer keys so that
    existing modules continue to work.
    """

    lines = len(code.splitlines())

    functions = len(
        re.findall(
            r"(?:async\s+def|def)\s+\w+\(",
            code
        )
    )

    classes = len(
        re.findall(
            r"class\s+\w+",
            code
        )
    )

    imports = len(
        re.findall(
            r"^\s*(import|from)\s+",
            code,
            re.MULTILINE
        )
    )

    loops = len(
        re.findall(
            r"\b(for|while)\b",
            code
        )
    )

    conditionals = len(
        re.findall(
            r"\b(if|elif|else)\b",
            code
        )
    )

    try:

        tree = ast.parse(code)

        visitor = ComplexityVisitor()

        visitor.visit(tree)

        complexity_score = visitor.complexity

    except SyntaxError:
        # Fallback for non-Python languages
        complexity_score = loops + conditionals + 1

    except Exception:
        complexity_score = loops + conditionals + 1

    if complexity_score < 10:
        risk = "Low"

    elif complexity_score < 20:
        risk = "Medium"

    else:
        risk = "High"

    return {

        # Legacy keys
        "lines": lines,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "loops": loops,
        "conditionals": conditionals,
        "complexity_score": complexity_score,
        "risk": risk,

        # New standardized keys
        "lines_of_code": lines,
        "cyclomatic_complexity": complexity_score,
    }
