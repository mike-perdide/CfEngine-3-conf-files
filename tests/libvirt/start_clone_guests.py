#!/usr/bin/env python
USAGE = """
SYNOPSIS
    start_clone_guests.py config.cfg
DESCRIPTION
    This script will start the clones created by the clone_guests.py sript,
    using the same .cfg file."""

import sys
from common import parse_cfg, is_defined_guest


if not len(sys.argv) == 2:
    print USAGE
    sys.exit(1)

configfilepath = sys.argv[1]
conn, machines_to_clone, cfg, xmlfilepath = parse_cfg(configfilepath)

clone_names = [cfg.get(orig_name, "clone_name")
               for orig_name in machines_to_clone]

# For some reason, some clones may not have been defined
defined_clone_names = [clone_name
                       for clone_name in clone_names
                       if is_defined_guest(conn, clone_name)]

for clone_name in defined_clone_names:
    guest = conn.lookupByName(clone_name)
    guest.create()
