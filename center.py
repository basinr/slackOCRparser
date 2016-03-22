import os
import OCRparse
from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.heroku import Heroku
import json
import sys
import client_mgr

app = Flask(__name__)
heroku = Heroku(app)
db = SQLAlchemy(app)
slack_thread_mgr = None


# Create our database model
# Stolen from a tutorial: http://blog.sahildiwan.com/posts/flask-and-postgresql-app-deployed-on-heroku/
class User(db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	access_token = db.Column(db.String(120), unique=True)
	team_name = db.Column(db.String(120), unique=True)
	processed_cnt = db.Column(db.Integer)
	subscription_type = db.Column(db.Integer)
	last_check_time = db.Column(db.Integer)

	def __init__(self, access_token, team_name):
		self.access_token = access_token
		self.team_name = team_name
		self.processed_cnt = 0
		self.subscription_type = 0 # default, free
		self.last_check_time = 0

	def inc_processed_cnt(self):
		db.session.query(User).filter(User.id == self.id).\
			update({"processed_cnt": (User.processed_cnt + 1)})
		self.processed_cnt += 1
		db.session.commit()

	def to_json(self):
		return json.dumps(self, default=lambda o: o.__dict__,  sort_keys=True, indent=4)

	def __repr__(self):
		"<user(access_token='%s')>" % self.access_token

# add to global context for Jinja
app.add_template_global(User, 'User')


# get dictionary of Users table (keys are row IDs)
def get_users():
	users = {}
	rows = db.session.query(User).all()
	for row in rows:
		# ID is an integer; it's the row number in the database (0,1,2,3 etc.)
		users[row.id] = row
	return users


@app.context_processor
def utility_processor():
	def is_slack_thread_active(user_key):
		return slack_thread_mgr.is_service_active(user_key)

	return dict(is_slack_thread_active=is_slack_thread_active)


@app.route('/')
def index():
	return render_template('index.html')


@app.route('/go/')
def start_scripts():
	lst = []

	# start testing purposes only #

	token1 = 'xoxp-13657523393-23584016902-23864788196-fed69d1b0a' #(garybasin) 
	token2 = 'xoxp-24674298112-24672378661-24674834576-80d28c0be8'  #(ronbasin) 
	
	lst.append(token1)
	lst.append(token2)

	# end testing purposes only #

	# grabs tokens from db (only in heroku server)
	# lst = get_access_tokens()

	# t1 = threading.Thread(target=OCRparse.alt_start, args=(lst,))
	# t1.start()

	return render_template('index.html')


# For new users, use this route. This does oauth, and saves the access_token and team_name to the DB
@app.route('/signup/')
def signup():

	if len(request.args) == 2:

		# Obtains code from initial oauth request. Only need to do this once per user
		code = request.args['code']

		# access_token that needs to be stored for each user
		token = OCRparse.get_access_token(code)

		print "token: " + token

		# get team name
		team_name = OCRparse.get_team_name(token)

		print "team: " + team_name

		# add user to db if does not exist
		if not db.session.query(User).filter(User.team_name == team_name).count():
			reg = User(access_token=token, team_name=team_name)
			db.session.add(reg)
			db.session.commit()
			print "User added to database: " + team_name
		return render_template('success.html')
			
	return render_template('index.html')


# Simple admin panel, create get request with pw=growingballer89!
@app.route('/admin/')
def cpanel():
	try:
		pw = request.args.get('pw')

		# local testing 
		# pw = request.args.getlist('pw')[0]

		if pw != 'growingballer89!':
			return index()

		cmd = request.args.get('cmd')

		if cmd == "start_loop":
			slack_thread_mgr.start_all()
		elif cmd == "stop_loop":
			slack_thread_mgr.stop_all()

		users = get_users()
		return render_template('cpanel.html', users=users)
	except:
		print "Unexpected error in cpanel():", sys.exc_info()[0]
		raise

if __name__ == "__main__":
	if slack_thread_mgr is None:
		slack_thread_mgr = client_mgr.slackThread.SlackThreadManager()

	port = int(os.environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port, threaded=True, debug=True, use_reloader=False)
