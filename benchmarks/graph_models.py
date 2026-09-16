from __future__ import annotations

import json
import time

from analyzer.core.repository_loader import RepositoryLoader
from analyzer.dependency import DependencyRepositoryAnalyzer
from analyzer.symbol import SymbolRepositoryAnalyzer
from analyzer.call import CallRepositoryAnalyzer


def graph_stats(graph):
    stats = {
        "type": type(graph).__name__,
    }

    for attr in (
        "modules",
        "symbols",
        "references",
        "calls",
        "edges",
        "nodes",
    ):
        value = getattr(graph, attr, None)
        if value is not None:
            try:
                stats[attr] = len(value)
            except TypeError:
                pass

    for attr in (
        "module_count",
        "symbol_count",
        "reference_count",
        "call_count",
        "edge_count",
        "node_count",
        "resolved_call_count",
        "unresolved_call_count",
    ):
        value = getattr(graph, attr, None)
        if value is not None:
            stats[attr] = value

    return stats


def main():
    repository = RepositoryLoader().load(".")

    analyzers = [
        DependencyRepositoryAnalyzer(),
        SymbolRepositoryAnalyzer(),
        CallRepositoryAnalyzer(),
    ]

    results = {}

    for analyzer in analyzers:
        started = time.perf_counter()
        result = analyzer.analyze(repository)
        elapsed = time.perf_counter() - started

        graph_key = {
            "dependency": "dependency_graph",
            "symbol": "symbol_graph",
            "call": "call_graph",
        }[analyzer.metadata.analyzer_id]

        graph = result.artifacts.get(graph_key)

        entry = {
            "analyzer_id": analyzer.metadata.analyzer_id,
            "status": result.status.value,
            "elapsed_seconds": elapsed,
            "graph": graph_stats(graph),
            "artifacts": {},
        }

        for key, value in result.artifacts.items():
            if key == graph_key:
                continue

            if isinstance(value, (int, float, str, bool)) or value is None:
                entry["artifacts"][key] = value
            elif isinstance(value, (list, tuple, set, frozenset, dict)):
                entry["artifacts"][key] = len(value)

        results[analyzer.metadata.analyzer_id] = entry

    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
