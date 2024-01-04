# DC Fabric Network Graph Generator

## Overview

This project provides a tool for generating network graphs for CLOS (Closed Loop Spine) fabric networks. It also facilitates the creation of diagrams illustrating the topology and configuration files for each node in the network. This is not a fully functional product at the moment; it is more of a proof of concept. I had some free time over a long weekend :)

## Prerequisites

In order to use it, you will need to install the following:

- NetworkX 
- Graphviz
- Pygraphviz (Python library)

## Features

- Retrieves global variables from etc/cfg.yml.
- Automatically allocates IP addresses and AS numbers.
- Parses a template from templates/switch.j2.
- Places rendered files in the diagrams/ and config/ directories.

## TODO
- Implement some network topology logic in the configuration file, as currently everything is in the Python code.
- Perform basic code cleanup to make it more readable.
- If you add more switches, the network diagram would "grow" horizontally. Implement vertical switch placement for better visibility.

Please let me know about any ideas you may have.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

