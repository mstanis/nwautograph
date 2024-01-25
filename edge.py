class EdgeNode:
    def __init__(self, name, interface, ip):
        """This represents the node at either side of an Edge"""
        self.name = name
        self.interface = interface
        self.ip = ip


class Edge:
    def __init__(self, spine: EdgeNode, leaf: EdgeNode, subnet: str):
        """This represents the edge between two nodes"""
        self.spine = spine
        self.leaf = leaf
        self.subnet = subnet

    def draw(self) -> dict:
        arguments = {
            "u_of_edge": self.spine.name,
            "v_of_edge": self.leaf.name,
            "decorate": "true",
            "leaf_ptp": self.subnet,
            "e_taillabel": f"e{self.spine.interface} ip: .{self.spine.ip}",
            "e_headlabel": f"e{self.leaf.interface} ip: .{self.leaf.ip}",
            "fontsize": 6,
            "arrowhead": "none",
        }
        return arguments
