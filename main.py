#!/usr/bin/env python

from netaddr import IPNetwork, IPAddress
from node import Node
from edge import Edge, EdgeNode
from graph import Graph
from role import Role
import yaml
import jinja2


def main() -> None:
    """The main function in the script, formatting data into Nodes and Edges"""

    # get configuration variables
    with open("etc/cfg.yml", "r") as cfg:
        config = yaml.load(cfg.read(), Loader=yaml.Loader)

    """Generate lists of subnets"""
    loopbacks = list(IPNetwork(config["ip"]["loopbacks"]).subnet(32))
    subnets = list(IPNetwork(config["ip"]["fabric_ptp"]).subnet(31))

    """Generate list of interfaces/as-numbers [1, 2, 3, 4] from input '1-4' """
    spine_interfaces = get_range(config["spines"]["fabric_interfaces"])
    leaf_interfaces = get_range(config["leaves"]["fabric_interfaces"])
    bgp_as_numbers = get_range(config["ip"]["asn_range"])

    """Create spine nodes"""
    spines: list[Node] = []
    for i in range(int(config["spines"]["number"])):
        spine = Node(
            name=f"spine{i + 1}",
            loopback=str(loopbacks.pop(0)),
            asn=str(bgp_as_numbers.pop(0)),
            interfaces=spine_interfaces.copy(),
            role=Role.SPINE,
        )
        spines.append(spine)

    """Create leaf nodes"""
    leaves: list[Node] = []
    for i in range(int(config["leaves"]["number"])):
        leaf = Node(
            name=f"leaf{i + 1}",
            loopback=str(loopbacks.pop(0)),
            asn=str(bgp_as_numbers.pop(0)),
            interfaces=leaf_interfaces.copy(),
            role=Role.LEAF,
        )
        leaves.append(leaf)

    """Create edges (links between nodes)"""
    edges: list[Edge] = []
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

    """Draw topology graph"""
    graph = Graph(config["dc_name"], spines, leaves, edges)
    graph.draw_topology()
    graph.draw_nodes()

    """Generate node config"""
    for node in spines + leaves:
        with open("templates/switch.j2", "r") as file:
            template = jinja2.Template(file.read())

        with open(f"config/{node.name}.txt", "w") as file:
            file.write(template.render(node.template_data()))


def get_range(my_range: str) -> list:
    range_split = my_range.split("-")
    return list(range(int(range_split[0]), int(range_split[1]) + 1))


if __name__ == "__main__":
    main()
