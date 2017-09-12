# ----------------------------------
#
#	Golden-Winged Manakin vision analysis
#	Working draft 08/30/17 
#   LU TAYLOR
#	MAIN PROGRAM FILE
#
# ----------------------------------

from FileVideoStream import FileVideoStream
import cv2
import time
import math
import argparse
import os
import sys
import gc

#
# VISION PARAMETERS
#
FPS_VAL = 30.0				# must match camera, must be hard-coded

END_BUFFER_CAP = 10 * FPS_VAL

RESIZE_FACTOR = 0.25 		# smaller videos are faster but may lose small motion

GAUSSIAN_BOX = 31			# blurring factor (larger is blurrier, must be odd)

DIFF_THRESHOLD = 30
SUM_THRESHOLD = 100000		# how many motion pixels for a reading? (*255)

def convertFrame(orgFrame):
	resize = cv2.resize(orgFrame, (0, 0), fx=RESIZE_FACTOR, fy=RESIZE_FACTOR)
	frame = cv2.cvtColor(resize, cv2.COLOR_BGR2GRAY)
	frame = cv2.GaussianBlur(frame, (GAUSSIAN_BOX, GAUSSIAN_BOX), 0)
	return frame

def getFrameDiffs(frame, prev_frame, prev_prev_frame):
	d1 = cv2.absdiff(frame, prev_frame)
	d2 = cv2.absdiff(prev_frame, prev_prev_frame)
	diffFrame = cv2.bitwise_xor(d1, d2)
	return diffFrame

def getThreshold(frameDiff):
	thresh = cv2.threshold(frameDiff, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
	return thresh

def getPixelSum(frame):
	return cv2.sumElems(frame)

def hmsString(secValue):
	secs = secValue
	hrs = math.floor(secs / 3600)
	secs = secs - (3600 * hrs)

	mins = math.floor(secs / 60)
	secs = secs - (60 * mins)

	s = str(hrs) + ":" + str(mins) + ":" + str(round(secs,2))
	return s

def clipDisplay(clipList, clipStartTimes):
	if len(clipList) > 0:
		while True:
			isReady = raw_input("Starting to display clips! Ready? [y]")
			if isReady == "y":
				print "Instructions: 'y' =  Retain // 'clear' = Remove, other = Replay"
				break

		clipCounter = 0
		numClipsDisplayed = 1

		while clipCounter < len(clipList):
			print "Displaying clip " + str(numClipsDisplayed) + "."
			print "Clip start time: " + str(clipStartTimes[clipCounter])

			clip = clipList[clipCounter]

			while True:
				for frame in clip:
					resize = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
					cv2.imshow("preview", resize)
					if cv2.waitKey(30) & 0xFF == ord('q'):
						break

				clipResponse = ""
				if clipCounter == len(clipStartTimes):
					clipResponse = raw_input("This is the last clip. Response? [y/clear/...]")
				else:
					clipResponse = raw_input("Response? [y/clear/...]")

				if clipResponse == "y":
					clipCounter = clipCounter + 1
					numClipsDisplayed = numClipsDisplayed + 1
					break
				elif clipResponse == "clear":
					clipList.pop(clipCounter)
					removedTimeStr = clipStartTimes.pop(clipCounter)
					numClipsDisplayed = numClipsDisplayed + 1
					print "Removed clip at " + removedTimeStr
					break
				else:
					print "Replaying clip " + str(numClipsDisplayed) + "."


	else:
		print "No clips to display!"

	return clipList, clipStartTimes

def infoPrint(clipStartTimes, t0, t1, fileName):
	totalTime = t1-t0
	print("\n\n")
	print("For video file " + fileName)
	print("Video length was about " + str(round(frameCount/FPS_VAL,2)) +
		  " seconds")
	print("Analysis done in " + str(round(totalTime,2)) + " seconds.")
	print("------------------------")
	print("   Final Movement Clip Times: " +
		  "\n------------------------")

	if len(clipStartTimes) == 0:
		print "NO MOTION DETECTED\n"
	else:
		for timeStr in clipStartTimes:
			print "    " + timeStr


#
# off to the races
#
t0 = time.time()

motionPeriod = False

prev_frame = None
prev_prev_frame = None

frameCount = 0
startBuffer = 0
endBuffer = 0

motionTimes = []
endTimes = []

hasOutput = False

clipStartTimes = []

clipList = []
clip = []

#
# Read in arguments and helpful help messages
#
parser = argparse.ArgumentParser(description="GWMA Motion Detection")
parser.add_argument("inFile", type=str,
					help="file path for input video")
parser.add_argument("-w", "--watch", help="watch threshold images",
					action="store_true")

ARGS = parser.parse_args()

#
# First, simple I/O check
#
if os.path.isfile(ARGS.inFile):
	inFile = ARGS.inFile
else:
	print("Input file does not exist. Exiting")
	sys.exit()

if os.path.exists(ARGS.outDirectory):
	hasOutput = True
	outDirectory = ARGS.outDirectory
else:
	print("Proceeding with no output ([-o] not supplied or does not exist).")

if (not isinstance(ARGS.firstFrameSec, int)):
	print("First frame selection is not an integer. Exiting")
	sys.exit()
else:
	firstFrameSec = ARGS.firstFrameSec

watch = ARGS.watch

#
# begin streaming video from file on separate thread
#
fvs = cv2.VideoCapture(inFile)

fvs = FileVideoStream(inFile).start()

while not fvs.isDone():

	if not fvs.more():
		continue

	orgFrame = fvs.read()

	frameCount = frameCount + 1
	
	frame = convertFrame(orgFrame)

	if frameCount == 1:
		prev_prev_frame = frame
		continue
	elif frameCount == 2:
		prev_frame = frame
		continue		

	frameDiff = getFrameDiffs(frame, prev_frame, prev_prev_frame)
	thresh = getThreshold(frameDiff)
	pixelSum = getPixelSum(thresh)

	if watch:
		cv2.imshow("Threshold Image", thresh)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

	if pixelSum[0] > SUM_THRESHOLD:
		if not motionPeriod:
			startTimeString = hmsString(frameCount / FPS_VAL)
			clipStartTimes.append(startTimeString)

		endBuffer = 0
		motionPeriod = True

	elif motionPeriod:
		endBuffer = endBuffer + 1

	if motionPeriod and (len(clip) < 2 * FPS_VAL):
		clip.append(orgFrame)

	if endBuffer >= END_BUFFER_CAP:
		endBuffer = 0
		motionPeriod = clipList.append(clip)
		clip = []

	# progress update
	if frameCount % 100 == 0:
		print "Working on frame " + str(frameCount)
		print "  " + str(len(clipList)) + " clips so far."

	prev_prev_frame = prev_frame
	prev_frame = frame

# append the final clip if the video ends during motion
if motionPeriod:
	clipList.append(clip)
	print "  " + str(len(clipList)) + " clips so far."

if watch:
	cv2.destroyAllWindows()

if frameCount == 0:
	print("Error reading input! Not a video? Try again.")
	sys.exit()

clipList, clipStartTimes = clipDisplay(clipList, clipStartTimes)

t1 = time.time()
infoPrint(clipStartTimes, t0, t1, inFile)
