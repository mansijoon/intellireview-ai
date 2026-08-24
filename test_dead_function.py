from analyzer.dead_function_detector import (
    detect_dead_functions
)

code = """
def helper():
    print("hello")

def main():
    print("world")

main()
"""

print(
    detect_dead_functions(
        code
    )
)
