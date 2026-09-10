from pathlib import Path

from analyzer.file_explorer import get_repository_files
from analyzer.repository_reviewer import review_repository


def test_review_repository(tmp_path, monkeypatch):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()

    (repo_path / "main.py").write_text(
        "def hello(name):\n"
        "    return f'Hello {name}'\n",
        encoding="utf-8",
    )

    repo_files = get_repository_files(str(repo_path))

    monkeypatch.setenv("INTELLIREVIEW_DISABLE_KNOWLEDGE", "1")

    results = review_repository(
        str(repo_path),
        repo_files,
    )

    assert isinstance(results, list)
    assert all("file" in result for result in results)
    assert all("review" in result for result in results)
