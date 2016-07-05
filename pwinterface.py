from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.ttk import Treeview, Style
from tkinter import ttk
from math import degrees, radians
from cmath import exp
from random import random
from time import sleep
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

        self.tkapp.mainloop()

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
        self.console_button = tkinter.Button(text=">")
        self.viewer.pw_canvas.create_window(-330, 330, anchor=SW, window=self.console_button)

        # RING CONTROL:
        self.pw_controller = PWController()
        self.pw_controller.pw_slider_radius.grid(row=1, column=1)
        self.pw_controller.pw_slider_count.grid(row=1, column=2)
        self.pw_controller.pw_slider_offset.grid(row=1, column=3)
        self.pw_controller.pw_input_submit.grid(row=2, column=1, columnspan=3)

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
        self.update_list_box()
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


    def update_list_box(self):
        '''Rebuild the pw_list_box from the current contents of working_struct.
        ring_array . IID's are explicitly set to coincide with the StickerRing.id       to simplify lookups for click events.'''
        for item in self.viewer.pw_list.get_children():
            self.viewer.pw_list.delete(item)
        for i, key in enumerate(self.working_struct.ring_array, start=1):
            ring = self.working_struct.ring_array[key]
            self.viewer.pw_list.insert(parent="", index=i, iid=int(ring.id), text=i,
                    values=ring.as_tuple())

    def clear_selection(self):
        '''Clear selection state of working_struct as well as PWViewer and PWController'''
        self.working_struct.clear_selection()
        self.pw_controller.clear_inputs()
        self.viewer.redraw()

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

