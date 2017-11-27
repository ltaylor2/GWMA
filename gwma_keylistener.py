import time
import sys
import termios
from pynput import keyboard

# KEY CODES
BEGIN_KEY = keyboard.Key.alt_r
EXIT_KEY = keyboard.Key.shift_r

ALAD_KEY = keyboard.Key.cmd_l
NURRT_KEY = keyboard.Key.ctrl_l
PERCH_KEY = keyboard.Key.alt_l

SECONDARY_ALAD_KEY = keyboard.Key.cmd_r

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
	if key == BEGIN_KEY:
		print "Beginning observations at " + time.strftime("%x %H:%M:%S")
		
		event = "begin"
		print_event(event, log)

		paused = False

	elif key == EXIT_KEY:
		if not paused:
			paused = True
			termios.tcflush(sys.stdin, termios.TCIOFLUSH)
			
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

	elif key == ALAD_KEY:
		if not paused:
			event = "ALAD"
			print_event(event,log)

	elif key == NURRT_KEY:
		if not paused:
			event = "nurrt"
			print_event(event, log)

	elif key == PERCH_KEY:
		if not paused:
			event = "perch"
			print_event(event, log)

	elif key == SECONDARY_ALAD_KEY:
		if not paused:
			event = "ALAD"
			print_event(event, secondary_log)

lis = keyboard.Listener(on_press=on_press)
lis.start()

print "-----------------------------"
print "INSTRUCTIONS:"
print "Begin = option(R)"
print "Nurrt = ctrl(L)"
print "Perch = option(L)"
print "ALAD = cmd(L)"
print "Secondary ALAD = cmd(R)"
print "Exit = shift(R)"
print "-----------------------------"

print "Enter option(R) to start observation."
lis.join()