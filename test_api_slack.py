"""Test Slack API endpoints."""
import requests


endpoint = "users.list"
token = "xoxb-31546818544-fuO6qY0OnAiwAfWEoxXXSpRP"
url = "https://slack.com/api/" + endpoint
params = {'token': token}

r = requests.get(url, params={'token': token})
if r.status_code == 200:
	print r.json()
else:
	print r.status_code
	print r.json()
