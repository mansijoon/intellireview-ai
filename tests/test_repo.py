from pathlib import Path
import zipfile

from analyzer.repository_analyzer import (
    extract_repository,
    collect_source_code,
)


def test_extract_repository_and_collect_source_code(tmp_path):
    source = tmp_path / "source"
    source.mkdir()

    (source / "main.py").write_text(
        "def hello():\n    return 'hello'\n",
        encoding="utf-8",
    )

    archive = tmp_path / "sample_repo.zip"

    with zipfile.ZipFile(archive, "w") as zf:
        zf.write(source / "main.py", "sample_repo/main.py")

    destination = tmp_path / "extracted"

    extract_repository(str(archive), str(destination))

    code, count = collect_source_code(str(destination))

    assert count >= 1
    assert "def hello()" in code
    assert "return 'hello'" in code
