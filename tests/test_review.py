from analyzer.review_engine import review_code

sample_code = """
password = "admin123"

for i in range(100):
    for j in range(100):
        print(i, j)
"""

result = review_code(
    sample_code
)

print(result)
