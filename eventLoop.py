import threading
import time
import center
import sys

EventLoopStopFlag = None
EventLoopThread = None


def start_event_loop():
	global EventLoopThread
	global EventLoopStopFlag

	if EventLoopThread and not (EventLoopThread is None) and EventLoopThread.is_alive():
		print "Event loop already running"
		stop_event_loop()

	EventLoopStopFlag = threading.Event()
	EventLoopThread = threading.Thread(target=event_loop, args=(EventLoopStopFlag,))
	EventLoopThread.start()
	print "Event loop thread started!"


def stop_event_loop():
	global EventLoopThread
	global EventLoopStopFlag

	print "Terminating event loop..."
	EventLoopStopFlag.set()
	EventLoopThread.join()
	print "Terminated!"


def event_loop(stop_flag):
	while not stop_flag.is_set():
		try:
			# sleep
			time.sleep(1)

			# get Users dict
			users_dict = center.get_users()

			# check for updates
			for key, user in users_dict.iteritems():
				print str(key) + ' ' + repr(user)
		except:
			print "Unexpected error in event_loop:", sys.exc_info()[0]
