from math import degrees, radians
from cmath import exp
from random import random, randint
from time import sleep
import json


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
    '''create and manage a ring of regularly-spaced poly objects.
    There's less math if we just throw the polys out and create a
    new set when changing base characteristics so that's what the
    setters do currently.'''

    baseStickerPoly = [[0, 0], [0, 20], [20, 20], [20, 0]]

    def __init__(self, radius, count, offsetDegrees=0, geometry=None, id=None):
        if id is None:
            self.id = randint(10000,99999)
        else:
            self.id = id
        self.selected = False
        if geometry is not None:
            self.baseStickerPoly = geometry
        self._initialize_geometry(radius, count, offsetDegrees)

    def _initialize_geometry(self, radius, count, offsetDegrees):
        self.radius = float(radius)
        self.count = int(count)
        self.offsetDegrees = float(offsetDegrees)
        self.sticker_list = []
        self.period = 360 / self.count
        for i in range(1, self.count + 1):
            s = PanawavePolygon(self.baseStickerPoly)
            # center the centroid at canvas origin before other moves
            s.translate((0 - s.centroid[0]), (0 - s.centroid[1]))
            s.translate(0, self.radius)
            s.rotate_about_origin(self.offsetDegrees + self.period * i)
            # position = position + 1
            self.sticker_list.append(s)

    def set_radius(self, new_radius):
        '''Setter for radius; will re-initialize the object.'''
        self._initialize_geometry(new_radius, self.count, self.offsetDegrees)

    def set_count(self, new_count):
        '''Setter for count; will re-initialize the object.'''
        self._initialize_geometry(self.radius, new_count, self.offsetDegrees)

    def set_offset(self, new_offset):
        '''Setter for offset; will re-intialize the object.'''
        self._initialize_geometry(self.radius, self.count, new_offset)

    def as_string(self):
        '''return string representing the StickerRing.'''
        width = 11
        string_rep = '{:<{width}.5g}{:<{width}d}{: <{width}.5g}'.format(
                self.radius, self.count, self.offsetDegrees, width=width)
        return string_rep

    def as_tuple(self):
        '''return a tuple representing the StickerRing. Used by UI listbox.'''
        ring_tuple = (self.radius, self.count, self.offsetDegrees)
        return ring_tuple

    def toggle_selected_state(self):
        '''Toggles .selected property.'''
        self.selected = not self.selected

    def draw(self, canvas):
        '''plot stickerRing to a canvas'''
        ring_tag = "ring-" + str(self.id)
        for sticker in self.sticker_list:
            if self.selected:
                # TODO maybe some fancy intereference-detection on stickers
                # that are touching.
                canvas.create_polygon(*sticker.points, outline="#4285F4",
                        width=2.0, tags=ring_tag)
            else:
                canvas.create_polygon(*sticker.points, tags=ring_tag)

    def rotate(self, angle):
        '''rotate the StickerRing. Use this instead of accessing the offset
        directly.'''
        for sticker in self.sticker_list:
            sticker.rotate_about_origin(angle)
        self.offsetDegrees = self.offsetDegrees + angle
        if self.offsetDegrees > 360:
            self.offsetDegrees = self.offsetDegrees - 360


class PanawaveStruct:
    '''data structure for storing our StickerRing composition'''

    def __init__(self, tkinstance=None, canvas=None, *args):
        '''We need to pass a reference to the canvas to store
        locally in order to use the tk .wait callbacks in animation'''
        # this is now a dict instead of a list so we can easily access 
        #rings by ID.
        self.ring_array = {}
        for arg in args:
            self.add_ring(*args)
        if tkinstance is not None:
            self.tkinstance=tkinstance
        if canvas is not None:
            self.canvas = canvas
        # This dictionary stores any state variables which we want to persist
        # along with saved documents. Only the contents of this dictionary and
        # the ring_array are currently written to file.
        self.persistent_state = {
            # master scaler for animations. can also be modified by
            # passing as argument to any of the animation methods.
            "master_orbit_speed": 1.5,
            # TODO this should move to an ephemeral_state array
            "animating": False
            }

    def draw(self, target_canvas=None):
        '''plot all elements to a canvas'''
        if target_canvas is None:
            target_canvas = self.canvas
        for ring in self.ring_array.values():
            ring.draw(target_canvas)

    # Working with child  objects:

    def add_ring(self, *args):
        '''create a new StickerRing using the arguments. Will attempt to
        eval the argument first, so you can pass arithmetic expressions also'''
        evaluated_args = []
        for arg in args:
            try:
                evaluated_args.append(eval(arg))
            except TypeError:
                # TODO probbably not particularly useful to pass input that 
                # fails an eval straight into our list? or did I do this to
                # handle strings or something?
                evaluated_args.append(arg)
        self.canvas.delete("all")

        # We need to initialize the new ring before adding it to the ring_array
        # so we can reference it's id as the key.
        new_ring = StickerRing(*evaluated_args)
        self.ring_array[str(new_ring.id)] = new_ring

    # File Input/Output Methods:

    def write_out(self, output_file):
        '''TODO write the current composition to file in a re-usable format'''
        try:
            os.rename(output_file, output_file + "~")
            backup_file = output_file + "~"
        except OSError:
            pass
        with open(output_file, "w") as file:
            json.dump(self.persistent_state, file, default=pw_json_serializer,
                    sort_keys=True, indent=4)
            file.write('\n')
            json.dump({"ring_array": self.ring_array}, file,
                    default=pw_json_serializer, sort_keys=True, indent=4)
            # other things we may want to include:
            # app state: selected struct, undo history?
            # selected anim method
            # input field contents, slider positions?
            # step var value, once implemented (for eval'd inputs)
            # target canvas? probably not, we should just let the app decide
            #    where to draw it when opening
            # member variables:
            # self.master_orbit_speed
            # self.animating: just let this be set to false on load
            # TODO dump self.persistent_state
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
            for ring in self.ring_array.values():
                ring.radial_speed = random()
        elif method == "linear":
            speed_step = 1 / len(self.ring_array)
            for index, ring in enumerate(self.ring_array.values()):
                ring.radial_speed = speed_step * index
        elif method == "inverse-linear":
            speed_step = 1 / len(self.ring_array)
            for index, ring in enumerate(self.ring_array.values()):
                ring.radial_speed = speed_step * (len(self.ring_array) - index)
        # Linear speed, units/sec.
        if canvas is None:
            canvas = self.canvas
        if speed is not None:
            self.persistent_state["master_orbit_speed"] = speed
        self.animating = True
        self._animation_index = 1
        self._animate_orbit()

    def _draw_one_frame(self, canvas, index):
        working_canvas = canvas
        working_canvas.delete("all")
        for ringnum, ring in enumerate(self.ring_array.values()):
            increment = self.persistent_state["master_orbit_speed"] * ring.radial_speed
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

