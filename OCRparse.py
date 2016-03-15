import requests
import json
import httplib2
import sys
import time
import python_slackclient
from python_slackclient.slackclient import SlackClient
import shutil
import re
# from unidecode import unidecode


# Downloads file from slack channel into test2.png
# RETURNS: the OCR text of the downloaded file
def slackAPI_download_file(sc, url, token):

	download_url = url
	headers = {"Authorization" : "Bearer " + token}
	r = requests.get(download_url, headers=headers)
	path = 'test2.png'
	if r.status_code == 200:
	    with open('test2.png', 'wb') as f:
			f.write(r._content)

	result = OCRclientcall(path)
	return result


# Calls the OCR web api
# RETURNS: the text of the OCR'd image
def OCRclientcall(download_file):

	# OCR logic using the web client

	payload = {'isOverlayRequired': 'False',
	           'apikey': 'helloworld',
	           'language': 'eng',
	           }

	with open(download_file, 'rb') as f:
        r = requests.post('https://api.ocr.space/parse/image',
                          files={download_file: f},
                          data=payload,
                          )

	text = r.json()

	text = text["ParsedResults"][0]["ParsedText"]

	return text

# Used with "Add to Slack" Button
# Does the second step of the oauth process, found here: https://api.slack.com/docs/oauth
# code comes from center.py's signup() function
# RETURNS: access_token to be added to db in signup()
def get_access_token(code):

	token = 'error'
	r = requests.get("https://slack.com/api/oauth.access", 
		params={'client_id': '13657523393.23587667329', 
		'client_secret': 'daa51f4cbf84779d2c01f8eafe59cd1f',
		'code': code,
		'redirect_uri': 'https://slackocrparse.herokuapp.com/signup/'
		})

	if r.status_code == 200:
		if (r.json()["ok"]):
			token = r.json()['access_token']
	else:
		print "invalid code (don't reuse, expires in 10 minutes, etc.)"

	return token

# Downloads file, OCRs content, posts file comment
def new_driver(sc, file_, token):
	
	# passes in the private url download link
	result = slackAPI_download_file(sc, file_["url_private_download"], token)

	# cleans up the text using parseText
	comment = result

	# posts the comment in the channel
	requests.get("https://slack.com/api/files.comments.add", params={
		'token': token, 
		'file': file_["id"], 
		'comment': comment})


# send "ping" messages to server to check for connectivity
def autoping(token, sc_obj):
	try:
		r = sc_list[0].server.send_to_websocket({
			'id': 1,
			'type': 'ping',
			'time': int(time.time())
		})
		print "clean"
		return sc_obj
	except:
		print "websocket broken. reconnecting..."
		return SlackClient(token)

# Takes in a list of all user tokens, and cycles through printing OCR outputs
# SHOULD ALWAYS BE RUNNING, IDEALLY
def alt_start(token_list):

	# A dictionary that maps the SC objects to its corresponding token
	token_dict = {}

	# A list of "SC" objects, using the python-slackclient library (github)

	sc_list = []

	# keeps track of token indexes for error output (see below)
	
	counter = 0

	for token in token_list:
		if token == 'error':
			print token
			print "error with token" + counter
			return False

		sc_list.append(SlackClient(token))

		# takes the last element in sc_list, and sets its value as the token

		token_dict[sc_list[-1]] = token
 
		# establish rtm connections with all tokens. This is a websocket that will always be open
		# error checking to make sure this is open is optimal!

		if not sc_list[counter].rtm_connect():
			print "error with rtm connection: " + "token: " + token_list[0]
		counter += 1

	# used for websocket ping pong (autoping())
	last_ping = 0

	for num in range(200): # temp hack to exit the program after 200 loops
		for connection in sc_list:
			# now = int(time.time())

			# if now > last_ping + 3:
			# 	autoping(token_dict[connection], connection)
			# 	last_ping = int(time.time())

			r = connection.rtm_read()
			# if r has content inside of it
			if len(r) > 0:

				# if the event is a "file created" 
				# ISSUE 1: indexing at '0' might be wrong. Will need to look into this.(may need to thread for each token)
				if r[0]["type"] == "file_created":
					
					print "start process"
					# ISSUE 1
					new_driver(connection,r[0]["file"],token_dict[connection])
					
					print "finished process"
		time.sleep(.1) # sleeps after all tokens have been checked, then loop restarts
	return


