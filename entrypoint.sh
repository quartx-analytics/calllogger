#!/bin/sh -e

case $1 in
  mock)
    exec calllogger-mock
  ;;
  *)
    exec calllogger
  ;;
esac

exit $?
