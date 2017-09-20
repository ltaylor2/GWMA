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

END_BUFFER_CAP = 2 * FPS_VAL

RESIZE_FACTOR = 0.25 		# smaller videos are faster but may lose small motion

GAUSSIAN_BOX = 31			# blurring factor (larger is blurrier, must be odd)

DIFF_THRESHOLD = 30
SUM_THRESHOLD = 80000		# how many motion pixels for a reading? (*255)

CLIP_STORAGE_FILENAME = "tmp_clip_storage.AVI"

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

	s = str(int(hrs)) + ":" + str(int(mins)) + ":" + str(round(secs,2))
	return s

def readClipFromStorage(clipLength, fvs):
	clip = []
	for frameIndex in range(0, clipLength):
		grabbed, frame = fvs.read()
		if not grabbed:
			print "UH OH! Weird error, clip lengths don't align with clip."
			return

		clip.append(frame)
	return clip

def writeClipToStorage(clip, clipStorage, clipStorageLengths):
	for frame in clip:
		clipStorage.write(frame)

	clipStorageLengths.append(len(clip))
	clip = []

	return clip, clipStorageLengths

def clipDisplay(clipStartTimes):
	if len(clipStorageLengths) > 0:
		while True:
			isReady = raw_input("Starting to display clips! Ready? [y]")
			if isReady == "y":
				print "Instructions: 'y' =  Retain // 'c' = Clear // anything else = replay"
				break

		clipCounter = 0
		numClipsDisplayed = 1

		# NOTE here we're going to single thread it, for now,
		# because imshow has its own thread as well, which bugs out
		fvs = cv2.VideoCapture(CLIP_STORAGE_FILENAME)

		while clipCounter < len(clipStartTimes):
			print "Displaying clip " + str(numClipsDisplayed) + "."
			print "Clip start time: " + str(clipStartTimes[clipCounter])

			clipLength = clipStorageLengths[clipCounter]

			clip = readClipFromStorage(clipLength, fvs)

			while True:
				for frame in clip:
					resize = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
					cv2.imshow("preview", resize)
					if cv2.waitKey(30) & 0xFF == ord('q'):
						break

				clipResponse = ""
				if clipCounter == len(clipStartTimes):
					clipResponse = raw_input("This is the last clip. Response? [y/c/...]")
				else:
					clipResponse = raw_input("Response? [y/c/...]")

				if clipResponse == "y":
					clipCounter = clipCounter + 1
					numClipsDisplayed = numClipsDisplayed + 1
					break
				elif clipResponse == "c":
					removedTimeStr = clipStartTimes.pop(clipCounter)
					clipStorageLengths.pop(clipCounter)
					numClipsDisplayed = numClipsDisplayed + 1
					print "Removed clip at " + removedTimeStr
					break
				else:
					print "Replaying clip " + str(numClipsDisplayed) + "."

	else:
		print "No clips to display!"

	return clipStartTimes


def infoPrint(clipStartTimes, t0, t1, t2, fileName, hasOutput, outFile):
	frameTime = t1-t0
	userTime =  t2-t1

	messageString = "\n\n"
	messageString += "For video file " + fileName + "\n"
	messageString += "Video length was about " + str(round(frameCount/FPS_VAL,2)) + " seconds\n"
	messageString += "Frame analysis done in " + str(round(frameTime,2)) + " seconds.\n"
	messageString += "User sorting done in " + str(round(userTime,2)) + " seconds.\n"
	messageString += "------------------------\n"
	messageString += "   Final Movement Clip Times: " + "\n------------------------\n"

	if len(clipStartTimes) == 0:
		messageString += "NO MOTION DETECTED\n"
	else:
		for timeStr in clipStartTimes:
			messageString += "    " + timeStr + "\n"

	print messageString

	if hasOutput:
		f = open(outFile, "a")
		f.write(messageString)
		f.close()
		print "Wrote motion info to file " + outFile


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

clipCounter = 0
clip = []
clipStorageLengths = []

written = False

outFile = ""
hasOutput = False

#
# Read in arguments and helpful help messages
#
parser = argparse.ArgumentParser(description="GWMA Motion Detection")
parser.add_argument("inFile", type=str,
					help="file path for input video")
parser.add_argument("-w", "--watch", help="watch threshold images",
					action="store_true")
parser.add_argument("-o", "--outFile", help="file to write final output message",
					type=str, default="none")

ARGS = parser.parse_args()

#
# First, simple I/O check
#
if os.path.isfile(ARGS.inFile):
	inFile = ARGS.inFile
else:
	print("Input file does not exist. Exiting")
	sys.exit()

if ARGS.outFile != "none" and os.path.isfile(ARGS.outFile):
	outFile = ARGS.outFile
	hasOutput = True
elif ARGS.outFile != "none" and not os.path.isfile(ARGS.outFile):
	print "Outfile does not exist. Won't print final info results (copy them yourself!)"

watch = ARGS.watch

#
# begin streaming video from file on separate thread
#
fvs = FileVideoStream(inFile).start()

clipStorage = cv2.VideoWriter(CLIP_STORAGE_FILENAME, cv2.VideoWriter_fourcc(*"XVID"), int(FPS_VAL),
						   	  (fvs.getWidth(), fvs.getHeight()))

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
		motionPeriod = False
		clip, clipStorageLengths = writeClipToStorage(clip, clipStorage, clipStorageLengths)

	# progress update
	if frameCount % 100 == 0:
		print "Working on frame " + str(frameCount)
		print "  " + str(len(clipStartTimes)) + " clips so far."

	prev_prev_frame = prev_frame
	prev_frame = frame

# append the final clip if the video ends during motion
if motionPeriod:
	clip, clipStorageLengths = writeClipToStorage(clip, clipStorage, clipStorageLengths)
	print "  " + str(len(clipStartTimes)) + " clips so far."

if watch:
	cv2.destroyAllWindows()

if frameCount == 0:
	print("Error reading input! Not a video? Try again.")
	sys.exit()

clipStorage.release()

t1 = time.time()
clipStartTimes = clipDisplay(clipStartTimes)

t2 = time.time()
infoPrint(clipStartTimes, t0, t1, t2, inFile, hasOutput, outFile)

os.remove(CLIP_STORAGE_FILENAME)