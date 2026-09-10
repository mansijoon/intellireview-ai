from analyzer.review_parser import extract_score

text = """
Overall Code Quality Score

Score: 10/100
"""

print(
    extract_score(text)
)
