import time
import sys

from pynput import keyboard

# KEY CODES
PAUSE_KEY = 'p'
BEGIN_KEY = "b"
EXIT_KEY = "x"

ALAD_KEY = 'a'
NURRT_KEY = 'n'
DANCE_KEY = 'd'
PERCH_KEY = 'e'

SECONDARY_ALAD_KEY = 's'

file_name = ""
paused = True

print "Starting key listener for GWMA observations"

file_name = raw_input("Enter filename: ")
f = open(file_name, 'a')

log = raw_input("Enter primary log: ")
secondary_log = raw_input("Enter secondary log: ")

def print_event(event, logName):
	timestamp = time.strftime("%H:%M:%S")
	date = time.strftime("%x")

	printStr = ""
	printStr += date + "," 
	printStr += timestamp + ","
	printStr += logName + ","
	printStr += event + "\n"

	global f
	f.write(printStr)
	print printStr 

def on_press(key):
	global paused
	global f

	# pause or unpause for all other behaviors
	if key == keyboard.KeyCode.from_char(BEGIN_KEY):
		print "Beginning observations at " + time.strftime("%x %H:%M:%S")
		
		event = "begin"
		print_event(event, log)

		paused = False

	elif key == keyboard.KeyCode.from_char(PAUSE_KEY):
		if paused:
			paused = False
			print "UNPAUSED"
		else:
			paused = True
			print "PAUSED NOW (\'p\' to unpause)"


	elif key == keyboard.KeyCode.from_char(EXIT_KEY):
		if not paused:
			paused = True
			is_sure = raw_input("Exit key pressed. Type \'exit\' to confirm: ")
			paused = False

			if is_sure == "exit":
				print "Ending observations at " + time.strftime("%x %H:%M:%S")

				event = "end"
				print_event(event, log)

				print "EXITING."
				sys.exit()

			else:
				return

	elif key == keyboard.KeyCode.from_char(ALAD_KEY):
		if not paused:
			event = "ALAD"
			print_event(event,log)

	elif key == keyboard.KeyCode.from_char(NURRT_KEY):
		if not paused:
			event = "nurrt"
			print_event(event, log)

	elif key == keyboard.KeyCode.from_char(PERCH_KEY):
		if not paused:
			event = "perch"
			print_event(event, log)

	elif key == keyboard.KeyCode.from_char(SECONDARY_ALAD_KEY):
		if not paused:
			event = "ALAD"
			print_event(event, secondary_log)

lis = keyboard.Listener(on_press=on_press)
lis.start()
print "Enter \'b\' to start observation."
lis.join()