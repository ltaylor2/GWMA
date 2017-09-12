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

START_BUFFER_CAP = 10		# buffer to avoid false positive blips (in frames)
END_BUFFER_CAP = 10			# buffer to avoid false gaps during motion (in frames)

RESIZE_FACTOR = 0.1 		# smaller videos are faster but may lose small motion

GAUSSIAN_BOX = 71			# blurring factor (larger is blurrier, must be odd)

DIFF_THRESHOLD = 50
SUM_THRESHOLD = 8000		# how many motion pixels for a reading? (*255)

#
# off to the races
#
t0 = time.time()

firstFrame = None
firstFrameSet = False
motionPeriod = False

frameCount = 0
startBuffer = 0
endBuffer = 0

motionTimes = []
endTimes = []
saveFrames = []

hasOutput = False

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

if (hasOutput):
	out = cv2.VideoWriter("", cv2.VideoWriter_fourcc(*"XVID"), int(FPS_VAL), 
				  		 (int(fvs.get(3)),
				  		  int(fvs.get(4))))

while (fvs.isOpened()):

	(grabbed, orgFrame) = fvs.read()

	if (not grabbed):
		break

	frameCount = frameCount + 1

	#
	# simplify video for motion recognition
	#
	frame = cv2.resize(orgFrame, (0, 0), fx=RESIZE_FACTOR, fy=RESIZE_FACTOR)
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	frame = cv2.GaussianBlur(frame, (GAUSSIAN_BOX, GAUSSIAN_BOX), 0)

	if (not firstFrameSet and (frameCount / FPS_VAL == firstFrameSec)):
		firstFrame = frame
		firstFrameSet = True
		continue
	
	if (firstFrameSet):
		#
		# threshold pixel diffs and sum to detect binary yes/no movement
		#
		frameDiff = cv2.absdiff(firstFrame, frame)
		thresh = cv2.threshold(frameDiff, DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
		thresh = cv2.dilate(thresh, None, iterations=2)

		pixelSum = cv2.sumElems(thresh)

		# is there sufficient movement?
		if pixelSum[0] > SUM_THRESHOLD:
			startBuffer = startBuffer + 1
			endBuffer = 0

			# once movement has been occuring for awhile, begin the motion reading
			if startBuffer == START_BUFFER_CAP and not motionPeriod:
				motionPeriod = True

				# back-adjust to not lose entry
				motionTimes.append((frameCount - START_BUFFER_CAP) / FPS_VAL)
			
			# store motion period frames for output clips
			if hasOutput:
				saveFrames.append(orgFrame)

		# is the movement over (for now)?
		else:
			startBuffer = 0
			
			# count buffer to avoid false endings
			if motionPeriod:
				endBuffer = endBuffer + 1

	    # is the movement over for good? if so end motion period
		if endBuffer == END_BUFFER_CAP:
			endTimes.append(frameCount / FPS_VAL)
			endBuffer = 0
			motionPeriod = False

			#
			# all output writing happens at once using stored frames list
			#
			if hasOutput:
				startTime = round(motionTimes[-1],2)
				endTime = round(endTimes[-1],2)
				outPath = outDirectory + os.path.split(inFile)[1][0:-4] + "_" + str(int(startTime)) + "_" + str(int(endTime)) + ".avi"

				out.open(outPath, cv2.VideoWriter_fourcc(*"XVID"), int(FPS_VAL), 
				  		 (int(fvs.get(3)),
				  		  int(fvs.get(4))))

				# only AVI output codec is working, may be machine/ffmpeg sensitive
				print("Saving clip:" + outPath)

				# write the frames to file
				for f in saveFrames:
					out.write(f)	

				# reset motion period frames and release file
				saveFrames = []

		# progress update
		if frameCount % 100 == 0:
			print("Working on frame " + str(frameCount))

		# neat-o display, q to quit program
		if watch:
			cv2.imshow("frame", thresh)
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break

if watch:
	cv2.destroyAllWindows()

if frameCount == 0:
	print("Error reading input! Not a video? Try again.")
	sys.exit()

#
# output results, including detecting periods
# but remember motion clips have already been written!
#
else:
	t1 = time.time()
	total = t1-t0

	print("\n\n")
	print("For video file " + inFile)
	print("Video length was about " + str(round(frameCount/FPS_VAL,2)) +
		  " seconds")
	print("Analysis done in " + str(round(total,2)) + " seconds.")

	print("------------------------")
	print("   Movement duration estimations: " +
		  "\n------------------------")

	if len(motionTimes) == 0:
		print("NO MOTION DETECTED\n")
	else:
		for t in range(0, len(motionTimes)):
			durationStr = "   " + str(round(motionTimes[t],2))
			if len(endTimes) > t:
				durationStr = durationStr + " -- " + str(round(endTimes[t],2))
			else:
				durationStr = durationStr + " -- " + "end"

			print(durationStr + "\n")