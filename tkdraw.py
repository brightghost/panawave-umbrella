from tkinter import *
from math import degrees, radians
from cmath import exp
from random import random
from time import sleep
import json
import os
import sys
# Debugging console
from IPython import embed

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


def test_poly():
    '''sample data for testing purposes.'''
    testpoints = [(10, 10), (70, 10), (70, 70), (10, 70)]
    our_polygon = PanawavePolygon(testpoints)
    return our_polygon

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
        self.working_struct = self.load_new_struct(file,
                target_canvas=self.pw_canvas)
        self.selected_ring = None
        self.working_struct.draw()
        self.update_list_box()

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

        # MAIN VIEW:
        self.pw_canvas = draw_canvas(master)
        # position canvas origin at center
        self.pw_canvas.configure(scrollregion=(-400,-400,400,400))
        self.pw_canvas.grid(row=0, column=0, rowspan=5, sticky=(N,E,W))

        # SIDE BAR:
        # struct listing
        # TODO: Replace this with ttk.treeview, because a listbox
        # Is completely incapable of sanely displaying tabular
        # data as it has no access to a monospaced font!
        # http://stackoverflow.com/questions/3794268/command-for-clicking-on-the-items-of-a-tkinter-treeview-widget
        self.pw_list_box = Listbox(master, height=10)
        self.pw_list_box.grid(row=0, column=1, sticky=(N,S), columnspan=4)
        self.pw_lb_s = Scrollbar(master, orient=VERTICAL,
                command=self.pw_list_box.yview)
        self.pw_lb_s.grid(row=0, column=4, sticky=(N,S))
        self.pw_list_box['yscrollcommand'] = self.pw_lb_s.set

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
        # change the text`
        self.pw_animate_label = Label(master, text="Animate:")
        self.pw_animate_label.grid(row=4, column=1, columnspan=2, sticky=W)
        self.pw_orbit_toggle = Button(master, text="Start",
                command=self.toggle_animation, width=5)
        self.pw_orbit_toggle.grid(row=4, column=3, columnspan=2)

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
        self.pw_orbit_begin_inverse_linear.grid(row=5, column=3, columnspan=2)

        # console
        self.pw_console = Entry(master)
        self.pw_console.grid(row=5, column=0, columnspan=1, sticky=(W,E))
        self.pw_console.bind("<Return>", self.execute_console_input)
        self.pw_console.bind("<Up>", self.navigate_console_history)
        self.pw_console.bind("<Down>", self.navigate_console_history)

    def update_list_box(self):
        self.pw_list_box.delete(0, END)
        for item in self.working_struct.ring_array:
            self.pw_list_box.insert(END, item.as_string())

    # Sliders modify selected ring's attributes in realtime;
    # if no ring is selected they just adjust the input value
    # and wait for the 'Submit' button to do anything with them.

    def update_active_ring_radius(self, rad):
        if self.selected_ring is not None:
            self.selected_ring.radius = rad
        else:
            self.pw_input_radius.delete(0, END)
            self.pw_input_radius.insert(0, rad)

    def update_active_ring_count(self, count):
        if self.selected_ring is not None:
            self.selected_ring.count = count
            self.selected_ring.draw(self.pw_canvas)
        else:
            self.pw_input_count.delete(0, END)
            self.pw_input_count.insert(0, count)

    def update_active_ring_offset(self, deg):
        if self.selected_ring is not None:
            self.selected_ring.offset = deg
            self.selected_ring.draw(self.pw_canvas)
        else:
            self.pw_input_offset.delete(0, END)
            self.pw_input_offset.insert(0, deg)

    def load_new_struct(self, file=None, target_canvas=None):
        '''create an empty struct, attach it to the canvas,
        and populate it from a file if one is given.'''
        if file is not None:
            self.working_struct = PanawaveStruct(canvas=target_canvas)
        else:
            self.working_struct = PanawaveStruct(canvas=target_canvas)
            self.working_struct.load_from_file(file)
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
            self.working_struct.orbit(method="random")
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


class RotatingPoly:
    '''test class for animating and rotating methods'''

    def __init__(self, poly=None):
        if poly==None:
            self.myPoly=testPoly()
            self.myCanvas = draw_canvas()

    def draw_one_frame(self):
        self.myCanvas.delete("all")
        self.myPoly.rotate(3)
        self.myPoly.draw(self.myCanvas)

    def animate(self):
        i = 0
        while i < 100:
            self.draw_one_frame()
            self.myCanvas.after(500, self.animate)
            i = i + 1


# TODO not really sure yet if polygon.point[s] should have a concept of global
# location, or if the polygon is treated as atomic and only has one location,
# for the centroid. anyway for now going to try to reference global position
# via the centroid only

class PanawavePolygon:
    '''create a polygon from a list of tuples defining an enclosed poly,
    optionally allowing manual definition of centroid point.
    '''

    def __init__(self, point_list, centroid=None):
        self.centroid = centroid
        for point in point_list:
            if type(point) is not "tuple":
                point = tuple(point)
        self.points = point_list
        if self.centroid is None:
            # calculate centroid
            # TODO this is a problematic method which is probably
            # only useful for rectangles
            xmean, ymean = 0, 0
            for point in point_list:
                xmean += point[0]
                ymean += point[1]
            xmean = xmean / len(point_list)
            ymean = ymean / len(point_list)
            self.centroid = (xmean, ymean)

    # pulled out the broken trig that was here and using imaginary nums
    # i guess that's how yr sposta do it? dumb at math

    def rotate(self, angle):
        '''rotate points about centroid. expects degrees.'''
        rotated_points = []
        complexCenter = complex(self.centroid[0], self.centroid[1])
        complex_angle = exp(radians(angle) * 1j)
        for x, y in self.points:
            new_complex_point = complex_angle * \
                (complex(x, y) - complexCenter) + complexCenter
            rotated_points.append((new_complex_point.real, \
                    new_complex_point.imag))
        self.points = rotated_points

    def translate(self, xTranslate, yTranslate):
        '''translate points by x, y value.'''
        translated_points = []
        for point in self.points:
            newX , newY = (point[0] + xTranslate) , \
                          (point[1] + yTranslate)
            translated_points.append((newX, newY))
        self.points = translated_points
        cX, cY = self.centroid
        self.centroid = (cX + xTranslate, cY + yTranslate)

    def rotate_about_origin(self, angle):
        '''rotate points about origin. expects degrees. note poly will be
        re-oriented also unless correspondeing inverse rotate() is performed.'''
        rotated_points = []
        complex_angle = exp(radians(angle) * 1j)
        for x, y in self.points:
            new_complex_point = complex_angle * complex(x, y)
            rotated_points.append((new_complex_point.real, \
                    new_complex_point.imag))
        self.points = rotated_points
        cX, cY = self.centroid
        new_complex_centroid = complex(cX, cY) * complex_angle
        self.centroid = new_complex_centroid.real, new_complex_centroid.imag

    def draw(self, canvas):
        '''draw our polygon to the indicated canvas.'''
        # '*self.points' unpacks the items as separate arguments 
        canvas.create_polygon(*self.points)


class StickerRing:
    '''create and manage a ring of regularly-spaced poly objects.'''

    baseStickerPoly = [[0, 0], [0, 20], [20, 20], [20, 0]]

    def __init__(self, radius, count, offsetDegrees=0, geometry=None):
        self.radius = float(radius)
        self.count = int(count)
        self.offsetDegrees = float(offsetDegrees)
        self.sticker_list = []
        period = 360 / self.count
        position = 1
        if geometry is not None:
            self.baseStickerPoly = geometry
        for i in range(self.count):
            s = PanawavePolygon(self.baseStickerPoly)
            # center the centroid at canvas origin before other moves
            s.translate((0 - s.centroid[0]), (0 - s.centroid[1]))
            s.translate(0, self.radius)
            s.rotate_about_origin(self.offsetDegrees + period * position)
            position = position + 1
            self.sticker_list.append(s)

    def as_string(self):
        '''return string representing the StickerRing. Used in the UI listbox.'''
        width = 11
        string_rep = '{:<{width}.5g}{:<{width}d}{: <{width}.5g}'.format(
                self.radius, self.count, self.offsetDegrees, width=width)
        return string_rep

    def draw(self, canvas):
        '''plot stickerRing to a canvas'''
        for sticker in self.sticker_list:
            canvas.create_polygon(*sticker.points)

    def rotate(self, angle):
        '''rotate the StickerRing. Use this instead of accessing the offset
        directly.'''
        for sticker in self.sticker_list:
            sticker.rotate_about_origin(angle)
        self.offsetDegrees = self.offsetDegrees + angle


class PanawaveStruct:
    '''data structure for storing our StickerRing composition'''

    def __init__(self, tkinstance=None, canvas=None, *args):
        '''We need to pass a reference to the canvas to store
        locally in order to use the tk .wait callbacks in animation'''
        self.ring_array = []
        for arg in args:
            self.add_ring(*args)
        if tkinstance is not None:
            self.tkinstance=tkinstance
        if canvas is not None:
            self.canvas = canvas
        # you can set this yourself if wanted; can also pass it as an argument
        # to any of the animation methods.
        self.master_orbit_speed = 1.5
        self.animating = False

    def draw(self, target_canvas=None):
        '''plot all elements to a canvas'''
        if target_canvas is None:
            target_canvas = self.canvas
        for stickerRing in self.ring_array:
            stickerRing.draw(target_canvas)

    # Working with child  objects:

    def add_ring(self, *args):
        '''create a new StickerRing using the arguments. Will attempt to
        eval the argument first, so you can pass arithmetic expressions also'''
        evaluated_args = []
        for arg in args:
            try:
                evaluated_args.append(eval(arg))
            except TypeError:
                evaluated_args.append(arg)

        self.ring_array.append(StickerRing(*evaluated_args))

    # File Input/Output Methods:

    def write_out(self, output_file):
        '''TODO write the current composition to file in a re-usable format'''
        try:
            os.rename(output_file, output_file + "~")
            backup_file = output_file + "~"
        except OSError:
            pass
        with open(output_file, "w") as file:
            json.dump(self, file, default=pw_json_serializer,
                    sort_keys=True, indent=4)
        if os.path.isfile(output_file):
            try:
                os.remove(backup_file)
            except (OSError, NameError):
                pass

    def write_out_instructions(self, output_file):
        '''TODO write to file in a format (tbd) which can be used as
        cnc control for a plotting device'''
        pass

    def load_from_file(self, input_file):
        '''TODO populate the struct from the given file'''
        pass

    # High-level manipulation methods:

    def stop_animation(self):
        self.animating = False

    def orbit(self, method="random", canvas=None, speed=None):
        ''' Several orbit methods are defined here. All will assign a
        speed value between 0 and 1 to each ring which is scaled
        by the master speed in the animation method below.'''
        if len(self.ring_array) is 0:
            # just return if the array is empty instead of catching all
            # the divide by zero errors below
            return
        if method == "random":
            for ring in self.ring_array:
                ring.radial_speed = random()
        elif method == "linear":
            speed_step = 1 / len(self.ring_array)
            for index, ring in enumerate(self.ring_array):
                ring.radial_speed = speed_step * index
        elif method == "inverse-linear":
            speed_step = 1 / len(self.ring_array)
            for index, ring in enumerate(self.ring_array):
                ring.radial_speed = speed_step * (len(self.ring_array) - index)
        # Linear speed, units/sec.
        if canvas is None:
            canvas = self.canvas
        if speed is not None:
            self.master_orbit_speed = speed
        self.animating = True
        self._animation_index = 1
        self._animate_orbit()

    def _draw_one_frame(self, canvas, index):
        working_canvas = canvas
        working_canvas.delete("all")
        for ringnum, ring in enumerate(self.ring_array):
            increment = self.master_orbit_speed * ring.radial_speed
            print("Ring ", ringnum, " position at start: ", ring.offsetDegrees)
            print("Rotating ring ", ringnum, " by increment ", increment)
            ring.rotate(increment)
            print("Ring ", ringnum, \
                    " position after rotation: ", ring.offsetDegrees)
        self.draw(working_canvas)

    def _animate_orbit(self):
        '''this is a mess. we're functioning without any arguments because
        tk's callback won't pass us any, so the canvas has to be passed
        allllll the way down. but we're
        accepting an arbitrary canvas in the related functions above, and
        accepting a self reference when called from orbit_randomly.'''
        if self.animating is True:
            self._draw_one_frame(self.canvas, self._animation_index)
            self._animation_index = self._animation_index + 1
            self.canvas.after(100, self._animate_orbit)


def pw_json_serializer(object):
    '''generic method for representing objects in json. will use an
    object's _as_json method if found.'''
    try :
        return object._as_json()
    except (NameError, AttributeError):
        return object.__dict__

if __name__ == "__main__":
    print("initializing Panawave Umbrella Editor...")
    master = Tk()
    global our_app
    our_app = PanawaveApp(master)

