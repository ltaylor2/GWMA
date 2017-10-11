require(ggplot2)
require(dplyr)
require(lubridate)

motionTimes <- read.csv("Results/Scraped_Times.csv", stringsAsFactors=FALSE)
motionTimes$Date <- mdy(motionTimes$Date)
motionTimes$Motion_Time <- hms(motionTimes$Motion_Time)
for (r in 1:nrow(motionTimes)) {
	if (motionTimes$Log[r] == "FIrstLog") {
		motionTimes$Log[r] <- "FirstLog"
	} else if(motionTimes$Log[r] == "Bare") {
		motionTimes$Log[r] <- "BareLog"
	}
}

startTimes <- read.csv("Results/Camera Start Times.csv", stringsAsFactors=FALSE)
startTimes$Date <- mdy(startTimes$Date)
startTimes$Start.Time <- hm(startTimes$Start.Time)

metaData <- read.csv("Results/Motion Metadata.csv", stringsAsFactors=FALSE)
metaData <- metaData[,c("Filename", "Date", "Video_Length_.s.")]

metaData$Log <- sapply(strsplit(metaData$Filename, "_"), "[[", 1)
for (r in 1:nrow(metaData)) {
	if (metaData$Log[r] == "FIrstLog") {
		metaData$Log[r] <- "FirstLog"
	} else if(metaData$Log[r] == "Bare") {
		metaData$Log[r] <- "BareLog"
	}
}

metaData$Video_Num <- sapply(strsplit(metaData$Filename, "_"),
	function(x) {
		s <- x[[5]]
		as.numeric(substr(s, 1,2))
})

metaData$Video_Length_.s. <- seconds_to_period(metaData$Video_Length_.s.)
metaData$Date <- mdy(metaData$Date)

for (r in 1:nrow(metaData)) {
	if (metaData$Log[r] == "FIrstLog") {
		metaData$Log[r] <- "FirstLog"
	} else if(motionTimes$Log[r] == "Bare") {
		metaData$Log[r] <- "BareLog"
	}
}

# recursively adjust motion time
adjustClipTime <- function(motionInfo, vidNum) {

	date <- motionInfo$Date
	log <- motionInfo$Log
	if (vidNum == 1) {
		startTime <- subset(startTimes, Date==date & Log==log)$Start.Time
		return (startTime)
	} else {
		timeAdjustment = subset(metaData, Date==date & Log==log & Video_Num==vidNum-1)$Video_Length_.s.
		return(timeAdjustment + adjustClipTime(motionInfo, vidNum-1))
	}
}

for (r in 1:nrow(motionTimes)) {
	time <- motionTimes$Motion_Time[r,]
	adjustedTime <- time + adjustClipTime(motionTimes[r,], motionTimes$Video_Num[r])
	motionTimes$Motion_Time[r] <- adjustedTime
}

# histogram of motiontimes
ggplot(motionTimes, aes(x=as.numeric(Motion_Time))) + geom_histogram() + theme_bw()




