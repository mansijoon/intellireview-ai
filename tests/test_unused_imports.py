from analyzer.unused_import_detector import (
    detect_unused_imports
)

code = """
import os
import math

print("hello")
"""

print(
    detect_unused_imports(
        code
    )
)
