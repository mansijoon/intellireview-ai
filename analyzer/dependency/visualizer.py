from pyvis.network import Network

from analyzer.dependency.models import DependencyGraph


def build_dependency_visualization(
    graph: DependencyGraph,
):
    """
    Creates an interactive dependency graph using PyVis.

    Returns:
        pyvis.network.Network
    """

    net = Network(
        height="750px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="black"
    )

    net.barnes_hut()

    # Add nodes
    for module_name in graph.modules:

        net.add_node(
            module_name,
            label=module_name,
            title=module_name,
            shape="box"
        )

    # Add edges
    for module_name, module in graph.modules.items():

        for dependency in module.imports:

            if dependency in graph.modules:

                net.add_edge(
                    module_name,
                    dependency
                )

    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -2500,
          "centralGravity": 0.2,
          "springLength": 150,
          "springConstant": 0.05
        },
        "minVelocity": 0.75
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "keyboard": true
      },
      "nodes": {
        "font": {
          "size": 16
        }
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true
          }
        },
        "smooth": true
      }
    }
    """)

    return net
