#!/usr/bin/env python

import os

#
# Server socket
#
#   bind - The socket to bind.
#
#       A string of the form: 'HOST', 'HOST:PORT', 'unix:PATH'.
#       An IP is a valid HOST.
#

PORT = int(os.getenv('PORT', 5000))  # default to 5000

bind = f'0.0.0.0:{PORT}'

#
# Debugging
#
#   reload - Restart workers when code changes.
#
#       This setting is intended for development. It will cause workers to be
#       restarted whenever application code changes.
#
#       The reloader is incompatible with application preloading. When using a
#       paste configuration be sure that the server block does not import any
#       application code or the reload will not work as designed.
#
#   spew - Install a trace function that spews every line of Python
#       that is executed when running the server. This is the
#       nuclear option.
#
#       True or False
#

reload = bool(os.getenv('GUNICORN_RELOAD', False))  # default to False for production
spew = False

#
#   Logging
#
#   logfile - The path to a log file to write to.
#
#       A path string. "-" means log to stdout.
#
#   loglevel - The granularity of log output
#
#       A string of "debug", "info", "warning", "error", "critical"
#

logfile = '-'
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')  # default to 'info' for production
