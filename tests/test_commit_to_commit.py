import subprocess
from pathlib import Path

from analyzer.baseline import compare_revisions


def create_git_repo(path: Path) -> tuple[str, str]:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Test"],
        check=True,
    )

    (path / "app.py").write_text(
        "def example():\n"
        "    return 1\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(path), "commit", "-qm", "initial"],
        check=True,
    )

    first = subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        text=True,
    ).strip()

    (path / "app.py").write_text(
        "def example():\n"
        "    try:\n"
        "        return 1\n"
        "    except:\n"
        "        return 0\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(path), "commit", "-qm", "second"],
        check=True,
    )

    second = subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        text=True,
    ).strip()

    return first, second


def test_compare_explicit_commits(tmp_path: Path):
    first, second = create_git_repo(tmp_path)

    comparison = compare_revisions(
        str(tmp_path),
        from_revision=first,
        to_revision=second,
    )

    assert comparison.baseline_revision == first
    assert comparison.current_revision == second
    assert comparison.new_count >= 1
