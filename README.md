# slackOCRparser
Makes images posted in slack chat channels searchable. 

Uses: python, flask, heroku, postgresql (postico has a nice GUI for viewing postgresql)

Resources: 
https://devcenter.heroku.com/articles/getting-started-with-python#introduction


Notes:

center.py: is the main flask file that routes the site. the /cakes/ route will show a form where an access token can be added to the DB. Alternatively, an access token can be added using the "Add to Slack" button on the homepage, but that's a full slack authentication process takes longer. 


index(): opens a new thread to run the (alt_start in OCRparse.py) (right now this is triggered by going to '/'). Also renders the homepage of the app at (www.slackocrparse.herokuapp.com), in a different thread. 

OCRparse.py-- all functions are fairly well documented


