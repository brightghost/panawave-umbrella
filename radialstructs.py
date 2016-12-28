import logging as log
from math import degrees, radians
from cmath import exp
from random import random, randint
from time import sleep
import json
import os


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

    def __init__(self, radius, count, offsetDegrees=0, scaler_list=[1],
            geometry=None, id=None):
        if id is None:
            self.id = randint(10000,99999)
        else:
            self.id = id
        self.selected = False #TODO kill this
        if geometry is not None:
            self.baseStickerPoly = geometry
        self.radius = float(radius)
        self.count = int(count)
        self.offsetDegrees = float(offsetDegrees)
        self.scaler_list = scaler_list
        log.debug("New ring being initialized with radius {0}, count {1}, "
                "offset {2}, and scaler_list {3}".format(
                    repr(self.radius),
                    repr(self.count),
                    repr(self.offsetDegrees),
                    repr(self.scaler_list)))
        self._initialize_geometry()

    def _initialize_geometry(self):
        self.increment = self._get_increment_val()
        self.sticker_list = []
        prev_offset = 0
        for s in self._stepper(self.count, self.scaler_list):
            p = PanawavePolygon(self.baseStickerPoly)
            # center the centroid at canvas origin before other moves
            p.translate((0 - p.centroid[0]), (0 - p.centroid[1]))
            p.translate(0, self.radius)
            curr_offset = prev_offset + self.increment * s
            p.rotate_about_origin(
                    self.offsetDegrees + \
                    curr_offset)
            self.sticker_list.append(p)
            prev_offset = curr_offset

    def _stepper(self, steps, scaler_list, step_val=None):
        '''Generator for scalers, as determined from the scaler_list
        (configured with PWPeriodController.)'''
        i = 0
        while i < steps:
            yield scaler_list[i % len(scaler_list)]
            i += 1

    def _get_increment_val(self):
        '''Calculate the base increment, from which the various step values
        will be derived.

        NOTE: while by default the interface enforces a 'count ==
        len(scaler_list) / x' relationship, no such restriction exists here,
        and self.count is the actual count of stickers. Rings which are not
        evenly divisible by the scaler list are possible; but they will not
        have clean radial symmetry.'''

        # That said....this *would* be easier if we only allowed divis. counts:
        #   full_sc_list = self.scaler_list * count
        #   incr = 360 / sum(full_sl_list)
        full_scaler_list = []
        for s in range(self.count):
            full_scaler_list.append(self.scaler_list[s % len(self.scaler_list)])
        increment = 360 / sum(full_scaler_list)
        log.debug("Calculated new ring increment of {0} from "
                "scaler_list: {1}".format(
                str(increment), repr(self.scaler_list)))
        return increment

    def set_radius(self, new_radius):
        '''Setter for radius; will re-initialize the object.'''
        self.radius = float(new_radius)
        self._initialize_geometry()

    def set_count(self, new_count):
        '''Setter for count; will re-initialize the object.'''
        self.count = int(new_count)
        self._initialize_geometry()

    def set_offset(self, new_offset):
        '''Setter for offset; will re-intialize the object.'''
        self.offsetDegrees = float(new_offset)
        self._initialize_geometry()

    def set_scaler_list(self, new_list):
        '''Setter for scaler list; will re-initialize the object. An
        empty set or [1] will both result in 'equidistant' spacing.'''
        self.scaler_list = []
        for item in new_list:
            self.scaler_list.append(int(item))
        self._initialize_geometry()

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
            # rings which have had .count uncoupled from multiples 
            # of len(.scaler_list)
            "unlocked_rings": []
            }
        # This dictionary is intended for variables that can be discarded when
        # saved to file.
        self.ephemeral_state = {
            "animating": False,
            "anim_method" : "linear"
            }

    def draw(self, target_canvas=None):
        '''plot all elements to a canvas'''
        if target_canvas is None:
            target_canvas = self.canvas
        for ring in self.ring_array.values():
            ring.draw(target_canvas)

    # Working with child  objects:

    def add_ring(self, *args, **kwargs):
        '''create a new StickerRing using the arguments. Will attempt to
        eval the argument first, so you can pass arithmetic expressions also'''
        evaluated_args = []
        for arg in args:
            try:
                evaluated_args.append(eval(arg))
            except TypeError:
                # Some of the args may handle strings, lists etc.,
                # so just let the StickerRing deal with them
                evaluated_args.append(arg)
        self.canvas.delete("all")

        # We need to initialize the new ring before adding it to the ring_array
        # so we can reference it's id as the key.
        new_ring = StickerRing(*evaluated_args, **kwargs)
        self.ring_array[str(new_ring.id)] = new_ring

    def clear_selection(self):
        '''un-select all rings. You need to handle redrawing after.'''
        for ring in self.ring_array.values():
            ring.selected = False

    def lock_ring_count_to_scaler(self, ring):
        '''Lock the given ring's count to multiples of the scaler_list. This is
        the default state for new rings.'''
        unlock_l = self.persistent_state['unlocked_rings']
            # True = lock
        if str(ring.id) in unlock_l:
            log.debug("Removing ring {0} from the unlocked_rings list because "
                    "lock_ring_count_to_scaler was called.".format(ring.id))
            unlock_l.remove(str(ring.id))
        else:
            log.debug("lock_ring_count_to_scaler was called on ring {0}, "
                    "but it is already locked.".format(ring.id))

    def unlock_ring_count_from_scaler(self, ring):
        '''Unlink the given ring's count from multiples of the scaler_list.
        This is not an attribute of the StickerRing itself, because it is
        considered an interface state.'''
        unlock_l = self.persistent_state['unlocked_rings']
            # True = lock
        if str(ring.id) not in unlock_l:
            log.debug("Adding ring {0} to the unlocked_ring list because "
                    "unlock_ring_count_from_scaler was called.".format(ring.id))
            unlock_l.append(str(ring.id))
        else:
            log.debug("unlock_ring_count_from_scaler was called on ring {0}, "
                    "but it is already unlocked.".format(ring.id))

    def is_count_locked_for_ring(self, ring):
        '''Returns True if given ring's sticker count is locked to multiples of
        the scaler list.'''
        unlock_l = self.persistent_state['unlocked_rings']
        if str(ring.id) not in unlock_l:
            return True

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
        self.ephemeral_state['animating'] = False

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
        elif method == "reverse-linear":
            speed_step = 1 / len(self.ring_array)
            for index, ring in enumerate(self.ring_array.values()):
                ring.radial_speed = speed_step * (len(self.ring_array) - index)
        else:
            log.debug("Received an invalid orbit method: '" + method + "'. exiting.")
            return
        # Linear speed, units/sec.
        if canvas is None:
            canvas = self.canvas
        if speed is not None:
            self.persistent_state["master_orbit_speed"] = speed
        self.ephemeral_state['animating'] = True
        self._animation_index = 1
        self._animate_orbit()

    def _draw_one_frame(self, canvas, index):
        working_canvas = canvas
        working_canvas.delete("all")
        for ringnum, ring in enumerate(self.ring_array.values()):
            increment = self.persistent_state["master_orbit_speed"] \
                    * ring.radial_speed
            log.debug("Ring {0} position at start: {1}".format(ringnum, ring.offsetDegrees))
            log.debug("Rotating ring {0} by increment {1}".format(ringnum, increment))
            ring.rotate(increment)
            log.debug("Ring {0} position after rotation: {1}".format(
                ringnum, ring.offsetDegrees))
        self.draw(working_canvas)

    def _animate_orbit(self):
        '''this is a mess. we're functioning without any arguments because
        tk's callback won't pass us any, so the canvas has to be passed
        allllll the way down. but we're
        accepting an arbitrary canvas in the related functions above, and
        accepting a self reference when called from orbit_randomly.'''
        if self.ephemeral_state['animating'] is True:
            self._draw_one_frame(self.canvas, self._animation_index)
            self._animation_index = self._animation_index + 1
            self.canvas.after(100, self._animate_orbit)

