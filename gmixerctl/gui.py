import logging
import tkinter
import tkinter.ttk as ttk
import time

from . import mixerctl
from . import util
from . import constants

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

def render_control(parent, control, tabs, tkvars):
    name = control["name"]


    # slider label - we do this as a separate "widget" to place the
    # label on the left of the control and thus free up vertical space
    text_widget = tkinter.Label(
            parent,
            text = name,
            width = constants.label_width)
    text_widget.pack(side=tkinter.LEFT)

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
        scale.pack(side=tkinter.RIGHT)

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
        menu.pack(side=tkinter.RIGHT)

    elif control["type"] == "set":

        menu = None
        if name in tkvars:
            menu = MultiSelect(
                    parent,
                    name,
                    control["possible"],
                    tkvars[name].choices
            )
            menu.pack(side=tkinter.RIGHT)
        else:
            menu = MultiSelect(
                    parent,
                    name,
                    control["possible"],
            )
            menu.pack(side=tkinter.RIGHT)
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
        frame = ttk.Frame(tabs[tab_name])
        render_control(frame, control, tabs, tkvars)
        frame.pack()


    # automatically generate the rest of the tabs
    for name in controls:
        control = controls[name]

        # make sure the tab for this type of control exists
        tab_name = name.split(".")[0]
        if tab_name not in tabs:
            tabs[tab_name] = ttk.Frame(nb)
            nb.add(tabs[tab_name], text=tab_name)

        # create the frame for this control
        frame = ttk.Frame(tabs[tab_name])
        render_control(frame, control, tabs, tkvars)
        frame.pack()

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

