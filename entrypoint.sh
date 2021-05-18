#!/bin/sh -e

isMounted    () { findmnt -rno SOURCE,TARGET "$1" >/dev/null;} # path or device
isDevMounted () { findmnt -rno SOURCE        "$1" >/dev/null;} # device only
isPathMounted() { findmnt -rno        TARGET "$1" >/dev/null;} # path only

# Ensure that the data directory is a docker volume
if ! isPathMounted "$DATA_LOCATION"; then
  echo "The $DATA_LOCATION directory is required to be a mounted docker volume."
  echo "Please add the following to your docker command."
  echo "--volume='calllogger-data:$DATA_LOCATION'"
fi

case $1 in
  mock)
    exec calllogger-mock
  ;;
  *)
    exec calllogger
  ;;
esac

exit $?
