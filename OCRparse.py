import requests
import json


# Downloads file from slack channel into temp file
# RETURNS: the OCR text of the downloaded file
def slack_download_and_ocr(sc, url, token, temp_file_name):

	download_url = url
	headers = {"Authorization": "Bearer " + token}
	r = requests.get(download_url, headers=headers)
	path = temp_file_name + '.png'
	if r.status_code == 200:
		with open(path, 'wb') as f:
			f.write(r._content)

	result = OCRclientcall(path)
	return result


# Calls the OCR web api (https://ocr.space)
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
			data=payload,)

	text = r.json()

	# TODO: Take out newline characters after 5 or so
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

	print "get_access_token reply: " + json.dumps(r.json())

	a_tokens = {}

	if r.status_code == 200:
		if r.json()["ok"]:

			access_token = r.json()['access_token']
			bot_access_token = r.json()["bot"]["bot_access_token"]
			bot_user_id = r.json()["bot"]["bot_user_id"]

			a_tokens["access_token"] = access_token
			a_tokens["bot_access_token"] = bot_access_token
			a_tokens["bot_user_id"] = bot_user_id

	else:
		print "invalid code (don't reuse, expires in 10 minutes, etc.)"

	# for test purposes. will return just token if fails


	return a_tokens


def get_team_name(token):
	r = requests.get("https://slack.com/api/team.info", params={
		'token':  token
	})

	if r.status_code == 200 and r.json()["ok"]:
		team_name = r.json()["team"]["name"]
		return team_name

	print "Failed to get team_name for token: " + token
	return ""


# Downloads file, OCRs content, posts file comment
def ocr_file(sc, file_, user):
	access_token = user.access_token
	bot_access_token = user.bot_access_token

	# passes in the private url download link
	temp_file = 'temp_' + user.id
	result = slack_download_and_ocr(sc, file_["url_private_download"], token=access_token, temp_file_name=temp_file)

	# cleans up the text using parseText
	comment = result

	if not comment:
		print "No text found in uploaded file for token: " + access_token
		return False

	print "Posting comment for boat access token: " + bot_access_token

	# posts the comment in the channel
	r = requests.post("https://slack.com/api/files.comments.add", data={
		'token': bot_access_token, 
		'file': file_["id"], 
		'comment': comment})

	if r.status_code != 200:
		print "Error posting comment: " + str(r.status_code) + " " + str(r.reason)
		return False

	if not r.json()["ok"]:
		print "Error posting comment: " + json.dumps(r.json())
		return False

	return True
