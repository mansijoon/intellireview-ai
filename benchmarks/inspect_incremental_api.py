from analyzer.core.analyzer_defaults import create_default_analyzer_registry
from analyzer.core.repository_orchestrator import RepositoryAnalysisOrchestrator

registry = create_default_analyzer_registry()

print("ANALYZERS =", len(registry.create_analyzers()))

for analyzer in registry.create_analyzers():
    metadata = analyzer.metadata
    print(
        metadata.analyzer_id,
        "| source_sensitive=", metadata.source_sensitive,
        "| depends_on=", sorted(metadata.depends_on),
    )

print("\nORCHESTRATOR ATTRIBUTES:")
print([
    name
    for name in dir(RepositoryAnalysisOrchestrator)
    if not name.startswith("_")
])
