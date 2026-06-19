from analyzer.repository_analyzer import (
    extract_repository,
    collect_source_code
)

extract_repository(
    "sample_repo.zip",
    "temp_repo"
)

code, count = collect_source_code(
    "temp_repo"
)

print(count)

print(code)
