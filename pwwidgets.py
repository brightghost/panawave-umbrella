import tkinter
from tkinter import N,E,S,W, VERTICAL, HORIZONTAL, END, CURRENT # just a handful of 
# tkinter constants that are really easier to # ref in the base namespace
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.ttk import Treeview
from tkinter import ttk


class PWWidget:
    '''
    Parent class for Panawave Widgets. PWWdigets all extent a tkinter widget,
as well as PWWidget.  Among other things, this parent class manages the
references to the PWApp, which extends Tk and thus serves as a master for the
tkinter widgets as well as a container for app state data.
    '''
    pwapp = None # this needs to be set when the app is instantiated.

class PWMenuBar(PWWidget, tkinter.Menu):
    def __init__(self, *args, **kwargs):
        tkinter.Menu.__init__(self, self.pwapp.master)
        self.pw_file_menu = Menu(self, tearoff=0)
        self.pw_file_menu.add_command(label="Open...", command=self.open_file)
        self.pw_file_menu.add_command(label="Save as...", command=self.save_file)
        self.pw_file_menu.add_separator()
        self.pw_file_menu.add_command(label="Quit", command=self.pwapp.master.destroy)
        self.add_cascade(label="File", menu=self.pw_file_menu)

        self.pwapp.master.config(menu=self.pw_menu_bar)

    def open_file(self):
        '''gets filename with standard tk dialog then calls load_new_struct'''
        filename = tkinter.askopenfilename(defaultextension=".pwv")
        if filename is None:
            return
        else:
            load_new_struct(file=filename)

    def save_file(self):
        filename = asksaveasfilename(defaultextension=".pwv")
        if filename is None:
            return
        else:
            working_struct.write_out(filename)


class PWViewer(PWWidget):
    '''PWViewer contains a PWCanvas and PWListBox and manages the callbacks
    which interconnect the two and reference the working_struct. PWViewer
    has no relevance within the tkinter context; the child PWCanvas and
    PWListBox can be laid out independently.'''

    def __init__(self):
        pass

    def create_canvas(self, *args, **kwargs):
        self.pw_canvas = PWCanvas(*args, **kwargs)
        self.pw_canvas.bind("<Button-1>", self._update_selected_ring_with_canvas_click)

    def create_list(self, *args, **kwargs):
        self.pw_list = PWListBox(*args, **kwargs)
        self.pw_list.bind('<ButtonRelease-1>', self._update_ring_selection_with_list_click)

    def _update_selected_ring_with_canvas_click(self, event):
        '''Formerly _update_clicked_canvas_item
        Bound to clicks on the pw_canvas. Checks for the tk 'CURRENT' tag,
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
                self.selected_ring = self.pwapp.working_struct.ring_array[clicked_ring_id] # Do we need to save this state here? Probably best not to duplicate it
                self.selected_ring.selected = True
                print("Updating selected_ring to", self.selected_ring)
                self.pwapp.working_struct.draw(self.pw_canvas)
            except NameError:
                # it's possible we'll click an object other than a sticker
                return
        else:
            print("No CURRENT tag returned, must not have clicked an object.")


    def _update_ring_selection_with_list_click():
        '''Formerly _update_ring_selection.  Bound to click events on
        pw_list_box. Unlike the canvas click handler, we don't need to track
        the selected item within the widgeth or explicitly highlight it, so we
        just need to pass the id of the selected ring back to the
        panawave_struct. pw_list_box.selection() returns an IID; these are
        explicitly set when refreshing the list to make this lookup trivial.'''

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
        for ring in self.pwapp.working_struct.ring_array.values():
            ring.selected = False
        for iid in list_selection_array:
            selected_ring = self.pwapp.working_struct.ring_array[iid]
            self.pw_interface_selected_rings.append(selected_ring)
            selected_ring.selected = True
        self.pw_canvas.delete("all")
        self.pwapp.working_struct.draw(self.pw_canvas)

    def _rebuild_list_box():
        '''Formerly update_list_box.
        Rebuild the pw_list_box from the current contents of working_struct.
        ring_array . IID's are explicitly set to coincide with the StickerRing.id       to simplify lookups for click events.'''

        for item in self.pw_list_box.get_children():
            self.pw_list_box.delete(item)
        for i, key in enumerate(self.pwapp.working_struct.ring_array, start=1):
            ring = self.pwapp.working_struct.ring_array[key]
            self.pw_list_box.insert(parent="", index=i, iid=int(ring.id), text=i,
                    values=ring.as_tuple())





class PWCanvas(PWWidget, tkinter.Canvas):
    # basic assumptions of the canvas: origin at center, radial
    # positions specified by setting radius along pos. Y axis and
    # then performing clockwise rotation.

    def __init__(self, width=None, height=None, row=None, column=None, columnspan=None, rowspan=None, **kwargs):
        tkinter.Canvas.__init__(self, self.pwapp.master, width=width, height=height, **kwargs) 
        self.configure(scrollregion=(-400,-400,400,400)) # this will position origin at center
        # center crosshairs
        self.create_line(-40, -20, 40, 20, fill="red", dash=(4, 4))
        self.create_line(-40, 20, 40, -20, fill="red", dash=(4, 4))
        self.configure(scrollregion=(-400,-400,400,400))
        self.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, sticky=(N,E,S,W))
        # self.bind("<Configure>", foo) 
        # will probably need to implement this binding in order to scale
        # drawn elements as the window resized.

#     def __init__(self, master, file=None):
#         self.master = master
#         self.create_ui(master)
#         self.pw_interface_selected_rings = []
#         self.pwapp.working_struct = self.load_new_struct(file,
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


        # SIDE BAR:
class PWListBox(PWWidget, tkinter.Frame):
    '''A listing of rings, using tkinter.Treeview for dumb reasons.'''
    def __init__(self, row=None, column=None, columnspan=None, **kwargs):
        # Parent frame for internal layout management
        tkinter.Frame.__init__(self, self.pwapp.master)

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

        # Layout
        self.list.grid(row=0, column=0, sticky=(N,S,E,W))
        self.scroll.grid(row=0, column=1, sticky=(N,S))
        self.columnconfigure(0, weight=1) # TODO is this accomplishing anything?
        self.rowconfigure(0, weight=1)
        self.grid(row=row, column=column, columnspan=columnspan, sticky=(N,S))



    def add_col(self, heading, text=None, width=64, anchor="e"):
        '''Encapsulating method for the moronic TreeView column interface.'''
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


class PWController(PWWidget):
    '''PWController contains widgets which modify existing rings or create new
    ones and manages the callbacks which interconnect these and access the
    working_struct. Although it inherits from PWWidget, PWController has no
    relevance within the tkinter context; the child control widgets are laid
    out independently.'''

    def __init__(self):
        # ring attribute sliders
        # Sliders modify selected ring's attributes in realtime;
        # if no ring is selected they just adjust the input value
        # and wait for the 'Submit' button to do anything with them.
        self.pw_slider_radius = PWSlider(setter_callback=self.update_active_ring_radius, from_=200.0, to=1.0)
        self.pw_slider_radius.input_box.bind("<Return>", self.submit_new_ring)
        self.pw_slider_count = PWDetailedSlider(setter_callback=self.update_active_ring_count, from_=50.0, to=1.0)
        self.pw_slider_count.input_box.bind("<Return>", self.submit_new_ring)
        self.pw_slider_offset = PWSlider(setter_callback=self.update_active_ring_offset, from_=360.0, to=0.0)
        self.pw_slider_offset.input_box.bind("<Return>", self.submit_new_ring)

        # new ring submit button
        self.pw_input_submit = PWSubmitButton(text="Submit")
        self.pw_input_submit.config(command=self.submit_new_ring)


    def update_active_ring_radius(self, rad):
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            print("updating ring radius with value: ", rad)
            self.pwapp.pw_interface_selected_rings[0].set_radius(rad)
        else:
            print("Not updating because not exactly one ring selected.")

    def update_active_ring_count(self, count):
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            print("updating ring count with value: ", count)
            self.pwapp.pw_interface_selected_rings[0].set_count(int(count))
            self.pwapp.pw_interface_selected_rings[0].draw(self.pw_canvas)
        else:
            print("Not updating because not exactly one ring selected.")

    def update_active_ring_offset(self, deg):
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            print("updating ring offset with value: ", deg)
            self.pwapp.pw_interface_selected_rings[0].set_offset(deg)
            self.pwapp.pw_interface_selected_rings[0].draw(self.pw_canvas)
        else:
            print("Not updating because not exactly one ring selected.")

    def submit_new_ring(self, *args):
        '''validate the input and submit it to our current struct.
        will accept event objects from bindings but currently ignores
        them.'''
        self.pwapp.working_struct.add_ring(self.pw_slider_radius.get_value(), \
                self.pw_slider_count.get_value(), \
                self.pw_slider_offset.get_value())
        self.pwapp.working_struct.draw(self.pwapp.viewer.pw_canvas)
        self.pw_slider_radius.input_box.focus_set()
        self.pwapp.update_list_box()


class PWSlider(tkinter.Frame, PWWidget):
    '''Slider with accompanying input box, native theme, and option to snap to
    integers. Set the 'var' local property to a variable that should be adjusted
    by the controller.'''
    def __init__(self, setter_callback=None, orient=VERTICAL, length=120, row=None, column=None, **kwargs):
        print("PWSlider being initted; self.pwapp.master is: " + repr(self.pwapp.master))
        super().__init__()
        print("***super().__init__ just called; current dir:")
        print(dir(self))
        print("***Now printing repr(self.tk): " + repr(self.tk))
        print("***Now printing LOCALS: " + repr(locals()))
        # self.row = kwargs.pop("row")
        # self.col = kwargs.pop("column")
        self.setter_callback = setter_callback
        self.length = length
        self.orient = orient
        print("child scale being initted; self is: " + repr(self))
        print("***orient= " + repr(self.orient))
        self.scale = ttk.Scale(self, orient=orient, length=self.length, command=self._slider_handler, takefocus=False, **kwargs)
        self.scale.grid(row=0, column=0, pady=4)
        # Input box
        self.input_box = tkinter.Entry(self, width=4)
        self.input_box.grid(row=1, column=0, sticky=N)
        self.input_box.bind("<FocusOut>", self._input_box_handler)
        self.grid(row=row, column=column, pady=4)

    def set_value(self, val):
        self.input_box.delete(0, END)
        self.input_box.insert(0, val)
        self.scale.set(val)

    def get_value(self):
        '''TODO In principle this is maybe not the most robust approach.'''
        return self.input_box.get()

    def _slider_handler(self, event):
        '''Passes the value from slider to input box and sets var when adjusted.'''
        new_val = self.scale.get()
        print("Updating input_box value due to slider adjustment, new val: ", new_val)
        self.input_box.delete(0, END)
        self.input_box.insert(0, new_val)
        self.setter_callback(new_val)

    def _input_box_handler(self, event):
        '''Passes value from input box to slider and sets var when losing focus.'''
        new_val = self.input_box.get()
        if new_val == "":
            new_val = 0
        print("Updating scale value due to input_box adjustment, new val: ", new_val)
        self.scale.set(new_val)
        self.setter_callback(new_val)


class PWDetailedSlider(PWSlider):
    '''Slider with addition of a context button for accessing additional config.
    Used for the 'count' controller.'''
    def __init__(self, *args, **kwargs):
        PWSlider.__init__(self, *args, **kwargs)
        self.details_button = ttk.Button(self, text="...", width=2)
        self.details_button.grid(row=0, column=0)
        self.scale.grid(row=1, column=0, pady=4)
        self.input_box.grid(row=2, column=0)
        # subtract the height of the new button from the slider
        print("PWDetailedSlider Frame height being reported as", self.winfo_height())
        print("Initial slider and button height being reported as: ", self.scale.winfo_height(), self.details_button.winfo_height())
        # button height is 30, at least on linux. It would be better to
        # reference details_button.winfo_height(), but apparently this value is
        # not calculated until the window is drawn and returns 1 here.
        self.scale.config(length=(self.length - 30))


class PWSubmitButton(PWWidget, ttk.Button):
    '''New ring submit button.'''


class PWAnimController(PWWidget, tkinter.Frame):
    '''Combined selection box and animation control button. This widget will
    operate on the working_struct.'''
    def __init__(self, values=None, row=None, column=None, columnspan=None):
        tkinter.Frame.__init__(self, self.pwapp.master)
        if values == None:
            methods = {"random": "Random",
                    "linear": "Linear",
                    "reverse-linear": "Reverse Linear"
                    }
        else:
            methods = values
        self.combo = ttk.Combobox(self, values=list(methods.values()), state="readonly", width=15) # apparently no way to not set a width? default is 20
        self.combo.grid(row=0, column=0, sticky=(E,W), pady=2)
        # self.combo.pack(expand=True, fill='x', side='left', anchor=W)
        self.combo.current(1) # init with 1st item selected
        self.combo.bind("<<ComboboxSelected>>", self._set_anim_method)
        self.toggle_button = ttk.Button(self, text="Start", width=5, command=self.toggle_animation)
        self.toggle_button.grid(row=0, column=1, rowspan=2, padx=4, pady=2)
        self.speedslider = ttk.Scale(self, orient=HORIZONTAL, takefocus=False)
        self.speedslider.set(.5) # init in middle
        self.speedslider.grid(row=1, column=0, sticky=(W,E), pady=2)
        self.grid(row=row, column=column, columnspan=columnspan, sticky=(E,W), pady=4)
        self.columnconfigure(0, weight=1)

    def _set_anim_method(self, method):
        '''Restart the animation with the new method if animation is currently active; otherwise don't do anything.'''
        working_struct.ephemeral_state['anim_method'] = method
        if working_struct.ephemeral_state['animating'] is True:
            working_struct.stop_animation()
            working_struct.orbit(method=ephemeral_state['anim_method'])

    def toggle_animation(self):
        if working_struct.ephemeral_state['animating'] is True:
            working_struct.stop_animation()
        else:
            working_struct.orbit(method=self.combo.get())

# =============================================================================
# Reference shite copied from the previous implementation below. All should be
# migrated to new classes.








    def toggle_animation(self):
        if self.pwapp.working_struct.animating is True:
            self.pwapp.working_struct.stop_animation()
            self.pw_orbit_toggle.configure(text="Start")
        else:
            self.pwapp.working_struct.orbit_randomly()
            self.pw_orbit_toggle.configure(text="Stop")

    def orbit_randomly(self):
        self.pw_orbit_toggle.configure(text="Stop")
        self.pwapp.working_struct.orbit(method="random")

    def orbit_linearly(self):
        self.pw_orbit_toggle.configure(text="Stop")
        self.pwapp.working_struct.orbit(method="linear")

    def orbit_inverse_linearly(self):
        self.pw_orbit_toggle.configure(text="Stop")
        self.pwapp.working_struct.orbit(method="inverse-linear")

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
        self.pwapp.working_struct.draw(self.pw_canvas)
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

