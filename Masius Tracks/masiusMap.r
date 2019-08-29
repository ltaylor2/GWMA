library(tidyverse)
setwd("~/Desktop/Masius Tracks")

track1 <- read_csv("Track_08Nov2017.csv")
track2 <- read_csv("Track_31Oct2017.csv")

tracks <- bind_rows(track1, track2)
ways <- read_csv("Waypoints.csv")

logs <- ways %>%
		filter(grepl("LOG", ident)) %>%
		separate(ident, c("type", "name"), sep=" ")

otherPoints <- ways %>%
		filter(ident %in% c("COCINA", "Bunkhouse"))

dotsize <- 2.5
ggplot() + 
	geom_path(data=tracks, aes(x=Longitude, y=Latitude, colour="Trails")) +
	geom_point(data=subset(logs, !(name %in% c("FIRST", "LUIS", "BARE"))), aes(x=Longitude, y=Latitude, colour="Other Logs"), size=dotsize) +
	geom_point(data=subset(logs, name == "LUIS"), aes(x=Longitude, y=Latitude, colour="Luis' Log"), size=dotsize) +
	geom_point(data=subset(logs, name == "BARE"), aes(x=Longitude, y=Latitude, colour="Bare Log"), size=dotsize) +
	geom_point(data=subset(logs, name == "FIRST"), aes(x=Longitude, y=Latitude, colour="First Log"), size=dotsize) +
	geom_point(data=subset(otherPoints, ident == "COCINA"), aes(x=Longitude, y=Latitude, colour="Cocina"), size=dotsize) +
	geom_point(data=subset(otherPoints, ident == "Bunkhouse"), aes(x=Longitude, y=Latitude, colour="Bunkhouse"), size=dotsize) +
	scale_colour_manual(values=c("Trails" = "gray",
				     "Other Logs" = "brown",
				     "First Log" = "coral",
				     "Luis' Log" = "red",
				     "Bare Log" = "black",
				     "Cocina" = "darkgreen",
				     "Bunkhouse" = "blue"),
			    breaks=c("Trails", "Cocina", "Bunkhouse",
			    	     "First Log", "Luis' Log", "Bare Log",
			    	     "Other Logs")) +
	guides(colour=guide_legend(title="")) +
	ggtitle("Milpe Golden-winged Manakin Map") +
	coord_map() +
	theme_void() +
	theme(plot.title = element_text(hjust=0.5, family="Times", size=14),
	      legend.text = element_text(family="Times", size=14),
	      legend.position = c(0.2, 0.5)) -> g

ggsave("MASIUS_MAP_LT.pdf", width=8, height=8)