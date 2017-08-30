# ----------------------------------
#
#	Golden-Winged Manakin vision analysis
#	Working draft 08/30/17 
#   LU TAYLOR
# 	FVS CLASS FOR MULTI-THREADING VIDEO READ-IN
#
# ----------------------------------
from threading import Thread
import Queue
import sys
import cv2

class FileVideoStream:
	def __init__(self, filePath):
		self.stream = cv2.VideoCapture(filePath)

		self.width = int(self.stream.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
		self.height = int(self.stream.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))

		self.stopped = False
		self.locked = False
		self.Q = Queue.Queue()

	def start(self):
		t = Thread(target=self.update, args=())
		t.daemon = True
		t.start()
		return self

	def update(self):
		while True:
			if self.stopped:
				return

			(grabbed, frame) = self.stream.read()
			if not grabbed:
				self.stop()
				return

			self.Q.put(frame)

	def read(self):
		return self.Q.get()

	def more(self):
		return self.Q.qsize() > 0

	def stop(self):
		self.stopped = True

	def isDone(self):
		return self.stopped and not self.more()

	def getWidth(self):
		return self.width

	def getHeight(self):
		return self.height
