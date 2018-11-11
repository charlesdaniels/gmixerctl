import logging
import traceback
import pprint

def setup_logging(level=logging.INFO):
    logging.basicConfig(level=level,
            format='%(levelname)s: %(message)s',
            datefmt='%H:%M:%S')

def log_exception(e):
    logging.error("Exception: {}".format(e))
    logging.debug("".join(traceback.format_tb(e.__traceback__)))

def log_pretty(logfunc, obj):
    logfunc(pprint.pformat(obj))
