import requests
import json
import httplib2
import sys
import time
import python_slackclient
from python_slackclient.slackclient import SlackClient
import shutil
import re


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
	files = {'media': open(download_file, 'rb')}

	ocr_web_url= "http://www.ocrwebservice.com/restservices/processDocument?language=english&pagerange=1&gettext=true&outputformat=doc"

	r = requests.post(ocr_web_url, auth=('ronb','0354B8E7-BEB0-4904-8B62-3CBAD37E2251'), files = files)
	text = r.json()

	return text

# Used with "Add to Slack" Button
# Does the second step of the oauth process, found here: https://api.slack.com/docs/oauth
# code comes from center.py's cake() function
# RETURNS: access_token to be added to db in cakes()
def get_access_token(code):

	token = 'error'
	r = requests.get("https://slack.com/api/oauth.access", 
		params={'client_id': '13657523393.23587667329', 
		'client_secret': 'daa51f4cbf84779d2c01f8eafe59cd1f',
		'code': code,
		'redirect_uri': 'https://slackocrparse.herokuapp.com/cakes/'
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
	comment = parseText(str(result["OCRText"]))

	# posts the comment in the channel
	requests.get("https://slack.com/api/files.comments.add", params={
		'token': token, 
		'file': file_["id"], 
		'comment': comment})
			
# RETURNS: cleaned up OCR Text
def parseText(line):
	words = re.split(r"[^A-Za-z]", line.strip())
	final = []
	for word in words:
		if word:
			final.append(word)
			
	finale = ""
	unique_words = final
	for worde in unique_words:
	    finale = finale + " " + str(worde)
	return finale


# Takes in a list of all user tokens, and cycles through printing OCR outputs
# SHOULD ALWAYS BE RUNNING, IDEALLY
def alt_start(token_list):
	
	print token_list[0]
	# keeps track of token indexes for error output (see below)
	counter = 0

	# A lit of "SC" objects, using the python-slackclient library (github)
	sc_list = []
	for token in token_list:
		if token == 'error':
			print token
			print "error with token" + counter
			return False


		sc_list.append(SlackClient(token))
		print "this is the token: " + token_list[counter]
 
		# establish rtm connections with all tokens. This is a websocket that will always be open
		# error checking to make sure this is open is optimal!
		# Potential solution: have 2 websockets open for each access_token
		if not sc_list[counter].rtm_connect():
			print "error with rtm connection: " + "token: " + token_list[0]
		counter = counter + 1

	counterance = 100  # temp hack to end thread after 100 loops
	while counterance:
		counter = 0
		for connection in sc_list:
			r = connection.rtm_read()
			# if r has content inside of it
			if len(r) > 0:

				# if the event is a "file created" 
				if r[0]["type"] == "file_created":
					print "start process"
					new_driver(connection,r[0]["file"],token_list[counter])
					print "finished process"
		counter += 1
		time.sleep(1)
		counterance -= 1
	return


# Use main for testing individual functions in this file
# def main():

# # ronbasin = 'xoxp-24674298112-24672378661-24674834576-80d28c0be8'
# 	garybasin = 'xoxp-13657523393-23584016902-23864788196-fed69d1b0a'


# if __name__ == "__main__":
#     main()




