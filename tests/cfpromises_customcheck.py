#!/usr/bin/env python
# Copyright (C) 2010 Julien Miotte <miotte.julien@gmail.com>
#
# This script is released under the GPLv3.
# License: http://www.gnu.org/licenses/gpl-3.0.txt

USAGE="""SYNOPSIS: 
    cfpromises_customcheck.py PROMISES_FILE
DESCRIPTION
    This script aims at detecting syntax errors in the cfengine files by
    running cf-promises while defining some classes for each run.

    The promises file should either contain a common ("any::") bundlesequence in
    the common control body or a list of test classes in the following form:
        # TEST_CLASSES:
        # class1
        # class2,class3 -class5,class6
        # class4
        # END

    When running the above example, the following commands will be run:
        cf-promises --define class1 -f promises.cf
        cf-promises --define class2,class3 --negate class5,class6 -f promises.cf
        cf-promises --define class4 -f promises.cf
"""

import sys
from subprocess import Popen, PIPE


def classes_from_file(filepath):
    with open(filepath) as handle:
        lines = handle.readlines()

    try:
        offset = lines.index("# TEST_CLASSES:\n")
        end = lines.index("# END\n")
    except ValueError, e:
        print "Warning: Couldn't find TEST_CLASSES correct declaration."
        return [""]

    if (offset + 1) == end:
        return [""]

    all_test_classes = []
    offset += 1

    while offset < end:
        line = lines[offset]
        line = line.strip()
        line = line.split("# ")[1]

        if " -" in line:
            all_test_classes.append(line.split(" -"))
        else:
            all_test_classes.append([line, ""])

        offset += 1

    return all_test_classes


def run_cfpromises(filepath, defined="", negated=""):
    command = ["/var/cfengine/bin/cf-promises", "-f", filepath]

    if defined:
        command.append("--define")
        command.append(defined)

    if negated:
        command.append("--negate")
        command.append(negated)

    handle = Popen(command, stdout=PIPE, stderr=PIPE)
    out, err = handle.communicate()

    return handle.returncode, out.rstrip(), err.rstrip()


if __name__ == "__main__":
    if not len(sys.argv) == 2:
        print USAGE
        sys.exit(1)

    filepath = sys.argv[1]

    fails = 0
    all_test_classes = classes_from_file(filepath)
    for defined, negated in all_test_classes:
        print "Testing class:", defined
        rtcode, out, err = run_cfpromises(filepath, defined, negated)

        if rtcode != 0:
            fails += 1

            print "TEST_CLASSES:", test_classes
            if out:
                print "STDOUT:"
                print out
            if err:
                print "STDERR:"
                print err

    sys.exit(fails)
