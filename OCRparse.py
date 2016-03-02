import requests
import json



# # OCR logic
# files = {'media': open('/Users/ronjon/Desktop/slackOCRparser/test1.png', 'rb')}

# webhook_url= "http://www.ocrwebservice.com/restservices/processDocument?language=english&pagerange=1&gettext=true&outputformat=doc"


# # r = requests.post(webhook_url, auth=('ronb','0354B8E7-BEB0-4904-8B62-3CBAD37E2251'), files = files)
# text = r.json()

import sys
import time
import python_slackclient
from python_slackclient.slackclient import SlackClient
import shutil

def main():
# Command line arguments
	token = "xoxp-13657523393-23584016902-23864788196-fed69d1b0a"
	# user = sys.argv[2]

	# found at https://api.slack.com/web#authentication
	sc = SlackClient(token)

	if sc.rtm_connect():

		im_lists = sc.api_call(
			"im.list"
		)
		# channel_lists = sc.api_call(
	 #        "channels.list"
	 #    )

		im_lists = im_lists["ims"]
		# channel_lists = channel_lists["channels"]

		# # im_lists = im_lists["ims"][counter]['id']
		# # channel_lists = channel_lists["channels"]
		# # [counter]['id']



		# for key in channel_lists:
		# 	file_lists =  sc.api_call("files.list", channel=key['id'])

		webhook_url = "https://files.slack.com/files-pri/T0DKBFDBK-F0PQM2JFN/download/pasted_image_at_2016_03_01_06_44_pm.png"
		headers = {"Authorization" : "bearer " +  token}
		r = requests.get(webhook_url, headers=headers)
		print r

		# import pdb
		# pdb.set_trace()
		# if r.status_code == 200:
		#     with open('test1.png', 'wb') as f:
		#         for chunk in r:
		#             f.write(chunk)
		# if r.status_code == 200:
		#     with open('test1.png', 'wb') as f:
		#         r.raw.decode_content = True
		#         shutil.copyfileobj(r.raw, f)

		# channel_lists = sc.api_call(
		#     "channels.list"
		# )


		# channel_convs = sc.api_call(
		#     "channels.history", channel="C08516EL8")

	# with open(path, 'wb') as f:
	#         r.raw.decode_content = True
	#         shutil.copyfileobj(r.raw, f)



	else:
		print "Connection Failed, invalid token?"

# In case i want to start usings bots...
# print sc.api_call(
# 	"chat.postMessage", channel="#general", text="How are you feeling today, sir?",
#      username='ronbot', icon_emoji=':robot_face:'
# )


if __name__ == "__main__":
    main()





