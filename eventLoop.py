import OCRparse
import threading
import time


eventLoopStopFlag = None
eventLoopThread = None


def start_event_loop():
	global eventLoopThread
	global eventLoopStopFlag

	if eventLoopThread and not (eventLoopThread is None) and eventLoopThread.is_alive():
		print "Event loop already running"
		stop_event_loop()

	eventLoopStopFlag = threading.Event()
	eventLoopThread = threading.Thread(target=OCRparse.event_loop, args=(eventLoopStopFlag,))
	eventLoopThread.start()
	print "Event loop thread started!"


def stop_event_loop():
	global eventLoopThread
	global eventLoopStopFlag

	print "Terminating event loop..."
	eventLoopStopFlag.set()
	eventLoopThread.join()
	print "Terminated!"


def event_loop(stop_flag):
	while not stop_flag.is_set():
		# get Users dict
		# check for updates
		# sleep
		time.sleep(1)
