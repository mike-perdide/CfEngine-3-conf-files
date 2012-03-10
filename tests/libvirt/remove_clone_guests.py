#!/usr/bin/env python
USAGE = """
SYNOPSIS
    shutdown_clone_hosts.py config.cfg
DESCRIPTION
    This script undoes everything id_clone_hosts did, using the same .cfg and
    .xml files.

    Please refer to the id_clone_hosts help for more information."""
import sys
from xml.etree import ElementTree

from common import parse_cfg, is_defined_guest, remove_all_disks, \
                   disk_path_from_guest_name


if __name__ == "__main__":
    if not len(sys.argv) == 2:
        print USAGE
        sys.exit(1)

    conn, machines_to_clone, cfg, xmlfilepath = parse_cfg(sys.argv[1])

    clone_names = [cfg.get(orig_name, "clone_name")
                   for orig_name in machines_to_clone]

    # For some reason, some clones may not have been defined
    defined_clone_names = [clone_name
                           for clone_name in clone_names
                           if is_defined_guest(conn, clone_name)]

    # Processing data and removing
    disks_to_remove = [disk_path_from_guest_name(conn, clone_name)
                       for clone_name in defined_clone_names]
    # The disks will be removed after we destroy the machines.

    for clone_name in defined_clone_names:
        clone_guest = conn.lookupByName(clone_name)

        if clone_guest.isActive():
            clone_guest.destroy()
        clone_guest.undefine()

    remove_all_disks(conn, disks_to_remove)
