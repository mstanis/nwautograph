import networkx as nx
from node import Node
from edge import Edge


class Graph:
    def __init__(
        self, label: str, spines: list[Node], leaves: list[Node], edges: list[Edge]
    ):
        self.label = label
        self.spines = spines
        self.leaves = leaves
        self.edges = edges

    def draw_topology(self):
        """Draw topology file"""
        self.graph = nx.DiGraph(
            label=self.label,
            ordering="out",
            fontsize=20,
            labelloc="t",
        )

        for node in self.spines + self.leaves:
            self.graph.add_node(**node.draw())

        for edge in self.edges:
            self.graph.add_edge(**edge.draw())

        VG = nx.drawing.nx_agraph.to_agraph(self.graph)
        VG.layout("dot")
        VG.draw("diagrams/topology.svg", format="svg")

    def draw_nodes(self):
        """Draw leaf to spine relation"""
        for leaf in self.leaves:
            leaf_neighbors = list(self.graph.predecessors(leaf.name))
            leaf_sub = leaf_neighbors + [leaf.name]
            L = self.graph.subgraph(leaf_sub)
            L.nodes[leaf.name]["URL"] = f"../config/{leaf.name}.txt"
            for leaf_edge in L.edges:
                L.edges[leaf_edge]["label"] = L.edges[leaf_edge]["leaf_ptp"]
                L.edges[leaf_edge]["taillabel"] = L.edges[leaf_edge]["e_taillabel"]
                L.edges[leaf_edge]["headlabel"] = L.edges[leaf_edge]["e_headlabel"]

            LG = nx.drawing.nx_agraph.to_agraph(L)
            LG.layout("dot")
            nx.drawing.nx_agraph.write_dot(L, f"diagrams/{leaf.name}.dot")
            LG.draw(f"diagrams/{leaf.name}.svg", format="svg")
