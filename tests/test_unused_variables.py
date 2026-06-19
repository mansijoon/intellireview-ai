from analyzer.unused_variable_detector import (
    detect_unused_variables
)

code = """
x = 10
y = 20

print(x)
"""

print(
    detect_unused_variables(
        code
    )
)
