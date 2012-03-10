#!/usr/bin/env python
USAGE = """
SYNOPSIS
    copy_clones_to_masters.py config.cfg
DESCRIPTION
    This command will copy the clone disks onto the master disks.
"""

import sys
from os.path import expanduser, join
from shutil import copyfile
from common import parse_cfg, disk_path_from_guest_name, is_defined_guest
import paramiko


if __name__ == "__main__":
    if not len(sys.argv) == 2:
        print USAGE
        sys.exit(1)

    configfilepath = sys.argv[1]
    #configfilepath = "config.cfg"
    conn, machines_to_clone, cfg, xmlfilepath = parse_cfg(configfilepath)

    server = cfg.get("virt_host", "server")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.load_host_keys(expanduser(join("~", ".ssh", "known_hosts")))
    ssh.connect(server)

    # Undefine the masters
    disks_to_remove = {}
    defined_clones_names = []
    for master_name in machines_to_clone:
        clone_name = cfg.get(master_name, "clone_name")
        # Check that we got a replacement before removing
        if not is_defined_guest(conn, clone_name):
            continue

        defined_clones_names.append(clone_name)
        # Make sure master and clone are inactive
        clone_guest = conn.lookupByName(clone_name)
        master_guest = conn.lookupByName(master_name)
        if clone_guest.isActive():
            clone_guest.destroy()

        if master_guest.isActive():
            master_guest.destroy()

        # Copy clone disk onto master disk
        disk_to_replace = disk_path_from_guest_name(conn, master_name)
        disk_to_copy = disk_path_from_guest_name(conn, clone_name)

        command = "cp %s %s" % (disk_to_replace, disk_to_copy)
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command)
