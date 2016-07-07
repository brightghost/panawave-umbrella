import tkinter
# tkinter constants that are easier to ref in the base namespace
from tkinter import N,E,S,W, VERTICAL, HORIZONTAL, END, CURRENT, DISABLED, NORMAL
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
        self.pw_canvas.bind("<Button-1>", self._click_pw_canvas)
        self.pw_canvas.bind("<Double-Button-1>", self._double_click_pw_canvas)

    def create_list(self, *args, **kwargs):
        self.pw_list = PWListBox(*args, **kwargs)
        self.pw_list.list.bind('<ButtonRelease-1>', self._update_ring_selection_with_list_click)
        self.pw_list.list.bind("<Key-Escape>", self._pw_interface_clear_selection)

    def _click_pw_canvas(self, event):
        self._update_selected_ring_with_canvas_click(event)

    def _update_selected_ring_with_canvas_click(self, event):
        '''Formerly _update_clicked_canvas_item
        Bound to clicks on the pw_canvas. Checks for the tk 'CURRENT' tag,
        which represents an item under the cursor, then update the
        selected_ring array if it's determined a ring was clicked.
        which represents an item under the cursor, then:
         1. Toggle the .selected property if it's determined a ring was clicked,
         2. Rebuild the interface's internal list of selected items,
         3. Redraw the canvas,
         4. Rebuild the pw_list_box from the RingArray.import
         5. Reset the input sliders (if applicable).'''
        # Check if we actually clicked something
        if self.pw_canvas.find_withtag(CURRENT):
            clicked_obj_id = self.pw_canvas.find_withtag(CURRENT)[0]
            print("Clicked on object with id ", clicked_obj_id)
            try:
                # check if it's tagges as part of a ring...
                clicked_ring_tag = next(
                        tag for tag in self.pw_canvas.gettags(
                            clicked_obj_id) if "ring-" in tag)
                print("The clicked object has the ring tag", clicked_ring_tag)
                clicked_ring = self.pwapp.working_struct.ring_array[clicked_ring_tag.strip("ring-")]
                clicked_ring_id = clicked_ring_tag.strip("ring-")
                print("Adding to the selected_ring list the ring with key",
                        clicked_ring_id)
            except NameError:
                # it's possible we'll click an object other than a sticker
                print("A canvas object was clicked but no 'ring-*' tag was found. Must not be a ring object.")
                return
        # Determine action based on which modifier keys may be held down
        # Bitwise 'AND' of the bitmask returned by .state
            if event.state & 0x004:
                # Ctrl-key modifier is enabled
                # Toggle the .selected state
                clicked_ring.toggle_selected_state()
                print("Ctrl-clicked ring; toggled the selected state of the ring with key", clicked_ring.id)
            else:
                # no Ctrl-key modifier; reset selection
                for ring in self.pwapp.working_struct.ring_array.values():
                    ring.selected = False
                clicked_ring.selected = True
                print("Clicked a ring without Ctrl modifier; clearing previous selection and selecting ring with key", clicked_ring.id)
            # Rebuild the pw_interface_selected_rings from the updated data in
            # the PanawaveStruct
            self.pwapp.pw_interface_selected_rings = [ring for ring in self.pwapp.working_struct.ring_array.values() if ring.selected]
            print("New contents of pw_interface_selected_rings:", self.pwapp.pw_interface_selected_rings)
            # Redraw with the newly-selected rings.
            self._rebuild_pw_canvas()
            # Rebuild the list_box with newly-selected rings.
            self._rebuild_list_box()
            # Reset or disable input sliders if ring(s) selected
            if len(self.pwapp.pw_interface_selected_rings) is 1:
                sel_ring = self.pwapp.pw_interface_selected_rings[0]
                print("Enabling and setting input sliders to selected ring values.")
                self.pwapp.pw_controller.enable_inputs()
                self.pwapp.pw_controller.set_inputs(sel_ring.radius, sel_ring.count, sel_ring.offsetDegrees)
            elif len(self.pwapp.pw_interface_selected_rings) > 1:
                print("Disabling inputs due to multiple selection.")
                self.pwapp.pw_controller.clear_inputs()
                self.pwapp.pw_controller.disable_inputs()
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
        print("REDRAWING CANVAS")
        self.pw_canvas.delete("all")
        self.pwapp.working_struct.draw(self.pw_canvas)

    def _rebuild_list_box(self):
        '''Formerly update_list_box.
        Rebuild the pw_list_box from the current contents of working_struct.
        ring_array . IID's are explicitly set to coincide with the StickerRing.id       to simplify lookups for click events.'''
        for item in self.pw_list.get_children():
            self.pw_list.delete(item)
        sorted_rings = sorted(self.pwapp.working_struct.ring_array.values(), key= lambda ring: ring.radius)
        # for i, key in enumerate(sorted_rings, start=1):
        for i, ring in enumerate(sorted_rings, start=1):
            # ring = self.pwapp.working_struct.ring_array[key]
            self.pw_list.insert(parent="", index=i, iid=int(ring.id), text=i,
                    values=ring.as_tuple())
            # update selected state also from .selected prop!
            if ring.selected:
                self.pw_list.selection_add(int(ring.id))

    def _update_ring_selection_with_list_click(self, event):
        '''Formerly _update_ring_selection.  Bound to click events on
        pw_list_box. Unlike the canvas click handler, we don't need to track
        the selected item within the widget or explicitly highlight it, so we
        just need to pass the id of the selected ring back to the
        panawave_struct. pw_list_box.selection() returns an IID; these are
        explicitly set when refreshing the list to make this lookup trivial.
        pw_list_box.selection() is stateful so we assume the values it returns 
        are canonical.
        1. Propogate selected state back to the working_struct,
        2. Update the interface's internal list of selected items,
        3. Redraw the rings on canvas with new selections.
        4. Reset the input sliders (if applicable).'''
        # IID's are set at creation to coincide with .id property 
        # so we can directly look up the clicked item.

        list_selection_array = self.pw_list.selection()
        print("List box is reporting current selection as: ",
                list_selection_array)
        # Clear the interface's working list of selected items
        self.pwapp.pw_interface_selected_rings = []
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
            self.pwapp.pw_interface_selected_rings.append(selected_ring)
            selected_ring.selected = True
        # self._pw_input_reset()
        self.pwapp.pw_controller.clear_inputs()
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            print("Exactly one ring selected; setting input sliders to its values.")
            (rad, count, offset) = self.pwapp.pw_interface_selected_rings[0].radius, \
            self.pwapp.pw_interface_selected_rings[0].count, \
            self.pwapp.pw_interface_selected_rings[0].offsetDegrees
            self.pwapp.pw_controller.set_inputs(rad, count, offset)
        elif len(self.pwapp.pw_interface_selected_rings) > 1:
            print("Disabling inputs as multiple rings are selected")
            self.pwapp.pw_controller.disable_inputs()
        self._rebuild_pw_canvas()

    def _pw_interface_clear_selection(self, event=None):
        '''Bound to ESC when pw_listbox has selection.'''
        # self.pw_list_box.selection_set('')
        self.pwapp.pw_interface_selected_rings = []
        for ring in self.pwapp.working_struct.ring_array.values():
            ring.selected = False
        self._rebuild_list_box()
        self._rebuild_pw_canvas()
        print("Cleared selection.")
        # TODO This is probably a messy interface but...just calling the click
        # handler to propogate the cleared selection back to the object
        # self._click_pw_listbox()

    # !!!!!!!!!!!!!!!!!! TODO TODO TODO !!!!!!!!!!!!!!!!!!!
    # This is being deprecated and replaced with PWController.clear_inputs() and
    # .set_inputs()
    def _pw_input_reset(self):
        '''Reset the input and sliders to reflect current selected ring.
        If more than one ring is selected, disable the inputs.'''
        # Sliders modify selected ring's attributes in realtime;
        # if no ring is selected they just adjust the input value
        # and wait for the 'Submit' button to do anything with them.
        sliders = (self.pw_slider_radius, self.pw_slider_count, self.pw_slider_offset)
        inputs = (self.pw_input_radius, self.pw_input_count, self.pw_input_offset)
        if len(self.pwapp.pw_interface_selected_rings) == 1:
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

    # !!!!!!!!!!!!!!!!!! TODO TODO TODO !!!!!!!!!!!!!!!!!!!
    # Are the following three methods being used? Think they need to migrate

    # to PanawaveStruct
    # Moved to PWController because this is only called by the widgets therein.
    # def update_active_ring_radius(self, rad):
    #     print("updating ring radius with value: ", rad)
    #     if len(self.pw_interface_selected_rings) == 1:
    #         self.pw_interface_selected_rings[0].set_radius(rad)
    #     self.pw_input_radius.delete(0, END)
    #     self.pw_input_radius.insert(0, rad)
    #     self._rebuild_pw_canvas()
    #     self._rebuild_list_box()

    # def update_active_ring_count(self, count):
    #     if len(self.pw_interface_selected_rings) == 1:
    #         self.pw_interface_selected_rings[0].set_count(count)
    #     if self.selected_ring is not None:
    #         self.selected_ring.set_count(int(count))
    #         self.selected_ring.draw(self.pw_canvas)
    #     self.pw_input_count.delete(0, END)
    #     self.pw_input_count.insert(0, count)
    #     self._rebuild_pw_canvas()
    #     self._rebuild_list_box()

    # def update_active_ring_offset(self, deg):
    #     if len(self.pw_interface_selected_rings) == 1:
    #         self.pw_interface_selected_rings[0].set_offset(deg)
    #     if self.selected_ring is not None:
    #         self.selected_ring.set_offset(deg)
    #         self.selected_ring.draw(self.pw_canvas)
    #     self.pw_input_offset.delete(0, END)
    #     self.pw_input_offset.insert(0, deg)
    #     self._rebuild_pw_canvas()
    #     self._rebuild_list_box()








class PWCanvas(PWWidget, tkinter.Canvas):
    # basic assumptions of the canvas: origin at center, radial
    # positions specified by setting radius along pos. Y axis and
    # then performing clockwise rotation.

    def __init__(self, width=600, height=600, row=None, column=None, columnspan=None, rowspan=None, **kwargs):
        tkinter.Canvas.__init__(self, self.pwapp.master, width=width, height=height, **kwargs)
        self.configure(scrollregion=(-300,-300,300,300)) # this will position origin at center
        # center crosshairs
        self.create_line(-40, -20, 40, 20, fill="red", dash=(4, 4))
        self.create_line(-40, 20, 40, -20, fill="red", dash=(4, 4))
        self.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, sticky=(N,E,S,W))
        # self.bind("<Configure>", foo) 
        # will probably need to implement this binding in order to scale
        # drawn elements as the window resized.


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

    def selection(self):
        return self.list.selection()

    def selection_add(self, id):
        self.list.selection_add(id)


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
        self.pw_input_submit = PWSubmitButton(text="Create")
        self.pw_input_submit.config(command=self.submit_new_ring)


    def update_active_ring_radius(self, rad):
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            print("updating ring radius with value: ", rad)
            self.pwapp.pw_interface_selected_rings[0].set_radius(rad)
            self.pwapp.viewer._rebuild_pw_canvas()
        else:
            print("Not updating ring properties because not exactly one ring selected.")

    def update_active_ring_count(self, count):
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            print("updating ring count with value: ", count)
            self.pwapp.pw_interface_selected_rings[0].set_count(int(count))
            self.pwapp.pw_interface_selected_rings[0].draw(self.pwapp.viewer.pw_canvas)
            self.pwapp.viewer._rebuild_pw_canvas()
        else:
            print("Not updating ring properties because not exactly one ring selected.")

    def update_active_ring_offset(self, deg):
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            print("updating ring offset with value: ", deg)
            self.pwapp.pw_interface_selected_rings[0].set_offset(deg)
            self.pwapp.pw_interface_selected_rings[0].draw(self.pwapp.viewer.pw_canvas)
            self.pwapp.viewer._rebuild_pw_canvas()
        else:
            print("Not updating ring properties because not exactly one ring selected.")

    def submit_new_ring(self, *args):
        '''validate the input and submit it to our current struct.
        will accept event objects from bindings but currently ignores
        them.'''
        if self.pwapp.working_struct.ephemeral_state['animating']:
            # TODO there's actually no reason we need to stop animation except
            # that the radial_speeds for rings are assigned when the anim. is
            # initialized, and because for most of the anim method adding a new
            # ring will neccessitate recalculating all speeds.  the simple
            # solution would just be to call toffle_animation again at the end
            # of this function.
            self.toggle_animation()
        self.pwapp.working_struct.add_ring(self.pw_slider_radius.get_value(), \
                self.pw_slider_count.get_value(), \
                self.pw_slider_offset.get_value())
        self.pwapp.working_struct.draw(self.pwapp.viewer.pw_canvas)
        # reset focus for a new ring entry
        self.pw_slider_radius.input_box.focus_set()
        self.pwapp.update_list_box()

    def set_inputs(self, radius, count, offset):
        '''Update input widgets to reflect selected values. Controls should be explicitly enabled with enable_inputs() if appropriate'''
        sliders = (self.pw_slider_radius, self.pw_slider_count, self.pw_slider_offset)
        for slider, value in zip(sliders, (radius, count, offset)):
            slider.set_value(value)

    def clear_inputs(self):
        '''Reset all input widgets to zero value. Controls should be explicitly disabled with disable_inputs() if appropriate.'''
        sliders = (self.pw_slider_radius, self.pw_slider_count, self.pw_slider_offset)
        for slider in sliders:
            slider.set_value(0)

    def disable_inputs(self):
        '''Disable input controls.'''
        sliders = (self.pw_slider_radius, self.pw_slider_count, self.pw_slider_offset)
        for slider in sliders:
            slider.scale.state(["disabled"]) # well this is stupid...
            slider.input_box.configure(state=DISABLED)

    def enable_inputs(self):
        ''''Enable input controls.'''
        sliders = (self.pw_slider_radius, self.pw_slider_count, self.pw_slider_offset)
        for slider in sliders:
            slider.scale.state(["!disabled"]) # ...and even stupider!
            slider.input_box.configure(state=NORMAL)


class PWSlider(tkinter.Frame, PWWidget):
    '''Slider with accompanying input box, native theme, and option to snap to
    integers. Set the 'var' local property to a variable that should be adjusted
    by the controller.'''
    def __init__(self, setter_callback=None, orient=VERTICAL, length=120, row=None, column=None, **kwargs):
        print("PWSlider being initted; self.pwapp.master is: " + repr(self.pwapp.master))
        super().__init__()
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
        # Initialize with minimum value. Otherwise these are set to null.
        if kwargs['from_']:
            print("Setting initial slider value to: " + str(kwargs['to']))
            self.set_value(kwargs['to'])
        else:
            print("Setting initial slider value to 0 as no 'to' was declared.")
            self.set_value(0)

    def set_value(self, val):
        '''Set child widgets to specified value. callback will not be triggered
        when using this method.'''
        self.scale.config(command='')
        self.input_box.delete(0, END)
        self.input_box.insert(0, val)
        self.scale.set(val)
        self.scale.config(command=self._slider_handler)

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
        self.details_button.configure(takefocus=0)# skip when tabbing thru fields
        self.details_button.grid(row=0, column=0)
        self.scale.grid(row=1, column=0, pady=4)
        self.input_box.grid(row=2, column=0)
        # subtract the height of the new button from the slider
        print("PWDetailedSlider Frame height being reported as", self.winfo_height())
        print("Initial slider and button height being reported as: ", self.scale.winfo_height(), self.details_button.winfo_height())
        # button height is 30, at least on linux. It would be better to
        # reference details_button.winfo_height(), but apparently this value is
        # not calculated until the window is drawn and returns 1 if used here.
        self.scale.config(length=(self.length - 30))


class PWSubmitButton(PWWidget, ttk.Button):
    '''New ring submit button.'''


class PWAnimController(PWWidget, tkinter.Frame):
    '''Combined selection box and animation control button. This widget will
    operate on the working_struct.'''
    def __init__(self, values=None, row=None, column=None, columnspan=None):
        tkinter.Frame.__init__(self, self.pwapp.master)
        if values == None:
            # TODO: We need to use an ordered dict to keep this in a consistent order!
            self.methods = {"Random": "random",
                    "Linear": "linear",
                    "Reverse Linear": "reverse-linear"
                    }
        else:
            self.methods = values
        self.combo = ttk.Combobox(self, values=list(self.methods.keys()), state="readonly", width=15) # apparently no way to not set a width? default is 20
        self.combo.grid(row=0, column=0, sticky=(E,W), pady=2)
        # self.combo.pack(expand=True, fill='x', side='left', anchor=W)
        self.combo.current(0) # init with 1st item selected
        self.combo.bind("<<ComboboxSelected>>", self._set_anim_method)
        self.toggle_button = ttk.Button(self, text="Start", width=5, command=self.toggle_animation)
        self.toggle_button.grid(row=0, column=1, rowspan=2, padx=4, pady=2)
        self.speedslider = ttk.Scale(self, orient=HORIZONTAL, from_=0, to=3, takefocus=False, command=self._set_anim_speed)
        self.speedslider.set(1.5) # init in middle
        self.speedslider.grid(row=1, column=0, sticky=(W,E), pady=2)
        self.grid(row=row, column=column, columnspan=columnspan, sticky=(E,W), pady=4)
        self.columnconfigure(0, weight=1)

    def _set_anim_method(self, event, method):
        '''Adjust animation method of working_struct and restart animation with the new method if currently active.'''
        self.pwapp.working_struct.ephemeral_state['anim_method'] = method
        self.restart_if_animating()

    def _set_anim_speed(self, speed):
        '''Adjust animation speed scaler of working_struct and restart animation if currently active. Currently, the default for this value is 1.5 so this is mapped to the center of the slider.'''
        self.pwapp.working_struct.persistent_state['master_orbit_speed'] = float(speed) # stupid ttk.Scale returns a string
        self.restart_if_animating()

    def toggle_animation(self):
        if self.pwapp.working_struct.ephemeral_state['animating'] is True:
            self.pwapp.working_struct.stop_animation()
            self.pwapp.pw_anim_control.toggle_button.configure(text="Start")
        else:
            self.pwapp.working_struct.orbit(method=self.methods[self.combo.get()])
            self.pwapp.pw_anim_control.toggle_button.configure(text="Stop")


    def restart_if_animating(self):
        '''Restart animation to incorporate value adjustments. Do nothing if not animating.'''
        if self.pwapp.working_struct.ephemeral_state['animating'] is True:
            self.pwapp.working_struct.stop_animation()
            self.pwapp.working_struct.orbit(method=self.pwapp.working_struct.ephemeral_state['anim_method'])

# =============================================================================
# Reference shite copied from the previous implementation below. All should be
# migrated to new classes.
#
#    def execute_console_input(self, *args):
#        '''execute arbitrary commands from the console box,
#        update the UI, and clear input's contents'''
#        statement = self.pw_console.get()
#        self.console_history.append(statement)
#        try:
#            eval(statement)
#        except:
#            e = sys.exc_info()
#            print("***Console input generated the following error:***")
#            print(e)
#        self.pwapp.working_struct.draw(self.pw_canvas)
#        self.update_list_box()
#        sleep(.5)
#        self.console_history_offset = 0
#        self.pw_console.delete(0, END)
#
#    def navigate_console_history(self, event):
#        '''walk through input history and replace pw_console contents
#        the offset is stored as a negative integer, used directly as
#        a reverse index. This is fine because although the list length
#        changes every time we input a command, we're not caring about
#        saving the history index then anyway.'''
#        print("keypress received: ", event.keysym)
#        if event.keysym == "Up":
#            new_offset = self.console_history_offset - 1
#        elif event.keysym == "Down":
#            new_offset = self.console_history_offset + 1
#        print("testing offset: ", new_offset)
#        hist = self.console_history
#        hist_len = len(hist)
#        print("hist len: ", hist_len)
#        if new_offset >= 0:
#            # return to a blank slate if we arrive back at the
#            # end of the history.
#            self.pw_input_offset = 0
#            self.pw_console.delete(0, END)
#            print("reset offset to zero.")
#            return
#        if (0 > new_offset >= -hist_len):
#            self.console_history_offset = new_offset
#            self.pw_console.delete(0, END)
#            self.pw_console.insert(END, hist[new_offset])
#            print ("decided offset ", new_offset, " is valid.")

