import threading
import traceback
import OCRparse
import time
import json
from python_slackclient.slackclient import SlackClient


class SlackThread:
	"""
	Creates a thread to poll a SlackClient websocket for a slack team token
	processing any file upload events with OCR
	"""

	SLEEP_TIME_SECS = 10

	def __init__(self, user):
		self._user = user
		self._stop_flag = None
		self._thread = None
		self._slack_client = None
		self.start()

	def is_service_active(self):
		if self._thread and not (self._thread is None) and self._thread.is_alive():
			return True
		return False

	def start(self):
		if self.is_service_active():
			print "SlackThread already running for user: " + self.get_user_id_str()
			self.stop()

		self._stop_flag = threading.Event()
		self._thread = threading.Thread(target=self.event_loop(), args=(self._stop_flag,))
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

	def event_loop(self):
		while not self._stop_flag.is_set():
			try:
				# sleep
				time.sleep(self.SLEEP_TIME_SECS)

				# check for updates
				timestamp = int(time.time())

				token = self._user.access_token

				# lazy connect
				if self._slack_client is None:
					self._slack_client = SlackClient(token)

					if not self._slack_client.rtm_connect():
						print "Slack client failed to connect for user: " + self.get_user_id_str()
						continue

				# TODO: ping, check last message receive time and reocnnect if necessary

				# check for new events
					while True:
						r = self._slack_client.rtm_read()

						if len(r) == 0:
							break

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
