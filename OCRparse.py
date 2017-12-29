"""OCR parse file."""
import json
from PIL import Image
import requests


# Downloads file from slack channel into temp file
# RETURNS: the OCR text of the downloaded file
def slack_download_and_ocr(url, token, temp_file_name):
	"""
	@type url: string

	@param url: download_url from Slack
	@type token: string
	@param token: Slack token
	@type temp_file_name: string
	@param temp_file_name: local name of file to be created
	:rtype: string of ocr'd file
	"""
	download_url = url
	headers = {"Authorization": "Bearer " + token}
	r = requests.get(download_url, headers=headers)

	# debugging purposes. attempting to identify if pdf
	print "----download_url-----: " + download_url

	is_pdf_file = False

	print "substring: " + download_url[-3:]
	if download_url[-3:] == "pdf":
		is_pdf_file = True
	#
	# print "debugging request" + r._content

	path = temp_file_name + '.png'

	# creates file if doesn't exist
	touch_file = open(path, 'a')

	if r.status_code == 200:
		with open(path, 'wb') as f:
			f.write(r._content)
	else:
		print "Error posting comment: " + str(r.status_code) + " " + str(r.reason)
		return False

	result = ocr_client_call(path, is_pdf_file)

	header = get_team_info(token)

	with open('team_info.txt', 'a') as json_file:
		entry = {'team_name': header["name"],
		         'domain': header["domain"],
		         'email_domain': header["email"],
		         'text': result
		         }
		json_file.write("{}\n".format(json.dumps(entry)))

	return result


def get_team_info(token):
	"""Get team info."""
	team_stuff = {}
	r = requests.get("https://slack.com/api/team.info", params={'token': token})
	if r.status_code == 200:
		print "debug get team info"
		print r.json()
		team_stuff["domain"] = r.json()["team"]["domain"]
		team_stuff["email"] = r.json()["team"]["email_domain"]
		team_stuff["name"] = r.json()["team"]["name"]

		print r.json()["team"]["domain"]
		print r.json()["team"]["email_domain"]
		print r.json()["team"]["name"]

	else:
		print r.status_code
		print "request for team info failed"

	return team_stuff


# RETURNS: the text of the OCR'd image

def ocr_client_call(download_file, bool_pdf):
	# OCR logic using the web client
	"""
	@type download_file: string
	@param download_file: local url of file to ocr
	@type bool_pdf: boolean
	@param bool_pdf: True if is PDF, False otherwise
	:rtype: string
	"""
	payload = dict(isOverlayRequired='False', apikey='PKMXB3310888A', language='eng')

	if not bool_pdf:
		resize_image(download_file)

	with open(download_file, 'rb') as f:
		r = requests.post('https://apipro1.ocr.space/parse/image',
			files={download_file:f}, data=payload,)

	text = r.json()
	print "First look at text which is r.json()"
	print text
	print "Then, look here: text[ParsedResults]"
	print text["ParsedResults"]

	temp_text = text["ParsedResults"][0]["ParsedText"]

	temp_text = temp_text.replace('\n', ' ')

	temp_text = temp_text.replace('\r', '')

	text = temp_text

	return text


# resize image if necessary before sending to OCR Space API
def resize_image(path):
	"""Resize image."""
	im = Image.open(path)

	print "Image size dimensions: "
	print im.size[0]
	print ", "
	print im.size[1]

	if (im.size[0] * im.size[1]) > 1000000:
		im_1 = im.size[0] * .7
		im_2 = im.size[1] * .7
		while int(im_1) * int(im_2) > 1000000:
			im_1 *= .8
			im_2 *= .8
		size = int(im_1), int(im_2)
		im.thumbnail(size, Image.ANTIALIAS)
		im.save(path)
		print "New size is {} x {}".format(im.size[0], im.size[1])
	elif im.size[0] > 2600 or im.size[1] > 2600:
		print "one dim is above 2600 --> 1000x1000"
		size = 1000, 1000
		im.resize(size, Image.ANTIALIAS)
		im.save(path)
	else:
		return


# Used with "Add to Slack" Button
# Does the second step of the oauth process, found here: https://api.slack.com/docs/oauth
# code comes from center.py's signup() function
# RETURNS: access_token to be added to db in signup()
def get_access_token(code):
	r = requests.get("https://slack.com/api/oauth.access",
	                 params={'client_id': '13657523393.23587667329',
	                         'client_secret': 'daa51f4cbf84779d2c01f8eafe59cd1f',
	                         'code': code,
	                         'redirect_uri': 'https://pixibot.co/signup/'
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
		'token': token
	})

	if r.status_code == 200 and r.json()["ok"]:
		team_name = r.json()["team"]["name"]
		return team_name

	print "Failed to get team_name for token: " + token
	return ""


def get_team_email(token):
	r = requests.get("https://slack.com/api/team.info", params={
		'token': token
	})

	if r.status_code == 200 and r.json()["ok"]:
		email = r.json()["team"]["email_domain"]
		return email

	print "Failed to get team email for token: "
	print token
	return ""


# Downloads file, OCRs content, posts file comment
def ocr_file(file_, user):
	"""
	:type user: some string

	:type file_: some string
	"""
	access_token = user.access_token
	bot_access_token = user.bot_access_token

	# passes in the private url download link
	temp_file = 'temp_' + str(user.id)
	result = slack_download_and_ocr(file_["url_private_download"],
	                                bot_access_token,
	                                temp_file)

	# cleans up the text using parseText
	comment = result

	if not comment:
		print "No text found in uploaded file for token: " + access_token
		return False

	print "Posting comment for bot access token: " + bot_access_token

	# posts the comment in the channel
	return user.post_comment(comment, file_["id"])
