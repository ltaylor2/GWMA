import sys
import os
import argparse

ACCEPTABLE_FILETYPES = [".txt", ".TXT"]

def getAllFiles(headPath):
	fullPathList = os.listdir(headPath)
	files = []
	for potentialFile in fullPathList:
		fileName = headPath + potentialFile
		if (os.path.isfile(fileName) and 
			potentialFile[-4:] in ACCEPTABLE_FILETYPES):
			files.append(fileName)

		elif os.path.isdir(fileName+"/"):
			recursiveFiles = getAllFiles(fileName+"/")
			for file in recursiveFiles:
				files.append(file)
	return files

def getAllUnderscores(s):
	indexList = []
	prevIndex = 0

	while '_' in s:
		index = s.find('_')
		indexList.append(index + prevIndex)
		s = s[index+1:]
		prevIndex += index + 1

	return indexList

parser = argparse.ArgumentParser(description="Scrapes times from motionDetection output")
parser.add_argument("inDirectory", type=str, help="directory path for results files")
parser.add_argument("outFile", type=str, help="Filepath for csv output")

ARGS = parser.parse_args()

#
# First, simple I/O stuff
#
if os.path.isdir(ARGS.inDirectory):
	inDirectory = ARGS.inDirectory
else:
	print ("\nInput directory does not exist.\n")
	sys.exit()

outFile = ARGS.outFile

# scrape files from input directory
fileNames = getAllFiles(inDirectory)	

if len(fileNames) == 0:
	print "Directory contained no acceptable output files. Exiting."
	sys.exit()

fOut = open(outFile, "w")
fOut.write("Filename,Log,Date,Video_Num,Motion_Time\n") # header file

print "Scraping files"

for fileName in fileNames:
	fIn = open(fileName)

	currVideoFile = ""
	log = ""
	date = ""
	videoNum = ""

	for line in fIn:

		if line.startswith("For video file"):
			currVideoFile = os.path.split(line[15:].strip())[1]

			indexList = getAllUnderscores(currVideoFile)

			# extract info from filename
			log = currVideoFile[0:indexList[0]]

			month = currVideoFile[indexList[0]+1:indexList[1]]
			day = currVideoFile[indexList[1]+1:indexList[2]]
			year = currVideoFile[indexList[2]+1:indexList[3]]

			date = month + "/" + day + "/" + year

			videoNum = currVideoFile[indexList[3]+1:-4]

		if line.startswith("    "):
			motionTime = line.strip()
			fOut.write(currVideoFile[:-4] + "," +
					   log + "," + 
					   date + "," + 
					   videoNum + "," + 
					   motionTime + "\n")

print "Done scraping files"
