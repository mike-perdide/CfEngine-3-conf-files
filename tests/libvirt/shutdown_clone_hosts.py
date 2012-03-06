#!/usr/bin/env python
USAGE = """
SYNOPSIS
    shutdown_clone_hosts.py config.cfg
DESCRIPTION
    This script undoes everything id_clone_hosts did, using the same .cfg and
    .xml files.

    Please refer to the id_clone_hosts help for more information."""
import sys
import libvirt
import ConfigParser
from xml.etree import ElementTree

from id_clone_hosts import parse_cfg


def net_name_from_xmlfile(xmlfilepath):
    tree = ElementTree.ElementTree()
    tree.parse(xmlfilepath)

    name_section = tree.find("name")
    return name_section.text


def pool_storage_path_from_name(conn, pool_name):
    pool = conn.storagePoolLookupByName(pool_name)

    root = ElementTree.fromstring(pool.XMLDesc(0))
    tree = ElementTree.ElementTree(element=root)
    name_section = tree.find("target/path")

    return name_section.text


def disk_path_from_guest_name(conn, clone_name):
    guest = conn.lookupByName(clone_name)

    root = ElementTree.fromstring(guest.XMLDesc(0))
    tree = ElementTree.ElementTree(element=root)
    disk_sections = tree.findall("devices/disk")

    for disk in disk_sections:
        if disk.attrib["device"] == "disk":
            return disk.find("source").attrib["file"]

def remove_all_disks(conn, storage_paths, disks_to_remove):
    for disk in disks_to_remove:
        for name, path in storage_paths:
            if path in disk:
                pool = conn.storagePoolLookupByName(name)
                storage_name = disk.split(path + "/")[1]
                pool.storageVolLookupByName(storage_name).delete(0)


if __name__ == "__main__":
    if not len(sys.argv) == 2:
        print USAGE
        sys.exit(1)

    conn, machines_to_clone, cfg = parse_cfg(sys.argv[1])
    storage_paths = [(name, pool_storage_path_from_name(conn, name))
                     for name in conn.listStoragePools()]

    print storage_paths

    disks_to_remove = [
        disk_path_from_guest_name(conn, cfg.get(orig_name, "clone_name"))
        for orig_name in machines_to_clone]

    for orig in machines_to_clone:
        clone_name = cfg.get(orig, "clone_name")
        clone_guest = conn.lookupByName(clone_name)
        clone_guest.destroy()
        clone_guest.undefine()

    net_file = cfg.get("virt_host", "network_definition")
    net_name = net_name_from_xmlfile(net_file)
    net = conn.networkLookupByName(net_name)

    net.destroy()

    remove_all_disks(conn, storage_paths, disks_to_remove)
