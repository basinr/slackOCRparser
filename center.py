import os
import OCRparse
from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.heroku import Heroku
import threading
import json

app = Flask(__name__)
heroku = Heroku(app)
db = SQLAlchemy(app)


# Create our database model
# Stolen from a tutorial: http://blog.sahildiwan.com/posts/flask-and-postgresql-app-deployed-on-heroku/
class User(db.Model):
    __tablename__ = "tokens"
    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String(120), unique=True)

    def __init__(self, access_token):
        self.access_token = access_token

    def __repr__(self):
        return '<access_token %r>' % self.access_token


def get_users():
	return db.session.query(User).all()

# takes the access_tokens from the database, and inserts them into a list that is then returned
def get_access_tokens():
	lst = []
	rows = db.session.query(User).all()
	for row in rows:
		lst.append(row.access_token)
	return lst

@app.route('/')
def index():

	lst = []

	# start testing purposes only #

	# token1 = 'xoxp-13657523393-23584016902-23864788196-fed69d1b0a' #(garybasin) 
	# token2 = 'xoxp-24674298112-24672378661-24674834576-80d28c0be8'  #(ronbasin) 
	
	# lst.append(token)
	# lst.append(token2)

	# end testing purposes only #

	# grabs tokens from db (only in heroku server)
	lst = get_access_tokens()

	t1 = threading.Thread(target=OCRparse.alt_start, args=(lst,))
	t1.start()
	
	return render_template('index.html')


# For new users, use this route. This does oauth, and saves the access_token to the DB
@app.route('/signup/')
def signup():

	if len(request.args) == 2:

		# Obtains code from initial oauth request. Only need to do this once per user
		code = request.args['code']

		# access_token that needs to be stored for each user
		token = OCRparse.get_access_token(code)

		# add token to db if does not exist
		if not db.session.query(User).filter(User.access_token == token).count():
			reg = User(token)
			db.session.add(reg)
			db.session.commit()
			print "token added to database"
			
	return render_template('success.html')

# Simple admin panel, create get request with pw=growingballer89!
@app.route('/admin/')
def cpanel():
	pw = request.args.get('pw')

	if pw != 'growingballer89!':
		return index()

	users = get_users()
	print json.dumps(users)
	return render_template('cpanel.html', users=get_users())

# @app.route('/cakes/booty/')
# def cakes_booty():
# 	# OCRparse.main("xoxp-13657523393-23584016902-23864788196-fed69d1b0a")
# 	return render_template('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)