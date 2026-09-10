
import json
import subprocess
import sys


REPO = "/tmp/intellireview-commit-test"


def run_cli(*args, env=None):
    import os

    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    return subprocess.run(
        [sys.executable, "-m", "intellireview_cli", *args],
        text=True,
        capture_output=True,
        env=process_env,
    )


def create_git_repo(path):
    subprocess.run(
        ["rm", "-rf", path],
        check=True,
    )

    subprocess.run(
        ["mkdir", "-p", path],
        check=True,
    )

    with open(f"{path}/test.py", "w") as f:
        f.write("def test():\\n    return 1\\n")

    subprocess.run(
        ["git", "init", "-q", path],
        check=True,
    )

    subprocess.run(
        ["git", "-C", path, "config", "user.email", "test@example.com"],
        check=True,
    )

    subprocess.run(
        ["git", "-C", path, "config", "user.name", "Test"],
        check=True,
    )

    subprocess.run(
        ["git", "-C", path, "add", "."],
        check=True,
    )

    subprocess.run(
        ["git", "-C", path, "commit", "-qm", "initial"],
        check=True,
    )


def test_analyze_invalid_revision_json():
    create_git_repo(REPO)

    result = run_cli(
        "analyze",
        REPO,
        "--revision",
        "DOES_NOT_EXIST",
        "--json",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "Invalid Git revision" in payload["error"]
    assert "Traceback" not in result.stderr


def test_baseline_compare_invalid_revision_json():
    create_git_repo(REPO)

    result = run_cli(
        "baseline",
        "compare",
        REPO,
        "--revision",
        "DOES_NOT_EXIST",
        "--json",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "Invalid Git revision" in payload["error"]
    assert "Traceback" not in result.stderr


def test_analyze_missing_baseline_json():
    repo = "/tmp/intellireview-no-baseline-cli-test"

    subprocess.run(
        ["rm", "-rf", repo],
        check=True,
    )

    subprocess.run(
        ["mkdir", "-p", repo],
        check=True,
    )

    with open(f"{repo}/test.py", "w") as f:
        f.write("def test():\n    return 1\n")

    result = run_cli(
        "analyze",
        repo,
        "--baseline",
        "--json",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "No IntelliReview baseline exists" in payload["error"]
    assert "Traceback" not in result.stderr


def test_compare_invalid_revision_json():
    create_git_repo(REPO)

    result = run_cli(
        "compare",
        REPO,
        "--from",
        "DOES_NOT_EXIST",
        "--to",
        "HEAD",
        "--json",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "Invalid Git revision" in payload["error"]
    assert "Traceback" not in result.stderr


def test_analyze_can_disable_knowledge(monkeypatch):
    monkeypatch.setenv("INTELLIREVIEW_DISABLE_KNOWLEDGE", "1")
    create_git_repo(REPO)

    result = run_cli(
        "analyze",
        REPO,
        "--json",
        env={"INTELLIREVIEW_DISABLE_KNOWLEDGE": "1"},
    )

    assert result.returncode == 0

    payload = json.loads(result.stdout)

    assert payload["status"] == "success"
    assert all(
        analyzer["analyzer_id"] != "knowledge"
        for analyzer in payload["analyzers"]
    )
