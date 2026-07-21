from analyzer.repository_reviewer import (
    review_repository
)

from analyzer.file_explorer import (
    get_repository_files
)

repo_path = "uploads/extracted_repo"

repo_files = get_repository_files(
    repo_path
)

results = review_repository(
    repo_path,
    repo_files
)

print(
    f"Reviewed {len(results)} files"
)

for result in results:

    print(
        result["file"]
    )
