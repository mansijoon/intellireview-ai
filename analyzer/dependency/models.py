from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass
class ModuleNode:
    """
    Represents a single Python module in the repository.
    """

    name: str
    path: str

    # Internal project dependencies
    imports: Set[str] = field(default_factory=set)

    # Reverse dependencies
    imported_by: Set[str] = field(default_factory=set)

    # Third-party / standard library imports
    external_imports: Set[str] = field(default_factory=set)


@dataclass
class DependencyGraph:
    """
    Represents the dependency graph of the repository.
    """

    modules: Dict[str, ModuleNode] = field(default_factory=dict)

    def add_module(self, module: ModuleNode):
        self.modules[module.name] = module

    def get_module(self, name: str):
        return self.modules.get(name)

    def __contains__(self, module_name):
        return module_name in self.modules

    def __len__(self):
        return len(self.modules)
