import requests
import json
import httplib2
import sys
import time
import python_slackclient
from python_slackclient.slackclient import SlackClient
import shutil

#GLOBAL VARIABLE#
token = ''


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
	files = {'media': open('/Users/ronjon/Desktop/slackOCRparser/' + download_file, 'rb')}

	ocr_web_url= "http://www.ocrwebservice.com/restservices/processDocument?language=english&pagerange=1&gettext=true&outputformat=doc"

	r = requests.post(ocr_web_url, auth=('ronb','0354B8E7-BEB0-4904-8B62-3CBAD37E2251'), files = files)
	text = r.json()

	return text


def parseText(json_obj):
	lst = []
	for word in json_obj:
		lst.append(word)
	return lst

def oauthSlack(code):
	# client_id = '13657523393.23587667329'
	r = requests.get("https://slack.com/api/oauth.access", 
		data={'client_id': '13657523393.23587667329', 
		'client_secret': 'daa51f4cbf84779d2c01f8eafe59cd1f',
		'code': code,
		'redirect_uri': 
		})
	token = r.json()['access_token']

def driver(sc):

	# im_lists = sc.api_call(
	# 	"im.list"
	# )
	# im_id = im_lists["ims"][counter]['id']
	# im_lists = im_lists["ims"]

	channel_lists = sc.api_call(
        "channels.list"
    )
	channel_lists = channel_lists["channels"]

	for channel in channel_lists:
		file_list = sc.api_call("files.list", channel=channel['id'])
		for file_ in file_list["files"]:
			
			# file_download_links.append(file_["private_url_download"])
			result = slackAPI_download_file(sc, file_["url_private_download"], token)

			# parseText(result)
			comment = str(result["OCRText"])
			sc.api_call("files.comments.add", file=file_["id"], comment=comment)

def main(token):
# Command line arguments
	# token = token
	# user = sys.argv[2]

	# found at https://api.slack.com/web#authentication
	sc = SlackClient(token)

	if sc.rtm_connect():


		r = oauthSlack('13657523393.24216510419.e8a5670d4e')
		# driver(sc)
		import pdb
		pdb_set_trace()
				# parseText(result)
		print "El Fin"


	else:
		print "Connection Failed, invalid token?"

# In case i want to start usings bots...
# print sc.api_call(
# 	"chat.postMessage", channel="#general", text="How are you feeling today, sir?",
#      username='ronbot', icon_emoji=':robot_face:'
# )

# if __name__ == "__main__":
#     main()




