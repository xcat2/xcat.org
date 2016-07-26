#!/bin/sh
#
# Run this by adding to the crontab
# - execute every day at 1:00 AM, deleting files older than 180 days
#
# 1 00 * * * xcat /var/www/xcat.org/backup/cleanup_files.sh 180
#

if [ -z ${1} ]; then
    echo "You must provide the number of days back to delete"
    exit 1
fi 

DAYS=${1}

BASE_DIRECTORY=$(dirname `pwd`)
FILES=${BASE_DIRECTORY}/files

if [ -d ${FILES} ]; then
    #
    # remove the files under xcat-cor
    #
    CORE_FILES=${FILES}/xcat/xcat-core

    #
    # search for files that start with a digit which should be snapshot builds
    # excluding ==> esp files 
    #
    for file in `find ${CORE_FILES} -mtime +${DAYS} -name '[[:digit:]]*bz2' -print | grep -v -i esp`; do
        if [ ! -L "${file}" ]; then
            echo "Removing file: ${file}"
            rm -f ${file}
        fi
    done
fi

exit 0

