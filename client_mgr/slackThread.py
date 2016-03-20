import threading
import traceback
import OCRparse
import time
import json
import center
from python_slackclient.slackclient import SlackClient


class SlackThread:
	"""
	Creates a thread to poll a SlackClient websocket for a slack team token
	processing any file upload events with OCR
	"""

	SLEEP_TIME_SECS = 10
	PING_FREQ_SECS = 3

	def __init__(self, user):
		self._user = user
		self._stop_flag = None
		self._thread = None
		self._slack_client = None
		self._last_msg_recv_time = 0
		self.start()

	def is_service_active(self):
		if self._thread and not (self._thread is None) and self._thread.is_alive():
			return True
		return False

	def start(self):
		print "Starting SlackThread for user: " + self.get_user_id_str() + "..."
		if self.is_service_active():
			print "SlackThread already running for user: " + self.get_user_id_str()
			self.stop()

		self._stop_flag = threading.Event()
		self._thread = threading.Thread(target=self.event_loop, args=())
		self._thread.setDaemon(daemonic=True)
		self._thread.start()
		print "SlackThread started for user: " + self.get_user_id_str()

	def stop(self):
		if not self.is_service_active():
			print "SlackThread not running for user: " + self.get_user_id_str()
			return

		print "Terminating SlackThread for user: " + self.get_user_id_str() + "..."
		self._stop_flag.set()
		self._thread.join()
		print "Terminated SlackThread for user: " + self.get_user_id_str() + "!"

	def get_user_id_str(self):
		return str(self._user.id)

	def get_last_msg_recv_time(self):
		return self._last_msg_recv_time

	def event_loop(self):
		while not self._stop_flag.is_set():
			try:
				# sleep
				time.sleep(self.SLEEP_TIME_SECS)

				# check for updates
				token = self._user.access_token

				# lazy connect
				if self._slack_client is None:
					self._slack_client = SlackClient(token)

					if not self._slack_client.rtm_connect():
						print "Slack client failed to connect for user: " + self.get_user_id_str()
						continue

				# send ping if PING_FREQ duration has elapsed
				if (int(time.time()) - self._last_msg_recv_time) > self.PING_FREQ_SECS:
					self._slack_client.server.ping()

				# check for new events
					while True:
						r = self._slack_client.rtm_read()

						if len(r) == 0:
							break

						self._last_msg_recv_time = int(time.time())
						msg_type = r[0]["type"]
						print "From user: " + self.get_user_id_str() + " -- " + json.dumps(r)

						# check for 'file created'
						if msg_type == "file_public":
							print "Processing file for user: " + self.get_user_id_str()
							OCRparse.new_driver(self._slack_client, r[0]["file"], token)
							# TODO: can we have the comment sent from a bot name instead of the user's name?
			except:
				print traceback.print_exc()
				print "Unexpected error in SlackThread for user: " + self.get_user_id_str()
				time.sleep(self.SLEEP_TIME_SECS)


class SlackThreadManager:
	"""
	Manages a SlackThread for each user
	"""

	SLEEP_TIME_SECS = 10
	CONNECTION_LOST_TIME_SECS = 30

	def __init__(self):
		self._slack_thread_dict = {}
		self._thread = threading.Thread(target=self.check_threads, args=())
		self._thread.setDaemon(daemonic=True)
		self._thread.start()

	def check_threads(self):
		while True:
			try:
				time.sleep(self.SLEEP_TIME_SECS)

				# check SlackThread for each User
				users = center.get_users()

				for key, user in users.iteritems():
					if key not in self._slack_thread_dict.keys():
						# create SlackThread for this user
						slack_thread = SlackThread(user=user)
						self._slack_thread_dict[key] = slack_thread
						time.sleep(self.SLEEP_TIME_SECS)  # wait for thread to start

					slack_thread = self._slack_thread_dict[key]

					# check if we haven't received a message in a while
					if (int(time.time()) - slack_thread.get_last_msg_recv_time()) > self.CONNECTION_LOST_TIME_SECS:
						# rebuild thread
						print "Rebuilding lost SlackThread for user: " + slack_thread.get_user_id_str()
						print str(int(time.time())) + " vs " + str(slack_thread.get_last_msg_recv_time())
						# slack_thread.start()

			except:
				print traceback.print_exc()
				print "SlackThreadManager exception!"
				time.sleep(self.SLEEP_TIME_SECS)

	def start_all(self):
		for slack_thread in self._slack_thread_dict.itervalues():
			slack_thread.start()

	def stop_all(self):
		for slack_thread in self._slack_thread_dict.itervalues():
			slack_thread.stop()

	def is_service_active(self, user_key):
		if user_key in self._slack_thread_dict:
			return self._slack_thread_dict[user_key].is_service_active()
		return False
