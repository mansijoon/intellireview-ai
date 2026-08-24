from __future__ import annotations

import argparse
import sys
from pathlib import Path

from analyzer.core import (
    RepositoryAnalysisOrchestrator,
    RepositoryLoader,
)
from analyzer.core.analyzer_defaults import (
    create_default_analyzer_registry,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="intellireview",
        description="Repository-scale IntelliReview analysis.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    analyze = subparsers.add_parser(
        "analyze",
        help="Analyze a repository.",
    )

    analyze.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository path.",
    )

    analyze.add_argument(
        "--repository-id",
        default=None,
        help="Repository identifier.",
    )

    analyze.add_argument(
        "--revision",
        default="working-tree",
        help="Repository revision identifier.",
    )

    analyze.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )

    return parser


def analyze_repository(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()

    if not root.is_dir():
        print(
            f"error: repository path does not exist: {root}",
            file=sys.stderr,
        )
        return 2

    repository_id = (
        args.repository_id
        or root.name
    )

    repository = RepositoryLoader().load(
        str(root),
        repository_id=repository_id,
        revision=args.revision,
    )

    registry = create_default_analyzer_registry()

    run = RepositoryAnalysisOrchestrator(
        registry
    ).analyze(repository)

    if args.json:
        import json

        analyzers = []

        for result in run.results:
            analyzers.append(
                {
                    "analyzer_id": result.analyzer_id,
                    "status": result.status.value,
                }
            )

        payload = {
            "repository_id": repository.repository_id,
            "revision": repository.revision,
            "status": run.status.value,
            "successful_count": run.successful_count,
            "analyzers": analyzers,
            "metadata": {
                "file_count": repository.file_count,
            },
        }

        print(
            json.dumps(
                payload,
                indent=2,
            )
        )

    else:
        print("===== IntelliReview =====")
        print(f"Repository: {repository.repository_id}")
        print(f"Revision:   {repository.revision}")
        print(f"Files:      {repository.file_count}")
        print()
        print(f"Status:     {run.status.value}")
        print(
            f"Successful: {run.successful_count}"
        )
        print()
        print("Analyzers:")

        for result in run.results:
            print(
                f"  {result.analyzer_id:<25}"
                f"{result.status.value}"
            )

    return (
        0
        if run.status.value == "success"
        else 1
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        return analyze_repository(args)

    parser.error(
        f"unknown command: {args.command}"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
