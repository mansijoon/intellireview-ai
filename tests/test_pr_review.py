from analyzer.pr_review import (
    review_pull_request
)

diff = """
+ import os
+ password = "admin123"
+
+ def add(
+     a,b,c,d,e,f,g
+ ):
+     return a+b
"""

print(
    review_pull_request(
        diff
    )
)
