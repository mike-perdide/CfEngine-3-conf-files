#!/usr/bin/env python
USAGE = """
SYNOPSIS
    setup_network.py config.cfg
DESCRIPTION

    The network is defined by a libvirt compatible xml file (see libvirt
    documentation for more specs). The xml declaration must contain an empty
    <dhcp></dhcp> declaration, it will be used to assign IP addresses and
    hostnames to the clones.
"""

import sys
from xml.etree import ElementTree
from common import parse_cfg


def net_name_from_xmlfile(xmlfilepath):
    tree = ElementTree.ElementTree()
    tree.parse(xmlfilepath)

    name_section = tree.find("name")
    return name_section.text


if not len(sys.argv) == 2:
    print USAGE
    sys.exit(1)

configfilepath = sys.argv[1]
conn, machines_to_clone, cfg, netxmlfilepath = parse_cfg(configfilepath)

net_name = net_name_from_xmlfile(netxmlfilepath)
net = conn.networkLookupByName(net_name)
net.destroy()
