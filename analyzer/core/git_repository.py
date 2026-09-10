from __future__ import annotations

from pathlib import Path

from git import BadName, Repo
from git.objects.commit import Commit


class GitRepository:
    """Read an exact committed repository tree without changing the worktree."""

    def __init__(self, root_path: str) -> None:
        root = Path(root_path).resolve()

        if not root.is_dir():
            raise NotADirectoryError(
                f"Repository path is not a directory: {root}"
            )

        try:
            self._repo = Repo(root, search_parent_directories=True)
        except Exception as exc:
            raise ValueError(
                f"Not a Git repository: {root}"
            ) from exc

    @property
    def root_path(self) -> Path:
        """Return the repository worktree root."""
        if self._repo.working_tree_dir is None:
            raise ValueError(
                "Git repository has no working tree."
            )

        return Path(self._repo.working_tree_dir).resolve()

    def resolve_revision(self, revision: str) -> str:
        """Resolve a Git revision expression to its full commit SHA."""
        if not revision.strip():
            raise ValueError(
                "revision must not be empty"
            )

        try:
            commit = self._repo.commit(revision)
        except (BadName, ValueError) as exc:
            raise ValueError(
                f"Invalid Git revision: {revision}"
            ) from exc

        return commit.hexsha

    def commit(self, revision: str) -> Commit:
        """Return the commit represented by a revision expression."""
        if not revision.strip():
            raise ValueError(
                "revision must not be empty"
            )

        try:
            return self._repo.commit(revision)
        except (BadName, ValueError) as exc:
            raise ValueError(
                f"Invalid Git revision: {revision}"
            ) from exc

    def list_files(
        self,
        revision: str,
    ) -> tuple[str, ...]:
        """Return all files present in the exact committed tree."""
        commit = self.commit(revision)

        paths: list[str] = []

        for item in commit.tree.traverse():
            if item.type == "blob":
                paths.append(item.path)

        return tuple(sorted(paths))

    def read_file(
        self,
        revision: str,
        relative_path: str,
    ) -> bytes:
        """Read a file directly from a committed tree."""
        if not relative_path.strip():
            raise ValueError(
                "relative_path must not be empty"
            )

        commit = self.commit(revision)

        try:
            blob = commit.tree / relative_path
        except KeyError as exc:
            raise FileNotFoundError(
                f"File does not exist at revision "
                f"{revision}: {relative_path}"
            ) from exc

        if blob.type != "blob":
            raise IsADirectoryError(
                f"Path is not a file at revision "
                f"{revision}: {relative_path}"
            )

        return blob.data_stream.read()
