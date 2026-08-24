from analyzer.repository_static_analysis import (
    analyze_repository_static
)

repo_files = [
    "test.py",
    "a.py",
    "b.py"
]

findings = analyze_repository_static(
    "sample_repo",
    repo_files
)

print(findings)
