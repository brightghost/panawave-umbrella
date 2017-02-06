import logging as log
import tkinter
# tkinter constants that are easier to ref in the base namespace
from tkinter import N,E,S,W, VERTICAL, HORIZONTAL, END, CURRENT, DISABLED, NORMAL
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.ttk import Treeview
from tkinter import ttk, TclError
import sys
import os
from time import sleep
from ast import literal_eval
try:
    from PIL import Image, ImageTk
    PIL_INSTALLED = True
except ImportError:
    PIL_INSTALLED = False

import radialstructs

class PWWidget:
    '''Parent class for Panawave Widgets. PWWdigets all extent a tkinter
    widget, as well as PWWidget.  Among other things, this parent class manages
    the references to the PWApp, which extends Tk and thus serves as a master
    for the tkinter widgets as well as a container for app state data.  '''
    pwapp = None # this needs to be overriden when the app is instantiated.

    def disable_children(self, widget):
        '''Make a best-effort to disable all child widgets of the given parent.
        Will not report any successes or failures.'''
        log.debug("Attempting to disable children for widget {0}".format(repr(widget)))
        # first, attempt to recurse to next level
        try:
            for child in widget.winfo_children():
                log.debug("Found winfo_children of object {0}; calling recursivley on them.".format(repr(widget)))
                self.disable_children(child)
        except AttributeError:
            log.debug("No further winfo_children found for object {0}; presuming we are at deepest level.".format(repr(widget)))
        # then, disable this level
        try:
            widget.state(["disabled"])
            log.debug("Disabled widget {0}".format(repr(widget)))
            return
        except (AttributeError, TclError):
            log.debug("Did not find state method for {0}; trying config.".format(widget))
            pass
        try:
            widget.config(state=DISABLED)
            log.debug("Disabled widget {0}".format(repr(widget)))
            return
        except (AttributeError, TclError):
            log.debug("Did not find config or state methods for {0}; "
                    "ignoring attempt to disable.".format(repr(widget)))
            return

    def enable_children(self, widget):
        '''Make a best-effort to enable all child widgets of the given parent.
        Will not report any successes or failures.'''
        log.debug("Attempting to enable children for widget {0}".format(repr(widget)))
        # first, attempt to recurse to next level
        try:
            for child in widget.winfo_children():
                log.debug("Found winfo_children of object {0}; calling recursivley on them.".format(repr(widget)))
                self.enable_children(child)
        except AttributeError:
            log.debug("No further winfo_children found for object {0}; presuming we are at deepest level.".format(repr(widget)))
        # then, enable this level
        try:
            widget.state(["!enabled"])
            log.debug("Disabled widget {0}".format(repr(widget)))
            return
        except (AttributeError, TclError):
            log.debug("Did not find state method for {0}; trying config.".format(widget))
            pass
        try:
            widget.config(state=NORMAL)
            log.debug("Disabled widget {0}".format(repr(widget)))
            return
        except (AttributeError, TclError):
            log.debug("Did not find config or state methods for {0}; "
                    "ignoring attempt to enable.".format(repr(widget)))
            return


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
        # TODO/DOH! Can't grab the working_struct from pwapp because it doesn't
        # have one yet when this is initted.... the order of intialization should
        # flipped to fix this but for now just gonna do it the lazy way.
        # self.working_struct = self.pwapp.working_struct
        pass

    def create_canvas(self, *args, **kwargs):
        self.pw_canvas = PWCanvas(*args, **kwargs)
        self.pw_canvas.bind("<Button-1>", self._click_pw_canvas)
        self.pw_canvas.bind("<Double-Button-1>", self._double_click_pw_canvas)
        # don't draw border when child console widgets are focused
        self.pw_canvas.configure(highlightthickness=0)

    def create_list(self, *args, **kwargs):
        self.pw_list = PWListBox(*args, **kwargs)
        self.pw_list.list.bind('<ButtonRelease-1>',
                self._update_ring_selection_with_list_click)
        self.pw_list.list.bind("<Key-Escape>",
                self._pw_interface_clear_selection)

    def rebuild(self):
        '''Rebuild all aspects of the views to reflect current conditions.'''
        self._rebuild_pw_canvas()
        self._rebuild_pw_list()

    def _rebuild_pw_canvas(self):
        '''Clear and then redraw the working_struct to the canvas.'''
        log.debug("REDRAWING CANVAS")
        self.pw_canvas.delete("all")
        self.pwapp.working_struct.draw(self.pw_canvas)

    def _rebuild_pw_list(self):
        '''Clear and then redraw the list. This lives here primarily so we
        don't need to bother with re-sorting the ring_array evertime a new draw
        call is issued. IID's are explicitly set to coincide with the
        StickerRing.id to simplify lookups for click events.'''
        log.debug("REBUILDING LIST")
        self._clear_pw_list()
        sorted_rings = sorted(self.pwapp.working_struct.ring_array.values(),
            key=lambda ring: ring.radius)
        log.debug("Sorted rings in prep for redrawing listbox; new order:")
        for r in sorted_rings:
             log.debug(r.radius)
        for i, ring in enumerate(sorted_rings, start=1):
            self.pw_list.insert(parent="", index=i, iid=int(ring.id),
                text=i, values=ring.as_tuple())
            # update selected state also from .selected prop! 
            if ring.selected:
                self.pw_list.selection_add(int(ring.id))

    def _clear_pw_list(self):
        for item in self.pw_list.get_children():
            self.pw_list.delete(item)

    def _click_pw_canvas(self, event):
        '''Handler for clicks on canvas.'''
        self._update_selected_ring_with_canvas_click(event)

    def _update_selected_ring_with_canvas_click(self, event):
        '''Formerly _update_clicked_canvas_item
        Bound to clicks on the pw_canvas. Checks for the tk 'CURRENT' tag,
        which represents an item under the cursor, then update the
        selected_ring array if it's determined a ring was clicked.
         1. Toggle the .selected property if it's determined a ring was clicked,
         2. Rebuild the interface's internal list of selected items,
         3. Redraw the canvas,
         4. Rebuild the pw_list_box from the ring_array,
         5. Reset the input sliders (if applicable),
         6. Reconfigure quantization on count slider per locked status.'''
        #TODO: There's no reason to replicate the selection state to the
        # working_struct and it's going to get us in trouble.
        # pwapp.pw_interface_selected_rings should be the canonical and only
        # record of this.
        if self.pw_canvas.find_withtag(CURRENT):
            clicked_obj_id = self.pw_canvas.find_withtag(CURRENT)[0]
            log.debug("Clicked on object with id {0}".format(clicked_obj_id))
            try:
                # check if it's tagged as part of a ring...
                clicked_ring_tag = next(
                        tag for tag in self.pw_canvas.gettags(
                            clicked_obj_id) if "ring-" in tag)
                log.debug("The clicked object has the ring tag {0}".format(clicked_ring_tag))
                clicked_ring = self.pwapp.working_struct.ring_array[clicked_ring_tag.strip("ring-")]
                clicked_ring_id = clicked_ring_tag.strip("ring-")
                log.debug("Adding to the selected_ring list the ring with "
                        "key {0}".format(clicked_ring_id))
            except NameError:
                # it's possible we'll click an object other than a sticker
                log.debug("A canvas object was clicked but no 'ring-*' tag was found. Must not be a ring object.")
                return
        # Determine action based on which modifier keys may be held down
        # Bitwise 'AND' of the bitmask returned by .state
            if event.state & 0x004:
                # Ctrl-key modifier is enabled
                # Toggle the .selected state
                clicked_ring.toggle_selected_state()
                log.debug("Ctrl-clicked ring; toggled the selected state of "
                        "the ring with key {0}".format(clicked_ring.id))
            else:
                # no Ctrl-key modifier; reset selection
                for ring in self.pwapp.working_struct.ring_array.values():
                    ring.selected = False
                clicked_ring.selected = True
                log.debug("Clicked a ring without Ctrl modifier; clearing "
                        "previous selection and selecting ring with "
                        "key {0}".format(clicked_ring.id))
            # Rebuild the pw_interface_selected_rings from the updated data in
            # the PanawaveStruct
            self.pwapp.pw_interface_selected_rings = [ring for ring in \
                    self.pwapp.working_struct.ring_array.values() if \
                    ring.selected]
            log.debug("New contents of pw_interface_selected_rings: {0}".format(
                self.pwapp.pw_interface_selected_rings))
            # Redraw with the newly-selected rings;
            # rebuild the list_box with newly-selected rings.
            self.rebuild()
            # Reset or disable input sliders if ring(s) selected
            if len(self.pwapp.pw_interface_selected_rings) is 1:
                sel_ring = self.pwapp.pw_interface_selected_rings[0]
                log.debug("Enabling and setting input sliders to selected "
                    "ring values.")
                self.pwapp.pw_controller.enable_inputs()
                self.pwapp.pw_controller.set_inputs_for_ring_obj(sel_ring)
            elif len(self.pwapp.pw_interface_selected_rings) > 1:
                log.debug("Disabling inputs due to multiple selection.")
                self.pwapp.pw_controller.clear_inputs()
                self.pwapp.pw_controller.disable_inputs()
        else:
            log.debug("No CURRENT tag returned, must not have clicked an object.")

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
        3. Redraw the rings on canvas with new selections,
        4. Reset the input sliders (if applicable),
        5. Set pw_slider_count.quantize in accordance with the
        persistent_state['unlocked_rings']'''
        # IID's are set at creation to coincide with .id property 
        # so we can directly look up the clicked item.

        list_selection_array = self.pw_list.selection()
        log.debug("List box is reporting current selection as: {0}".format(
                list_selection_array))
        # Clear the interface's working list of selected items
        self.pwapp.pw_interface_selected_rings = []
        # there's probably a more clever way to do this with a list
        # comprehension but the scoping issues with listcomps are way over
        # my head at the moment:
        # http://stackoverflow.com/q/13905741
        # Just going to reset the .selected atribute on all rings then
        # set it again based on what's reported by the TreeView.
        for ring in self.pwapp.working_struct.ring_array.values():
            ring.selected = False
        for iid in list_selection_array:
            selected_ring = self.pwapp.working_struct.ring_array[iid]
            self.pwapp.pw_interface_selected_rings.append(selected_ring)
            selected_ring.selected = True
        self.pwapp.pw_controller.clear_inputs()
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            log.debug("Exactly one ring selected; "
                "setting input sliders to its values.")
            sel_ring = self.pwapp.pw_interface_selected_rings[0]
            self.pwapp.pw_controller.set_inputs_for_ring_obj(sel_ring)
        elif len(self.pwapp.pw_interface_selected_rings) > 1:
            log.debug("Disabling inputs due to multiple selection.")
            self.pwapp.pw_controller.clear_inputs()
            self.pwapp.pw_controller.disable_inputs()
        self._rebuild_pw_canvas()

    def _double_click_pw_canvas(self, event=None):
        '''Bound to double click on canvas. Clears ring selection if empty area
        is double-clicked. NOTE: Our single click handler will still fire!
        This is okay, because that handler does nothing when empty canvas is
        clicked.'''
        if self.pw_canvas.find_withtag(CURRENT):
            log.debug("Double clicked but there was an object under the mouse, "
                "taking no action")
        else:
            log.debug("Double clicked empty canvas area; clearing selection.")
            self._pw_interface_clear_selection()

    def _pw_interface_clear_selection(self, event=None):
        '''Bound to ESC when pw_listbox has selection.'''
        # self.pw_list_box.selection_set('')
        self.pwapp.pw_interface_selected_rings = []
        for ring in self.pwapp.working_struct.ring_array.values():
            ring.selected = False
        self.rebuild()
        log.debug("Cleared selection.")


class PWCanvas(PWWidget, tkinter.Canvas):
    '''basic assumptions of the canvas: origin will remain at center, radial
    positions are specified by setting radius along pos. Y axis and then
    performing clockwise rotation. In the future, will support scaling contents
    to remain within viewport as the canvas is resized.'''

    def __init__(self, master=None, **kwargs):
        '''PWCanvas extends tkinter canvas so all of it's arguments can be
        passed. Optionally, additional grid layout arguments can be provided
        (see gridargs for available options). If row and column are emitted, no
        layout will be performed.'''
        log.debug("Initializing a PWCanvas with arguments: " + repr(kwargs.items()))
        if master is None:
            master = self.pwapp.master
        # TODO: It was a mistake to support layout arguments when initializing
        # PWWidgets.  Now we are using different geometry managers in different
        # windows, so we're really not making anything cleaner with this. These
        # should be removed and all layout code should call the native .grid
        # method; PWWidget could have a .grid class method which allows
        # it to be called on 'compound' widgets which do not inherit PWWidget
        # directly. (Or perhaps they should all just inherit tkinter.Frame to
        # end this nonsense.)
        gridargs = {'row': None, 'column': None, 'columnspan': None, 'rowspan': None}
        for arg in gridargs:
            try:
                gridargs[arg] = kwargs.pop(arg)
            except KeyError:
                pass
        tkinter.Canvas.__init__(self, master, **kwargs)
        # center crosshairs
        # self.create_line(-40, -20, 40, 20, fill="red", dash=(4, 4))
        # self.create_line(-40, 20, 40, -20, fill="red", dash=(4, 4))
        if gridargs['row'] is not None and gridargs['column'] is not None:
            self.grid(row=gridargs['row'], column=gridargs['column'], rowspan=gridargs['rowspan'],
                columnspan=gridargs['columnspan'], sticky=(N,E,S,W))

        # BINDINGS
        self.bind("<Configure>", self._recenter_scroll_region)
        # TODO: implement additional bindings in order to scale
        # drawn elements as the window resized.

    def _recenter_scroll_region(self, event=None):
        '''Scroll the origin point back to the center of the canvas. This
        should be called any time the canvas size changes.'''
        h, w = (self.winfo_height(), self.winfo_width())
        log.debug("Re-scrolling origin to center of canvas based on new " +
                "dimensions {0},{1}.".format(w, h))
        self.configure(scrollregion=(-w*.5, -h*.5, w*.5, h*.5))
        self._scale_items()

    def _scale_items(self, event=None):
        '''Currently this only flips all items along the y axis, effectively
        letting us use a conventional Cartesian coordinate system. This
        abstraction will break, however, every time a new object is drawn, so
        we must bind it to all canvas manipulations. In the future this
        function will also scale the items in order to fill available space, if
        the canvas is so configured.'''
        self.scale("all", 0, 0, 1, -1)

    def clear(self):
        '''Remove all canvas items.'''
        self.delete("all")



class PWListBox(PWWidget, tkinter.Frame):
    '''A listing of rings, using tkinter.Treeview for dumb reasons.'''

    def __init__(self, row=None, column=None, columnspan=None, **kwargs):
        # Parent frame for internal layout management
        tkinter.Frame.__init__(self, self.pwapp.master)

        # Struct List
        # This is now using ttk.Treeview because tkinter listboxes are
        # completely incapable of sanely displaying tabular data due to having
        # no access to a monospaced font!
        # http://stackoverflow.com/q/3794268
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
        ''' Create ring attribute control sliders and ring submit button.
        Sliders modify selected ring's attributes in realtime; if no ring is
        selected they just adjust the input value and wait for the 'Submit'
        button to do anything with them. In the future, a second mode will be
        implemented for the sliders which modifies multiple selected rings
        equally using pushbuttons, rather than disabling for multiple
        selections.'''
        self.pw_slider_radius = PWSlider(
                setter_callback=self.update_active_ring_radius,
                quantize=2,
                from_=200.0,
                to=1.0)
        self.pw_slider_radius.input_box.bind("<Return>", self.submit_new_ring)
        self.pw_slider_count = PWDetailedSlider(
                setter_callback=self.update_active_ring_count,
                details_button_callback=self.spawn_period_dialog,
                quantize=0,
                from_=50.0,
                to=1.0)
        self.pw_slider_count.input_box.bind("<Return>", self.submit_new_ring)
        self.pw_slider_offset = PWSlider(
                setter_callback=self.update_active_ring_offset,
                quantize=1,
                from_=360.0,
                to=0.0)
        self.pw_slider_offset.input_box.bind("<Return>", self.submit_new_ring)

        # new ring submit button
        self.pw_input_submit = PWButton(text="Create")
        self.pw_input_submit.config(command=self.submit_new_ring)

    def update_active_ring_radius(self, rad):
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            log.debug("updating ring radius with value: {0}".format(rad))
            self.pwapp.pw_interface_selected_rings[0].set_radius(rad)
            self.pwapp.rebuild_views()
        else:
            log.debug("Not updating ring properties because not exactly "
                    "one ring selected.")

    def update_active_ring_count(self, count):
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            log.debug("updating ring count with value: {0}".format(count))
            self.pwapp.pw_interface_selected_rings[0].set_count(int(count))
            self.pwapp.rebuild_views()
        else:
            log.debug("Not updating ring properties because not exactly "
                    "one ring selected.")

    def update_active_ring_offset(self, deg):
        if len(self.pwapp.pw_interface_selected_rings) == 1:
            log.debug("updating ring offset with value: {0}".format(deg))
            self.pwapp.pw_interface_selected_rings[0].set_offset(deg)
            self.pwapp.rebuild_views()
        else:
            log.debug("Not updating ring properties because not exactly "
                    "one ring selected.")

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
        self.pwapp.working_struct.add_ring(
                self.pw_slider_radius.get_value(),
                self.pw_slider_count.get_value(),
                self.pw_slider_offset.get_value())
        self.pwapp.working_struct.draw(self.pwapp.viewer.pw_canvas)
        # reset focus for a new ring entry
        self.pw_slider_radius.input_box.focus_set()
        self.pwapp.rebuild_views()

    def set_inputs(self, radius, count, offset):
        '''Update input widgets to reflect selected values. Controls should be
        explicitly enabled with enable_inputs() if appropriate'''
        sliders = (self.pw_slider_radius,
                self.pw_slider_count,
                self.pw_slider_offset)
        for slider, value in zip(sliders, (radius, count, offset)):
            slider.set_value(value)

    def set_inputs_for_ring_obj(self, sticker_ring_obj):
        '''Should be called whenever a new ring is selected. Use this rather
        than setting sliders directly with set_inputs in order to take in
        account the ring's 'unlocked_rings' state, as well.'''
        r = sticker_ring_obj
        (rad, count, offset) = r.radius, \
            r.count, \
            r.offsetDegrees
        self.set_inputs(rad, count, offset)
        if r.id in self.pwapp.working_struct.persistent_state['unlocked_rings']:
            self.pw_slider_count.quantize = 0
        else:
            self.pw_slider_count.quantize = 1 / len(r.scaler_list)

    def clear_inputs(self):
        '''Reset all input widgets to zero value. Controls should be explicitly
        disabled with disable_inputs() if appropriate.'''
        sliders = (self.pw_slider_radius,
                self.pw_slider_count,
                self.pw_slider_offset)
        for slider in sliders:
            slider.set_value(0)

    def disable_inputs(self):
        '''Disable input controls.'''
        sliders = (self.pw_slider_radius,
                self.pw_slider_count,
                self.pw_slider_offset)
        for slider in sliders:
            slider.scale.state(["disabled"]) # well this is stupid...
            slider.input_box.configure(state=DISABLED)

    def enable_inputs(self):
        ''''Enable input controls.'''
        sliders = (self.pw_slider_radius,
                self.pw_slider_count,
                self.pw_slider_offset)
        for slider in sliders:
            slider.scale.state(["!disabled"]) # ...and even stupider!
            slider.input_box.configure(state=NORMAL)

    def spawn_period_dialog(self):
        self.pwapp.spawn_period_dialog()


class PWFileChooser(ttk.Frame, PWWidget):
    '''Combined widget with file chooser button and file name display.'''

    def __init__(self, master, **kwargs):
        '''setter_callback: A function to be called when a new file is chosen.
                            The TextIOWrapper is discarded and only string
                            representing the path is passed, because you may
                            want to do something other than reading the file in
                            as text.
        '''
        super().__init__(master=master)
        try:
            self.setter_callback = kwargs.pop('setter_callback')
        except KeyError:
            self.setter_callback = lambda: None
        self.f_display_name = tkinter.StringVar()
        self.selected_file = None
        self.label = ttk.Label(self, textvariable=self.f_display_name, relief=tkinter.SUNKEN)
        self.button = ttk.Button(self, text="...", width=5, command=self.spawn_dialog)

        # Layout
        self.label.pack(side=tkinter.LEFT, fill='both', expand=True, ipadx=2, padx=(0,4))
        self.button.pack(side=tkinter.RIGHT)

    def spawn_dialog(self):
        '''Spawn a standard tkinter file chooser dialog and report the new selection via callback.'''
        f = tkinter.filedialog.askopenfile(parent=self.winfo_toplevel())
        self.set_selection(f.name)

    def get_selection(self):
        '''Returns the selected file, if any, in the form of an IOWrapper
        object. This will automatically be passed to the setter_callback if
        defined.'''
        return self.selected_file

    def set_selection(self, path):
        '''Set selection to the given IOWrapper file object.'''
        log.debug("Setting file selection to {0}".format(repr(path)))
        if path is not None:
            f = path
            f_display = os.path.split(f)[-1]
            self.f_display_name.set(f_display)
            self.selected_file = f
            log.info("New file selected: {0}.".format(f_display))
            self.setter_callback(f)
        else:
            f_display = ""
            self.f_display_name.set("")
            self.selected_file = None
            log.info("Selection cleared.")
            self.setter_callback(None)

    def clear_selection(self):
        '''Clear selection, and fire callback, if defined, with 'None' as input.'''
        self.set_selection()


class PWSlider(tkinter.Frame, PWWidget):
    '''Slider with accompanying input box, native theme, and option to snap to
    integers. Set setter_callback to a function which should receive the final
    value, and 'quantize' to indicate a max number of significant digits (e.g
    '3' for '3.556', '0' for '3'). Alternately, a fractional 'quantize' value
    will round to whole number increments, (e.g. .25 (1/4) to round up to 4's).
    '''

    def __init__(self, setter_callback=None, orient=VERTICAL, length=120,
            row=None, column=None, quantize=None, **kwargs):
        log.debug("PWSlider being initted; self.pwapp.master is: {0}".format(
                repr(self.pwapp.master)))
        super().__init__()
        # self.row = kwargs.pop("row")
        # self.col = kwargs.pop("column")
        self.setter_callback = setter_callback
        self.length = length
        self.orient = orient
        self.quantize = quantize
        self.scale = ttk.Scale(self,
                orient=orient,
                length=self.length,
                command=self._slider_handler,
                takefocus=False,
                **kwargs)
        self.scale.grid(row=0, column=0, pady=4)
        # Input box
        self.input_box = ttk.Entry(self, width=3)
        self.input_box.grid(row=1, column=0, sticky=N)
        self.input_box.bind("<FocusOut>", self._input_box_handler)
        self.grid(row=row, column=column, pady=4)
        # Initialize with minimum value. Otherwise these are set to null.
        if kwargs['from_']:
            log.debug("Setting initial slider value to: " + str(kwargs['to']))
            self.set_value(self._quantize_value(kwargs['to']))
        else:
            log.debug("Setting initial slider value to 0 as no 'to' was declared.")
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

    def _quantize_value(self, val):
        '''Sanitize raw values according to spec:

           negative value:  no quantization performed
                        0:  truncate all decimals
        whole num. values:  truncate to specified decimal places
        fractional values:  round up to the reciprocal whole-number increment.

        NOTE: there is a sort of quantization done also by the ttk.Scale before
        its values are given to us, as it tries to rationalize the range of the
        control with it's pixel size as drawn. Therefor, it may not be possible
        to extract more precision from the controller by setting a higher
        quantization value. Even so, relying on this method will result in more
        predictable values, as ttk.Scale's quantization does not correct for
        floating point math errors.'''
        if (self.quantize == 0 or self.quantize >= 1):
            log.debug("Quantizing value to nearest "
                     "{0}  decimals".format(str(self.quantize)))
            new_val = round(val, int(self.quantize))
            if new_val % 1 == 0:
                new_val = int(new_val) # cast ints to ints for display
            log.debug("Raw value: {0}; quantized value: {1}".format(
                    str(val), str(new_val)))
            return new_val
        elif 0 < self.quantize < 1:
            step = int(1 / self.quantize)
            log.debug("Quantizing value to whole number units of {0}".format(
                    str(step)))
            new_val = int(val // step * step)
            if val % step:
                new_val = new_val + step # round up instead of down
            log.debug("Raw value: {0}; quantized value: {1}".format(
                    str(val), str(new_val)))
            return new_val
        else:
            return val

    def _slider_handler(self, event):
        '''Passes the value from slider to input box and sets var when
        adjusted.'''
        new_val = self._quantize_value(self.scale.get())
        log.debug("Updating input_box value due to slider adjustment, "
            "new val: {0}".format( new_val))
        self.input_box.delete(0, END)
        self.input_box.insert(0, new_val)
        self.setter_callback(new_val)

    def _input_box_handler(self, event):
        '''Passes value from input box to slider and sets var when losing
        focus.'''
        new_val = self.input_box.get()
        if new_val == "":
            new_val = 0
        log.debug("Updating scale value due to input_box adjustment, "
            "new val: {0}".format(new_val))
        self.scale.set(new_val)
        self.setter_callback(new_val)


class PWDetailedSlider(PWSlider):
    '''Slider with addition of a context button for accessing additional config.
    Used for the 'count' controller.'''

    def __init__(self, *args, **kwargs):
        self.details_button_callback = kwargs.pop("details_button_callback")
        PWSlider.__init__(self, *args, **kwargs)
        self.details_button = ttk.Button(
                self,
                text="...",
                width=2,
                command=self.details_button_callback)
        self.details_button.configure(takefocus=0)# skip when tabbing thru fields
        self.details_button.grid(row=0, column=0)
        self.scale.grid(row=1, column=0, pady=4)
        self.input_box.grid(row=2, column=0)
        # subtract the height of the new button from the slider
        log.debug("PWDetailedSlider Frame height being reported as {0}".format(
                self.winfo_height()))
        log.debug("Initial slider and button height being reported as: ".format(
                self.scale.winfo_height(), self.details_button.winfo_height()))
        # button height is 30, at least on linux. It would be better to
        # reference details_button.winfo_height(), but apparently this value is
        # not calculated until the window is drawn and returns 1 if used here.
        self.scale.config(length=(self.length - 30))


class PWPeriodController(PWWidget, tkinter.Frame):
    '''Combined widget which allows selecting either equidistant sticker
    spacing or a custom periodic sequence for the selected ring.'''

    def __init__(self, master=None, *args, **kwargs):
        log.debug("INITTING a PWPeriodController. {0}".format(repr(self)))
        if master:
            self.master = master
        else:
            self.master = self.pwapp.master
        tkinter.Frame.__init__(self, self.master, *args, **kwargs)
        self.mode_var = tkinter.IntVar()
        self.mode_var.set(0) #  0 == 'simple' i.e. equidistant
                             #  1 == 'complex'
                             # -1 == mixed (no mode selected)
        # http://stackoverflow.com/a/6549535
        self.period_var = tkinter.StringVar()
        self.period_var.trace("w",
                lambda name,
                index,
                mode,
                sv=self.period_var: self._entry_handler(self.period_var))
        self.f_smpl = tkinter.Frame(self, padx=18, pady=12)
        self.f_cmpx = tkinter.Frame(self, padx=18, pady=12)
        self.f_cmpx_inner = tkinter.Frame(self.f_cmpx, padx=18, pady=0)
        self.f_smpl.pack(fill='x')
        self.f_cmpx.pack(fill='x')
        self.pw_rb_simple = ttk.Radiobutton(master=self.f_smpl,
            text="Equidistant", variable=self.mode_var, value=0,
            command=self.pw_rb_simple_selected)
        self.pw_rb_complex = ttk.Radiobutton(master=self.f_cmpx, text="Complex",
            variable=self.mode_var, value=1, command=self.pw_rb_complex_selected)
        self.pw_pattern_input = tkinter.Entry(
                master=self.f_cmpx_inner, textvariable=self.period_var)
        self.pw_pattern_input_label = tkinter.Label(master=self.f_cmpx_inner,
                text="Enter a comma-delimited list of ratios, "
                "for example '1,2,2,1'.",
                state=tkinter.DISABLED,
                justify=tkinter.LEFT,
                wraplength=280)
        self.lock_var = tkinter.BooleanVar()
        self.lock_var.set(True)
        self.pw_chkbx_pattern_lock = tkinter.Checkbutton(
                master=self.f_cmpx_inner,
                text="Lock sticker count to multiples of pattern",
                variable=self.lock_var,
                command=self.update_active_ring_lock_status)

        # Layout
        self.pw_rb_simple.pack(anchor='w', pady=4)
        self.pw_rb_complex.pack(anchor='w', pady=4)
        self.f_cmpx_inner.pack(fill='x')
        self.pw_pattern_input.pack(anchor='w', fill='x', pady=4)
        self.pw_pattern_input_label.pack(anchor='w', pady=4)
        self.pw_chkbx_pattern_lock.pack(anchor='w', pady=4)

        # Attempt to bind to selection
        self.bind_to_ring(self.pwapp.pw_interface_selected_rings)

    def _entry_handler(self, string_var):
        '''Callback attached to updates of the 'Complex' text entry.'''
        entered_text = string_var.get()
        l = entered_text.split(",")
        try:
            for item in l:
                int(item)
        except (TypeError, ValueError):
            return
        self.update_active_ring_period(l)

    def fmt_scaler_list(self, sl):
        '''Returns a textual representaion of a scaler_list, compatible with
        PWPeriodController's text input.'''
        str_sl = [str(v) for v in sl]
        repr = ', '.join(str_sl)
        return repr

    def bind_to_ring(self, ring_or_rings):
        '''Manually attach this widget to a ring(s). If a selection exists
        when the widget is initialized, you do not need to call this manually.'''
        r = ring_or_rings
        if type(r) is radialstructs.StickerRing:
            # TODO: Realized in testing...this will never be reached,
            # because the pw_interface_selected_rings is always a list of 
            # one or more members.
            if r.scaler_list is None or '1':
                self.mode_var.set(0)
                self.pw_rb_simple_selected()
            elif len(r.scaler_list) > 1:
                self.mode_var.set(1)
                self.pw_pattern_input.delete(0, END)
                self.pw_pattern_input.insert(
                        0,
                        self.fmt_scaler_list(r.scaler_list))
                self.pw_rb_complex_selected()
        else:
            # attempt to enable the widget only if all selected rings
            # are in agreement
            first_sl = r[0].scaler_list
            if all(len(ring.scaler_list) == 1 for ring in r):
                self.mode_var.set(0)
                self.pw_rb_simple_selected()
            elif all(ring.scaler_list == first_sl for ring in r):
                self.mode_var.set(1)
                self.pw_pattern_input.delete(0, END)
                self.pw_pattern_input.insert(0, self.fmt_scaler_list(first_sl))
                self.pw_rb_complex_selected()
            else:
                log.debug("Multiple rings selected and their scaler_lists are "
                    "not in agreement; not selecting either mode.")
                self.mode_var.set(-1)
                log.debug("mode_var is: {0}".format(self.mode_var))

    def pw_rb_simple_selected(self):
        '''Changing the selected mode in the interface and propogate change to
        selected ring(s) scaler_list's.'''
        log.debug("Switching selected ring(s) to simple period; disabling input "
                "box because simple mode was selected.")
        self.pw_pattern_input.config(state=tkinter.DISABLED)
        self.pw_pattern_input_label.config(state=tkinter.DISABLED)
        self.pw_chkbx_pattern_lock.config(state=tkinter.DISABLED)
        self.update_active_ring_period([1])

    def pw_rb_complex_selected(self):
        '''Enable input box when complex mode is selected.'''
        log.debug("Swtching selected ring(s) to complex period; enabling input "
                "box because complex mode was selected.")
        self.pw_pattern_input.config(state=tkinter.NORMAL)
        self.pw_pattern_input_label.config(state=tkinter.NORMAL)
        self.pw_chkbx_pattern_lock.config(state=tkinter.NORMAL)
        self.update_lock_checkbox_with_active_ring_status()
        self._entry_handler(self.period_var)

    def commit_changes(self):
        '''Apply the inputted settings to the selected ring(s)'''
        pass

    def cancel_changes(self):
        #TODO: rollback "previewed" changes
        pass

    def update_active_ring_period(self, scaler_list):
        '''Apply the given scaler_list to the selected rings(s)'''
        for ring in self.pwapp.pw_interface_selected_rings:
            log.debug("updating scaler_list of ring {0} with value: {1}".format(
                repr(ring), repr(scaler_list)))
            ring.set_scaler_list(scaler_list)
        self.pwapp.viewer._rebuild_pw_canvas()

    def update_active_ring_lock_status(self, event=None):
        lock = self.lock_var.get()
            # True = lock
        if lock:
            for ring in self.pwapp.pw_interface_selected_rings:
                self.pwapp.working_struct.lock_ring_count_to_scaler(ring)
        else:
            for ring in self.pwapp.pw_interface_selected_rings:
                self.pwapp.working_struct.unlock_ring_count_from_scaler(ring)

    def update_lock_checkbox_with_active_ring_status(self):
        '''If any selected ring is locked, set checkbox to checked state.'''
        unlock_l = self.pwapp.working_struct.persistent_state['unlocked_rings']
        l = False
        for ring in self.pwapp.pw_interface_selected_rings:
            if self.pwapp.working_struct.is_count_locked_for_ring(ring):
                l = True
        if l:
            self.lock_var.set(1)


class PWBaseStickerController(PWWidget, tkinter.Frame):
    '''Combined widget which allows setting a custom sticker geometry or bitmap
    file, either for the selected ring or the whole struct.'''

    def __init__(self, master=None, *args, **kwargs):
        '''Arguments:
            master          tkinter master widget
            master_mode     modify BaseSticker for
                            the whole struct (default=False)
            all other arguments are passed to Frame.'''
        log.debug("INITTING a PWBaseStickerController. {0}".format(repr(self)))
        if master:
            self.master = master
        else:
            self.master = self.pwapp.master
        try:
            self.master_mode = kwargs.pop('master_mode')
        except KeyError:
            self.master_mode = False
        tkinter.Frame.__init__(self, self.master, *args, **kwargs)
        self.preview_sticker = None
        self.mode_var = tkinter.IntVar() #  0 == none (inherit from PWStruct; not valid in master_mode)
                                         #  1 == polygon
                                         #  2 == bitmap
                                         # -1 == mixed (no mode selected)
        self.geometry_var = tkinter.StringVar()
        # http://stackoverflow.com/a/6549535
        self.geometry_var.trace("w",
                lambda name,
                index,
                mode,
                sv=self.geometry_var: self._entry_handler(self.geometry_var))
        self.geometry_var._report_exception = lambda err=None: log.debug(
                "Exception encountered while tracing geomtry_var. {0}".format(err))

        ## Top-level widgets
        self.preview_canvas = PWCanvas(self, height=50, width=50)
        self.preview_canvas.config(relief="sunken", border=2, height=150)
        self.f_inherit = tkinter.Frame(self, height=52, width=150, padx=18, pady=12)
        if self.master_mode is False:
            self.pw_rb_inherit = ttk.Radiobutton(master=self.f_inherit,
                    text="Inherit from master", variable=self.mode_var, value=0,
                    command=self.pw_rb_inherit_selected)
        self.f_poly = tkinter.Frame(self, padx=18, pady=12)
        self.f_bmp = tkinter.Frame(self, padx=18, pady=12)
        self.f_poly_inner = tkinter.Frame(self.f_poly, padx=18, pady=0)
        self.f_bmp_inner = tkinter.Frame(self.f_bmp, padx=18, pady=0)
        self.pw_rb_poly = ttk.Radiobutton(master=self.f_poly,
            text="Polygon", variable=self.mode_var, value=1,
            command=self.pw_rb_poly_selected)
        self.pw_rb_bmp = ttk.Radiobutton(master=self.f_bmp, text="Bitmap",
            variable=self.mode_var, value=2, command=self.pw_rb_bmp_selected)

        # Poly mode inner contents
        self.pw_geom_input = tkinter.Entry(
                master=self.f_poly_inner, textvariable=self.geometry_var)
        self.pw_geom_input_label = tkinter.Label(master=self.f_poly_inner,
                text="Enter a list of points defining a polygon, "
                "in the form '(x1,y1)(x2,y2)(x3,y3)...'",
                justify=tkinter.LEFT,
                wraplength=260)
        self.centroid_var = tkinter.BooleanVar()
        self.centroid_var.set(True)
        self.pw_chkbx_auto_centroid = tkinter.Checkbutton(
                master=self.f_poly_inner,
                text="Calculate centroid automatically",
                variable=self.centroid_var,
                command=self.update_centroid_calc_method)

        # Bitmap mode inner contents
        if PIL_INSTALLED:
            self.pw_bmp_input = PWFileChooser(self.f_bmp_inner, setter_callback=self._bmp_entry_handler)
            self.bmp_size_enabled = tkinter.BooleanVar()
            self.bmp_size_var = tkinter.StringVar()
            self.bmp_size_var.trace("w",
                    lambda name, index, mode,
                    sv=self.bmp_size_var: self._bmp_entry_handler(self.pw_bmp_input.get_selection()))
            self.bmp_size_var._report_exception = lambda err=None: log.debug(
                    "Exception encountered while tracing geomtry_var. {0}".format(err))
            self.pw_chkbx_bmp_size = tkinter.Checkbutton(
                    master=self.f_bmp_inner,
                    text="Resize:",
                    variable=self.bmp_size_enabled,
                    command=self.configure_bmp_size)
            self.pw_bmp_size_input = ttk.Entry(
                    master=self.f_bmp_inner,
                    width=8,
                    textvariable=self.bmp_size_var)
        else:
            self.pw_rb_bmp.config(state=tkinter.DISABLED)
            log.info("Disabling Bitmap control because 'pil' not importable.")
            self.pw_bmp_input_disabled_label = tkinter.Label(
                    master=self.f_bmp_inner,
                    state=tkinter.DISABLED,
                    text="Bitmap sticker support requires 'pillow'")
            self.pw_bmp_input_disabled_label.pack(anchor='w', pady=4)

        # Layout
        self.preview_canvas.pack(fill='x')
        self.f_inherit.pack(fill='x')
        self.f_inherit.pack_propagate(0) # this allows us to set absolute height, 
                                         # so we can keep the layout fixed in
                                         # master and selectio modes whether
                                         # inherit option is visible or not
        if self.master_mode is False:
            self.pw_rb_inherit.pack(anchor='w', pady=4)
        self.f_poly.pack(fill='x')
        self.f_bmp.pack(fill='x')
        self.pw_rb_poly.pack(anchor='w', pady=4)
        self.f_poly_inner.pack(fill='x')
        self.pw_geom_input.pack(anchor='w', fill='x', pady=4)
        self.pw_geom_input_label.pack(anchor='w', pady=4)
        self.pw_chkbx_auto_centroid.pack(anchor='w', pady=4)
        self.pw_rb_bmp.pack(anchor='w', pady=4)
        self.f_bmp_inner.pack(fill='x')
        if PIL_INSTALLED:
            self.pw_bmp_input.pack(fill='x', pady=8)
            self.pw_chkbx_bmp_size.pack(side='left')
            self.pw_bmp_size_input.pack(side='right')

        self.bind_to_appropriate_target()

    def bind_to_appropriate_target(self, event=None):
        '''Attempt to bind to appropriate struct(s) per the widget mode.'''
        if self.master_mode:
            self.bind_to_target(self.pwapp.working_struct)
        else:
            self.bind_to_target(self.pwapp.pw_interface_selected_rings)

    def configure_bmp_size(self):
        '''Set or unset the PanawaveBitmap's size attribute based on interface state.'''
        log.debug("Reconfiguring size for the inputted PWBitmap.")
        self._bmp_entry_handler(self.pw_bmp_input.get_selection())

    def _entry_handler(self, string_var):
        '''Callback attached to updates of the polygon geometry text entry.'''
        parsed_text = self.parse_input_string(string_var.get())
        if parsed_text is None:
            return
        if self.centroid_var.get():
            self.preview_sticker = radialstructs.PanawavePolygon(parsed_text, centroid=None)
        else:
            self.preview_sticker = radialstructs.PanawavePolygon(parsed_text, centroid=(0,0))
        self.update_preview_canvas(self.preview_sticker)
        self.update_appropriate_base_polys(self.preview_sticker)

    def _bmp_entry_handler(self, file):
        '''Callback attached to updates of the bitmap file entry.'''
        if file is None:
            return
        if self.bmp_size_enabled.get():
            try:
                size = int(self.bmp_size_var.get())
            except ValueError:
                size = None
        else:
            size = None
        self.preview_sticker = radialstructs.PanawaveBitmap(file, size=size)
        self.update_preview_canvas(self.preview_sticker)
        self.update_appropriate_base_polys(self.preview_sticker)

    def pw_rb_poly_selected(self):
        '''Update input states and ring attributes when poly mode is selected.'''
        log.info("Switching selected ring(s) to geometric basepoly")
        log.debug("Disabling bmp inputs because polygon mode was selected.")
        # TODO disable bmp inputs
        self.disable_children(self.f_bmp_inner)
        self.enable_children(self.f_poly_inner)
        self._entry_handler(self.geometry_var)

    def pw_rb_bmp_selected(self):
        '''Update input states and ring attributes when bitmap mode is selected.'''
        log.info("Swtching selected ring(s) to bitmap base sticker.")
        log.debug("Disabling poly inputs becuase bitmap mode was selected.")
        self.disable_children(self.f_poly_inner)
        self.enable_children(self.f_bmp_inner)
        self._bmp_entry_handler(self.pw_bmp_input.get_selection())

    def pw_rb_inherit_selected(self):
        '''Update input states and ring attributes when None/Inherit mode is selected.'''
        self.disable_children(self.f_poly_inner)
        self.disable_children(self.f_bmp_inner)
        self.update_appropriate_base_polys(None)
        self.preview_sticker = self.pwapp.working_struct.persistent_state['base_sticker']
        self.update_preview_canvas(self.pwapp.working_struct.persistent_state['base_sticker'])

    def update_preview_canvas(self, bitmap_or_poly):
        '''clear the preview canvas and draw the new preview object.'''
        self.preview_canvas.clear()
        bitmap_or_poly.draw(self.preview_canvas)
        self.draw_centroid_indicator(bitmap_or_poly)
        self.preview_canvas._recenter_scroll_region()

    def draw_centroid_indicator(self, bitmap_or_poly):
        # TODO either this should be passed an explicit object, or
        # update_preview_canvase should also reference the class
        # preview_sticker
        # center crosshairs
        (cx, cy) = bitmap_or_poly.centroid
        self.preview_canvas.create_line(-20 + cx, -10 + cy, 20 + cx, 10 + cy, fill="#4285F4", dash=(4, 4))
        self.preview_canvas.create_line(-20 + cx, 10 + cy, 20 + cx, -10 + cy, fill="#4285F4", dash=(4, 4))

    def parse_input_string(self, entered_text):
        '''Convenience parsing to allow various bracket styles and
        omission of inter-point commas; allows valid input like
        "[0,0][10,4][5,5]".'''
        if len(entered_text) <  15:
            return None
        entered_text = entered_text.replace("{","(").replace("[","(")
        entered_text = entered_text.replace("}",")").replace("]",")")
        entered_text = entered_text.replace(")(","),(")
        try:
            l = literal_eval(entered_text)
        except (ValueError, SyntaxError):
            return None
        log.debug("Succesfully parsed valid literals from the entered text: {0}".format(l))
        return l

    # def fmt_polygon(self, point_list):
    #     '''Return a textual representaion of a polygon, compatible with
    #     the controller's text input.'''
    #     repr = repr(point_list)
    #     repr = repr.replace("),(",")(")
    #     return repr

    def bind_to_target(self, struct_or_ring_list):
        '''Manually attach this widget ring(s) or a struct. Will be bound
        automatically when initializeed if a valid target for the indicated
        mode is found.'''
        t = struct_or_ring_list
        log.debug("Testing object {0} for type and reconciliability.".format(repr(t)))
        if type(t) is radialstructs.PanawaveStruct:
            # Presumably we are in master mode...
            bs = t.persistent_state['base_sticker']
            self.update_state_per_target_sticker(bs)
        else:
            # 'selection' mode, then
            # set the widget state only if all selected base_stickers are equivalent
            try:
                if len(t) is 0:
                    # An empty list indicates no selection...
                    self.disable_widget()
                    return
                first_r = t[0]
                first_st = first_r.base_sticker
                if not all(type(ring.base_sticker) == type(first_st) for ring in t):
                    raise IrreconcilableDifferencesError("Cannot reconcile because the selected rings do not have equivalent base_sticker types")
                elif all(ring.base_sticker is None for ring in t):
                    self.update_state_per_target_sticker(None)
                elif not all(ring.base_sticker == first_st for ring in t):
                    raise IrreconcilableDifferencesError("Cannot reconcile because the selected rings do not have equivalent base_stickers characteristics.")
                else:
                    # all rings have base_stickers of the same type and value
                    self.update_state_per_target_sticker(first_st)
            except IrreconcilableDifferencesError as e:
                log.info("IrreconcilableDifferencesError raised while binding to target: {0}".format(e.args[0]))
                self.set_ambiguous_mode()

    def update_state_per_target_sticker(self, target):
        '''Update the interface state to reflect the given target. Must provide
        a single sticker-like object.'''
        bs = target
        if bs is None:
            # No explicit base_sticker on a ring indicates we are inheriting from PWStruct
            self.mode_var.set(0)
            self.pw_rb_inherit_selected()
        elif type(bs) is radialstructs.PanawavePolygon:
            self.mode_var.set(1)
            self.pw_geom_input.delete(0, END)
            self.pw_geom_input.insert(0, bs.as_string())
            if bs.centroid == (0, 0):
                self.centroid_var.set(False)
            else:
                self.centroid_var.set(True)
            self.pw_rb_poly_selected()
        elif type(bs) is radialstructs.PanawaveBitmap:
            self._bind_bmp_size_input_to_target(bs)
            self.mode_var.set(2)
            self.pw_bmp_input.set_selection(bs.as_string())
            self.pw_rb_bmp_selected()

    def _bind_bmp_size_input_to_target(self, target):
        '''Update status of the size input to reflect the target object.'''
        if target.size is not None:
            self.bmp_size_var.set(str(target.size))
            self.bmp_size_enabled.set(1)
        else:
            self.bmp_size_var.set("")
            self.bmp_size_enabled.set(0)

    def set_ambiguous_mode(self):
        '''Set mode to -1, which represents a set of selected objects which
        cannot be reconciled. All radiobuttons will be unselected to represent
        this, and selecting any will bring all selected object in-line.'''
        log.debug("Multiple rings selected and their base_stickers are "
            "not in agreement; not selecting either mode.")
        self.mode_var.set(-1) # This will also unselect the rb's

    def disable_widget(self):
        '''The widget should be disabled entirely if a valid target for the
        given mode cannot be identified.'''
        self.disable_children(self)
        pass

    def update_centroid_calc_method(self):
        '''Just call the rb_poly_selected callback again, which will update with the current value of centroid_var'''
        self.pw_rb_poly_selected()

    def update_appropriate_base_polys(self, bmp_or_poly):
        '''Apply the given base poly to the selected ring(s) or master object,
        depending on widget mode.'''
        log.debug("Applying BaseSticker {0} to appropriate rings.".format(bmp_or_poly))
        # if self.master_mode and (type(bmp_or_poly) is radialstructs.PanawaveBitmap):
        if self.master_mode:
            log.debug("Updating base_sticker for PanawaveStruct due to 'master_mode'.")
            self.pwapp.working_struct.set_base_sticker(bmp_or_poly)
      # elif self.master_mode:
      #     log.debug("Updating master BaseSticker with new poly.")
      #     self.pwapp.working_struct.set_base_sticker(point_list=bmp_or_poly)
        elif (type(bmp_or_poly) is radialstructs.PanawaveBitmap):
            log.debug("Updating selected ring(s) with new bitmap.")
            for ring in self.pwapp.pw_interface_selected_rings:
                ring.set_base_sticker(bmp_or_poly)
        else:
            log.debug("Updating selected ring(s) with new poly.")
            for ring in self.pwapp.pw_interface_selected_rings:
                ring.set_base_sticker(bmp_or_poly)
        self.pwapp.viewer._rebuild_pw_canvas()


class IrreconcilableDifferencesError(Exception):
    '''Failure to identify a common attribute amongst the given objects which
    can be controlled in unison.'''


class PWButton(PWWidget, ttk.Button):
    '''A button.'''


class PWAnimController(PWWidget, tkinter.Frame):
    '''Combined selection box and animation control button. This widget will
    operate on the working_struct.'''

    def __init__(self, values=None, row=None, column=None, columnspan=None):
        '''Define the animation methods list, create and define default values,
        and lay them out.'''
        tkinter.Frame.__init__(self, self.pwapp.master)
        if values == None:
            # TODO: We need to use an ordered dict to keep this consistent!
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
        self.toggle_button = ttk.Button(self, text="Start", width=5,
                command=self.toggle_animation)
        self.toggle_button.grid(row=0, column=1, rowspan=2, padx=4, pady=2)
        self.toggle_button.grid_configure(sticky='NS')
        self.speedslider = ttk.Scale(self, orient=HORIZONTAL, from_=0, to=3,
                value=1.5, takefocus=False, command=self._set_anim_speed)
        self.speedslider.grid(row=1, column=0, sticky=(W,E), pady=2)
        self.grid(row=row, column=column, columnspan=columnspan, sticky=(E,W),
                pady=4)
        self.columnconfigure(0, weight=1)

    def _set_anim_method(self, event, method=None):
        '''Adjust animation method of working_struct and restart animation with
        the new method if currently active. Can be passed a shortname of a
        valid anim method; otherwise will read the selected value from the
        combo box.'''
        if not method:
            method = self.methods[self.combo.get()]
        print("_set_anim_method invoked with method {0}".format(repr(method)))
        self.pwapp.working_struct.ephemeral_state['anim_method'] = method
        self.restart_if_animating()

    def _set_anim_speed(self, speed):
        '''Adjust animation speed scaler of working_struct and restart
        animation if currently active. Currently, the default for this value is
        1.5 so this is mapped to the center of the slider.'''
        self.pwapp.working_struct.persistent_state['master_orbit_speed'] = \
            float(speed) # stupid ttk.Scale returns a string
        self.restart_if_animating()

    def toggle_animation(self):
        if self.pwapp.working_struct.ephemeral_state['animating'] is True:
            self.pwapp.working_struct.stop_animation()
            self.pwapp.pw_anim_control.toggle_button.configure(text="Start")
        else:
            self.pwapp.working_struct.orbit(
                    method=self.methods[self.combo.get()])
            self.pwapp.pw_anim_control.toggle_button.configure(text="Stop")

    def restart_if_animating(self):
        '''Restart animation to incorporate value adjustments. Do nothing if
        not animating.'''
        if self.pwapp.working_struct.ephemeral_state['animating'] is True:
            meth = self.pwapp.working_struct.ephemeral_state['anim_method']
            self.pwapp.working_struct.stop_animation()
            self.pwapp.working_struct.orbit(method=meth)


class PWConsole(PWWidget):
    '''A textual console to allow the user to interact directly with the
    underlying methods. A redraw cycle will be triggered after executing each
    input, to avoid tedium.'''

    def __init__(self, *args, master=None, **kwargs):
        if master:
            self.master = master
        self.input_var = tkinter.StringVar
        self.console_history = []
        self.console_history_offset = 0
        self.console_input = ttk.Entry(*args, master=self.master, textvariable=self.input_var, **kwargs)

    def draw_console(self):
        self.console_input.place(relx=0.1, rely=.92, relwidth=.85)

    def hide_console(self):
        self.console_input.place_forget()

    def toggle_console(self):
        if self.console_input.winfo_viewable():
            self.hide_console()
        else:
            self.draw_console()

    def execute_console_input(self, *args):
        '''execute arbitrary commands from the console box,
        update the UI, and clear input's contents'''
        statement = self.console_input.get()
        self.console_history.append(statement)
        try:
            eval(statement)
        except:
            e = sys.exc_info()
            log.debug("***Console input generated the following error:***")
            log.debug(e)
        self.pwapp.rebuild_views()
        sleep(.5)
        self.console_history_offset = 0
        self.console_input.delete(0, END)

    def navigate_console_history(self, event):
        '''walk through input history and replace console_input contents.
        the offset is stored as a negative integer, used directly as
        a reverse index. This is fine because although the list length
        changes every time we input a command, we're not caring about
        saving the history index then anyway.'''
        log.debug("keypress received: {0}".format(event.keysym))
        if event.keysym == "Up":
            new_offset = self.console_history_offset - 1
        elif event.keysym == "Down":
            new_offset = self.console_history_offset + 1
        log.debug("testing offset: {0}".format(new_offset))
        hist = self.console_history
        hist_len = len(hist)
        log.debug("hist len: {0}".format(hist_len))
        if new_offset >= 0:
            # return to a blank slate if we arrive back at the
            # end of the history.
            self.pw_input_offset = 0
            self.console_input.delete(0, END)
            log.debug("reset offset to zero.")
            return
        if (0 > new_offset >= -hist_len):
            self.console_history_offset = new_offset
            self.console_input.delete(0, END)
            self.console_input.insert(END, hist[new_offset])
            log.debug("decided offset {0} is valid.".format(new_offset))

