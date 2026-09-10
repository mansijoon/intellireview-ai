from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from analyzer.baseline import (
    compare_current_run,
    compare_revisions,
    create_baseline,
)
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

    parser.add_argument(
        "--version",
        action="version",
        version="intellireview 2.0.0",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    _add_analyze_parser(subparsers)
    _add_baseline_parser(subparsers)
    _add_compare_parser(subparsers)

    return parser


def _add_analyze_parser(
    subparsers: argparse._SubParsersAction,
) -> None:
    analyze = subparsers.add_parser(
        "analyze",
        help="Analyze a repository.",
    )

    _add_repository_arguments(analyze)

    analyze.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )

    analyze.add_argument(
        "--baseline",
        action="store_true",
        help="Compare analysis against the stored baseline.",
    )


def _add_baseline_parser(
    subparsers: argparse._SubParsersAction,
) -> None:
    baseline = subparsers.add_parser(
        "baseline",
        help="Create or compare an analysis baseline.",
    )

    baseline_subparsers = baseline.add_subparsers(
        dest="baseline_command",
        required=True,
    )

    create = baseline_subparsers.add_parser(
        "create",
        help="Create a baseline from repository analysis.",
    )
    _add_repository_arguments(create)

    create.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )

    compare = baseline_subparsers.add_parser(
        "compare",
        help="Compare repository analysis against the baseline.",
    )
    _add_repository_arguments(compare)

    compare.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )


def _add_compare_parser(
    subparsers: argparse._SubParsersAction,
) -> None:
    compare = subparsers.add_parser(
        "compare",
        help="Analyze and compare two Git revisions.",
    )

    _add_repository_arguments(compare)

    compare.add_argument(
        "--from",
        dest="from_revision",
        required=True,
        help="Starting Git revision.",
    )

    compare.add_argument(
        "--to",
        dest="to_revision",
        required=True,
        help="Ending Git revision.",
    )

    compare.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )


def _add_repository_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository path.",
    )

    parser.add_argument(
        "--repository-id",
        default=None,
        help="Repository identifier.",
    )

    parser.add_argument(
        "--revision",
        default="working-tree",
        help="Repository revision identifier.",
    )


def _load_repository(
    path: str,
    repository_id: str | None,
    revision: str,
):
    root = Path(path).resolve()

    if not root.is_dir():
        print(
            f"error: repository path does not exist: {root}",
            file=sys.stderr,
        )
        return None, root

    repository = RepositoryLoader().load(
        str(root),
        repository_id=repository_id or root.name,
        revision=revision,
    )

    return repository, root


def _analyze_repository(repository):
    registry = create_default_analyzer_registry()

    if os.getenv("INTELLIREVIEW_DISABLE_KNOWLEDGE") == "1":
        registry.disable("knowledge")

    return RepositoryAnalysisOrchestrator(
        registry
    ).analyze(repository)


def _analyze_args(
    args: argparse.Namespace,
):
    repository, root = _load_repository(
        args.path,
        args.repository_id,
        args.revision,
    )

    if repository is None:
        return None, root, None

    run = _analyze_repository(repository)

    return repository, root, run


def _serialize_analyzers(run) -> list[dict[str, str]]:
    return [
        {
            "analyzer_id": result.analyzer_id,
            "status": result.status.value,
        }
        for result in run.results
    ]


def _serialize_analysis(
    repository,
    run,
    comparison=None,
) -> dict:
    payload = {
        "repository_id": repository.repository_id,
        "revision": repository.revision,
        "status": run.status.value,
        "successful_count": run.successful_count,
        "analyzers": _serialize_analyzers(run),
        "metadata": {
            "file_count": repository.file_count,
        },
    }

    if comparison is not None:
        payload["baseline"] = comparison.to_dict()

    return payload


def _print_analysis(
    repository,
    run,
    comparison=None,
) -> None:
    print("===== IntelliReview =====")
    print(f"Repository: {repository.repository_id}")
    print(f"Revision:   {repository.revision}")
    print(f"Files:      {repository.file_count}")
    print()
    print(f"Status:     {run.status.value}")
    print(f"Successful: {run.successful_count}")
    print()
    print("Analyzers:")

    for result in run.results:
        print(
            f"  {result.analyzer_id:<25}"
            f"{result.status.value}"
        )

    if comparison is not None:
        _print_baseline_summary(comparison)


def _print_baseline_summary(comparison) -> None:
    print()
    print("===== Baseline =====")
    print(f"Baseline:   {comparison.baseline_revision}")
    print(f"New:        {comparison.new_count}")
    print(f"Resolved:   {comparison.resolved_count}")
    print(f"Unchanged:  {comparison.unchanged_count}")
    print(
        "Regression: "
        + ("YES" if comparison.has_regressions else "NO")
    )


def _compare_run_against_baseline(
    run,
    root: Path,
):
    return compare_current_run(
        run,
        str(root),
    )


def analyze_repository(
    args: argparse.Namespace,
) -> int:
    try:
        repository, root, run = _analyze_args(args)
    except Exception as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "error": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print(
                f"error: {exc}",
                file=sys.stderr,
            )
        return 1

    if repository is None:
        return 2

    comparison = None

    if args.baseline:
        try:
            comparison = _compare_run_against_baseline(
                run,
                root,
            )
        except Exception as exc:
            if args.json:
                print(
                    json.dumps(
                        {
                            "status": "failed",
                            "error": str(exc),
                        },
                        indent=2,
                    )
                )
            else:
                print(
                    f"error: {exc}",
                    file=sys.stderr,
                )
            return 1

    if args.json:
        print(
            json.dumps(
                _serialize_analysis(
                    repository,
                    run,
                    comparison,
                ),
                indent=2,
            )
        )
    else:
        _print_analysis(
            repository,
            run,
            comparison,
        )

    if run.status.value != "success":
        return 1

    if comparison is not None and comparison.has_regressions:
        return 1

    return 0


def create_baseline_command(
    args: argparse.Namespace,
) -> int:
    try:
        repository, root, run = _analyze_args(args)
    except Exception as exc:
        if getattr(args, "json", False):
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "error": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print(
                f"error: {exc}",
                file=sys.stderr,
            )
        return 1

    if repository is None:
        return 2

    if run.status.value != "success":
        print(
            f"error: repository analysis failed: "
            f"{run.status.value}",
            file=sys.stderr,
        )
        return 1

    baseline = create_baseline(
        run,
        str(root),
    )

    print("===== IntelliReview Baseline =====")
    print(f"Repository: {baseline.repository_id}")
    print(f"Revision:   {baseline.revision}")
    print(f"Findings:   {len(baseline.findings)}")
    print("Status:     created")

    return 0


def compare_baseline_command(
    args: argparse.Namespace,
) -> int:
    try:
        repository, root, run = _analyze_args(args)
    except Exception as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "error": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print(
                f"error: {exc}",
                file=sys.stderr,
            )
        return 1

    if repository is None:
        return 2

    if run.status.value != "success":
        print(
            f"error: repository analysis failed: "
            f"{run.status.value}",
            file=sys.stderr,
        )
        return 1

    try:
        comparison = _compare_run_against_baseline(
            run,
            root,
        )
    except Exception as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "error": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print(
                f"error: {exc}",
                file=sys.stderr,
            )
        return 1

    if args.json:
        print(
            json.dumps(
                comparison.to_dict(),
                indent=2,
            )
        )
    else:
        _print_comparison(comparison)

    return 1 if comparison.has_regressions else 0


def compare_revisions_command(
    args: argparse.Namespace,
) -> int:
    try:
        comparison = compare_revisions(
            args.path,
            from_revision=args.from_revision,
            to_revision=args.to_revision,
            repository_id=args.repository_id,
        )
    except Exception as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "error": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print(
                f"error: {exc}",
                file=sys.stderr,
            )
        return 1

    if args.json:
        print(
            json.dumps(
                comparison.to_dict(),
                indent=2,
            )
        )
    else:
        print("===== IntelliReview Commit Comparison =====")
        print(f"Repository: {comparison.repository_id}")
        print(f"From:       {comparison.baseline_revision}")
        print(f"To:         {comparison.current_revision}")
        print()
        print(f"New:        {comparison.new_count}")
        print(f"Resolved:   {comparison.resolved_count}")
        print(f"Unchanged:  {comparison.unchanged_count}")
        print()
        print(
            "Regression: "
            + ("YES" if comparison.has_regressions else "NO")
        )

    return 1 if comparison.has_regressions else 0


def _print_comparison(comparison) -> None:
    print("===== IntelliReview Baseline Comparison =====")
    print(f"Repository: {comparison.repository_id}")
    print(f"Baseline:   {comparison.baseline_revision}")
    print(f"Current:    {comparison.current_revision}")
    print()
    print(f"New:        {comparison.new_count}")
    print(f"Resolved:   {comparison.resolved_count}")
    print(f"Unchanged:  {comparison.unchanged_count}")
    print()
    print(
        "Regression: "
        + ("YES" if comparison.has_regressions else "NO")
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        return analyze_repository(args)

    if args.command == "compare":
        return compare_revisions_command(args)

    return _dispatch_baseline_command(
        parser,
        args,
    )


def _dispatch_baseline_command(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> int:
    if args.command != "baseline":
        parser.error(
            f"unknown command: {args.command}"
        )

    if args.baseline_command == "create":
        return create_baseline_command(args)

    if args.baseline_command == "compare":
        return compare_baseline_command(args)

    parser.error(
        f"unknown baseline command: "
        f"{args.baseline_command}"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
