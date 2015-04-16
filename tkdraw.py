from tkinter import *
from math import *
import cmath
from time import sleep

def drawCanvas():
    # basic assumptions of the canvas: origin at center, radial
    # positions specified by setting radius along pos. Y axis and
    # then performing clockwise rotation.
    master = Tk()
    w = Canvas(master, width=800, height=800)
    # this will position origin at center
    w.configure(scrollregion=(-400,-400,400,400))
    w.pack()
    w.create_line(-40, -20, 40, 20)
    w.create_line(-40, -20, 40, 20, fill="red", dash=(4, 4))
    return w


def testPoly():
    '''sample data for testing purposes'''
    testpoints = [(10, 10), (70, 10), (70, 70), (10, 70)]
    testPoly = Polygon(testpoints)
    return testPoly


class rotatingPoly:
    '''test class for animating and rotating methods'''
    def __init__(self, poly=None):
        if poly==None:
            self.myPoly=testPoly()
            self.myCanvas = drawCanvas()
        
    def drawOneFrame(self):
        self.myCanvas.delete("all")
        self.myPoly.rotate(3)
        self.myPoly.draw(self.myCanvas)

    def animate(self):
        i = 0
        while i < 100:
            self.drawOneFrame()
            self.myCanvas.after(500, self.animate)
            i = i + 1


# TODO so tk has a polygon class already, not sure why I didn't use that 
# in the first place? So really we should extend that class with our custom
# interfaces and values; now to figure out how to do that...
#
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


    # okayyyyyy this is stupid, pulling it out and doing it with imaginary nums
    # i guess that's how yr sposta do it? dumb at math

    def rotate(self, angle):
        '''rotate points about centroid. expects degrees.'''
        rotatedPoints = []
        complexCenter = complex(self.centroid[0], self.centroid[1])
        complexAngle = cmath.exp(radians(angle) * 1j)
        for x, y in self.points:
            newComplexPoint = complexAngle * \
                (complex(x, y) - complexCenter) + complexCenter
            rotatedPoints.append((newComplexPoint.real, newComplexPoint.imag))
        self.points = rotatedPoints


    def translate(self, xTranslate, yTranslate):
        '''translate points by x, y value'''
        translatedPoints = []
        for point in self.points:
            newX , newY = (point[0] + xTranslate) , \
                          (point[1] + yTranslate)
            translatedPoints.append((newX, newY))
        self.points = translatedPoints
        cX, cY = self.centroid
        self.cetroid = (cX + xTranslate, cY + yTranslate)  

            
    def rotateAboutOrigin(self, angle):
        '''rotate points about origin. expects degrees. note poly will be re-oriented also 
        unless correspondeing inverse rotate() is performed'''
        rotatedPoints = [] 
        complexAngle = cmath.exp(radians(angle) * 1j)
        for x, y in self.points:
            newComplexPoint = complexAngle * complex(x, y)
            rotatedPoints.append((newComplexPoint.real, newComplexPoint.imag))
        self.points = rotatedPoints


    def draw(self, canvas):
        '''draw our polygon to the indicated canvas'''
        # '*self.points' unpacks the items as separate arguments 
        canvas.create_polygon(*self.points)


class StickerRing:
    '''create and manage a ring of regularly-spaced poly objects'''    

    baseStickerPoly = [[0,0], [0,20], [20,20], [20,0]]

    def __init__(self, radius, count, offsetDegrees=0):
        self.stickerList = []
        period = 360 / count
        position = 1
        for i in range(count):
            s = Polygon(self.baseStickerPoly)
            s.translate(0,radius)
            s.rotateAboutOrigin(offsetDegrees + period * position)
            position = position + 1
            self.stickerList.append(s)

    def draw(self, canvas):
        '''plot stickerRing to a canvas'''
        for sticker in self.stickerList:
            canvas.create_polygon(*sticker.points)

    def rotate(self, angle):
        '''rotate the StickerRing. Use this instead of accessing offset directly'''
        for sticker in self.stickerList:
            sticker.rotateAboutOrigin(angle)

    

        
if __name__ == "__main__":
    print("drawing canvas")
    drawCanvas()

