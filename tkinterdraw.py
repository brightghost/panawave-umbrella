from tkinter import *
from math import *


def drawCanvas():
    master = Tk()
    w = Canvas(master, width=800, height=800)
    w.pack()
    w.create_line(0, 0, 200, 100)
    w.create_line(0, 100, 200, 0, fill="red", dash=(4, 4))
    w.create_rectangle(50, 25, 150, 75, fill="blue")
    return w

# basic assumptions of the canvas: origin at center, radial
# positions specified by setting radius along pos. Y axis and
# then performing clockwise rotation.

# basic geometry of our sticker
baseStickerPoly = [[0,0], [0,2], [2,2], [2,0]]


def place_sticker(radius, offsetAngle):
    # stickerOrigin = some trig here
    Pass

# TODO so tk has a polygon class already, not sure why I didn't use that 
# in the first place? So really we should extend that class with our custom
# interfaces and values; now to figure out how to do that...

# ah, that's why: its not actually a polygon class; it is a polygon generator
# don't think tk canvas elements are objects so let's create one
class Polygon:
    '''Polygon class expects a list of tuples defining an enclosed poly,
    optionally allowing manual definition of centroid point
    '''

    def __init__(self, pointList, centroid=None):
        self.centroid = centroid
        for point in pointList:
            if type(point) is not "tuple":
                point = tuple(point)
        self.points = pointList
        if self.centroid is None:
            # calculate centroid
            # this is a problematic method which is probably
            # only useful for rectangles
            xmean, ymean = 0, 0
            for point in pointList:
                xmean += point[0]
                ymean += point[1]
            xmean = xmean / len(pointList)
            ymean = ymean / len(pointList)
            self.centroid = (xmean, ymean)

    points = []

    def rotate(self, angle):
        '''rotate about centroid and return new polygon. accepts degrees.'''
        rotatedPoints = []
        for point in self.points:
            a , b = (point[0] - self.centroid[0]) , \
                    (point[1] - self.centroid[1])
            # the pythagorean theorem only holds true for positive values, so
            # we'll convert everythin and remember so we can switch it back.
            # there's probably a more elagant way for this but math gives me a
            # headache
            if a < 0:
                absA = True
                a = -a
            if b < 0:
                absB = True
                b = -b
	    radius = sqrt(a*a + b*b)
            startAngle = atan(b / a)
            newAngle = startAngle + radians(angle)
            newA = radius * cos(newAngle)
            newB = radius * sin(newAngle)
            # switch back to negative if neccesarry
            if absA == True:
                newA = -newA
            if absB == True:
                newB = -newB
            newX, newY = (newA + self.centroid[0], \
                          newB + self.centroid[1])
            rotatedPoints.append((newX, newY))
        # return Polygon(rotatedPoints, self.centroid)
        # actually I don't think we want to generate a new object..
        self.points = rotatedPoints

    def translate(self, xTranslate, yTranslate):
        translatedPoints = []
        for point in self.points:
            newX , newY = (point[0] + xTranslate) , \
                          (point[1] + yTranslate)
            translatedPoints.append((newX, newY))
        self.points = translatedPoints
        cX, cY = self.centroid
        self.cetroid = (cX + xTranslate, cY + yTranslate)  
            


    def draw(self, canvas):
        '''draw our polygon to the indicated canvas'''
        canvas.create_polygon(*self.points)
        
if __name__ == "__main__":
    print("drawing canvas")
    drawCanvas()
    
    

