from analyzer.github_integration import (
    GitHubClient,
    GitHubPullRequest,
)


def test_github_pull_request_model():
    pull_request = GitHubPullRequest(
        owner="example",
        repository="repo",
        number=42,
        title="Improve analyzer",
        head_sha="abc123",
    )

    assert pull_request.owner == "example"
    assert pull_request.repository == "repo"
    assert pull_request.number == 42
    assert pull_request.head_sha == "abc123"


def test_github_client_requires_token(monkeypatch):
    monkeypatch.delenv(
        "GITHUB_TOKEN",
        raising=False,
    )

    try:
        GitHubClient()
    except ValueError as exc:
        assert "GITHUB_TOKEN" in str(exc)
    else:
        raise AssertionError(
            "GitHubClient should require a token"
        )
