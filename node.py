from role import Role


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
