# slackOCRparser
Makes images posted in slack chat channels searchable. 

Notes:

center.py: is the main flask file that routes the site. the /cakes/ route will show a form where an access token can be added to the DB. Alternatively, an access token can be added using the "Add to Slack" button on the homepage, but that's a full slack authentication process takes longer. 

Right now, the main issue is getting the 'OCRparse.alt_start(lst)' call to be async. This function calls alt_start in in OCRparse with a list of tokens that it pulls from the postgresql database (this has been tested, and it works). It then goes about opening websockets for each access_token and listening for file uploads.

index(): renders the homepage of the app at (www.slackocrparse.heroku.com)

OCRparse.py-- all functions are fairly well documented
