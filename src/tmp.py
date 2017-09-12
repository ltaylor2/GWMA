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
import argparse
import os
import sys
import gc
#
# VISION PARAMETERS
#
FPS_VAL = 30.0				# must match camera, must be hard-coded

START_BUFFER_CAP = 0	
END_BUFFER_CAP = 10 * FPS_VAL

MOVE_CHECK_TIMING = 60 * FPS_VAL

RESIZE_FACTOR = 0.25 		# smaller videos are faster but may lose small motion

GAUSSIAN_BOX = 31			# blurring factor (larger is blurrier, must be odd)

DIFF_THRESHOLD = 30
SUM_THRESHOLD = 100000		# how many motion pixels for a reading? (*255)

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


def getFrameDiffs(frame, prev_frame, prev_prev_frame):
	d1 = cv2.absdiff(frame, prev_frame)
	d2 = cv2.absdiff(prev_frame, prev_prev_frame)
	diffFrame = cv2.bitwise_xor(d1, d2)
	return diffFrame
#
# Read in arguments and helpful help messages
#
parser = argparse.ArgumentParser(description="GWMA Motion Detection")
parser.add_argument("inFile", type=str,
					help="file path for input video")
parser.add_argument("-o", "--outDirectory", type=str, default="none",
					help="folder for output motion clips")
parser.add_argument("-w", "--watch", help="watch threshold images",
					action="store_true")
parser.add_argument("-f", "--firstFrameSec", type=int, help="select first frame (s)",
					default=1)

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

if not isinstance(ARGS.firstFrameSec, int):
	print("First frame selection is not an integer. Exiting")
	sys.exit()
else:
	firstFrameSec = ARGS.firstFrameSec

watch = ARGS.watch

fvs = FileVideoStream(inFile).start()

while not fvs.isDone():

	if not fvs.more():
		continue

	orgFrame = fvs.read()

	frameCount = frameCount + 1

	resize = cv2.resize(orgFrame, (0, 0), fx=RESIZE_FACTOR, fy=RESIZE_FACTOR)
	frame = cv2.cvtColor(resize, cv2.COLOR_BGR2GRAY)
	frame = cv2.GaussianBlur(frame, (GAUSSIAN_BOX, GAUSSIAN_BOX), 0)

	if frameCount == 1:
		prev_frame = frame
		continue

	prev_prev_frame = prev_frame
	prev_frame = frame

	frameDiff = getFrameDiffs(frame, prev_frame, prev_prev_frame)
	thresh = cv2.threshold(frameDiff, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
	pixelSum = cv2.sumElems(thresh)

	if watch:
		cv2.imshow("frame", thresh)

	# is there sufficient movement?
	if pixelSum[0] > SUM_THRESHOLD:
		if not motionPeriod:
			clipStartTimes.append(frameCount / FPS_VAL)

		endBuffer = 0
		motionPeriod = True

	elif motionPeriod:
		endBuffer = endBuffer + 1

	if motionPeriod and (len(clip) < 2 * FPS_VAL):
		clip.append(orgFrame)

	if endBuffer >= END_BUFFER_CAP:
		print "APPENDING CLIP! [" + str(len(clip)) + " / " + str(len(clipList)) + "]"
		endBuffer = 0
		motionPeriod = False
		clipList.append(clip)
		clip = []

	if watch:
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

	if frameCount % 100 == 0:
		print "Working on frame " + str(frameCount)

if motionPeriod:
	clipList.append(clip)

if watch:
	cv2.destroyAllWindows()

if frameCount == 0:
	print("Error reading input! Not a video? Try again.")
	sys.exit()

if len(clipList) > 0:
	while True:
		isReady = raw_input("Starting to display clips! Ready? [y]")
		if isReady == "y":
			break

	clipCounter = 1

	for clip in clipList:

		print "Displaying clip " + str(clipCounter) + "."
		print "Clip start time: " + str(clipStartTimes[clipCounter])

		clipCounter = clipCounter + 1

		while True:
			for frame in clip:
				cv2.imshow("preview", frame)
				if cv2.waitKey(1) & 0xFF == ord('q'):
					break

			goNextClip = raw_input("Go to next clip? [y]")
			if goNextClip == "y":
				break

	cv2.destroyAllWindows()
else:
	print "No motion detected! Wrapping up."
#
# output results, including detecting periods
# but remember motion clips have already been written!
#
t1 = time.time()
total = t1-t0

print("\n\n")
print("For video file " + inFile)
print("Video length was about " + str(round(frameCount/FPS_VAL,2)) +
	  " seconds")
print("Analysis done in " + str(round(total,2)) + " seconds.")

print("------------------------")
print("   Final Movement Clip Times: " +
	  "\n------------------------")

if len(clipStartTimes) == 0:
	print("NO MOTION DETECTED\n")
else:
	for time in clipStartTime:
		print "    " + str(round(time, 2))

