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
        # inherited by all PWWidgets. This greatly simplifies widget instantiation.
        PWWidget.pwapp = self
        self.pw_interface_selected_rings = []
        self.create_ui()
        self.working_struct = self.load_new_struct(file,
                target_canvas=self.viewer.pw_canvas)

        # Interface history variables
        self.console_history = []
        self.console_history_offset = 0

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
        self.console_button = ttk.Button(text=">", width=2)
        self.viewer.pw_canvas.create_window(-330, 330, anchor=SW, window=self.console_button)

        # RING CONTROL:
        self.pw_controller = PWController()
        self.pw_controller.pw_slider_radius.grid(row=1, column=1)
        self.pw_controller.pw_slider_count.grid(row=1, column=2)
        self.pw_controller.pw_slider_offset.grid(row=1, column=3)
        self.pw_controller.pw_input_submit.grid(row=2, column=1, columnspan=3)

        # Bind controller's button to spawn period dialog
        self.pw_controller.pw_slider_count.details_button.config(command=self.spawn_period_dialog)

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

        # # console
        # self.pw_console = Entry()
        # self.pw_console.grid(row=5, column=0, columnspan=1, sticky=(W,E))
        # self.pw_console.bind("<Return>", self.execute_console_input)
        # self.pw_console.bind("<Up>", self.navigate_console_history)
        # self.pw_console.bind("<Down>", self.navigate_console_history)

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
            print("Clicked on object with id ", clicked_obj_id)
            try:
                clicked_ring_tag = next(
                        tag for tag in self.pw_canvas.gettags(
                            clicked_obj_id) if "ring-" in tag)
                print("The clicked object has the ring tag", clicked_ring_tag)
                clicked_ring_id = clicked_ring_tag.strip("ring-")
                print("Adding to the selected_ring list the ring with key",
                        clicked_ring_id)
                self.selected_ring = self.working_struct.ring_array[clicked_ring_id]
                print("Updating selected_ring to", self.selected_ring)
            except NameError:
                # it's possible we'll click an object other than a sticker
                return
        else:
            print("No CURRENT tag returned, must not have clicked an object.")


    def rebuild_views(self):
        '''Rebuild the pw_list_box from the current contents of working_struct.  ring_array .'''
        self.viewer.rebuild()

    def clear_selection(self):
        '''Clear selection state of working_struct as well as PWViewer and PWController'''
        self.working_struct.clear_selection()
        self.pw_controller.clear_inputs()
        self.viewer.rebuild() # really entirely unneccesary to rebuild the list
            # here as well but...does it matter?

    def set_selection(ringlist):
        '''Set selection state of working_struct and update interface elements accordingly.'''
        self.working_struct.set_selection(ringlist)
        self.viewer.redraw()
        if len(ringlist) is 1:
            self.pw_controller.enable()
            self.pw_controller.set_inputs(ringlist[0].radius, ringlist[0].count, ringlist[0].offset)
        else:
            self.pw_controller.clear_inputs()
            self.pw_controller.disable()

    def spawn_period_dialog(self):
        '''Creates a PWPeriodDialog window and waits for it to return.'''
        print("Spawning a PWPeriodDialog and waiting for its return...")
        self.period_dialog = PWPeriodDialog(self.master)
        self.wait_window(period_dialog.win)


class PWPeriodDialog:
    '''see PWApp.spawn_period_dialog for handling of the event loop when dialog is created.'''
    def __init__(self, master):
        self.win = tkinter.Toplevel(master)
        period_controller = PWPeriodController(master=self.win) #override the master inherited from PWWidget because we're casting it in a new window.
        period_controller.grid(row=0, column=0)
        cancel_button = PWButton(master=win, text="Cancel", command=self.cancel)
        submit_button = PWButton(master=win, text="Set", command=self.submit)
        cancel_button.grid(row=1, column=0)
        submit_button.grid(row=1, column=1)

    def cancel(self):
        '''Close the dialog, discarding changes.'''
        self.win.destroy()

    def submit(self):
        '''Close the dialog, saving changes.'''
        # TODO do stuff here....
        self.win.destroy()

    def spawn_period_dialog(self):
        '''Creates a PWPeriodDialog window and waits for it to return.'''
        print("Spawning a PWPeriodDialog and waiting for its return...")
        self.period_dialog = PWPeriodDialog(self.master)
        self.master.wait_window(self.period_dialog)


class PWPeriodDialog(tkinter.Toplevel, PWWidget):
    '''see PWApp.spawn_period_dialog for handling of the event loop when dialog is created. Inherits from PWWidget only so we can ref pwapp when saving state.'''
    def __init__(self, master):

        # Stash pre-state for use by self.cancel
        self.prior_scaler_states = []
        for r in self.pwapp.pw_interface_selected_rings:
            self.prior_scaler_states.append(deepcopy(r.scaler_list))
        print("Stashed scaler_list states prior to spawning period dialog: ",
                repr(self.prior_scaler_states))
        self.prior_locked_ring_list_state = deepcopy(self.pwapp.working_struct.persistent_state['unlocked_rings'])
        print("Stashed unlocked_rings list prior to spawning period dialog: ",
                repr(self.prior_locked_ring_list_state))

        # Interface
        tkinter.Toplevel.__init__(self, master)
        self.period_controller = PWPeriodController(master=self) #override the master inherited from PWWidget because we're casting it in a new window.
        self.btn_box = tkinter.Frame(self)
        self.period_controller.pack(padx=12, pady=0, fill='x')
        self.btn_box.pack(padx=12, pady=12, fill='x')
        cancel_button = PWButton(master=self.btn_box, text="Cancel", command=self.cancel)
        submit_button = PWButton(master=self.btn_box, text="Set", command=self.submit, default='active')
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
        self.parent_center_x = self.master.winfo_rootx() + (self.master.winfo_width() / 2)
        self.parent_center_y = self.master.winfo_rooty() + (self.master.winfo_height() / 2)
        self.offset_x = self.parent_center_x - (self.winfo_width() / 2)
        # y a bit above center because it looks better
        self.offset_y = self.parent_center_y - (self.winfo_height() /2) - 100

        self.geometry("+%d+%d" % (self.offset_x,
            self.offset_y))

        # handle closing window from window manager
        self.protocol("WM_DELETE_WINDOW", self.cancel)


    def cancel(self, *args):
        '''Close the dialog and roll back changes.'''
        print("Rolling back to prior_scaler_states: ",
                repr(self.prior_scaler_states))
        for ring, prior_state in zip(
                self.pwapp.pw_interface_selected_rings,
                self.prior_scaler_states):
            print("Resetting scaler_list of ring ", repr(ring),
                    " to prior value: ", repr(prior_state))
            ring.set_scaler_list(prior_state)
        self.pwapp.working_struct.persistent_state['unlocked_rings'] = self.prior_locked_ring_list_state
        self.pwapp.viewer._rebuild_pw_canvas()
        self.destroy()

    def submit(self, *args):
        '''Close the dialog, saving changes.'''
        # Changes are applied in real-time, so there is nothing to "submit"
        # We do however need to reset the PWController; although the slider
        # values cannot be changed by actions taken in the PWPeriodDailog, the
        # quantize setting for the count slider may.
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            self.pwapp.pw_controller.set_inputs_for_ring_obj(self.pwapp.pw_interface_selected_rings[0])
            # TODO: Eventually PWController will fully support multiple sel;
            # then we should be calling a version of set_inputs_for_ring_obj
            # that supports both scenarios.
        self.destroy()

# ===========================================================================
# Reference shite left over below.
#     def _update_ring_selection(self, event):
#         '''Bound to click events on listbox. pw_list_box.selection()
#         returns an IID; we explicitly set these when refreshing the list
#         to make it easier to do this lookup.'''
#         list_selection_array = self.pw_list_box.selection()
#         print("List box is reporting current selection as: ",
#                 list_selection_array)
#         self.pw_interface_selected_rings = []
#         # there's probably a more clever way to do this with a list
#         # comprehension but the scoping issues with listcomps are way over
#         # my head at the moment:
#         # http://stackoverflow.com/questions/13905741/accessing-class-variables-from-a-list-comprehension-in-the-class-definition
#         # Just going to reset the .selected atribute on all rings then
#         # set it again based on what's reported by the TreeView.
#         for ring in self.working_struct.ring_array.values():
#             ring.selected = False
#         for iid in list_selection_array:
#             selected_ring = self.working_struct.ring_array[iid]
#             self.pw_interface_selected_rings.append(selected_ring)
#             selected_ring.selected = True
#         self.pw_canvas.delete("all")
#         self.working_struct.draw(self.pw_canvas)
# 
#     # Sliders modify selected ring's attributes in realtime;
#     # if no ring is selected they just adjust the input value
#     # and wait for the 'Submit' button to do anything with them.
# 
#     def update_active_ring_radius(self, rad):
#         print("updating ring radius with value: ", rad)
#         if len(self.pw_interface_selected_rings) == 1:
#             self.pw_interface_selected_rings[0].set_radius(rad)
#         self.pw_input_radius.delete(0, END)
#         self.pw_input_radius.insert(0, rad)
# 
#     def update_active_ring_count(self, count):
#         if self.selected_ring is not None:
#             self.selected_ring.set_count(int(count))
#             self.selected_ring.draw(self.pw_canvas)
#         self.pw_input_count.delete(0, END)
#         self.pw_input_count.insert(0, count)
# 
#     def update_active_ring_offset(self, deg):
#         if self.selected_ring is not None:
#             self.selected_ring.set_offset(deg)
#             self.selected_ring.draw(self.pw_canvas)
#         self.pw_input_offset.delete(0, END)
#         self.pw_input_offset.insert(0, deg)
# 
# 
#     def load_new_struct(self, file=None, target_canvas=None):
#         '''create an empty struct, attach it to the canvas,
#         and populate it from a file if one is given.'''
#         self.selected_ring = None
#         self.working_struct = PanawaveStruct(canvas=target_canvas)
#         if file is not None:
#             self.working_struct.load_from_file(file)
#         self.working_struct.draw()
#         self.update_list_box()
#         return self.working_struct
# 
#     def submit_new_ring(self, *args):
#         '''validate the input and submit it to our current struct.
#         will accept event objects from bindings but currently ignores
#         them.'''
#         self.working_struct.add_ring(self.pw_input_radius.get(), \
#                 self.pw_input_count.get(), \
#                 self.pw_input_offset.get())
#         self.working_struct.draw(self.pw_canvas)
#         self.pw_input_radius.focus_set()
#         self.update_list_box()
# 
#     def toggle_animation(self):
#         if self.working_struct.animating is True:
#             self.working_struct.stop_animation()
#             self.pw_orbit_toggle.configure(text="Start")
#         else:
#             self.working_struct.orbit_randomly()
#             self.pw_orbit_toggle.configure(text="Stop")
# 
#     def orbit_randomly(self):
#         self.pw_orbit_toggle.configure(text="Stop")
#         self.working_struct.orbit(method="random")
# 
#     def orbit_linearly(self):
#         self.pw_orbit_toggle.configure(text="Stop")
#         self.working_struct.orbit(method="linear")
# 
#     def orbit_inverse_linearly(self):
#         self.pw_orbit_toggle.configure(text="Stop")
#         self.working_struct.orbit(method="inverse-linear")
# 
#     def execute_console_input(self, *args):
#         '''execute arbitrary commands from the console box,
#         update the UI, and clear input's contents'''
#         statement = self.pw_console.get()
#         self.console_history.append(statement)
#         try:
#             eval(statement)
#         except:
#             e = sys.exc_info()
#             print("***Console input generated the following error:***")
#             print(e)
#         self.working_struct.draw(self.pw_canvas)
#         self.update_list_box()
#         sleep(.5)
#         self.console_history_offset = 0
#         self.pw_console.delete(0, END)
# 
#     def navigate_console_history(self, event):
#         '''walk through input history and replace pw_console contents
#         the offset is stored as a negative integer, used directly as
#         a reverse index. This is fine because although the list length
#         changes every time we input a command, we're not caring about
#         saving the history index then anyway.'''
#         print("keypress received: ", event.keysym)
#         if event.keysym == "Up":
#             new_offset = self.console_history_offset - 1
#         elif event.keysym == "Down":
#             new_offset = self.console_history_offset + 1
#         print("testing offset: ", new_offset)
#         hist = self.console_history
#         hist_len = len(hist)
#         print("hist len: ", hist_len)
#         if new_offset >= 0:
#             # return to a blank slate if we arrive back at the
#             # end of the history.
#             self.pw_input_offset = 0
#             self.pw_console.delete(0, END)
#             print("reset offset to zero.")
#             return
#         if (0 > new_offset >= -hist_len):
#             self.console_history_offset = new_offset
#             self.pw_console.delete(0, END)
#             self.pw_console.insert(END, hist[new_offset])
#             print ("decided offset ", new_offset, " is valid.")
# 
# 
# if __name__ == "__main__":
#     print("initializing Panawave Umbrella Editor...")
#     master = Tk()
#     global our_app
#     our_app = PanawaveApp()

