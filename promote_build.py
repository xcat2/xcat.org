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
parser.add_option("--force", dest="FORCE", help="Force the command to run, disregarding the error checking", action="store_true", default=False)
parser.add_option("--link_latest", dest="LINK_LATEST", help="Force update the latest link to the promoted build.", action="store_true", default=False)

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
        print "Running cmd: %s" %(cmd)
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
        1) Take the latest devel snap build and use that for the GA 
        2) Copy over the yum/apt repos to be the latest Build
        3) Update the links in the yum/apt repos 
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
        if os.path.exists(ga_root_dir) and not options.FORCE:
            print "ERROR: The version requested (%s) has already been promoted at: %s" %(major, ga_root_dir)
            print "If you really want to re-promote the GA, use the --force option"
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

        # Create the GA xcat-core directory, which makes the root directory in the same process
        ga_dest = "%s/xcat-core" %(ga_root_dir)
        create_directory(ga_dest)

        # Create the snap drectory for snapshot builds - this may not be needed since snap builds will create it later 
        snap_dest = "%s/core-snap" %(ga_root_dir)
        #create_directory(snap_dest) 

        # Calculate the GA filename
        ga_file = "%s/xcat-core-%s-%s.tar.bz2" %(ga_dest, minor, str.lower(t))

        # Copy the core-file over to the GA root directory
        cmd = "cp %s %s" %(snap_build, ga_file)
        run_command(cmd)

        cmd = "ls -ltR %s" %(ga_dest)
        run_command(cmd)

        #
        # Promote the yum/apt repos
        # 
        repo_source_dir = "%s/xcat/repos/%s/%s/core-snap" %(options.TARGET, repo_type, options.TYPE)

        repo_dirs = []
        for ver in ['%s' %(major), 'latest']:
            print "Version: %s" %(ver)
            repo_target_dir = "%s/xcat/repos/%s/%s" %(options.TARGET, repo_type, ver)
            repo_dirs.append(repo_target_dir)

            #
            # if --force options is specified, clear out the repo first to copy over the new repo
            # 
            # Removing the old repo directory if it exists. Prompt the user to validate the path is
            # correct so that we do not accidently remove too much. 
            #
            if options.FORCE:
                import shutil 
                repo_remove = "%s/xcat-core" %(repo_target_dir)

                if os.path.exists(repo_remove):
                    print "Removing the following directory: %s" %(repo_remove)
                    if (get_confirmation() != True):
                        sys.exit(1) 
                    if not options.DEBUG:
                        shutil.rmtree('%s' %(repo_remove))
     
            create_directory(repo_target_dir)

            # move the core-snap and rename to xcat-core 
            cmd = "cp -rp %s %s" %(repo_source_dir, repo_target_dir)
            run_command(cmd)
            cmd = "mv %s/core-snap %s/xcat-core" %(repo_target_dir, repo_target_dir)
            run_command(cmd)

            if "yum" in repo_type:
                repo_file = "%s/xcat-core/xCAT-core.repo" %(repo_target_dir)
                cmd = "sed -i s#%s/%s/core-snap#%s/%s/xcat-core#g %s" %(repo_type, options.TYPE, repo_type, ver, repo_file)
                run_command(cmd)


"""
Promoting the 'snap' build is done when we want to release a mod release of xCAT. 
For example, 2.11 is GA, and we want to promote the snap build of 2.11.1

The weekly builds for the snap release should automatically built and should be uploaded
to xcat.org, so we just need to move around the files in the correct place to promote 
the 2.11.1 release

Files:
    Linux RPM:    xcat/xcat-core/2.11.x_Linux/core-snap
    Linux Debian: xcat/xcat-core/2.11.x_Ubuntu/core-snap
Repo:
    Linux RPM:    xcat/repos/yum/2.11/core-snap
    Linux Debian: xcat/repos/apt/2.11/core-snap

When promoting the 2.11.1 snapshot build to GA, the following needs to happen:

    1) The last file in 2.11.x_Linux/core-snap needs to be copied over to 
       2.11.x_Linux/xcat-core and assigned the mod release number
    2) The xcat/repos/yum/2.11/xcat-core repo should be removed
    3) The xcat/repos/yum/2.11/core-snap should replace xcat-core repo 
"""
def promote_snap_build():

    """
    promote means to do the following:
    1) take the devel/Linux/core-snap -> 2.X.x_Linux/core-snap
    2) take the latest snap and create the GA
    3) update the yum repo to hold the latest
    4) repeat for Ubuntu 
    """
    major, minor = get_major_minor_versions(VERSION)
    root_dir = "%s/xcat/xcat-core" %(options.TARGET)

    types = ['Linux', 'Ubuntu']
    for t in types:
        print "=== Promoting %s release ===" %(t)
        snap_source_dir = "%s/%s.x_%s/core-snap" %(root_dir, major, t)
        snap_dest_dir = "%s/%s.x_%s/xcat-core" %(root_dir, major, t)
        print ". . Looking at source directory: %s" %(snap_source_dir)
        print ". . Looking at destination directory: %s" %(snap_dest_dir)

        core_file = "core-rpms-snap.tar.bz2"
        repo_type = "yum"
        if 'Ubuntu' in t: 
            core_file = "core-debs-snap.tar.bz2"
            repo_type = "apt"

        # Do all the error checking first, so we don't have to undo anything... 
        print ". . Pre-verification starting . . . "

        # Make sure the target_version is NOT already promoted 
        target_ga_filename = "%s/xcat-core-%s-%s.tar.bz2" %(snap_dest_dir, minor, str.lower(t))
        if not options.FORCE:
            if os.path.isfile(target_ga_filename):
                print "ERROR: The version requested (%s) has already been promoted at: %s" %(minor, target_ga_filename)
                sys.exit(1)
            else:
                print "\t1) Version %s does not exist, it is OK to promote" %(os.path.basename(target_ga_filename))

        # Make sure there is a snap build that can be used for the GA
        snap_build = "%s/%s" %(snap_source_dir, core_file)

        real_file = os.path.realpath(snap_build)
        if not os.path.exists(real_file): 
            print "ERROR, snap file (%s) does not link to an actual file!" %(snap_build)
            sys.exit(1)
        else:
            print "\n\t2) Will promote the following snap build to GA"
            print "\t  %s => %s" %(core_file, os.path.basename(real_file))

        print ". . Pre-verification complete . . . "

        if (get_confirmation() != True):
            sys.exit(1) 

        print "Promoting..."

        # Copy the core-snap file
        cmd = "cp %s %s" %(os.path.realpath(snap_build), target_ga_filename)
        run_command(cmd) 

        # remove the xcat-core repo
        repo_source_dir = "%s/xcat/repos/%s/%s/core-snap" %(options.TARGET, repo_type, major)
        repo_target_dir = "%s/xcat/repos/%s/%s/xcat-core" %(options.TARGET, repo_type, major)

        #cmd = "mv -f %s %s.old" %(repo_target_dir, repo_target_dir)
        #run_command(cmd)

        # move the snapshot repo 
        cmd = "cp -rp %s %s" %(repo_source_dir, repo_target_dir)
        run_command(cmd)

        if "yum" in repo_type:
            repo_file = "%s/xCAT-core.repo" %(repo_target_dir)
            cmd = "sed -i s#%s/%s/core-snap#%s/%s/xcat-core#g %s" %(repo_type, major, repo_type, major, repo_file)
            run_command(cmd) 
       
        if options.LINK_LATEST:
            #
            # Promote the yum/apt repos
            # 
            repo_source_dir = "%s/xcat/repos/%s/%s/core-snap" %(options.TARGET, repo_type, major)

            print "source dir: %s" %(repo_source_dir)
            
            for ver in ['latest']:
                print "Version: %s" %(ver)
                repo_target_dir = "%s/xcat/repos/%s/%s" %(options.TARGET, repo_type, ver)

                # Since this is a snap build, we just want to remove the existing xcat-core repo 
                # and replace it with the core-snap repo, only keeping the latest
                repo_remove = "%s/xcat-core" %(repo_target_dir)
                if options.FORCE:
                    import shutil 

                    if os.path.exists(repo_remove):
                        if options.DEBUG:
                            print "DEBUG: Removing the following directory: %s" %(repo_remove)
                        else:
                            if (get_confirmation() != True):
                                sys.exit(1) 
                            if not options.DEBUG:
                                shutil.rmtree('%s' %(repo_remove))
                else:
                    if os.path.exists(repo_remove):
                        print "The directory exists: %s, you need to force remove to continue..." %(repo_remove)
                        sys.exit(1)

                create_directory(repo_target_dir)

                cmd = "cp -rp %s %s" %(repo_source_dir, repo_target_dir)
                run_command(cmd)
                cmd = "mv %s/core-snap %s/xcat-core" %(repo_target_dir, repo_target_dir)
                run_command(cmd)

                if "yum" in repo_type:
                    repo_file = "%s/xcat-core/xCAT-core.repo" %(repo_target_dir)
                    cmd = "sed -i s#%s/%s/core-snap#%s/%s/xcat-core#g %s" %(repo_type, major, repo_type, ver, repo_file)
                    run_command(cmd)

        else: 
            print "<< Updating the latest xCAT repository >>"
            print "The default behavior for updating the 'latest' repo on a snap build promote is NO." 
            print "If this snapshot build is in fact the latest version of xCAT, rerun the command with --link_latest option"

if __name__ == '__main__':

     check_args()
     promote_build()

     sys.exit(0)

