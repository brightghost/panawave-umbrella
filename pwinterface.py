import logging as log
import tkinter
# TODO will be deprecating the toplevel import below in favor of above
# to clean up our namespace
from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.ttk import Treeview, Style
from tkinter import ttk
from math import degrees, radians
from cmath import exp
from random import random
from time import sleep
from copy import deepcopy
import json
import os
import sys
# Debugging console
from IPython import embed

from radialstructs import *
from pwwidgets import *


class PanawaveApp:
    '''our GUI app for working with PanawaveStructs.
    Requires reference to a Tk instance, and optionally a
    file to load initially.

    Window layout: (via asciiflow.com)
                                                       
     0                        1 2 3 4                  
                                                       
     +-------------------------------+ 0 List          
     |                        |     ||   List          
     |                        |     ||                 
     |                        |     ||                 
     |                        |     ||                 
     |                        +------+ 1               
     |                        | | |  |   Sliders       
     |                        | | |  |                 
     |                        +------+ 2               
     |                        | | |  |   Input         
     |                        +------+ 3               
     |                        | | |  |   Anim. methods 
     +-------------------------------+ 4               
     |                        |      |   Toggle anim.  
     +-------------------------------+                 
                                                       
      Console                         
    '''
    def __init__(self, master, file=None):
        self.master = master
        # Pass self reference to the base PWWidget class, so it will be
        # inherited by all PWWidgets. This greatly simplifies widget
        # instantiation.
        PWWidget.pwapp = self
        self.pw_interface_selected_rings = []
        self.create_ui()
        self.working_struct = self.load_new_struct(file,
                target_canvas=self.viewer.pw_canvas)

        # DEBUG IPython Console:
        embed()

        # TODO somehow this isn't actually being used...and I'm  not entirely
        # clear where the tk loop *is* entered!
        # self.tkapp.mainloop()

    def create_ui(self):

        master = self.master
        master.wm_title("Panawave Umbrella Editor")
        master.columnconfigure(0, weight=1, minsize=100)
        master.rowconfigure(0, weight=1, minsize=100)

        # THEME:
        styler = Style()
        if "clam" in styler.theme_names():
            styler.theme_use("clam")

        # MENU BAR:
        self.pw_menu_bar = Menu()
        self.pw_file_menu = Menu(self.pw_menu_bar, tearoff=0)
        self.pw_file_menu.add_command(label="Open...", command=self.open_file)
        self.pw_file_menu.add_command(label="Save as...", command=self.save_file)
        self.pw_file_menu.add_separator()
        self.pw_file_menu.add_command(label="Quit", command=master.destroy)
        self.pw_menu_bar.add_cascade(label="File", menu=self.pw_file_menu)

        master.config(menu=self.pw_menu_bar)

        # MAIN VIEW:
        self.viewer = PWViewer()

        # CANVAS
        self.viewer.create_canvas(row=0, column=0, rowspan=5)

        # LISTBOX
        self.viewer.create_list(row=0, column=1, columnspan=3)

        # CONSOLE BUTTON
        # Originally was pursuing use of canvas.create_window for this, but it
        # requires a redraw every time the canvas is cleared. While this method
        # works, it results in the button flickering every time the canvas is
        # drawn. Research suggests best-practice is to not redraw canvas by
        # deleting, but instead to move existing objects. This will
        # substantially complicate our existing PanawaveStruct layout code
        # however, and anyway the current method behaves well with polygon
        # objects.  Currently investigating use of .pack() geom. manager,
        # instead.

        self.console = PWConsole(master=self.viewer.pw_canvas)
        self.console_button = PWButton(self.viewer.pw_canvas, text=">",
                width=2, command=self.console.toggle_console)
        self.console_button.place(relx=0.02, rely=.92)
                # This is currently broken; the geom. of the parent window
                # currently seems to be larger than the actual geometry drawn,
                # and thus rel. values are not drawing where expected and don't
                # stay in the same relative position as window is resized.
        self.console.console_input.bind("<Return>",
                self.console.execute_console_input)
        self.console.console_input.bind("<Up>",
                self.console.navigate_console_history)
        self.console.console_input.bind("<Down>",
                self.console.navigate_console_history)

        # RING CONTROL:
        self.pw_controller = PWController()
        self.pw_controller.pw_slider_radius.grid(row=1, column=1)
        self.pw_controller.pw_slider_count.grid(row=1, column=2)
        self.pw_controller.pw_slider_offset.grid(row=1, column=3)
        self.pw_controller.pw_input_submit.grid(row=2, column=1, columnspan=3)

        # Bind controller's button to spawn period dialog
        self.pw_controller.pw_slider_count.details_button.config(
                command=self.spawn_period_dialog)

        self.pw_anim_control = PWAnimController(row=3, column=1, columnspan=3)

        # # animation control buttons, row 1 (on/off)
        # # set width manually so layout doesn't jump around when we
        # # change the text
        # self.pw_orbit_toggle = Button(text="Stop",
        #         command=self.toggle_animation, width=5)
        # self.pw_orbit_toggle.grid(row=4, column=1)

        # # animation control buttons, row 2 (anim methods)
        # self.pw_orbit_begin_random = Button(text="Random",
        #         width=5, command=self.orbit_randomly)
        # self.pw_orbit_begin_random.grid(row=5, column=1)
        # self.pw_orbit_begin_linear = Button(text="Linear",
        #         width=5, command=self.orbit_linearly)
        # self.pw_orbit_begin_linear.grid(row=5, column=2)

        # self.pw_orbit_begin_inverse_linear = Button(,
        #         text="Inverse Linear", width=5,
        #         command=self.orbit_inverse_linearly)
        # self.pw_orbit_begin_inverse_linear.grid(row=5, column=3)


        # CANVAS BINDINGS


    def open_file(self):
        '''gets filename with standard tk dialog then calls load_new_struct'''
        filename = askopenfilename(defaultextension=".pwv")
        if filename is None:
            return
        else:
            self.load_new_struct(file=filename)

    def save_file(self):
        filename = asksaveasfilename(defaultextension=".pwv")
        if filename is None:
            return
        else:
            self.working_struct.write_out(filename)

    def load_new_struct(self, file=None, target_canvas=None):
        '''create an empty struct, attach it to the canvas,
        and populate it from a file if one is given.'''
        self.selected_ring = None
        self.working_struct = PanawaveStruct(canvas=target_canvas)
        if file is not None:
            self.working_struct.load_from_file(file)
        self.working_struct.draw()
        self.rebuild_views()
        return self.working_struct

    def _update_clicked_canvas_item(self, event):
        '''Bound to clicks on the pw_canvas. Checks for the tk 'CURRENT' tag,
        which represents an item under the cursor, then update the
        selected_ring array if it's determined a ring was clicked.'''
        if self.pw_canvas.find_withtag(CURRENT):
            clicked_obj_id = self.pw_canvas.find_withtag(CURRENT)[0]
            log.debug("Clicked on object with id {0}".format(clicked_obj_id))
            try:
                clicked_ring_tag = next(
                        tag for tag in self.pw_canvas.gettags(
                            clicked_obj_id) if "ring-" in tag)
                log.debug("The clicked object has the ring tag {0}".format(
                    clicked_ring_tag))
                clicked_ring_id = clicked_ring_tag.strip("ring-")
                log.debug("Adding to the selected_ring list the ring with "
                        "key {0}".format(clicked_ring_id))
                self.selected_ring = \
                        self.working_struct.ring_array[clicked_ring_id]
                log.debug("Updating selected_ring to {0}".format(
                    self.selected_ring))
            except NameError:
                # it's possible we'll click an object other than a sticker
                return
        else:
            log.debug("No CURRENT tag returned, must not have clicked "
                    "an object.")

    def rebuild_views(self):
        '''Rebuild the pw_list_box from the current contents of working_struct.
        ring_array .'''
        self.viewer.rebuild()

    def clear_selection(self):
        '''Clear selection state of working_struct as well as PWViewer and
        PWController'''
        self.working_struct.clear_selection()
        self.pw_controller.clear_inputs()
        self.viewer.rebuild() # really entirely unneccesary to rebuild the list
            # here as well but...does it matter?

    def set_selection(ringlist):
        '''Set selection state of working_struct and update interface elements
        accordingly.'''
        self.working_struct.set_selection(ringlist)
        self.viewer.redraw()
        if len(ringlist) is 1:
            self.pw_controller.enable()
            self.pw_controller.set_inputs(ringlist[0].radius,
                    ringlist[0].count, ringlist[0].offset)
        else:
            self.pw_controller.clear_inputs()
            self.pw_controller.disable()

    def spawn_period_dialog(self):
        '''Creates a PWPeriodDialog window and waits for it to return.'''
        log.debug("Spawning a PWPeriodDialog and waiting for its return...")
        self.period_dialog = PWPeriodDialog(self.master)
        self.wait_window(period_dialog.win)


class PWPeriodDialog(tkinter.Toplevel, PWWidget):
    '''see PWApp.spawn_period_dialog() for handling of the event loop when dialog
    is created. Inherits from PWWidget only so we can ref pwapp when saving
    state.'''

    def __init__(self, master):
        # Stash pre-state for use by self.cancel

        self.prior_scaler_states = []
        for r in self.pwapp.pw_interface_selected_rings:
            self.prior_scaler_states.append(deepcopy(r.scaler_list))
        log.debug("Stashed scaler_list states prior to spawning period "
                "dialog: {0}".format(repr(self.prior_scaler_states)))
        self.prior_locked_ring_list_state = deepcopy(
                self.pwapp.working_struct.persistent_state['unlocked_rings'])
        log.debug("Stashed unlocked_rings list prior to spawning period "
                "dialog: {0}".format(repr(self.prior_locked_ring_list_state)))

        # Interface

        tkinter.Toplevel.__init__(self, master)
        # override the master inherited from PWWidget because we're casting it
        # in a new window.
        self.period_controller = PWPeriodController(master=self)
        self.btn_box = tkinter.Frame(self)
        self.period_controller.pack(padx=12, pady=0, fill='x')
        self.btn_box.pack(padx=12, pady=12, fill='x')
        cancel_button = PWButton(master=self.btn_box, text="Cancel",
                command=self.cancel)
        submit_button = PWButton(master=self.btn_box, text="Set",
                command=self.submit, default='active')
        submit_button.pack(side=tkinter.RIGHT)
        cancel_button.pack(side=tkinter.RIGHT, padx=6)

        # Bindings
        self.bind("<Return>", self.submit)
        self.bind("<Escape>", self.cancel)


        # window management

        self.wm_title("Set Sticker Spacing...")
        self.resizable(width=FALSE, height=FALSE)
        # grab all input events from other windows
        self.grab_set()
        # bunch of bullshit to visually center the dialog over parent...
        # Force the geometry manager to arrange the widgets so we can
        # calculate placement based on size
        self.update()
        self.parent_center_x = \
                self.master.winfo_rootx() + (self.master.winfo_width() / 2)
        self.parent_center_y = \
                self.master.winfo_rooty() + (self.master.winfo_height() / 2)
        self.offset_x = \
                self.parent_center_x - (self.winfo_width() / 2)
        # y a bit above center because it looks better
        self.offset_y = \
                self.parent_center_y - (self.winfo_height() /2) - 100

        self.geometry("+%d+%d" % (self.offset_x, self.offset_y))

        # handle closing window from window manager
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def cancel(self, *args):
        '''Close the dialog and roll back changes.'''
        log.debug("Rolling back to prior_scaler_states: {0}".format(
                repr(self.prior_scaler_states)))
        for ring, prior_state in zip(
                self.pwapp.pw_interface_selected_rings,
                self.prior_scaler_states):
            log.debug("Resetting scaler_list of ring {0} to prior "
                    "value: {1}".format(repr(ring), repr(prior_state)))
            ring.set_scaler_list(prior_state)
        self.pwapp.working_struct.persistent_state['unlocked_rings'] = \
                self.prior_locked_ring_list_state
        self.pwapp.viewer._rebuild_pw_canvas()
        self.destroy()

    def submit(self, *args):
        '''Close the dialog, saving changes.'''
        # Changes are applied in real-time, so there is nothing to "submit"
        # We do however need to reset the PWController; although the slider
        # values cannot be changed by actions taken in the PWPeriodDailog, the
        # quantize setting for the count slider may.
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            self.pwapp.pw_controller.set_inputs_for_ring_obj(
                    self.pwapp.pw_interface_selected_rings[0])
            # TODO: Eventually PWController will fully support multiple sel;
            # then we should be calling a version of set_inputs_for_ring_obj
            # that supports both scenarios.
        self.destroy()

