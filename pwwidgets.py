import tkinter
from tkinter import N,E,S,W, VERTICAL, HORIZONTAL # just a handful of things that are really easier to
# ref in the base namespace
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.ttk import Treeview
from tkinter import ttk

class PWCanvas(tkinter.Canvas):
    # basic assumptions of the canvas: origin at center, radial
    # positions specified by setting radius along pos. Y axis and
    # then performing clockwise rotation.

    def __init__(self, tkinstance, width=None, height=None, row=None, column=None, columnspan=None, rowspan=None, **kwargs):
        tkinter.Canvas.__init__(self, tkinstance, width=width, height=height, **kwargs)        
        self.configure(scrollregion=(-400,-400,400,400)) # this will position origin at center
        # center crosshairs
        self.create_line(-40, -20, 40, 20, fill="red", dash=(4, 4))
        self.create_line(-40, 20, 40, -20, fill="red", dash=(4, 4))
        self.configure(scrollregion=(-400,-400,400,400))
        self.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, sticky=(N,E,S,W))
        self.bind("<Button-1>", self._update_clicked_canvas_item)
        # self.bind("<Configure>", foo) 
        # will probably need to implement this binding in order to scale
        # drawn elements as the window resized.

#     def __init__(self, master, file=None):
#         self.master = master
#         self.create_ui(master)
#         self.pw_interface_selected_rings = []
#         self.working_struct = self.load_new_struct(file,
#                 target_canvas=self.pw_canvas)
# 
#         # Interface history variables
#         self.console_history = []
#         self.console_history_offset = 0
# 
#         # DEBUG IPython Console:
#         embed()
# 
#         self.tkapp.mainloop()
    def _update_clicked_canvas_item(event):
        pass


        # SIDE BAR:
class PWListBox(tkinter.Frame):
    '''Extended from tkinter.Treeview for dumb reasons.'''
    def __init__(self, tkinstance, row=None, column=None, columnspan=None, **kwargs):
        # Parent frame for internal layout management
        tkinter.Frame.__init__(self, tkinstance)

        # Struct List
        # This is now using ttk.Treeview because tkinter listboxes are
        # completely incapable of sanely displaying tabular data due to having
        # no access to a monospaced font!
        # http://stackoverflow.com/questions/3794268/command-for-clicking-on-the-items-of-a-tkinter-treeview-widget
        self.list = Treeview(self, **kwargs)
        self.list.configure(columns=("Radius", "Count", "Offset"),
                displaycolumns=(0,1,2),
                show="headings") # "tree headings" is the default; 
                                 # this hides the tree column.

        # List Access Methods
        # define some access methods in this namespace for ease of use.
        # TODO the methods which call these from pwinterface should become
        # class methods here.
        self.get_children = self.list.get_children
        self.delete = self.list.delete
        self.insert = self.list.insert

        self.add_col("Radius")
        self.add_col("Count")
        self.add_col("Offset", text="Offset°")

        # Scrollbar
        self.scroll = ttk.Scrollbar(self, orient=VERTICAL,
                command=self.list.yview)
        self.list['yscrollcommand'] = self.scroll.set
        # If we were to bind <Button-1>, our callback would be executed before
        # the selection changes and give us the *previous* selection.
        self.bind('<ButtonRelease-1>', self._update_ring_selection)

        # Layout
        self.list.grid(row=0, column=0, sticky=(N,S,E,W))
        self.scroll.grid(row=0, column=1, sticky=(N,S))
        self.columnconfigure(0, weight=1) # TODO is this accomplishing anything?
        self.rowconfigure(0, weight=1)
        self.grid(row=row, column=column, columnspan=columnspan, sticky=(N,S))



    def add_col(self, heading, text=None, width=64, anchor="e"):
        '''Method for encapsulating the moronic TreeView column interface.'''
        try:
            heading = str(heading)
        except TypeError:
            raise
        if text is None:
            text = heading
        # TODO surely we can just not specify an exact width and let
        # tkinter proportion them equally?
        # '#0' is the "primary" tree view column. this can be hidden 
        # with the 'show' configure option.
        # self.pw_list_box.column("#0", width="40", anchor="center")
        self.list.column(heading, width=width, anchor=anchor)
        self.list.heading(heading, text=text)

    def _update_ring_selection(event):
        pass


class PWSlider(tkinter.Frame):
    '''Slider with accompanying input box, native theme, and option to snap to
    integers.'''
    def __init__(self, tkinstance, orient=VERTICAL, length=120, row=None, column=None, **kwargs):
        tkinter.Frame.__init__(self, tkinstance)
        # self.row = kwargs.pop("row")
        # self.col = kwargs.pop("column")
        self.scale = ttk.Scale(self, orient=orient, length=length, command=self._update_input_box, **kwargs) 
        self.scale.grid(row=0, column=0, pady=4)
        # Input box
        self.input_box = tkinter.Entry(self, width=4)
        self.input_box.grid(row=1, column=0, sticky=N)
        self.input_box.bind("<FocusOut>", self._update_slider)
        self.input_box.bind("<Return>", submit_new_ring)
        self.grid(row=row, column=column, pady=4)

    def _update_input_box(self, event):
        '''Passes the value from slider to input box when adjusted.'''
        self.input_box.set(self.get())

    def _update_slider(self, event):
        self.set(self.input_box.get())


class PWSubmitButton(ttk.Button):
    '''New ring submit button.'''
    def __init__(self, tkinstance, row=None, column=None, columnspan=None):
        ttk.Button.__init__(self, tkinstance, text="Create", command=submit_new_ring)
        self.grid(row=row, column=column, columnspan=columnspan, pady=4)


def submit_new_ring():
    '''TODO this should maybe go somewhere else? Needs to be called by PWSlider and PWSubmitButton.'''


class PWAnimController(tkinter.Frame):
    '''Combined selection box and animation control button. This widget will
    operate on the working_struct .'''
    def __init__(self, tkinstance, values=None, row=None, column=None, columnspan=None):
        tkinter.Frame.__init__(self, tkinstance)
        if values == None:
            methods = {"random": "Random",
                    "linear": "Linear",
                    "reverse-linear": "Reverse Linear"
                    }
        else:
            methods = values
        self.combo = ttk.Combobox(self, values=list(methods.values()), state="readonly", width=15) # apparently no way to not set a width? default is 20
        self.combo.grid(row=0, column=0, sticky=(E,W))
        # self.combo.pack(expand=True, fill='x', side='left', anchor=W)
        self.combo.current(1) # init with 1st item selected
        self.combo.bind("<<ComboboxSelected>>", self._set_anim_method)
        self.toggle_button = ttk.Button(self, text="Start", width=5, command=self.toggle_animation)
        self.toggle_button.grid(row=0, column=1, padx=4)
        self.speedslider = ttk.Scale(self, orient=HORIZONTAL)
        self.speedslider.set(.5) # init in middle
        self.speedslider.grid(row=1, column=0, sticky=(W,E))
        self.grid(row=row, column=column, columnspan=columnspan, sticky=(E,W), pady=4)
        self.columnconfigure(0, weight=1)

    def _set_anim_method():
        pass

    def toggle_animation():
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
        for item in self.pw_list_box.get_children():
            self.pw_list_box.delete(item)
        for i, key in enumerate(self.working_struct.ring_array, start=1):
            ring = self.working_struct.ring_array[key]
            self.pw_list_box.insert(parent="", index=i, iid=int(ring.id), text=i,
                    values=ring.as_tuple())

    def _update_ring_selection(self, event):
        '''Bound to click events on listbox. pw_list_box.selection()
        returns an IID; we explicitly set these when refreshing the list
        to make it easier to do this lookup.'''
        list_selection_array = self.pw_list_box.selection()
        print("List box is reporting current selection as: ",
                list_selection_array)
        self.pw_interface_selected_rings = []
        # there's probably a more clever way to do this with a list
        # comprehension but the scoping issues with listcomps are way over
        # my head at the moment:
        # http://stackoverflow.com/questions/13905741/accessing-class-variables-from-a-list-comprehension-in-the-class-definition
        # Just going to reset the .selected atribute on all rings then
        # set it again based on what's reported by the TreeView.
        for ring in self.working_struct.ring_array.values():
            ring.selected = False
        for iid in list_selection_array:
            selected_ring = self.working_struct.ring_array[iid]
            self.pw_interface_selected_rings.append(selected_ring)
            selected_ring.selected = True
        self.pw_canvas.delete("all")
        self.working_struct.draw(self.pw_canvas)

    # Sliders modify selected ring's attributes in realtime;
    # if no ring is selected they just adjust the input value
    # and wait for the 'Submit' button to do anything with them.

    def update_active_ring_radius(self, rad):
        print("updating ring radius with value: ", rad)
        if len(self.pw_interface_selected_rings) == 1:
            self.pw_interface_selected_rings[0].set_radius(rad)
        self.pw_input_radius.delete(0, END)
        self.pw_input_radius.insert(0, rad)

    def update_active_ring_count(self, count):
        if self.selected_ring is not None:
            self.selected_ring.set_count(int(count))
            self.selected_ring.draw(self.pw_canvas)
        self.pw_input_count.delete(0, END)
        self.pw_input_count.insert(0, count)

    def update_active_ring_offset(self, deg):
        if self.selected_ring is not None:
            self.selected_ring.set_offset(deg)
            self.selected_ring.draw(self.pw_canvas)
        self.pw_input_offset.delete(0, END)
        self.pw_input_offset.insert(0, deg)

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

    def submit_new_ring(self, *args):
        '''validate the input and submit it to our current struct.
        will accept event objects from bindings but currently ignores
        them.'''
        self.working_struct.add_ring(self.pw_input_radius.get(), \
                self.pw_input_count.get(), \
                self.pw_input_offset.get())
        self.working_struct.draw(self.pw_canvas)
        self.pw_input_radius.focus_set()
        self.update_list_box()

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
        self.update_list_box()
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

