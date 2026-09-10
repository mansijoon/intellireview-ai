from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import analyzer.github_integration as github_integration
from analyzer.github_analyzer import clone_repository
from analyzer.github_integration import GitHubClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_github_client_requires_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    try:
        GitHubClient()
    except ValueError as exc:
        assert "GITHUB_TOKEN" in str(exc)
    else:
        raise AssertionError("GITHUB_TOKEN should be required")


def test_github_client_headers():
    client = GitHubClient(token="test-token")

    headers = client._headers()

    assert headers["Authorization"] == "Bearer test-token"
    assert headers["Accept"] == "application/vnd.github+json"
    assert headers["X-GitHub-Api-Version"] == "2022-11-28"


def test_get_pull_request(monkeypatch):
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs

        return FakeResponse(
            {
                "title": "Test PR",
                "head": {
                    "sha": "abc123",
                },
            }
        )

    monkeypatch.setattr(
        github_integration.requests,
        "get",
        fake_get,
    )

    client = GitHubClient(token="test-token")

    result = client.get_pull_request(
        "owner",
        "repo",
        42,
    )

    assert result.owner == "owner"
    assert result.repository == "repo"
    assert result.number == 42
    assert result.title == "Test PR"
    assert result.head_sha == "abc123"

    assert (
        captured["url"]
        == "https://api.github.com/repos/owner/repo/pulls/42"
    )
    assert captured["kwargs"]["timeout"] == 30


def test_get_pull_request_files(monkeypatch):
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs

        return FakeResponse(
            [
                {
                    "filename": "app.py",
                    "status": "modified",
                }
            ]
        )

    monkeypatch.setattr(
        github_integration.requests,
        "get",
        fake_get,
    )

    client = GitHubClient(token="test-token")

    result = client.get_pull_request_files(
        "owner",
        "repo",
        42,
    )

    assert result == [
        {
            "filename": "app.py",
            "status": "modified",
        }
    ]

    assert (
        captured["url"]
        == "https://api.github.com/repos/owner/repo/pulls/42/files"
    )
    assert captured["kwargs"]["params"] == {"per_page": 100}


def test_create_review_comment(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs

        return FakeResponse(
            {
                "id": 123,
            }
        )

    monkeypatch.setattr(
        github_integration.requests,
        "post",
        fake_post,
    )

    client = GitHubClient(token="test-token")

    result = client.create_review_comment(
        "owner",
        "repo",
        42,
        body="Test finding",
        commit_id="abc123",
        path="app.py",
        line=10,
    )

    assert result == {"id": 123}

    assert (
        captured["url"]
        == "https://api.github.com/repos/owner/repo/pulls/42/comments"
    )

    assert captured["kwargs"]["json"] == {
        "body": "Test finding",
        "commit_id": "abc123",
        "path": "app.py",
        "line": 10,
        "side": "RIGHT",
    }


def test_clone_repository(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"

    source.mkdir()

    subprocess = __import__("subprocess")

    subprocess.run(
        ["git", "init", str(source)],
        check=True,
        stdout=subprocess.DEVNULL,
    )

    (source / "README.md").write_text(
        "# Test repository\n",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "-C", str(source), "add", "."],
        check=True,
    )

    subprocess.run(
        [
            "git",
            "-C",
            str(source),
            "-c",
            "user.name=IntelliReview Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            "Initial commit",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )

    result = clone_repository(
        source.as_uri(),
        str(destination),
    )

    assert Path(result).resolve() == destination.resolve()
    assert (destination / "README.md").exists()
    assert (
        destination / "README.md"
    ).read_text(encoding="utf-8") == "# Test repository\n"
