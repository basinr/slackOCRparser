import requests
import json
import httplib2
import sys
import time
import python_slackclient
from python_slackclient.slackclient import SlackClient
import shutil
import re

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

def OCRclientcall(download_file):

	# OCR logic using the web client
	files = {'media': open(download_file, 'rb')}

	ocr_web_url= "http://www.ocrwebservice.com/restservices/processDocument?language=english&pagerange=1&gettext=true&outputformat=doc"

	r = requests.post(ocr_web_url, auth=('ronb','0354B8E7-BEB0-4904-8B62-3CBAD37E2251'), files = files)
	text = r.json()

	return text

def get_access_token(code):

	token = '###################'
	r = requests.get("https://slack.com/api/oauth.access", 
		params={'client_id': '13657523393.23587667329', 
		'client_secret': 'daa51f4cbf84779d2c01f8eafe59cd1f',
		'code': code,
		'redirect_uri': 'https://slackocrparse.herokuapp.com/cakes/booty/'
		})
	
	if r.status_code == 200:
		if (r.json()["ok"]):
			token = r.json()['access_token']
	else:
		print "invalid code (don't reuse, expires in 10 minutes, etc.)"

	return token

def driver(sc, token):

	# im_lists = sc.api_call(
	# 	"im.list"
	# )
	# im_id = im_lists["ims"][counter]['id']
	# im_lists = im_lists["ims"]
	# channel_lists = sc.api_call(
 #        "channels.list"
 #    )
	import datetime
	yesterday = datetime.date.today() - datetime.timedelta(1)
	unix_time= yesterday.strftime("%s")
	channel_lists = requests.get("https://slack.com/api/channels.list", 
		params={'token': token})
	channel_lists = channel_lists.json()
	channel_lists = channel_lists["channels"]

	unix_time = int(unix_time)

	for channel in channel_lists:
		file_list = requests.get("https://slack.com/api/files.list", 
			params={
			'token': token,
			'channel': channel['id']})
		file_list = file_list.json()
		for file_ in file_list["files"]:


			if file_["timestamp"] > unix_time:
			
			# file_download_links.append(file_["private_url_download"])
				result = slackAPI_download_file(sc, file_["url_private_download"], token)

				# parseText(result)
				comment = parseText(str(result["OCRText"]))

				requests.get("https://slack.com/api/files.comments.add", params={
					'token': token, 
					'file': file_["id"], 
					'comment': comment})
			
	return True



# smarter way to parse text from image
def parseText(line):
	words = re.split(r"[^A-Za-z]", line.strip())
	final = []
	for word in words:
		if word:
			final.append(word)
			
	finale = ""
	unique_words = set(final)
	for worde in unique_words:
	    finale = finale + ", " + str(worde)
	return finale

def start(token):

	if (token == " "):
		print "error with token"
		return False

	sc = SlackClient(token)

	if sc.rtm_connect():
		# time.sleep(200)
		# counter = 0
				# parseText(result)
		driver(sc, token)
		print "successful driver ent/ex"
			# counter += 1
			#evey 10 minutes
			# time.sleep(600)

		return True

	else:
		print "##################" + token + "$$$$$$$$$$$$$$$$$$"
		print "Connection Failed, invalid token?"
		return False


def main():
	start('xoxp-13657523393-23584016902-24270415890-381512abb5')

	# Command line arguments
	# token = token
	# user = sys.argv[2]

	# found at https://api.slack.com/web#authentication
	# oauthSlack()
	# r = requests.get("https://slack.com/oauth/authorize", 
	# 	params={'client_id': '13657523393.23587667329', 
	# 	'scope': 'incoming-webhook',
	# 	'redirect_uri': 'https://slackocrparse.herokuapp.com/cakes/'
	# 	})


	# token = get_access_token('13657523393.24268060881.bee654eb47')
	# import pdb
	# pdb.set_trace()
	# start(token)
	# 	# driver(sc)
	# print r


# In case i want to start usings bots...
# print sc.api_call(
# 	"chat.postMessage", channel="#general", text="How are you feeling today, sir?",
#      username='ronbot', icon_emoji=':robot_face:'
# )

if __name__ == "__main__":
    main()




