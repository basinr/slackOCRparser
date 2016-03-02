from slacker import Slacker
import requests 
import json

token = 'xoxp-13657523393-23584016902-23864788196-fed69d1b0a'

slack = Slacker(token)

webhook_url = "https://slack.com/oauth/authorize"
data={
     'client_id': 13657523393.23587667329,
     'scope': 'files:read'
 }

headers = {"Authorization" : "Bearer " + token}
r = requests.get("https://slack.com/oauth/authorize", 
	params = {
     'client_id': 13657523393.23587667329,
     'scope': 'files:read'
     # 'token': 'xoxp-13657523393-23584016902-23864788196-fed69d1b0a'
 })
print r
import pdb
pdb.set_trace()