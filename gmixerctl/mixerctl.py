import os
import logging
import subprocess
import re

from . import util
from . import constants

def parse_line(line):
    """parse_line

    Parse a single line from the output of mixerctl -v

    :param line:
    """

    if len(line.split("=")) != 2:
        logging.warning(
                "don't know what to do with line '{}', no '='".format(line))
        return (line, {})

    name = line.split("=")[0]
    rest = line.split("=")[1].strip()

    state = {}
    state["name"] = name

    # enum case, i.e. off [ off on ]
    if re.match("^[a-zA-Z0-9:-]+\s+\[[a-zA-Z0-9 :-]+\]$", rest):
        state["type"] = "enum"
        state["current"] = rest.split("[")[0].strip()

        state["possible"] = []
        for val in rest.split("[")[1].split():
            if val == "]":
                continue
            else:
                state["possible"].append(val)

    # set case, i.e. hp  { spkr hp }
    elif re.match("((^[a-zA-Z0-9,:-]+\s+)|^)\{[a-zA-Z0-9 :-]+\}$", rest):
        state["type"] = "set"
        rest = rest.replace("}", "")
        state["current"] = tuple(rest.split("{")[0].strip().split(","))

        state["possible"] = []
        for val in rest.split("{")[1].split():
            if val == "]":
                continue
            else:
                state["possible"].append(val)

    # value case, single int value
    elif re.match("^[0-9]+$", rest):
        state["type"] = "value"
        state["current"] = int(rest)

    # value case, pair of int values
    elif re.match("^[0-9]+[,][0-9]+$", rest):
        state["type"] = "value"
        state["current"] = tuple((int(x) for x in rest.split(",")))

    # value case, single int value, with annotation
    elif re.match("^[0-9]+\s+[a-zA-Z]+$", rest):
        state["type"] = "value"
        state["current"] = int(rest.split(' ')[0])

    # value case, pair of int values, with annotation
    elif re.match("^[0-9]+[,][0-9]+\s+[a-zA-Z]+$", rest):
        state["type"] = "value"
        rest = rest.split(' ')[0]
        state["current"] = tuple((int(x) for x in rest.split(",")))

    else:
        logging.warning("unhanded format for '{}', giving up".format(rest))
        return (line, {})

    return name, state

def get_state():
    """get_state

    Get the current mixer state.
    """

    raw = subprocess.check_output(["mixerctl", "-f", constants.mixer_device,
        "-v"], stderr=subprocess.STDOUT)
    raw = raw.decode()

    control = {}

    for line in [x.strip() for x in raw.split("\n")]:
        if line == "":
            # ignore blank lines
            continue

        key, val = parse_line(line)

        if len(val.keys()) == 0:
            logging.warning(
                "discarding key '{}' due to empty value".format(key))
            continue

        control[key] = val

    return control

def set_value(control, value):
    """set_value

    :param control:
    :param value:
    """
    logging.debug("setting {} = {}".format(control, value))
    raw = subprocess.check_output(
            ["mixerctl", "-f", constants.mixer_device,
                "{}={}".format(control, value)],
            stderr=subprocess.STDOUT)
    logging.debug("mixerctl says {}".format(raw))
