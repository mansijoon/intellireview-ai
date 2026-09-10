from analyzer.ast_analyzer import analyze_ast
from analyzer.unused_variable_detector import detect_unused_variables


def run_static_analysis(code):
    findings = []

    findings.extend(
        analyze_ast(code)
    )

    findings.extend(
        detect_unused_variables(code)
    )

    return findings
