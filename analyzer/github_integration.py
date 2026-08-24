from __future__ import annotations

import os
from dataclasses import dataclass

import requests


@dataclass(frozen=True, slots=True)
class GitHubPullRequest:
    owner: str
    repository: str
    number: int
    title: str
    head_sha: str


class GitHubClient:
    """Minimal GitHub API client for IntelliReview PR integration."""

    def __init__(
        self,
        token: str | None = None,
    ) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")

        if not self.token:
            raise ValueError(
                "GITHUB_TOKEN is required"
            )

        self.base_url = "https://api.github.com"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_pull_request(
        self,
        owner: str,
        repository: str,
        number: int,
    ) -> GitHubPullRequest:
        response = requests.get(
            (
                f"{self.base_url}/repos/"
                f"{owner}/{repository}/pulls/{number}"
            ),
            headers=self._headers(),
            timeout=30,
        )

        response.raise_for_status()

        payload = response.json()

        return GitHubPullRequest(
            owner=owner,
            repository=repository,
            number=number,
            title=payload["title"],
            head_sha=payload["head"]["sha"],
        )

    def get_pull_request_files(
        self,
        owner: str,
        repository: str,
        number: int,
    ) -> list[dict]:
        response = requests.get(
            (
                f"{self.base_url}/repos/"
                f"{owner}/{repository}/pulls/{number}/files"
            ),
            headers=self._headers(),
            params={"per_page": 100},
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def create_review_comment(
        self,
        owner: str,
        repository: str,
        number: int,
        *,
        body: str,
        commit_id: str,
        path: str,
        line: int,
    ) -> dict:
        response = requests.post(
            (
                f"{self.base_url}/repos/"
                f"{owner}/{repository}/pulls/"
                f"{number}/comments"
            ),
            headers=self._headers(),
            json={
                "body": body,
                "commit_id": commit_id,
                "path": path,
                "line": line,
                "side": "RIGHT",
            },
            timeout=30,
        )

        response.raise_for_status()

        return response.json()
