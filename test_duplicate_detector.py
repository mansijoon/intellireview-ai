from analyzer.duplicate_detector import (
    detect_duplicate_functions
)

code = """
def add():
    x = 1
    y = 2
    return x + y

def sum_values():
    x = 1
    y = 2
    return x + y
"""

print(
    detect_duplicate_functions(
        code
    )
)
