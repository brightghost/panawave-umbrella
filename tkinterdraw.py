from tkinter import *
from math import sqrt, sin, cos, tan, asin, acos, atan


def drawCanvas():
	master = Tk()
	w = Canvas(master, width=800, height=800)
	w.pack()
	w.create_line(0, 0, 200, 100)
	w.create_line(0, 100, 200, 0, fill="red", dash=(4, 4))
	w.create_rectangle(50, 25, 150, 75, fill="blue")

# basic assumptions of the canvas: origin at center, radial
# positions specified by setting radius along pos. Y axis and
# then performing clockwise rotation.

# basic geometry of our sticker
baseStickerPoly = [[0,0], [0,2], [2,2], [2,0]]


def place_sticker(radius, offsetAngle):
 	# stickerOrigin = some trig here
	Pass


class Polygon:
	'''Polygon class expects a list of tuples defining an enclosed poly,
		optionally allowing manual definition of centroid point'''
	def __init__(self, pointList, centroid=None):
		self.centroid = centroid
		self.points = pointList
		if self.centroid is None:
			# calculate centroid
			# this is a very imperfect method which is probably
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
		'''rotate about centroid and return new polygon'''
		rotatedPoints = []
		for point in self.points:
			x , y = (point[0] - self.centroid[0]) , \
				(point[1] - self.centroid[1])
			rad = sqrt(x * x + y * y)
			startAngle = tan(y / x)
			newAngle = startAngle + angle
			newX = rad * cos(newAngle)
			newY = rad * sin(newAngle)
			rotatedPoints.append((newX, newY))
		# return Polygon(rotatedPoints, self.centroid)
	 	# actually I don't think we want to generate a new object..
		self.points = rotatedPoints
		
if __name__ == "__main__":
	drawCanvas()
	
	

