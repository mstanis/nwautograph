#!/usr/bin/env python

import networkx as nx
from netaddr import IPNetwork, IPAddress
import yaml
import jinja2
from enum import Enum


class Role(Enum):
    SPINE = "spine"
    LEAF = "leaf"


class Node:
    def __init__(
        self, name: str, loopback: str, asn: str, interfaces: list, role: Role
    ):
        self.name = name
        self.loopback = loopback
        self.asn = asn
        self.interfaces = interfaces
        self.role = role
        self.ip_interfaces = {}
        self.bgp_neighbors = {}

    def get_interface(self) -> int:
        """Fetch first available interface in list"""
        return self.interfaces.pop(0)

    def generate(self) -> dict:
        """Generate arguments necessary to draw node"""
        label = f"{self.name}\n"
        label += f"lo0: {self.loopback}\n"
        label += f"as: {self.asn}\n"
        arguments = {
            "node_for_adding": self.name,
            "label": label,
            "hostname": self.name,
            "role": self.role.value,
            "shape": "box",
            "asn": self.asn,
            "int": self.interfaces,
            "if_ip": self.ip_interfaces,
            "constraint": "false",
            "fontsize": 10,
            "bgp_neigh": self.bgp_neighbors,
        }
        if self.role == Role.SPINE:
            arguments["fillcolor"] = "grey88"
            arguments["rank"] = "same; spine1; spine2; "
            arguments["style"] = "rounded,filled"
            arguments["tailport"] = "s"
        elif self.role == Role.LEAF:
            arguments["fillcolor"] = "honeydew2"
            arguments["headport"] = "s"
            arguments["style"] = "filled"

        return arguments

    def template(self):
        """Generate jinja template input"""
        return {
            "hostname": self.name,
            "asn": self.asn,
            "ip_interfaces": self.ip_interfaces,
            "bgp_neighbors": self.bgp_neighbors,
        }

    def connect(self):
        pass


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

    def generate(self) -> dict:
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


def main() -> None:
    # get configuration variables
    with open("etc/cfg.yml", "r") as cfg:
        config = yaml.load(cfg.read(), Loader=yaml.Loader)

    # create NetwrkX graph
    G = nx.DiGraph(label=config["dc_name"], ordering="out", fontsize=20, labelloc="t")

    """Generate lists of subnets"""
    loopbacks = list(IPNetwork(config["ip"]["loopbacks"]).subnet(32))
    subnets = list(IPNetwork(config["ip"]["fabric_ptp"]).subnet(31))

    """Generate list of interfaces/as-numbers [1, 2, 3, 4] from input '1-4' """
    spine_interfaces = get_range(config["spines"]["fabric_interfaces"])
    leaf_interfaces = get_range(config["leaves"]["fabric_interfaces"])
    bgp_as_numbers = get_range(config["ip"]["asn_range"])

    """Generate spine nodes"""
    spines = []
    for i in range(int(config["spines"]["number"])):
        spine = Node(
            name=f"spine{i + 1}",
            loopback=str(loopbacks.pop(0)),
            asn=str(bgp_as_numbers.pop(0)),
            interfaces=spine_interfaces.copy(),
            role=Role.SPINE,
        )
        spines.append(spine)

    """Generate leaf nodes"""
    leaves = []
    for i in range(int(config["leaves"]["number"])):
        leaf = Node(
            name=f"leaf{i + 1}",
            loopback=str(loopbacks.pop(0)),
            asn=str(bgp_as_numbers.pop(0)),
            interfaces=leaf_interfaces.copy(),
            role=Role.LEAF,
        )
        leaves.append(leaf)

    """Generate edges (links between nodes)"""
    edges = []
    for leaf in leaves:
        for spine in spines:
            subnet = subnets.pop(0)
            spine_if = spine.get_interface()
            leaf_if = leaf.get_interface()
            spine_ip = str(IPAddress(subnet.first))
            leaf_ip = str(IPAddress(subnet.last))
            spine_ip_last_octet = spine_ip.split(".")[-1]
            leaf_ip_last_octet = leaf_ip.split(".")[-1]

            spine.ip_interfaces[f"eth{spine_if}"] = f"{spine_ip}/31"
            leaf.ip_interfaces[f"eth{leaf_if}"] = f"{leaf_ip}/31"
            spine.bgp_neighbors[leaf_ip] = leaf.asn
            leaf.bgp_neighbors[spine_ip] = spine.asn

            spine_edge = EdgeNode(spine.name, spine_if, spine_ip_last_octet)
            leaf_edge = EdgeNode(leaf.name, leaf_if, leaf_ip_last_octet)
            edge = Edge(spine_edge, leaf_edge, subnet)
            edges.append(edge)

    for node in spines + leaves:
        G.add_node(node.name, **node.generate())

    for edge in edges:
        G.add_edge(**edge.generate())

    # draw master topology
    VG = nx.drawing.nx_agraph.to_agraph(G)
    VG.layout("dot")
    VG.draw("diagrams/topology.svg", format="svg")

    # draw leaf to spine relation
    for leaf in leaves:
        leaf_neighbors = list(G.predecessors(leaf.name))
        leaf_sub = leaf_neighbors + [leaf.name]
        L = G.subgraph(leaf_sub)
        L.nodes[leaf.name]["URL"] = f"../config/{leaf.name}.txt"
        for leaf_edge in L.edges:
            L.edges[leaf_edge]["label"] = L.edges[leaf_edge]["leaf_ptp"]
            L.edges[leaf_edge]["taillabel"] = L.edges[leaf_edge]["e_taillabel"]
            L.edges[leaf_edge]["headlabel"] = L.edges[leaf_edge]["e_headlabel"]

        LG = nx.drawing.nx_agraph.to_agraph(L)
        LG.layout("dot")
        nx.drawing.nx_agraph.write_dot(L, f"diagrams/{leaf.name}.dot")
        LG.draw(f"diagrams/{leaf.name}.svg", format="svg")

    """Generate node config"""
    for node in spines + leaves:
        with open("templates/switch.j2", "r") as file:
            template = jinja2.Template(file.read())

        with open(f"config/{node.name}.txt", "w") as file:
            file.write(template.render(node.template()))


def get_range(my_range: str) -> list:
    range_split = my_range.split("-")
    return list(range(int(range_split[0]), int(range_split[1]) + 1))


if __name__ == "__main__":
    main()
