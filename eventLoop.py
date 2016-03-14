import threading
import time
import center
import sys
import traceback
import json
from python_slackclient.slackclient import SlackClient

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
	slack_clients = {}

	while not stop_flag.is_set():
		try:
			# sleep
			time.sleep(10)

			# get Users dict
			users_dict = center.get_users()

			# check for updates
			for key, user in users_dict.iteritems():
				token = user.access_token

				# create and connect slack client if doesn't exist
				if token in slack_clients:
					client = slack_clients[token]
				else:
					client = SlackClient(token)

					if not client.rtm_connect():
						print "Slack client failed to connect for user ID: " + str(key) + ", token: " + token
						continue

					slack_clients[token] = client

				# check for new event
				r = client.rtm_read()

				if len(r) > 0:
					print r[0]["type"]
					print json.dumps(r)

					# check for 'file created'
					if r[0]["type"] == "file_created":
						print 'processing file for user ID: ' + str(key)
		except:
			print "Unexpected error in event_loop:", sys.exc_info()[0]
			print traceback.print_exc()
