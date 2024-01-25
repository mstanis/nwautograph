#!/usr/bin/env python

import networkx as nx
from netaddr import IPNetwork, IPAddress
import yaml
import jinja2


def main() -> None:
    # get configuration variables
    with open("etc/cfg.yml", "r") as cfg:
        config = yaml.load(cfg.read(), Loader=yaml.Loader)

    # create NetwrkX graph
    G = nx.DiGraph(label=config["dc_name"], ordering="out", fontsize=20, labelloc="t")

    spines = []
    leaves = []

    """Generate lists of subnets"""
    loopbacks = list(IPNetwork(config["ip"]["loopbacks"]).subnet(32))
    subnets = list(IPNetwork(config["ip"]["fabric_ptp"]).subnet(31))

    """Generate list of interfaces/as-numbers [1, 2, 3, 4] from input '1-4' """
    spine_interfaces = get_range(config["spines"]["fabric_interfaces"])
    leaf_interfaces = get_range(config["leaves"]["fabric_interfaces"])
    bgp_as_numbers = get_range(config["ip"]["asn_range"])

    # add spines
    for i in range(1, int(config["spines"]["number"]) + 1):
        spine_name = "spine" + str(i)
        spine_loopback = str(loopbacks.pop(0))
        spine_as = str(bgp_as_numbers.pop(0))

        G.add_node(
            spine_name,
            label=generate_label(spine_name, spine_loopback, spine_as),
            hostname=spine_name,
            role="spine",
            shape="box",
            asn=spine_as,
            style="rounded,filled",
            int=spine_interfaces.copy(),
            if_ip={},
            constraint="false",
            rank="same; spine1; spine2; ",
            tailport="s",
            fontsize=10,
            bgp_neigh={},
            fillcolor="grey88",
        )
        spines.append(spine_name)

    # add leaves
    for i in range(1, int(config["leaves"]["number"]) + 1):
        leaf_name = "leaf" + str(i)
        leaf_loopback = str(loopbacks.pop(0))
        leaf_as = str(bgp_as_numbers.pop(0))

        G.add_node(
            leaf_name,
            label=generate_label(leaf_name, leaf_loopback, leaf_as),
            hostname=leaf_name,
            role="leaf",
            shape="box",
            style="filled",
            int=leaf_interfaces.copy(),
            if_ip={},
            bgp_neigh={},
            URL=f"{leaf_name}.svg",
            headport="s",
            asn=leaf_as,
            fontsize=10,
            fillcolor="honeydew2",
        )
        leaves.append(leaf_name)

    # connect leaves to spines
    for leaf in leaves:
        for sp in spines:
            ptp = subnets.pop(0)
            spine_if = G.nodes[sp]["int"].pop(0)
            leaf_if = G.nodes[leaf]["int"].pop(0)
            spine_ip = str(IPAddress(ptp.first)) + "/31"
            leaf_ip = str(IPAddress(ptp.last)) + "/31"
            G.nodes[sp]["if_ip"].update({"eth" + str(spine_if): spine_ip})
            G.nodes[leaf]["if_ip"].update({"eth" + str(leaf_if): leaf_ip})
            G.nodes[sp]["bgp_neigh"].update(
                {leaf_ip.split("/")[0]: G.nodes[leaf]["asn"]}
            )
            G.nodes[leaf]["bgp_neigh"].update(
                {spine_ip.split("/")[0]: G.nodes[sp]["asn"]}
            )
            spine_ip_last_octet = spine_ip.split("/")[0].split(".")[-1]
            leaf_ip_last_octet = leaf_ip.split("/")[0].split(".")[-1]
            G.add_edge(
                sp,
                leaf,
                leaf_ptp=ptp,
                decorate="true",
                e_taillabel=f"e{spine_if} ip: .{spine_ip_last_octet}",
                e_headlabel=f"e{leaf_if} ip: .{leaf_ip_last_octet}",
                fontsize=6,
                arrowhead="none",
            )

    # draw master topology
    VG = nx.drawing.nx_agraph.to_agraph(G)
    VG.layout("dot")
    VG.draw("diagrams/topology.svg", format="svg")

    # draw leaf to spine relation
    for leaf in leaves:
        leaf_neighbors = list(G.predecessors(leaf))
        leaf_sub = leaf_neighbors + [leaf]
        L = G.subgraph(leaf_sub)
        L.nodes[leaf]["URL"] = f"../config/{leaf}.txt"
        for leaf_edge in L.edges:
            L.edges[leaf_edge]["label"] = L.edges[leaf_edge]["leaf_ptp"]
            L.edges[leaf_edge]["taillabel"] = L.edges[leaf_edge]["e_taillabel"]
            L.edges[leaf_edge]["headlabel"] = L.edges[leaf_edge]["e_headlabel"]

        LG = nx.drawing.nx_agraph.to_agraph(L)
        LG.layout("dot")
        nx.drawing.nx_agraph.write_dot(L, f"diagrams/{leaf}.dot")
        LG.draw(f"diagrams/{leaf}.svg", format="svg")

    # Parse Jinja2 template and save configuration for each node
    for sw in G.nodes:
        t_vars = G.nodes[sw]
        with open("templates/switch.j2", "r") as template_f:
            templ = jinja2.Template(template_f.read())

        with open("config/" + sw + ".txt", "w") as config_o:
            config_o.write(templ.render(t_vars))


def get_range(my_range: str) -> list:
    range_split = my_range.split("-")
    return list(range(int(range_split[0]), int(range_split[1]) + 1))


def generate_label(name: str, loopback: str, asn: str) -> str:
    label = f"{name}\n"
    label += f"lo0: {loopback}\n"
    label += f"as: {asn}\n"
    return label


if __name__ == "__main__":
    main()
