#!/usr/bin/env python
USAGE = """
SYNOPSIS
    stop_clone_guests.py config.cfg
DESCRIPTION
    This script shuts down the clones created by id_clone_hosts.py, using the
    same .cfg file.

    Please refer to the id_clone_hosts.py help for more information."""
import sys
from common import parse_cfg, is_defined_guest, is_active_guest


if not len(sys.argv) == 2:
    print USAGE
    sys.exit(1)

conn, machines_to_clone, cfg, xmlfilepath = parse_cfg(sys.argv[1])

clone_names = [cfg.get(orig_name, "clone_name")
               for orig_name in machines_to_clone]

defined_clones_names = [clone_name
                        for clone_name in clone_names
                        if is_defined_guest(conn, clone_name)]

for clone_name in defined_clones_names:
    guest = conn.lookupByName(clone_name)
    if guest.isActive():
        guest.destroy()
