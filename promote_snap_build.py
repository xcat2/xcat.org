#!/usr/bin/python
# vim: set tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab
#

#
# This script should be used to promote the latest snap build to GA
#
# The valid options are:
# 1. promoting devel builds to GA
# 2. promoting Shapshot builds to GA for next minor release

# The following needs to be done during the "promote"
# * update the xCAT-*.repo files to point from core-snap -> xcat-core
# * rename the tar.gz file to contain the release number 

# Usage: 
# ./promote.sh [devel | snap] [release_number]

#
#
# DO NOT MODIFY THE VERSION ON xcat.org, the master file is located in c910
#   git clone <uid>@c910loginx01:/u/vhu/xcat2_autobuild.git
#
# After you clone the project, you can go into the xcat.org directory to find this script
#
#
import sys
import os
from optparse import OptionParser

usage = "usage: %prog [options] target_version"

parser = OptionParser(usage=usage)
parser.add_option("--target", dest="TARGET", help="[OPTIONAL] Specify the target directory for the script to run against. Default: files", default="files")
parser.add_option("--type", dest="TYPE", help="Specify the type of build to promote [devel|snap]", default="devel")
parser.add_option("--debug", dest="DEBUG", help="Does not execute, only print out commands", action="store_true", default=False)

(options, args) = parser.parse_args()


VERSION=None

def get_major_minor_versions(ver):
    minor_version = ver
    major_version = ver

    if len(ver.split('.')) > 2:
        major_version =  "%s.%s" %(ver.split('.')[0], ver.split('.')[1])
    
    if options.DEBUG:
        print "Version passed in: "
        print "    Major Version . . .: %s" %(major_version)
        print "    Minor Version . . .: %s" %(minor_version)

    return major_version, minor_version
 

def check_args():
    if len(args) != 1: 
        print "ERROR: The release number must be specified when running this script\n"
        parser.print_help()
        sys.exit(1)

    global VERSION
    VERSION=args[0]

    major, minor = get_major_minor_versions(VERSION)
    if major != minor:
        if options.TYPE == "devel":
            # default type is to promote the development build in major release of xCAT
            print "ERROR: --type=%s speficied but target_version is a minor release (%s).  You must use the --type=snap option" %(options.TYPE, minor)
            sys.exit(1)




def promote_build():
    if options.TYPE == "devel":
        promote_devel_build()
    elif options.TYPE == "snap":
        promote_snap_build()
    else:
        print "ERROR: Type %s is not supported\n" %(options.TYPE)
        parser.print_help()
        sys.exit(1)

def run_command(cmd): 
    if options.DEBUG: 
        print "DEBUG: %s" %(cmd)
    else:
        os.system(cmd)

def create_directory(destination): 
    # create directory if it doesn't exist
    cmd = "mkdir -p %s" %(destination)
    run_command(cmd)

def create_latest_link(): 
    print "creating the link!"

def get_confirmation():
    yes = set(['yes','ye','y'])
    no = set(['no','n'])

    choice = raw_input("Are you sure you want to continue? (y/n): ").lower()
    if choice in yes:
        return True
    elif choice in no:
        return False
    else:
        print "Please respond with 'y' or 'n'"
    return False

"""
Promoting the 'devel' build is done when we are about to GA the next release 
of xCAT. The 'devel' is the 'master' branch. The files are in the following
structure: 

Files:
    Linux RPM:    xcat/xcat-core/devel/Linux/core-snap
    Linux Debian: xcat/xcat-core/devel/Ubuntu/core-snap
Repo:
    Linux RPM:    xcat/repos/yum/devel/core-snap
    Linux Debian: xcat/repos/apt/devel/core-snap

When promoting to the GA, the following needs to happen: 

Files:
    Linux RPM     devel/Linux -> 2.X.x_Linux
                  2.X.x_Linux/xcat-core <-- create GA tar, symlink to latest core-snap 
"""
def promote_devel_build():
    print "Promoting devel build for xCAT %s" %(VERSION)

    devel_source_dir = "%s/xcat/xcat-core/devel" %(options.TARGET)
    """
    promote means to do the following:
    1) take the devel/Linux/core-snap -> 2.X.x_Linux/core-snap
    2) take the latest snap and create the GA
    3) update the yum repo to hold the latest
    4) repeat for Ubuntu 
    """
    major, minor = get_major_minor_versions(VERSION)
    types = ['Linux', 'Ubuntu']
    for t in types:
        print "=== Promoting %s release ===" %(t)
        core_file = "core-rpms-snap.tar.bz2"
        repo_type = "yum"
        if 'Ubuntu' in t: 
            core_file = "core-debs-snap.tar.bz2"
            repo_type = "apt"


        # Do all the error checking first, so we don't have to undo anything... 
        print "Verification starting..."

        # Make sure the release is not already GA
        ga_root_dir = "%s/xcat/xcat-core/%s.x_%s" %(options.TARGET, major, t)
        if os.path.exists(ga_root_dir):
            print "ERROR: The version requested (%s) has already been promoted at: %s" %(major, ga_root_dir)
            sys.exit(1)
        else:
            print "\tVersion %s is OK to promote" %(major)

        snap_source = "%s/%s/core-snap" %(devel_source_dir, t)

        # Make sure there is a snap build that can be used for the GA
        snap_build = "%s/%s" %(snap_source, core_file)

        real_file = os.path.realpath(snap_build)
        if not os.path.exists(real_file): 
            print "ERROR, snap file (%s) does not link to an actual file!" %(snap_build)
            sys.exit(1)
        else:
            print "\t%s => %s" %(core_file, os.path.basename(real_file))

        print "Verification complete... "
        if (get_confirmation() != True):
            sys.exit(1) 

        print "Promoting..."

        #
        # Promote the files area
        # 
        snap_dest = "%s/core-snap" %(ga_root_dir)

        # Create the GA directory 
        create_directory(ga_root_dir)

        # Move the core-snap directory to the GA root directory
        cmd = "mv %s %s/" %(snap_source, ga_root_dir)
        run_command(cmd)

        # Create the xcat-core directory
        ga_dest = "%s/xcat-core" %(ga_root_dir)
        create_directory(ga_dest)

        # Create a symlink pointing to the latest core-snap to be the GA file
        ga_file = "%s/xcat-core-%s.tar.bz2" %(ga_dest, minor)

        cmd = "ln -s ../core-snap/%s %s" %(os.path.basename(real_file), ga_file)
        run_command(cmd) 

        # Clean up the devel directory for the target 
        cmd = "rmdir %s/%s" %(devel_source_dir, t)
        run_command(cmd)

        #
        # Promote the yum/apt repos
        # 
 
        repo_source_dir = "%s/xcat/repos/%s/%s/core-snap" %(options.TARGET, repo_type, options.TYPE)
        repo_target_dir = "%s/xcat/repos/%s/%s" %(options.TARGET, repo_type, major)
        print repo_source_dir
        print repo_target_dir

        create_directory(repo_target_dir)

        # move the core-snap to xcat-core 
        cmd = "mv %s %s" %(repo_source_dir, repo_target_dir)
        run_command(cmd)
        cmd = "mv %s/core-snap %s/xcat-core" %(repo_target_dir, repo_target_dir)
        run_command(cmd)

        if "yum" in repo_type:
            repo_file = "%s/xcat-core/xCAT-core.repo" %(repo_target_dir)
            cmd = "sed -i s#%s/%s/core-snap#%s/%s/xcat-core#g %s" %(repo_type, options.TYPE, repo_type, major, repo_file)
            run_command(cmd) 

def promote_snap_build():
    print "Promoting snap build, not yet implemented, TODO\n"


if __name__ == '__main__':

     check_args()
     promote_build()

     sys.exit(0)

