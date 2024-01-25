#!/usr/bin/env python

import networkx as nx
from netaddr import IPNetwork, IPAddress
import yaml
import jinja2

def main():

    # get configuration variables
    with open('etc/cfg.yml', 'r') as cfg:
        config = yaml.load(cfg.read(), Loader=yaml.Loader)

    # create NetwrkX graph
    G = nx.DiGraph(label=config['dc_name'], ordering='out', fontsize=20,
                labelloc='t')


    spines = []
    leaves = []

    # generate IP and ASN
    loopbacks = list(IPNetwork(config['ip']['loopbacks']).subnet(32))
    f_ptp_subnet = list(IPNetwork(config['ip']['fabric_ptp']).subnet(31))

    f_if_range_spine = config['spines']['fabric_interfaces'].split('-')
    f_if_list_spine = list(range(int(f_if_range_spine[0]),
                        int(f_if_range_spine[1])+1))

    f_if_range_leaf = config['leaves']['fabric_interfaces'].split('-')
    f_if_list_leaf = list(range(int(f_if_range_leaf[0]),
                        int(f_if_range_leaf[1])+1))

    f_asn_range = config['ip']['asn_range'].split('-')
    f_asn_list = list(range(int(f_asn_range[0]), int(f_asn_range[1])+1))

    # add spines
    for i in range(1, int(config['spines']['number'])+1):
        s_name = 'spine' + str(i)
        s_loopback = str(loopbacks.pop(0))
        s_as = str(f_asn_list.pop(0))

        G.add_node(s_name, label=s_name + '\nlo0: ' + s_loopback + '\nAS:' + s_as,
                hostname=s_name, role='spine', shape='box', asn=s_as,
                style='rounded,filled', f_int=f_if_list_spine.copy(),
                f_if_ip={}, constraint='false',
                rank='same; spine1; spine2; ', tailport='s', fontsize=10,
                bgp_neigh={}, fillcolor='grey88')
        spines.append(s_name)

    # add leaves
    for i in range(1, int(config['leaves']['number'])+1):
        l_name = 'leaf' + str(i)
        l_loopback = str(loopbacks.pop(0))
        l_as = str(f_asn_list.pop(0))
        G.add_node(l_name, label=l_name + '\nlo0: ' + l_loopback + '\nAS: ' + l_as,
                hostname=l_name, role='leaf', shape='box', style='filled',
                f_int=f_if_list_leaf.copy(), f_if_ip={}, bgp_neigh={},
                URL=l_name + '.svg', headport='s', asn=l_as,
                fontsize=10, fillcolor='honeydew2')
        leaves.append(l_name)

    # connect leaves to spines
    for leaf in leaves:
        for sp in spines:
            f_ptp = f_ptp_subnet.pop(0)
            spine_if = G.nodes[sp]['f_int'].pop(0)
            leaf_if = G.nodes[leaf]['f_int'].pop(0)
            spine_ip = str(IPAddress(f_ptp.first)) + '/31'
            leaf_ip = str(IPAddress(f_ptp.last)) + '/31'
            G.nodes[sp]['f_if_ip'].update({'eth'+str(spine_if): spine_ip})
            G.nodes[leaf]['f_if_ip'].update({'eth'+str(leaf_if): leaf_ip})
            G.nodes[sp]['bgp_neigh'].update({leaf_ip.split('/')[0]:
                                            G.nodes[leaf]['asn']})
            G.nodes[leaf]['bgp_neigh'].update({spine_ip.split('/')[0]:
                                            G.nodes[sp]['asn']})
            G.add_edge(sp, leaf, l_ptp=f_ptp, decorate='true',
                    e_taillabel='e' + str(spine_if) + ' ip: .' +
                    spine_ip.split('/')[0].split('.')[-1],
                    e_headlabel='e' + str(leaf_if) + ' ip: .' +
                    leaf_ip.split('/')[0].split('.')[-1],
                    fontsize=6, arrowhead='none')

    # draw master topology
    VG = nx.drawing.nx_agraph.to_agraph(G)
    VG.layout('dot')
    VG.draw('diagrams/topology.svg', format='svg')


    # draw leaf to spine relation
    for le in leaves:
        l_neighbors = list(G.predecessors(le))
        l_sub = l_neighbors + [le]
        L = G.subgraph(l_sub)
        L.nodes[le]['URL'] = '../config/' + le + '.txt'
        for l_edge in L.edges:
            L.edges[l_edge]['label'] = L.edges[l_edge]['l_ptp']
            L.edges[l_edge]['taillabel'] = L.edges[l_edge]['e_taillabel']
            L.edges[l_edge]['headlabel'] = L.edges[l_edge]['e_headlabel']

        LG = nx.drawing.nx_agraph.to_agraph(L)
        LG.layout('dot')
        nx.drawing.nx_agraph.write_dot(L, 'diagrams/' + le + '.dot')
        LG.draw('diagrams/' + le + '.svg', format='svg')

    # Parse Jinja2 template and save configuration for each node
    for sw in G.nodes:
        t_vars = G.nodes[sw]
        with open('templates/switch.j2', 'r') as template_f:
            templ = jinja2.Template(template_f.read())

        with open('config/' + sw + '.txt', 'w') as config_o:
            config_o.write(templ.render(t_vars))

if __name__ == "__main__":
    main()