from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.ttk import Treeview
# this import will override the standard tkinter widgets with the 
# themed ones. Theming is done differently on the ttk versions so 
# we'll need to make several adjustments in order to enable them.
# from tkinter.ttk import *
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

def draw_canvas(tkinstance):
    # basic assumptions of the canvas: origin at center, radial
    # positions specified by setting radius along pos. Y axis and
    # then performing clockwise rotation.

    w = Canvas(tkinstance, width=800, height=800)
    # this will position origin at center
    w.configure(scrollregion=(-400,-400,400,400))
    w.pack()
    # center crosshairs
    w.create_line(-40, -20, 40, 20, fill="red", dash=(4, 4))
    w.create_line(-40, 20, 40, -20, fill="red", dash=(4, 4))
    return w


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
        self.create_ui(master)
        self.pw_interface_selected_rings = []
        self.working_struct = self.load_new_struct(file,
                target_canvas=self.pw_canvas)

        # Interface history variables
        self.console_history = []
        self.console_history_offset = 0

        # DEBUG IPython Console:
        embed()

        self.tkapp.mainloop()

    def create_ui(self, master):
        master = self.master
        master.wm_title("Panawave Umbrella Editor")
        master.columnconfigure(0, weight=1, minsize=400)
        master.rowconfigure(0, weight=1, minsize=400)

        # MENU BAR:
        self.pw_menu_bar = Menu(master)
        self.pw_file_menu = Menu(self.pw_menu_bar, tearoff=0)
        self.pw_file_menu.add_command(label="Open...", command=self.open_file)
        self.pw_file_menu.add_command(label="Save as...", command=self.save_file)
        self.pw_file_menu.add_separator()
        self.pw_file_menu.add_command(label="Quit", command=master.destroy)
        self.pw_menu_bar.add_cascade(label="File", menu=self.pw_file_menu)

        master.config(menu=self.pw_menu_bar)

        # MAIN VIEW:
        self.pw_canvas = draw_canvas(master)
        # position canvas origin at center
        self.pw_canvas.configure(scrollregion=(-400,-400,400,400))
        self.pw_canvas.grid(row=0, column=0, rowspan=5, sticky=(N,E,W))
        self.pw_canvas.bind("<Button-1>", self._click_pw_canvas)
        self.pw_canvas.bind("<Double-Button-1>", self._double_click_pw_canvas)


        # SIDE BAR:
        # struct listing
        # This is now using ttk.Treeview because tkinter listboxes are
        # completely incapable of sanely displaying tabular data due to having
        # no access to a monospaced font!
        # http://stackoverflow.com/questions/3794268/command-for-clicking-on-the-items-of-a-tkinter-treeview-widget
        self.pw_list_box = Treeview(master, height=10)
        self.pw_list_box.configure(columns=("Radius", "Count", "Offset"),
                displaycolumns=(0,1,2),
                show="headings") # "tree headings" is the default; 
                                 # this hides the tree column.
        # TODO surely we can just not specify an exact width and let
        # tkinter proportion them equally?
        # '#0' is the "primary" tree view column. this can be hidden 
        # with the 'show' configure option.
        self.pw_list_box.column("#0", width="40", anchor="center")
        self.pw_list_box.column("Radius", width="64", anchor="e")
        self.pw_list_box.heading("Radius", text="Radius") # what a brain-dead API...
        self.pw_list_box.column("Count", width="64", anchor="e")
        self.pw_list_box.heading("Count", text="Count")
        self.pw_list_box.column("Offset", width="64", anchor="e")
        self.pw_list_box.heading("Offset", text="Offset°")
        self.pw_list_box.grid(row=0, column=1, sticky=(N,S), columnspan=4)
        self.pw_lb_s = Scrollbar(master, orient=VERTICAL,
                command=self.pw_list_box.yview)
        self.pw_lb_s.grid(row=0, column=4, sticky=(N,S))
        self.pw_list_box['yscrollcommand'] = self.pw_lb_s.set

        # If we bind to <Button-1>, our callback is executed before the
        # selection changes and gives us the *previous* selection.
        self.pw_list_box.bind('<ButtonRelease-1>', self._click_pw_listbox)
        self.pw_list_box.bind("<Key-Escape>", self._pw_interface_clear_selection)

        # ring attribute sliders
        self.pw_slider_radius = Scale(master, orient=VERTICAL, length=120,
                from_=200.0, to=1.0,
                resolution=-1, command=self.update_active_ring_radius)
        self.pw_slider_radius.grid(row=1, column=1)
        self.pw_slider_count = Scale(master, orient=VERTICAL, length=120,
                from_=50.0, to=1.0,
                command=self.update_active_ring_count)
        self.pw_slider_count.grid(row=1, column=2)
        self.pw_slider_offset = Scale(master, orient=VERTICAL, length=120,
                from_=360.0, to=0.0,
                command=self.update_active_ring_offset)
        self.pw_slider_offset.grid(row=1, column=3)

        def _update_slider_radius(event):
            self.pw_slider_radius.set(self.pw_input_radius.get())

        def _update_slider_count(event):
            self.pw_slider_count.set(self.pw_input_count.get())

        def _update_slider_offset(event):
            self.pw_slider_offset.set(self.pw_input_offset.get())

        # ring attribute entry boxes
        self.pw_input_radius = Entry(master)
        self.pw_input_radius.configure(width=4)
        self.pw_input_radius.bind("<FocusOut>", _update_slider_radius)
        self.pw_input_radius.grid(row=2, column=1, sticky=N)
        self.pw_input_radius.bind("<Return>", self.submit_new_ring)
        self.pw_input_count = Entry(master)
        self.pw_input_count.configure(width=4)
        self.pw_input_count.bind("<FocusOut>", _update_slider_count)
        self.pw_input_count.grid(row=2, column=2, sticky=N)
        self.pw_input_count.bind("<Return>", self.submit_new_ring)
        self.pw_input_offset = Entry(master)
        self.pw_input_offset.configure(width=4)
        self.pw_input_offset.bind("<FocusOut>", _update_slider_offset)
        self.pw_input_offset.grid(row=2, column=3, sticky=N)
        self.pw_input_offset.bind("<Return>", self.submit_new_ring)

        # new ring submit button
        self.pw_input_submit = Button(master, text="Create",
                command=self.submit_new_ring)
        self.pw_input_submit.grid(row=3, column=1, columnspan=4)

        # animation control buttons, row 1 (on/off)
        # set width manually so layout doesn't jump around when we
        # change the text
        self.pw_orbit_toggle = Button(master, text="Stop",
                command=self.toggle_animation, width=5)
        self.pw_orbit_toggle.grid(row=4, column=1)

        # animation control buttons, row 2 (anim methods)
        self.pw_orbit_begin_random = Button(master, text="Random",
                width=5, command=self.orbit_randomly)
        self.pw_orbit_begin_random.grid(row=5, column=1)
        self.pw_orbit_begin_linear = Button(master, text="Linear",
                width=5, command=self.orbit_linearly)
        self.pw_orbit_begin_linear.grid(row=5, column=2)

        self.pw_orbit_begin_inverse_linear = Button(master,
                text="Inverse Linear", width=5,
                command=self.orbit_inverse_linearly)
        self.pw_orbit_begin_inverse_linear.grid(row=5, column=3)

        # console
        self.pw_console = Entry(master)
        self.pw_console.grid(row=5, column=0, columnspan=1, sticky=(W,E))
        self.pw_console.bind("<Return>", self.execute_console_input)
        self.pw_console.bind("<Up>", self.navigate_console_history)
        self.pw_console.bind("<Down>", self.navigate_console_history)

        # CANVAS BINDINGS

    def _click_pw_canvas(self, event=None):
        '''Bound to clicks on the pw_canvas. Checks for the tk 'CURRENT' tag,
        which represents an item under the cursor, then:
        1. Toggle the .selected property if it's determined a ring was clicked,
        2. Rebuild the interface's internal list of selected items,
        3. Redraw the canvas,
        4. Rebuild the pw_list_box from the RingArray.
        5. Reset the input sliders (if applicable).'''
        # Check if we actually clicked something
        if self.pw_canvas.find_withtag(CURRENT):
            clicked_obj_id = self.pw_canvas.find_withtag(CURRENT)[0]
            print("Clicked on object with id ", clicked_obj_id)
            try:
                # See if it's tagged as part of a ring...
                clicked_ring_tag = next(
                        tag for tag in self.pw_canvas.gettags(
                            clicked_obj_id) if "ring-" in tag)
                print("The clicked object has the ring tag", clicked_ring_tag)
                clicked_ring = self.working_struct.ring_array[clicked_ring_tag.strip("ring-")]
            except NameError:
                # it's possible we'll click an object other than a sticker
                print("A canvas object was clicked but no 'ring-*' tag was found. Must not be a ring object.")
                return
            # Bitwise 'AND' of the bitmask returned by .state
            if event.state & 0x004:
                # Ctrl-key modifier is enabled
                # Toggle the .selected state
                clicked_ring.toggle_selected_state()
                print("Ctrl-clicked ring; toggled the selected state of the ring with key", clicked_ring.id)
            else:
                # no Ctrl-key modifier; reset selection
                for ring in self.working_struct.ring_array.values():
                    ring.selected = False
                clicked_ring.selected = True
                print("Clicked a ring without Ctrl modifier; clearing previous selection and selecting ring with key", clicked_ring.id)
            # Rebuild the pw_interface_selected_rings from the updated data in
            # the PanawaveStruct
            self.pw_interface_selected_rings = [ring for ring in self.working_struct.ring_array.values() if ring.selected]
            print("New contents of pw_interface_selected_rings:", self.pw_interface_selected_rings)
            # Redraw with the newly-selected rings.
            self._rebuild_pw_canvas()
            # Rebuild the list_box with newly-selected rings.
            self._rebuild_list_box()
            # Reset input sliders, if a single ring is selected
            self._pw_input_reset()
        else:
            print("No CURRENT tag returned, must not have clicked an object.")

    def _double_click_pw_canvas(self, event=None):
        '''Bound to double click on canvas. Clears ring selection if empty area
        is double-clicked. NOTE: Our single click handler will still fire!
        This is okay, because that handler does nothing when empty canvas is
        clicked.'''
        if self.pw_canvas.find_withtag(CURRENT):
            print("Double clicked but there was an object under the mouse, taking no action")
        else:
            print("Double clicked empty canvas area; clearing selection.")
            self._pw_interface_clear_selection()

    def _rebuild_pw_canvas(self):
        '''Clear and then redraw the working_struct to the canvas.'''
        self.pw_canvas.delete("all")
        self.working_struct.draw(self.pw_canvas)

    def _rebuild_list_box(self):
        '''Rebuild the pw_list_box from the current contents of
        working_struct.ring_array . This is only called when interacting with
        the canvas or the ring input controls, because the TreeView is stateful
        and handles its own updates internally.'''
        for item in self.pw_list_box.get_children():
            self.pw_list_box.delete(item)
        # Think we can safely assume deleting all items will also clear selection?
        # if not: self.pw_list_box.selection_set('')
        sorted_rings = sorted(self.working_struct.ring_array.values(), key= lambda ring: ring.radius)
        for i, ring in enumerate(sorted_rings, start=1):
            # IID's are explicitly set to coincide with StickerRing.id to
            # simplify lookups for click events.
            self.pw_list_box.insert(parent="", index=i, iid=int(ring.id), text=i,
                    values=ring.as_tuple())
            # update selected state also from .selected prop!
            if ring.selected:
                self.pw_list_box.selection_add(int(ring.id))

    def _click_pw_listbox(self, event=None):
        '''Bound to click events on listbox. pw_list_box.selection()
        is stateful so we assume the values it returns are canonical;
        1. Propogate selected state back to the working_struct,
        2. Update the interface's internal list of selected items,
        3. Redraw the rings on canvas with new selections.
        4. Reset the input sliders (if applicable).'''
        # IID's are set at creation to coincide with .id property 
        # so we can directly look up the clicked item.
        list_selection_items = self.pw_list_box.selection()
        print("List box is reporting current selection as: ",
                list_selection_items)
        # Clear the interface's working list of selected items
        self.pw_interface_selected_rings = []
        # there's probably a more clever way to do this with a list
        # comprehension but the scoping issues with listcomps are way over
        # my head at the moment:
        # http://stackoverflow.com/questions/13905741/accessing-class-variables-from-a-list-comprehension-in-the-class-definition
        # Reset the .selected atribute on all rings then
        # set it again based on what's reported by the TreeView.
        for ring in self.working_struct.ring_array.values():
            ring.selected = False
        for iid in list_selection_items:
            selected_ring = self.working_struct.ring_array[iid]
            self.pw_interface_selected_rings.append(selected_ring)
            selected_ring.selected = True
        self._rebuild_pw_canvas()
        self._pw_input_reset()

    def _pw_interface_clear_selection(self, event=None):
        '''Bound to ESC when pw_listbox has selection.'''
        # self.pw_list_box.selection_set('')
        self.pw_interface_selected_rings = []
        for ring in self.working_struct.ring_array.values():
            ring.selected = False
        self._rebuild_list_box()
        self._rebuild_pw_canvas()
        print("Cleared selection.")
        # TODO This is probably a messy interface but...just calling the click
        # handler to propogate the cleared selection back to the object
        # self._click_pw_listbox()

    def _pw_input_reset(self):
        '''Reset the input and sliders to reflect current selected ring.
        If more than one ring is selected, disable the inputs.'''
        # Sliders modify selected ring's attributes in realtime;
        # if no ring is selected they just adjust the input value
        # and wait for the 'Submit' button to do anything with them.
        sliders = (self.pw_slider_radius, self.pw_slider_count, self.pw_slider_offset)
        inputs = (self.pw_input_radius, self.pw_input_count, self.pw_input_offset)
        if len(self.pw_interface_selected_rings) == 1:
            print("Exactly one ring has been selected, setting input controls to its values.")
            (rad, count, offset) = self.pw_interface_selected_rings[0].radius, \
            self.pw_interface_selected_rings[0].count, \
            self.pw_interface_selected_rings[0].offsetDegrees
            for elem in (sliders + inputs):
                elem.configure(state=NORMAL)
            for slider, value in zip(sliders, (rad, count, offset)):
                    slider.set(value)
        elif len(self.pw_interface_selected_rings) > 1:
            print("Disabling inputs as multiple rings are selected.")
            for slider in sliders:
                slider.set(0)
                slider.configure(state=DISABLED)
            for input in inputs:
                input.configure(state=DISABLED)

    def update_active_ring_radius(self, rad):
        if len(self.pw_interface_selected_rings) == 1:
            self.pw_interface_selected_rings[0].set_radius(rad)
        self.pw_input_radius.delete(0, END)
        self.pw_input_radius.insert(0, rad)
        self._rebuild_pw_canvas()
        self._rebuild_list_box()

    def update_active_ring_count(self, count):
        if len(self.pw_interface_selected_rings) == 1:
            self.pw_interface_selected_rings[0].set_count(count)
        self.pw_input_count.delete(0, END)
        self.pw_input_count.insert(0, count)
        self._rebuild_pw_canvas()
        self._rebuild_list_box()

    def update_active_ring_offset(self, deg):
        if len(self.pw_interface_selected_rings) == 1:
            self.pw_interface_selected_rings[0].set_offset(deg)
        self.pw_input_offset.delete(0, END)
        self.pw_input_offset.insert(0, deg)
        self._rebuild_pw_canvas()
        self._rebuild_list_box()

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
        self._rebuild_list_box()
        return self.working_struct

    def submit_new_ring(self, *args):
        '''validate the input and submit it to our current struct.
        will accept event objects from bindings but currently ignores
        them.'''
        self.working_struct.add_ring(self.pw_input_radius.get(), \
                self.pw_input_count.get(), \
                self.pw_input_offset.get())
        self.working_struct.draw(self.pw_canvas)
        self.pw_input_radius.focus_set()
        self._rebuild_list_box()

    def toggle_animation(self):
        if self.working_struct.animating is True:
            self.working_struct.stop_animation()
            self.pw_orbit_toggle.configure(text="Start")
        else:
            self.working_struct.orbit_randomly()
            self.pw_orbit_toggle.configure(text="Stop")

    def orbit_randomly(self):
        self.pw_orbit_toggle.configure(text="Stop")
        self.working_struct.orbit(method="random")

    def orbit_linearly(self):
        self.pw_orbit_toggle.configure(text="Stop")
        self.working_struct.orbit(method="linear")

    def orbit_inverse_linearly(self):
        self.pw_orbit_toggle.configure(text="Stop")
        self.working_struct.orbit(method="inverse-linear")

    def execute_console_input(self, *args):
        '''execute arbitrary commands from the console box,
        update the UI, and clear input's contents'''
        statement = self.pw_console.get()
        self.console_history.append(statement)
        try:
            eval(statement)
        except:
            e = sys.exc_info()
            print("***Console input generated the following error:***")
            print(e)
        self.working_struct.draw(self.pw_canvas)
        self._rebuild_list_box()
        sleep(.5)
        self.console_history_offset = 0
        self.pw_console.delete(0, END)

    def navigate_console_history(self, event):
        '''walk through input history and replace pw_console contents
        the offset is stored as a negative integer, used directly as
        a reverse index. This is fine because although the list length
        changes every time we input a command, we're not caring about
        saving the history index then anyway.'''
        print("keypress received: ", event.keysym)
        if event.keysym == "Up":
            new_offset = self.console_history_offset - 1
        elif event.keysym == "Down":
            new_offset = self.console_history_offset + 1
        print("testing offset: ", new_offset)
        hist = self.console_history
        hist_len = len(hist)
        print("hist len: ", hist_len)
        if new_offset >= 0:
            # return to a blank slate if we arrive back at the
            # end of the history.
            self.pw_input_offset = 0
            self.pw_console.delete(0, END)
            print("reset offset to zero.")
            return
        if (0 > new_offset >= -hist_len):
            self.console_history_offset = new_offset
            self.pw_console.delete(0, END)
            self.pw_console.insert(END, hist[new_offset])
            print ("decided offset ", new_offset, " is valid.")


if __name__ == "__main__":
    print("initializing Panawave Umbrella Editor...")
    master = Tk()
    global our_app
    our_app = PanawaveApp(master)

