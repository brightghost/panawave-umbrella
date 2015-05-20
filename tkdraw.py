from tkinter import *
from math import degrees
import cmath.exp
from time import sleep

def draw_canvas(tkinstance):
    # basic assumptions of the canvas: origin at center, radial
    # positions specified by setting radius along pos. Y axis and
    # then performing clockwise rotation.

    w = Canvas(tkinstance, width=800, height=800)
    # this will position origin at center
    w.configure(scrollregion=(-400,-400,400,400))
    w.pack()
    # just some doodles to verify everything's working...
    w.create_line(-40, -20, 40, 20)
    w.create_line(-40, -20, 40, 20, fill="red", dash=(4, 4))
    return w


def test_poly():
    '''sample data for testing purposes'''
    testpoints = [(10, 10), (70, 10), (70, 70), (10, 70)]
    our_polygon = PanawavePanawavePolygon(testpoints)
    return our_polygon

class PanawaveApp:
    '''our GUI app for working with PanawaveStructs'''
    def __init__(self):
        self.create_ui()


    def create_ui(self):
        master = Tk()
        panawave_canvas = draw_canvas(master)
        panawave_control_frame = Frame(master)
        panawave_list_box = ListBox(panawave_control_frame)
        panawave_input_radius = Text(panawave_control_frame)
        panawave_input_count = Text(panawave_control_frame)
        panawave_input_offset = Text(panawave_control_frame)
        panawave_input_submit = Button(panawave_control_frame, text="Create")


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


# TODO so tk has a polygon class already, not sure why I didn't use that 
# in the first place? So really we should extend that class with our custom
# interfaces and values; now to figure out how to do that...
#
# ah, that's why: its not actually a polygon class; just a  polygon generator
# don't think tk canvas elements are implemented as objects so let's create one
#
# not really sure yet if polygon.point[s] should have a concept of global location,
# or if the polygon is treated as atomic and only has one location, for the centroid...
# anyway for now going to try to reference global position via the centroid only

class PanawavePolygon:
    '''PanawavePolygon class expects a list of tuples defining an enclosed poly,
    optionally allowing manual definition of centroid point
    '''

    def __init__(self, point_list, centroid=None):
        self.centroid = centroid
        for point in point_list:
            if type(point) is not "tuple":
                point = tuple(point)
        self.points = point_list
        if self.centroid is None:
            # calculate centroid
            # this is a problematic method which is probably
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
        complex_angle = cmath.exp(radians(angle) * 1j)
        for x, y in self.points:
            new_complex_point = complex_angle * \
                (complex(x, y) - complexCenter) + complexCenter
            rotated_points.append((new_complex_point.real, new_complex_point.imag))
        self.points = rotated_points


    def translate(self, xTranslate, yTranslate):
        '''translate points by x, y value'''
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
        re-oriented also unless correspondeing inverse rotate() is performed'''
        rotated_points = [] 
        complex_angle = cmath.exp(radians(angle) * 1j)
        for x, y in self.points:
            new_complex_point = complex_angle * complex(x, y)
            rotated_points.append((new_complex_point.real, new_complex_point.imag))
        self.points = rotated_points


    def draw(self, canvas):
        '''draw our polygon to the indicated canvas'''
        # '*self.points' unpacks the items as separate arguments 
        canvas.create_polygon(*self.points)


class StickerRing:
    '''create and manage a ring of regularly-spaced poly objects'''    

    baseStickerPoly = [[0, 0], [0, 20], [20, 20], [20, 0]]

    def __init__(self, radius, count, offsetDegrees=0, geometry=None):
        self.sticker_list = []
        period = 360 / count
        position = 1
        if geometry is not None:
            self.baseStickerPoly = geometry
        for i in range(count):
            s = PanawavePolygon(self.baseStickerPoly)
            # center the centroid at canvas origin before other moves
            s.translate((0 - s.centroid[0]), (0 - s.centroid[1]))
            s.translate(0, radius)
            s.rotate_about_origin(offsetDegrees + period * position)
            position = position + 1
            self.sticker_list.append(s)

    def draw(self, canvas):
        '''plot stickerRing to a canvas'''
        for sticker in self.sticker_list:
            canvas.create_polygon(*sticker.points)

    def rotate(self, angle):
        '''rotate the StickerRing. Use this instead of accessing offset directly'''
        for sticker in self.sticker_list:
            sticker.rotate_about_origin(angle)

class PanawaveStruct:
    '''data structure for storing our StickerRing composition'''

    def __init__(self, *args):
        self.ring_array = []
        for arg in self.args:
            self.ring_array.append(StickerRing(args*))

    def draw(self, canvas):
        '''plot all elements to a canvas'''
        for stickerRing in self.ring_array:
            stickerRing.draw(canvas)

    def write_out(self, file):
        '''write the current composition to file in a re-usable format'''
        pass

    def write_out_instructions(self, file):
        '''write to file in a format (tbd) which can be used as cnc control for a 
        plotting device'''
        pass



if __name__ == "__main__":
    print("initializing Panawave Umbrella Creator")
    our_app = PanawaveApp()

