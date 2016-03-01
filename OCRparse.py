import requests
import json

files = {'media': open('/Users/ronjon/Desktop/slackOCRparser/test1.png', 'rb')}

webhook_url= "http://www.ocrwebservice.com/restservices/processDocument?language=english&pagerange=1&gettext=true&outputformat=doc"


r = requests.post(webhook_url, auth=('ronb','0354B8E7-BEB0-4904-8B62-3CBAD37E2251'), files = files)
text = r.json()
import pdb
pdb.set_trace()