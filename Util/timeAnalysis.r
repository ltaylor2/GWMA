require(ggplot2)
require(dplyr)
require(tidyr)
require(lubridate)

motionTimes <- read.csv("Results/Scraped_Times.csv", stringsAsFactors=FALSE)
motionTimes$Date <- mdy(motionTimes$Date)
for (r in 1:nrow(motionTimes)) {
	if (motionTimes$Log[r] == "FIrstLog") {
		motionTimes$Log[r] <- "FirstLog"
	} else if(motionTimes$Log[r] == "Bare") {
		motionTimes$Log[r] <- "BareLog"
	}
}

motionTimes <- unite(motionTimes, datetime, Date, Motion_Time, sep=" ", remove=FALSE)
motionTimes$datetime <- ymd_hms(motionTimes$datetime)

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

# find start time
getStartTime <- function(motionInfo) {
	date <- motionInfo$Date
	log <- motionInfo$Log
	startTime <- subset(startTimes, Date==date & Log==log)$Start.Time
	return (startTime)
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
	time <- motionTimes$datetime[r]
	adjustedTime <- time + adjustClipTime(motionTimes[r,], motionTimes$Video_Num[r])
	motionTimes$datetime[r] <- adjustedTime
}

# 
# calculate observation effort
#
latestVid <- metaData %>%
				group_by(Log, Date) %>%
				filter(Video_Num==max(Video_Num))

latestVidStartTimes <- c(period(0))
latestVidEndTimes <- c(period(0))

for (r in 1:nrow(latestVid)) {
	time <- getStartTime(latestVid[r,])
	latestVidStartTimes <- c(latestVidStartTimes, time)

	time <- latestVid$Video_Length_.s.[r]
	adjustedTime <- time + adjustClipTime(latestVid[r,], latestVid$Video_Num[r])
	latestVidEndTimes <- c(latestVidEndTimes, adjustedTime)
}

latestVid <- bind_cols(latestVid, Start.Time=latestVidStartTimes[-1],
								  End.Time=latestVidEndTimes[-1])

observationBins <- matrix(0, ncol=1, nrow=86400)

for (r in 1:nrow(latestVid)) {
	start <- as.numeric(floor(seconds(latestVid$Start.Time[r])))
	end <- as.numeric(floor(seconds(latestVid$End.Time[r])))

	for (t in start:end) {
		observationBins[t] <- observationBins[t] + 1
	}
}

observations <- data.frame(hour=hours(floor((1:86400)/3600)), obs=observationBins)
hourObs <- observations %>%
			group_by(as.numeric(hour)) %>%
			summarise(obs=sum(obs))
colnames(hourObs) <- c("hour", "numObs")
hourObs$hour <- hourObs$hour/3600

activity <- motionTimes %>%
			group_by(hour(datetime)) %>%
			count()
colnames(activity) <- c("hour", "numActs")

activity <- left_join(ungroup(activity), ungroup(hourObs), by="hour")

activity <- mutate(activity, adjustedActs = numActs/numObs)
# histogram of motiontimes
activity <- mutate(activity, adjustedActs = numActs/numObs)
# histogram of motiontimes
ggplot(activity, aes(x=hour, y=adjustedActs)) + 
	geom_bar(stat="identity") + 
	scale_x_continuous(limits=c(0, 24), breaks=0:24, labels=0:24)  +
	theme_minimal()




