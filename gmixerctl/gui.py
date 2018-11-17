import logging
import tkinter
import tkinter.ttk as ttk
import tkinter.messagebox
import time
import subprocess
import glob

from . import mixerctl
from . import util
from . import constants
from . import sndiod

def update_state(root, tkvars):
    """update_state

    Update the state of the GUI to reflect the current mixer status.
    """

    controls = mixerctl.get_state()
    for name in controls:
        control = controls[name]
        if control["type"] == "value":
            if type(control["current"]) == tuple:
                tkvars[name].set(control["current"][0])
            else:
                tkvars[name].set(control["current"])

        elif control["type"] == "enum":
            tkvars[name].set(control["current"])

        elif control["type"] == "set":
            for p in control["possible"]:
                if p in control["current"]:
                    tkvars[name].choices[p].set(1)
                else:
                    tkvars[name].choices[p].set(0)

    # schedule ourself to run again
    root.after(constants.update_interval, update_state, root, tkvars)

class update_value:

    def __init__(this, name, first=True):
        this.name = name
        this.first = first;

    def __call__(this, val):
        if this.first:
            # don't set values when we first initialize the sliders
            logging.debug("drop request {}={}".format(this.name, val))
            this.first = False
        else:
            mixerctl.set_value(this.name, val)

class SndiodButton(tkinter.Button):
    # button which check sndio checkboxes and runs an appropriate
    # rcctl command.

    def __init__(this, parent, text):
        tkinter.Button.__init__(this, parent, text=text, command = this.on_press)
        this.parent = parent

        # each element is (var, device)
        this.watchvars = []
        this.flags = ""

    def on_press (this):
        cmd = "doas -n /usr/sbin/rcctl set sndiod flags "
        cmd = cmd + this.flags
        cmd = cmd + ' '.join(["-f {}".format(x[1]) for x in this.watchvars if x[0].get() == 1])
        logging.debug("generated rcctl command {}".format(cmd))

        try:
            subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
            subprocess.check_output("doas -n /usr/sbin/rcctl restart sndiod".split(), stderr=subprocess.STDOUT)
        except Exception as e:
            tkinter.messagebox.showwarning(
                        "Apply Changes",
                        "Failed to apply rcctl flags. Maybe you need to add" +
                        "\n\npermit nopass youruser as root cmd /usr/sbin/rcctl" +
                        "\n\nto /etc/doas.conf ?" +
                        "\n\nerror was:\n\n{}".format(e)
                    )

class SetMixerDevice:
    def __init__(this, parent):
        this.parent = parent

    def __call__(this, val):
        # implement callback for setting mixer device

        constants.mixer_device = val
        logging.debug("updated mixer device to {}".format(val))
        this.parent.destroy()
        main()

class MultiSelect(tkinter.Frame):
    # https://stackoverflow.com/a/34550169
    #
    def __init__(this, parent, text, choices, choiceptr = None):
        tkinter.Frame.__init__(this, parent)

        menubutton = tkinter.Menubutton(this,
                text=text,
                indicatoron=True,
                borderwidth=1,
                relief="raised")

        menu = tkinter.Menu(menubutton, tearoff=False)
        menubutton.configure(menu=menu)
        menubutton.configure(width = constants.control_width)
        menubutton.pack(padx=10, pady=10)

        this.name = text

        this.choices = {}
        if choiceptr is not None:
            this.choices = choiceptr

        for choice in choices:
            choiceVar = None
            if choiceptr is None:
                this.choices[choice] = tkinter.IntVar(value=0)
                choiceVar = this.choices[choice]
            else:
                choiceVar = choiceptr[choice]

            menu.add_checkbutton(label=choice,
                    variable=choiceVar,
                    onvalue=1,
                    offvalue=0,
                    command=this.update
            )

    def update(this):
        mixerctl.set_value(this.name, ",".join(
            [x for x in this.choices if this.choices[x].get() == 1]))

def render_control(parent, control, tabs, tkvars, row):
    name = control["name"]


    # slider label - we do this as a separate "widget" to place the
    # label on the left of the control and thus free up vertical space
    text_widget = tkinter.Label(
            parent,
            text = name,
            width = constants.label_width)
    text_widget.grid(row = row, column = 0)

    # create a new callback object - we need to use the update_value
    # class so that mixerctl.set_value() knows what control we want
    # changed
    callback = update_value(name)

    # handle "value" types
    if control["type"] == "value":

        # backing integer variable for the slider
        if name not in tkvars:
            tkvars[name] = tkinter.IntVar();

        scale = tkinter.Scale(
                parent,
                variable = tkvars[name],
                label = "",
                to = 255,
                orient = tkinter.HORIZONTAL,
                length = 200,
                command = callback,
                )
        #  scale.config(width = constants.control_width)
        scale.grid(row = row, column = 1)

    elif control["type"] == "enum":

        # don't drop the first input for dropdowns
        callback.first = False

        if name not in tkvars:
            tkvars[name] = tkinter.StringVar()

        # single-item selection dropdown
        menu = tkinter.OptionMenu(
                parent,
                tkvars[name],
                *control["possible"],
                command = callback,
        )
        menu.config(width = constants.control_width)
        menu.grid(row = row, column = 1)

    elif control["type"] == "set":

        menu = None
        if name in tkvars:
            menu = MultiSelect(
                    parent,
                    name,
                    control["possible"],
                    tkvars[name].choices
            )
            menu.grid(row = row, column = 1)
        else:
            menu = MultiSelect(
                    parent,
                    name,
                    control["possible"],
            )
            menu.grid(row = row, column = 1)
            tkvars[name] = menu


    else:
        logging.warning("unhandled control type for control {}".format(control))


def main():

    util.setup_logging(level=constants.log_level)

    logging.debug("gmixerctl GUI started")

    root = tkinter.Tk()
    nb = ttk.Notebook(root)

    # get initial state
    controls = mixerctl.get_state()
    util.log_pretty(logging.debug, controls)

    tabs = {}
    tkvars = {}

    # custom-build "basic" tab
    row_counter = 0
    for name in controls:

        # only display the controls we have configured
        if name not in constants.basic_controls:
            continue

        control = controls[name]

        # make sure the tab for this type of control exists
        tab_name = "basic"
        if tab_name not in tabs:
            tabs[tab_name] = ttk.Frame(nb)
            nb.add(tabs[tab_name], text=tab_name)

        # create the frame for this control
        render_control(tabs[tab_name], control, tabs, tkvars, row_counter)
        row_counter += 1

    # add mixer device selector to basic tab
    dev_selector_label = tkinter.Label(tabs[tab_name],
            text = "select mixer device")
    dev_selector_label.grid(row = row_counter, column = 0)

    callback = SetMixerDevice(root)
    available_device = []
    dev_selector_var = tkinter.StringVar()
    dev_selector_var.set(constants.mixer_device)
    mixer_dev_selector = tkinter.OptionMenu(
            tabs[tab_name],
            dev_selector_var,
            *list(glob.glob("/dev/mixer*")),
            command = callback,
        )
    mixer_dev_selector.grid(row = row_counter, column = 1)


    # sndiod control tab
    tab_name = "sndiod"
    row_counter = 0
    tabs[tab_name] = ttk.Frame(nb)
    nb.add(tabs[tab_name], text=tab_name)

    # allow editing non-device flags
    current_flags, current_devices = sndiod.get_sndiod_flags()

    entry_label = ttk.Label(tabs[tab_name], text="sndiod flags")
    entry_label.grid(row = row_counter, column = 0)

    entry_box = ttk.Entry(tabs[tab_name])
    entry_box.insert(0, current_flags)
    entry_box.grid(row = row_counter, column = 1)

    row_counter += 1

    # button to apply settings
    sndiod_button = SndiodButton(tabs[tab_name], text="Apply")
    sndiod_button.flags = current_flags

    # check boxes for each device
    rsnd_buttons = []
    for device in sndiod.enumerate_rsnd_dev():
        tkvars[device] = tkinter.IntVar()
        if device in current_devices:
            tkvars[device].set(1)
        else:
            tkvars[device].set(0)

        rsnd_buttons.append(
                tkinter.Checkbutton(tabs[tab_name],
                    text=device, variable=tkvars[device])
            )
        rsnd_buttons[-1].grid(column = 0, row = row_counter)
        row_counter += 1

        sndiod_button.watchvars.append((tkvars[device], device))

    sndiod_button.grid(row = row_counter, column = 0)


    # automatically generate the rest of the tabs
    row_counter = 0
    for name in controls:
        control = controls[name]

        # make sure the tab for this type of control exists
        tab_name = name.split(".")[0]
        if tab_name not in tabs:
            tabs[tab_name] = ttk.Frame(nb)
            nb.add(tabs[tab_name], text=tab_name)

        # create the frame for this control
        render_control(tabs[tab_name], control, tabs, tkvars, row_counter)
        row_counter += 1

    # add about tab
    about = ttk.Frame(nb)
    version = tkinter.Label(
            about,
            text = "gmixerctl version {}".format(constants.version),
    )
    version.pack()

    license = tkinter.Label(
        about,
        text = constants.license
    )
    license.pack()
    about.pack()
    nb.add(about, text = "about")

    nb.pack()

    root.after(10, update_state, root, tkvars)
    root.mainloop()

