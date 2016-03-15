import threading
import time
import center
import sys
import traceback
import json
import OCRparse
from python_slackclient.slackclient import SlackClient

EventLoopStopFlag = None
EventLoopThread = None


def start_event_loop():
	global EventLoopThread
	global EventLoopStopFlag

	if is_service_active()
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


def is_service_active()
	if EventLoopThread and not (EventLoopThread is None) and EventLoopThread.is_alive():
		return True

	return False


def event_loop(stop_flag):
	slack_clients = {}

	while not stop_flag.is_set():
		try:
			# sleep
			time.sleep(10)

			# get Users dict
			users_dict = center.get_users()

			timestamp = int(time.time())

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

				# TODO: ping each connection every few seconds

				# TODO: check last message receive time for each connection, if too long ago then reconnect; need to store in User object, modify DB structure

				# check for new event
				r = client.rtm_read()

				if len(r) > 0:
					msg_type = r[0]["type"]
					print json.dumps(r)

					# check for 'file created'
					if msg_type == "file_public":
						print 'processing file for user ID: ' + str(key)
						OCRparse.new_driver(client, r[0]["file"], token)
						# TODO: can we have the comment sent from a bot name instead of the user's name?
		except:
			print "Unexpected error in event_loop:", sys.exc_info()[0]
			print traceback.print_exc()
