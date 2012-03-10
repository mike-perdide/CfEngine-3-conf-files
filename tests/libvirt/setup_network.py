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
from common import parse_cfg, is_defined_guest


def first_mac_address(conn, clone_name):
    machine = conn.lookupByName(clone_name)
    desc = machine.XMLDesc(0)

    tree = ElementTree.fromstring(desc)
    mac_element = tree.find("devices/interface/mac")
    return mac_element.get("address")


if __name__ == "__main__":
    if not len(sys.argv) == 2:
        print USAGE
        sys.exit(1)

    configfilepath = sys.argv[1]
    conn, machines_to_clone, cfg, xmlfilepath = parse_cfg(configfilepath)

    clone_names = dict([(orig, cfg.get(orig, "clone_name"))
                        for orig in machines_to_clone])

    # Ignore the undefined clone guests
    mac_addresses = [(orig, first_mac_address(conn, clone_names[orig]))
                     for orig in machines_to_clone
                     if is_defined_guest(conn, clone_names[orig])]

    tree = ElementTree.ElementTree()
    tree.parse(xmlfilepath)

    dhcp_section = tree.find("ip/dhcp")
    for orig_name, mac in mac_addresses:
        hostname = cfg.get(orig_name, "hostname")
        ip = cfg.get(orig_name, "ip")
        element = ElementTree.Element("host", {"mac": mac,
                                               "name": hostname,
                                               "ip": ip})
        dhcp_section.insert(0, element)

    netxml = ElementTree.tostring(tree.getroot())
    conn.networkCreateXML(netxml)
