from analyzer.architecture_analyzer import (
    analyze_repository_architecture
)

print(
    analyze_repository_architecture(
        "sample_repo",
        ["test.py"]
    )
)
