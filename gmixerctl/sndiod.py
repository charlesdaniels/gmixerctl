import logging
import os
import subprocess
import re

from . import util
from . import constants

def enumerate_rsnd_dev():
    """enumerate_rsnd_dev

    Return a list of rsnd/* devices that are likely to exist.
    """

    dev_num = 0
    devices = []

    while True:
        dev_path = "/dev/mixer{}".format(dev_num)
        logging.debug("testing mixer path {}".format(dev_path))

        if os.path.exists(dev_path):
            logging.debug("path exists")
            devices.append("rsnd/{}".format(dev_num))
        else:
            logging.debug("path did not exist")
            break

        dev_num += 1

    return devices

def get_sndiod_flags():
    """get_sndiod_flags

    Get the currently configured sndiod flags via rcctl.

    This function returns a tuple, the first element being a list of currently
    configured devices (-f), and the second element being all other flags as a
    string.

    """

    raw = subprocess.check_output("rcctl get sndiod".split())
    flags = None
    devices = None

    for line in (x.strip() for x in raw.decode('utf8').split("\n")):
        if "sndiod_flags" in line:
            flags = '='.join(line.split("=")[1:])

    logging.debug("picked up sndiod flags {}".format(flags))

    # regex to select flag parmeters
    regex = '[-]f[ ]+[a-zA-Z/0-9]+([ ]+|$)'

    devices = [x.group(0).split(' ')[1] for x in re.finditer(regex, flags)]
    logging.debug("devices: {}".format(devices))

    flags = re.sub(regex, '', flags)
    logging.debug("stripped -f flags and got: {}".format(flags))

    return flags, devices
