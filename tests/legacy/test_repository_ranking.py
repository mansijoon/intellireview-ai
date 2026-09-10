from analyzer.repository_risk_ranking import (
    rank_repository_files
)

repo_files = [
    "a.py",
    "b.py",
    "test.py"
]

results = rank_repository_files(
    "sample_repo",
    repo_files
)

print(results)
