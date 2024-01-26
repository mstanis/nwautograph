# DC Fabric Network Graph Generator

## Overview

This project provides a tool for generating network graphs for CLOS (Closed Loop Spine) fabric networks. It also facilitates the creation of diagrams illustrating the topology and configuration files for each node in the network. This is not a fully functional product at the moment; it is more of a proof of concept. I just had some free time over a long weekend :)

## Prerequisites

In order to use it, you will need to install the following:

- NetworkX 
- Graphviz
- Pygraphviz (Python library)

Install the prerequisites using the following command:
```
$ python -m venv venv
$ source venv/bin/activate
(venv) $ pip install --upgrade pip
(venv) $ pip install -r requirements.txt
```
*You may need to install additional pygraphviz packages*

## Features

- Retrieves global variables from `etc/cfg.yml`.
- Automatically allocates IP addresses and AS numbers.
- Parses a template from `templates/switch.j2`.
- Places rendered files in the diagrams/ and `config/` directories.
- Leaves are 'clickable' in SVG files; however, Github will not display links in the preview mode. Pleae clone the repository locally or right-click on `topology.svg` preview and select "Open image in new tab" 

## TODO
- Implement some network topology logic in the configuration file, as currently everything is in the Python code.
- Exception condition handling;
- add a concept of PODs and DC aggregation switches
- Perform basic code cleanup to make it more readable.
- If you add more switches, the network diagram would "grow" horizontally. Implement vertical switch placement for better visibility.


This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Please let me know about any ideas you may have or buy me a cup of double Espresso if you find this project is usefull :-)
