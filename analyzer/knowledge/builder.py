from __future__ import annotations

from collections import defaultdict

from analyzer.core.repository_context import RepositoryContext
from analyzer.call import CallRepositoryAnalyzer
from analyzer.dependency import DependencyRepositoryAnalyzer
from analyzer.symbol import SymbolRepositoryAnalyzer
from analyzer.knowledge.models import (
    KnowledgeCall,
    KnowledgeDependency,
    KnowledgeFile,
    KnowledgeSymbol,
    RepositoryKnowledgeModel,
)


def _build_files(
    repository: RepositoryContext,
) -> tuple[KnowledgeFile, ...]:
    files = []

    for context in repository.iter_contexts():
        source = context.source

        files.append(
            KnowledgeFile(
                file_path=context.file_path,
                language=getattr(
                    context,
                    "language",
                    None,
                )
                or "unknown",
                size_bytes=len(
                    source.encode("utf-8")
                ),
                line_count=(
                    source.count("\n") + 1
                    if source
                    else 0
                ),
            )
        )

    return tuple(
        sorted(
            files,
            key=lambda item: item.file_path,
        )
    )


def _build_symbols(
    repository: RepositoryContext,
) -> tuple[KnowledgeSymbol, ...]:
    graph = repository.get_artifact(
        "symbol_graph"
    )

    if graph is None:
        result = repository.get_artifact(
            "symbol_analysis"
        )

        if result is not None:
            graph = result.artifacts.get(
                "symbol_graph"
            )

    if graph is None:
        return ()

    symbols = []

    for symbol in graph.symbols.values():
        symbols.append(
            KnowledgeSymbol(
                symbol_id=symbol.symbol_id,
                name=symbol.name,
                kind=symbol.kind,
                file_path=symbol.location.file_path,
                line_start=symbol.location.line_start,
                line_end=symbol.location.line_end,
                parent_symbol_id=symbol.parent_id,
            )
        )

    return tuple(
        sorted(
            symbols,
            key=lambda item: (
                item.file_path,
                item.line_start,
                item.symbol_id,
            ),
        )
    )


def _build_calls(
    repository: RepositoryContext,
) -> tuple[KnowledgeCall, ...]:
    graph = repository.get_artifact(
        "call_graph"
    )

    if graph is None:
        result = repository.get_artifact(
            "call_analysis"
        )

        if result is not None:
            graph = result.artifacts.get(
                "call_graph"
            )

    if graph is None:
        return ()

    calls = []

    for call in graph.calls:
        calls.append(
            KnowledgeCall(
                caller_symbol_id=call.caller_symbol_id,
                callee_symbol_id=call.callee_symbol_id,
                callee_name=call.callee_name,
                file_path=call.location.file_path,
                line_start=call.location.line_start,
                resolved=(
                    call.callee_symbol_id
                    is not None
                ),
            )
        )

    return tuple(
        sorted(
            calls,
            key=lambda item: (
                item.file_path,
                item.line_start,
                item.callee_name,
            ),
        )
    )


def _build_dependencies(
    repository: RepositoryContext,
) -> tuple[KnowledgeDependency, ...]:
    graph = repository.get_artifact(
        "dependency_graph"
    )

    if graph is None:
        result = repository.get_artifact(
            "dependency_analysis"
        )

        if result is not None:
            graph = result.artifacts.get(
                "dependency_graph"
            )

    if graph is None:
        return ()

    dependencies = []

    for module in graph.modules.values():
        for target in sorted(module.imports):
            dependencies.append(
                KnowledgeDependency(
                    source=module.name,
                    target=target,
                    dependency_type="internal",
                )
            )

        for target in sorted(
            module.external_imports
        ):
            dependencies.append(
                KnowledgeDependency(
                    source=module.name,
                    target=target,
                    dependency_type="external",
                )
            )

    return tuple(
        sorted(
            dependencies,
            key=lambda item: (
                item.source,
                item.target,
                item.dependency_type,
            ),
        )
    )


def _build_indexes(
    symbols: tuple[KnowledgeSymbol, ...],
    calls: tuple[KnowledgeCall, ...],
    dependencies: tuple[KnowledgeDependency, ...],
):
    symbol_by_id = {
        symbol.symbol_id: symbol
        for symbol in symbols
    }

    symbols_by_file = defaultdict(list)

    for symbol in symbols:
        symbols_by_file[
            symbol.file_path
        ].append(symbol.symbol_id)

    calls_by_caller = defaultdict(list)
    calls_by_callee = defaultdict(list)

    for call in calls:
        if call.caller_symbol_id:
            calls_by_caller[
                call.caller_symbol_id
            ].append(call)

        if call.callee_symbol_id:
            calls_by_callee[
                call.callee_symbol_id
            ].append(call)

    dependencies_by_source = defaultdict(list)
    dependencies_by_target = defaultdict(list)

    for dependency in dependencies:
        dependencies_by_source[
            dependency.source
        ].append(dependency)

        dependencies_by_target[
            dependency.target
        ].append(dependency)

    return (
        symbol_by_id,
        {
            key: tuple(value)
            for key, value in symbols_by_file.items()
        },
        {
            key: tuple(value)
            for key, value in calls_by_caller.items()
        },
        {
            key: tuple(value)
            for key, value in calls_by_callee.items()
        },
        {
            key: tuple(value)
            for key, value in dependencies_by_source.items()
        },
        {
            key: tuple(value)
            for key, value in dependencies_by_target.items()
        },
    )


def _ensure_knowledge_graphs(
    repository: RepositoryContext,
) -> None:
    # Knowledge construction must not depend on analyzer execution order.
    # Existing artifacts are reused; analyzers run only when required.

    dependency_graph = repository.get_artifact(
        "dependency_graph"
    )

    if dependency_graph is None:
        result = DependencyRepositoryAnalyzer().analyze(
            repository
        )

        if result.status.value != "success":
            raise RuntimeError(
                "Dependency analysis failed while building repository knowledge"
            )

    symbol_graph = repository.get_artifact(
        "symbol_graph"
    )

    if symbol_graph is None:
        result = SymbolRepositoryAnalyzer().analyze(
            repository
        )

        if result.status.value != "success":
            raise RuntimeError(
                "Symbol analysis failed while building repository knowledge"
            )

    call_graph = repository.get_artifact(
        "call_graph"
    )

    if call_graph is None:
        result = CallRepositoryAnalyzer().analyze(
            repository
        )

        if result.status.value != "success":
            raise RuntimeError(
                "Call analysis failed while building repository knowledge"
            )


def build_repository_knowledge(
    repository: RepositoryContext,
) -> RepositoryKnowledgeModel:
    _ensure_knowledge_graphs(repository)

    files = _build_files(repository)
    symbols = _build_symbols(repository)
    calls = _build_calls(repository)
    dependencies = _build_dependencies(repository)

    (
        symbol_by_id,
        symbols_by_file,
        calls_by_caller,
        calls_by_callee,
        dependencies_by_source,
        dependencies_by_target,
    ) = _build_indexes(
        symbols,
        calls,
        dependencies,
    )

    return RepositoryKnowledgeModel(
        repository_id=repository.repository_id,
        revision=repository.revision,
        files=files,
        symbols=symbols,
        calls=calls,
        dependencies=dependencies,
        symbol_by_id=symbol_by_id,
        symbols_by_file=symbols_by_file,
        calls_by_caller=calls_by_caller,
        calls_by_callee=calls_by_callee,
        dependencies_by_source=dependencies_by_source,
        dependencies_by_target=dependencies_by_target,
        metadata={
            "file_count": len(files),
            "symbol_count": len(symbols),
            "call_count": len(calls),
            "resolved_call_count": sum(
                call.resolved
                for call in calls
            ),
            "dependency_count": len(
                dependencies
            ),
        },
    )
