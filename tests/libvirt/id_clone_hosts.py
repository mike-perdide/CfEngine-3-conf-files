#!/usr/bin/env python
USAGE = """
SYNOPSIS
    id_clone_hosts.py config.cfg
DESCRIPTION
    The config file given in parameter should specify the IP of the libvirt
    host and the name of the virtual machines that must be cloned in the 
    following fashion:

        [virt_host]
            server=192.168.0.110
            network_definition=network.xml

        [MASTER-cfengine-hub]
            clone_name=cfengine-hub
            hostname=cfhub
            ip=192.168.1.1
        
        [MASTER-cfengine-client]
            clone_name=cfengine-client
            hostname=cfclient
            ip=192.168.1.1

    This command performs identical cloning of virtual machines for test
    purposes. The cloned machine will have the same hardware configuration as
    the original machine.

    The network is defined by a libvirt compatible xml file (see libvirt
    documentation for more specs). The xml declaration must contain an empty
    <dhcp></dhcp> declaration, it will be used to assign IP addresses and
    hostnames to the clones.

    To avoid having two identifical machines running at the same time, the
    program will stop if the original machine is running."""

import sys
import libvirt
import ConfigParser
from xml.etree import ElementTree
from virtinst.CloneManager import CloneDesign, start_duplicate, \
                                  generate_clone_disk_path


def parse_cfg(filepath):
    config = ConfigParser.ConfigParser()
    config.read(filepath)

    virt_host = config.get("virt_host", "server")

    conn = libvirt.open("qemu+ssh://%s/system" % virt_host)
    if conn == None:
        print "Failed to open connection to the hypervisor"
        sys.exit(1)

    machines_to_clone = set(config.sections()) - set(["virt_host"])
    available_machines = conn.listDefinedDomains()

    for machine in machines_to_clone:
        if machine not in available_machines:
            print machine, "is not amongst the avalaible virtual machines."
            print "Please check below:"
            print available_machines

            sys.exit(2)

        if conn.lookupByName(machine).isActive():
            print machine, "is running. Aborting to avoid mac collision."
            sys.exit(3)

    return conn, machines_to_clone, config


def clone(conn, guest_name, cfg):
    clone_mgr = CloneDesign(conn=conn)
    print "guest_name", guest_name
    clone_mgr.original_guest = guest_name
    clone_mgr.setup_original()

    clone_mgr.clone_name = cfg.get(guest_name, "clone_name")

    new_disk_paths = []
    for disk in clone_mgr.get_original_devices():
        new_disk_paths.append(generate_clone_disk_path(disk, clone_mgr))

    clone_mgr.set_clone_devices(new_disk_paths)
    clone_mgr.setup_clone()

    start_duplicate(clone_mgr)


def first_mac_address(conn, clone_name):
    machine = conn.lookupByName(clone_name)
    desc = machine.XMLDesc(0)

    tree = ElementTree.fromstring(desc)
    mac_element = tree.find("devices/interface/mac")
    return mac_element.get("address")


def setup_network(conn, machines_to_clone):
    mac_addresses = [(orig, first_mac_address(conn,
                                              cfg.get(orig, "clone_name")))
                     for orig in machines_to_clone]
    xmlfilepath = cfg.get("virt_host", "network_definition")

    tree = ElementTree.ElementTree()
    tree.parse(xmlfilepath)

    dhcp_section = tree.find("ip/dhcp")
    for orig_name, mac in mac_addresses:
        hostname = cfg.get(orig_name, "hostname")
        ip = cfg.get(orig_name, "ip")
        element = ElementTree.Element("host", { "mac": mac,
                                                "name": hostname,
                                                "ip": ip})
        dhcp_section.insert(0, element)

    netxml = ElementTree.tostring(tree.getroot())
    conn.networkCreateXML(netxml)


if __name__ == "__main__":
#    if not len(argv) == 2:
#        print USAGE
#        sys.exit(1)

    conn, machines_to_clone, cfg = parse_cfg("config.cfg")

    # Clone the machines
    for machine in machines_to_clone:
        clone(conn, machine, cfg)

    # Setup the dhcp parameters
    setup_network(conn, machines_to_clone)

    # Start the cloned machines
    for orig in machines_to_clone:
        clone_name = cfg.get(orig, "clone_name")
        clone_guest = conn.lookupByName(clone_name)
        clone_guest.create()
