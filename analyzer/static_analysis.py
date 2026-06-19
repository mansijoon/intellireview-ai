from analyzer.ast_analyzer import (
    analyze_ast
)

from analyzer.secret_detector import (
    detect_secrets
)

from analyzer.duplicate_detector import (
    detect_duplicate_functions
)

from analyzer.unused_import_detector import (
    detect_unused_imports
)
from analyzer.unused_variable_detector import (
    detect_unused_variables
)
from analyzer.dead_function_detector import (
    detect_dead_functions
)


def run_static_analysis(code):

    findings = []

    findings.extend(
        analyze_ast(code)
    )
    
    findings.extend(
        detect_unused_variables(
            code
        )
    )
    
   # findings.extend(
   #     detect_dead_functions(
   #         code
   #     )
   # )

    findings.extend(
        detect_secrets(code)
    )

    findings.extend(
        detect_duplicate_functions(
            code
        )
    )

    findings.extend(
        detect_unused_imports(
            code
        )
    )

    return findings
