from analyzer.static_analysis import (
    run_static_analysis
)

code = """
password = "admin123"

def add(
    a,b,c,d,e,f,g
):
    x = 1
    y = 2
    return x + y

def sum_values():
    x = 1
    y = 2
    return x + y
"""

print(
    run_static_analysis(
        code
    )
)
