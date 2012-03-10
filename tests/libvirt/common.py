import libvirt
import ConfigParser
import sys
from os.path import join, dirname
from xml.etree import ElementTree


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

    net_file = config.get("virt_host", "network_definition")
    xmlfilepath = join(dirname(filepath), net_file)

    return conn, machines_to_clone, config, xmlfilepath


def disk_path_from_guest_name(conn, guest_name):
    guest = conn.lookupByName(guest_name)

    root = ElementTree.fromstring(guest.XMLDesc(0))
    tree = ElementTree.ElementTree(element=root)
    disk_sections = tree.findall("devices/disk")

    for disk in disk_sections:
        if disk.attrib["device"] == "disk":
            return disk.find("source").attrib["file"]


def is_defined_guest(conn, name):
    defined_domains = set(conn.listDefinedDomains()).union(
        set([conn.lookupByID(id).name()
             for id in conn.listDomainsID()]))
    return name in defined_domains


def is_active_guest(conn, name):
    guest = conn.lookupByName(name)
    print name, "active" if guest.isActive() else "inactive"
    return guest.isActive()


def pool_storage_path_from_name(conn, pool_name):
    pool = conn.storagePoolLookupByName(pool_name)

    root = ElementTree.fromstring(pool.XMLDesc(0))
    tree = ElementTree.ElementTree(element=root)
    name_section = tree.find("target/path")

    return name_section.text


def remove_all_disks(conn, disks_to_remove):
    storage_paths = [(name, pool_storage_path_from_name(conn, name))
                     for name in conn.listStoragePools()]

    for disk in disks_to_remove:
        for name, path in storage_paths:
            if path in disk:
                pool = conn.storagePoolLookupByName(name)
                storage_name = disk.split(path + "/")[1]
                pool.storageVolLookupByName(storage_name).delete(0)
