from tkinter import *
from math import degrees, radians
from cmath import exp
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
    '''our GUI app for working with PanawaveStructs.'''
    def __init__(self, file=None):
        self.tkapp = self.create_ui()
        self.working_struct = self.load_new_struct(file)
        self.working_struct.draw(self.pw_canvas)
        self.update_list_box()

        # Interface history variables
        self.console_history = []
        self.console_history_offset = 0

        # DEBUG IPython Console:
        embed()

        self.tkapp.mainloop()

    def create_ui(self):
        master = Tk()
        master.wm_title("Panawave Umbrella Editor")
        master.columnconfigure(0, weight=1, minsize=400)
        master.rowconfigure(0, weight=1, minsize=400)

        # MAIN VIEW:
        self.pw_canvas = draw_canvas(master)
        # position canvas origin at center
        self.pw_canvas.configure(scrollregion=(-400,-400,400,400))
        self.pw_canvas.grid(row=0, column=0, rowspan=6, sticky=(N,E,S,W))

        # SIDE BAR:
        # struct listing
        # TODO: Replace this with ttk.treeview, because a listbox
        # Is completely incapable of sanely displaying tabular
        # data as it has no access to a monospaced font!
        # http://stackoverflow.com/questions/3794268/command-for-clicking-on-the-items-of-a-tkinter-treeview-widget
        self.pw_list_box = Listbox(master, height=10)
        self.pw_list_box.grid(row=0, column=1, sticky=(N,S), columnspan=4)
        self.pw_lb_s = Scrollbar(master, orient=VERTICAL, \
                command=self.pw_list_box.yview)
        self.pw_lb_s.grid(row=0, column=5, sticky=(N,S))
        self.pw_list_box['yscrollcommand'] = self.pw_lb_s.set

        # ring attribute entry
        self.pw_input_radius = Entry(master)
        self.pw_input_radius.configure(width=4)
        self.pw_input_radius.grid(row=1, column=2, sticky=N)
        self.pw_input_radius.bind("<Return>", self.submit_new_ring)
        self.pw_input_count = Entry(master)
        self.pw_input_count.configure(width=4)
        self.pw_input_count.grid(row=1, column=3, sticky=N)
        self.pw_input_count.bind("<Return>", self.submit_new_ring)
        self.pw_input_offset = Entry(master)
        self.pw_input_offset.configure(width=4)
        self.pw_input_offset.grid(row=1, column=4, sticky=N)
        self.pw_input_offset.bind("<Return>", self.submit_new_ring)

        self.pw_input_submit = Button(master, text="Create", \
                command=self.submit_new_ring)
        self.pw_input_submit.grid(row=3, column=1, columnspan=4)

        self.pw_console = Entry(master)
        self.pw_console.grid(row=4, column=1, columnspan=4)
        self.pw_console.bind("<Return>", self.execute_console_input)
        self.pw_console.bind("<Up>", self.navigate_console_history)
        self.pw_console.bind("<Down>", self.navigate_console_history)
        return master

    def update_list_box(self):
        self.pw_list_box.delete(0, END)
        for item in self.working_struct.ring_array:
            self.pw_list_box.insert(END, item.as_string())

    def load_new_struct(self, file=None):
        '''create an empty struct, attach it to the canvas, 
        and populate it from a file if one is given.'''
        if file is not None:
            self.working_struct = PanawaveStruct()
        else:
            self.working_struct = PanawaveStruct()
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
        self.update_list_box()

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
        sabing the history index then anyway.'''
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
        self.centroid = complex(self.centroid[0], self.centroid[1]) * \
                complex_angle

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
        string_rep = '{:<{width}.5g}{:<{width}d}{: <{width}.5g}'.format(self.radius, self.count, self.offsetDegrees, width=width)
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

    def __init__(self, *args):
        ''''''
        self.ring_array = []
        for arg in args:
            self.add_ring(*args)

    def draw(self, canvas):
        '''plot all elements to a canvas'''
        for stickerRing in self.ring_array:
            stickerRing.draw(canvas)

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
            json.dump(self, file, default=pw_json_serializer, \
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

    def orbit_randomly():
        for ring in self.ring_array:
            # speed specified between 0 and 1; we can apply a scale 
            # factor to the overall speed if desired
            ring.radial_speed = random()
        # Linear speed, units/sec.
        if not self.master_orbit_speed:
            self.master_orbit_speed = 10
        self.orbiting = True
        self._animate_orbit()

    def _draw_one_frame(canvas):
        canvas.delete("all")
        for ring in self.ring_array:
            ring.rotate(master_orbit_speed * ring.radial_speed)
        self.myPoly.draw(self.myCanvas)

    def _animate_orbit(self):
        while self.orbiting is True:
            self._draw_one_frame()
            self.myCanvas.after(500, self.animate)
            i = i + 1


def pw_json_serializer(object):
    '''generic method for representing objects in json. will use an
    object's _as_json method if found.'''
    try :
        return object._as_json()
    except (NameError, AttributeError):
        return object.__dict__

if __name__ == "__main__":
    print("initializing Panawave Umbrella Editor...")
    our_app = PanawaveApp()

