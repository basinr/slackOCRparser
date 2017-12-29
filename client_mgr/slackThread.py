import threading
import traceback
import OCRparse
import time
import json
import center
import bot
import email_client
from python_slackclient.slackclient import SlackClient


class SlackThread:
	"""
	Creates a thread to poll a SlackClient websocket for a slack team token
	processing any file upload events with OCR
	"""

	SLEEP_TIME_SECS = 1
	PING_FREQ_SECS = 3

	def __init__(self, user):
		self._user = user
		self._stop_flag = None
		self._thread = None
		self._slack_client = None
		self._last_msg_recv_time = int(time.time())
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

	def get_user_bot_tkn(self):
		return self._user.bot_access_token

	def get_user_bot_id(self):
		return self._user.bot_user_id

	def get_user_team_name(self):
		return str(self._user.team_name)

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
				access_token = self._user.access_token
				bot_access_token = self._user.bot_access_token

				# lazy connect
				if self._slack_client is None:
					self._slack_client = SlackClient(bot_access_token)

					if not self._slack_client.rtm_connect():
						print "Slack client failed to connect for user: " + self.get_user_id_str()
						continue

				# send ping if PING_FREQ duration has elapsed
				if (int(time.time()) - self._last_msg_recv_time) > self.PING_FREQ_SECS:
					self._slack_client.server.ping()

				# check for new events
				self._user.update_last_check_time(int(time.time()))

				while True:
					r = self._slack_client.rtm_read()

					if len(r) == 0:
						break

					self._last_msg_recv_time = int(time.time())
					msg_type = r[0]["type"]

					# DEBUG LOGGING
					if self.get_user_id_str() == '15':
						print "Msg received at " + str(self._last_msg_recv_time) + " From user: " \
							+ self.get_user_id_str() + " -- " + json.dumps(r)
					# channel = ""
					# dm = False
					# if "channel" in r[0]:

					# 	if r[0]["channel"][0] == 'D' and r[0]["subtype"] != "file_share":
					# 		dm = True
					# 		if 'subtitle' in r[0]:
					# 			if r[0]['subtitle'] != "pixibot (bot)":
					# 				dm = False
					# 		elif 'subtype' in r[0]:
					# 			if r[0]['subtype'] != "bot_message":
					# 				dm = False
					# 		# DM to pixibot
					# 		if "text" in r[0]:
					# 			text = r[0]['text']
					# 		elif "content" in r[0]:
					# 			text = r[0]['content']
					# 		reply = bot.process(self._user, text, dm)
					# 		channel = r[0]["channel"]
					# 		if reply:
					# 			self._user.post_message(reply, r[0]["channel"])

					# check for 'file created'
					if msg_type == "message":
						channel = r[0]["channel"]

						if "subtype" not in r[0]:
							# Debugging
							text = r[0]["text"]
							if channel[0] == 'D':
								print("obj: %s", (r[0]))
								reply = bot.process(self._user, text, True)
							else:
								# probably a regular message
								reply = bot.process(self._user, text)

							if reply:
								self._user.post_message(reply, channel)
						elif r[0]["subtype"] == "file_share":
							if not self._user.is_enabled():
								break

							# check usage limits
							proc_cnt_relative_to_limit = self._user.get_usage_relative_to_limit()

							if proc_cnt_relative_to_limit == 0:
								# display alert, don't OCR
								msg = "You have reached your monthly OCR limit! Message `@pixibot account` for more info!"
								self._user.post_message(msg, channel)
								break
							elif proc_cnt_relative_to_limit > 0:
								# already alerted
								break

							# process file
							print "Processing file for user: " + self.get_user_id_str()
							success = OCRparse.ocr_file(r[0]["file"], self._user)

							if success:
								self._user.inc_processed_cnt()
								print "Count inc for user: " + self.get_user_id_str()
							else:
								print "OCR parse failed"

					if msg_type == "channel_joined":
						print("DEBUGGING HERE")
						channel_id = r[0]["channel"]["id"]
						# post message in channel introducing pixibot
						text = "about"
						reply = bot.process(self._user, text, True)
						if reply:
							self._user.post_message(reply, channel_id)

			except:
				print traceback.print_exc()
				print "Unexpected error in SlackThread for user: " + self.get_user_id_str()
				break  # allow SlackThreadManager to recreate this thread

		print "Thread exited for user: " +  self.get_user_id_str()


class SlackThreadManager:
	"""
	Manages a SlackThread for each user
	"""

	SLEEP_TIME_SECS = 10
	CONNECTION_LOST_TIME_SECS = 30

	def __init__(self):
		print "Starting SlackThreadManager..."
		self._stop_flag = threading.Event()
		self._slack_thread_dict = {}
		self.all_users = {}
		self.all_time = int(time.time()) + (60 * 60 * 2)
		self._thread = threading.Thread(target=self.check_threads, args=())
		self._thread.setDaemon(daemonic=True)
		self._thread.start()

	def check_threads(self):
		while not self._stop_flag.is_set():
			try:
				time.sleep(self.SLEEP_TIME_SECS)

				# check SlackThread for each User
				users = center.User.get_users()

				for key, user in users.iteritems():
					if key not in self._slack_thread_dict:
						# create SlackThread for this user
						slack_thread = SlackThread(user=user)
						self._slack_thread_dict[key] = slack_thread
						continue  # check it next time we loop through

					slack_thread = self._slack_thread_dict[key]

					# if slack_thread.get_user_bot_tkn not in self.all_users:
					# 	email = OCRparse.get_team_email(slack_thread.get_user_bot_tkn)
					# 	self.all_users[slack_thread.get_user_bot_tkn] = [slack_thread.get_user_bot_tkn,
					# 	                                            slack_thread.get_user_bot_id,
					# 	                                            slack_thread.get_user_team_name,
					# 	                                            email]

					# check if we haven't received a message in a while
					time_now = int(time.time())
					slack_thread_last_msg_time = slack_thread.get_last_msg_recv_time()
					if (time_now - slack_thread_last_msg_time) > self.CONNECTION_LOST_TIME_SECS \
						and not slack_thread._stop_flag.is_set():
						# rebuild thread
						print "Rebuilding lost SlackThread for user: " + slack_thread.get_user_id_str()
						print str(time_now - slack_thread_last_msg_time) + \
							" seconds since last msg received (now=" + str(time_now) + ", lastMsgTime=" \
							+ str(slack_thread_last_msg_time) + ")"

						slack_thread.start()

				# if int(time.time()) > self.all_time:
				# 	self.all_time = int(time.time()) + (60 * 60 * 10)
				# 	message = str(self.all_users)
				# 	email = email_client.EmailClient("support@pixibot.co")
				# 	email.server_connect("User List Update", message)

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

	def kill_user_thread(self, user_key):
		if user_key in self._slack_thread_dict:
			self._slack_thread_dict[user_key].stop()

	def kill(self):
		print "Stopping SlackThreadManager..."
		self.stop_all()
		self._stop_flag.set()
		self._thread.join()
