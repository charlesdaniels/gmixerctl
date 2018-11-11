import os
import logging
import subprocess

from . import util

def parse_line(line):
    """parse_line

    Parse a single line from the output of mixerctl -v

    :param line:
    """

    name = line.split("=")[0]
    rest = line.split("=")[1]

    state = {}
    state["name"] = name

    if "[" in rest:
        state["type"] = "enum"
        state["current"] = rest.split("[")[0].strip()

        state["possible"] = []
        for val in rest.split("[")[1].split():
            if val == "]":
                continue
            else:
                state["possible"].append(val)

    elif "{" in rest:
        state["type"] = "set"
        rest = rest.replace("}", "")
        state["current"] = tuple(rest.split("{")[0].strip().split(","))

        state["possible"] = []
        for val in rest.split("{")[1].split():
            if val == "]":
                continue
            else:
                state["possible"].append(val)

    else:
        state["type"] = "value"
        if "," in rest:
            state["current"] = tuple((int(x) for x in rest.split(",")))
        else:
            state["current"] = int(rest)


    return name, state

def get_state():
    """get_state

    Get the current mixer state.
    """

    raw = subprocess.check_output(["mixerctl", "-v"], stderr=subprocess.STDOUT)
    raw = raw.decode()

    control = {}

    for line in [x.strip() for x in raw.split("\n")]:
        if line == "":
            # ignore blank lines
            continue

        key, val = parse_line(line)
        control[key] = val

    return control

def set_value(control, value):
    """set_value

    :param control:
    :param value:
    """
    logging.debug("setting {} = {}".format(control, value))
    raw = subprocess.check_output(["mixerctl", "{}={}".format(control, value)],
            stderr=subprocess.STDOUT)
    logging.debug("mixerctl says {}".format(raw))
