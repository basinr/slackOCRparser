import os
import OCRparse
from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.heroku import Heroku
import json
import sys
import client_mgr
import requests
import stripe

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
	bot_access_token = db.Column(db.String(120))
	bot_user_id = db.Column(db.String(120))
	processed_cnt = db.Column(db.Integer)
	proc_cnt_since_last_rollover = db.Column(db.Integer)
	subscription_type = db.Column(db.Integer)
	last_check_time = db.Column(db.Integer)
	enabled = db.Column(db.Boolean)

	def __init__(self, access_token, bot_access_token, bot_user_id, team_name):
		self.access_token = access_token
		self.team_name = team_name
		self.processed_cnt = 0
		self.proc_cnt_since_last_rollover = 0
		self.subscription_type = 0  # default, free
		self.last_check_time = 0
		self.bot_access_token = bot_access_token
		self.bot_user_id = bot_user_id
		self.enabled = True

	@staticmethod
	def add_new_user(access_token, bot_access_token, bot_user_id, team_name):
		if not db.session.query(User).filter(User.team_name == team_name).count():
			reg = User(access_token=access_token, bot_access_token=bot_access_token,
					   bot_user_id=bot_user_id, team_name=team_name)
			db.session.add(reg)
			db.session.commit()
			print "User added to database: " + team_name

	@staticmethod
	def get_users():
		# get dictionary of Users table (keys are row IDs)
		users = {}
		rows = db.session.query(User).all()
		for row in rows:
			# ID is an integer; it's the row number in the database (0,1,2,3 etc.)
			users[row.id] = row
		return users

	@staticmethod
	def delete_user(user_id):
		User.query.filter_by(id=user_id).delete()
		db.session.commit()

	def get_obj(self):
		return db.session.query(User).filter(User.id == self.id).first()

	def inc_processed_cnt(self):
		#user = self.get_obj()
		#user.processed_cnt += 1
		#user.proc_cnt_since_last_rollover += 1
		self.processed_cnt += 1
		db.session.commit()

	def update_last_check_time(self, time_secs):
		'''db.session.query(User).filter(User.id == self.id).\
			update({"last_check_time": time_secs})
		self.last_check_time = time_secs
		db.session.commit()'''
		# causing some kaka, seems to update occasionally though
		return

	def post_message(self, text, channel):
		r = requests.post("https://slack.com/api/chat.postMessage", data={
			'token': self.bot_access_token,
			'username': 'pixibot',
			'channel': channel,
			'text': text})

		if not User.error_check(r):
			return False

		return True

	def post_comment(self, text, file_id):
		r = requests.post("https://slack.com/api/files.comments.add", data={
			'token': self.bot_access_token,
			'file': file_id,
			'comment': text})

		if not User.error_check(r):
			return False

		return True

	@staticmethod
	def error_check(response):
		if response.status_code != 200:
			print "Error making slack call: " + str(response.status_code) + " " + str(response.reason)
			return False

		if not response.json()["ok"]:
			print "Error making slack call: " + json.dumps(response.json())
			return False

		return True

	def account_info_str(self):
		user_obj = self.get_obj()
		txt = "\n Team Name = " + user_obj.team_name
		txt += "\n Subscription Type = " + str(user_obj.subscription_type)
		txt += "\n Total Processed = " + str(user_obj.processed_cnt)
		txt += "\n Processed This Month = " + str(user_obj.proc_cnt_since_last_rollover)
		txt += "\n OCR Enabled  =  " + str(user_obj.enabled)
		txt += "\n Manage Subscription = <link goes here>"
		return txt

	def to_json(self):
		return json.dumps(self, default=lambda o: o.__dict__,  sort_keys=True, indent=4)

	def __repr__(self):
		"<user(access_token='%s')>" % self.access_token

# add to global context for Jinja
app.add_template_global(User, 'User')


@app.context_processor
def utility_processor():
	def is_slack_thread_active(user_key):
		return slack_thread_mgr.is_service_active(user_key)

	return dict(is_slack_thread_active=is_slack_thread_active)


@app.route('/')
def index():
	return render_template('index_old.html')


# For new users, use this route. This does oauth, and saves the access_token and team_name to the DB
@app.route('/signup/')
def signup():

	if len(request.args) == 2:

		# Obtains code from initial oauth request. Only need to do this once per user
		code = request.args['code']

		# access_token that needs to be stored for each user
		token_dict = OCRparse.get_access_token(code)

		access_token = token_dict["access_token"]
		bot_access_token = token_dict["bot_access_token"]
		bot_user_id = token_dict["bot_user_id"]

		print "access token: " + access_token
		print "bot access token: " + bot_access_token
		print "bot user id: " + bot_user_id

		# get team name
		team_name = OCRparse.get_team_name(bot_access_token)

		print "team: " + team_name

		# add user to db if does not exist
		User.add_new_user(access_token, bot_access_token, bot_user_id, team_name)
		return render_template('success.html')

	return render_template('index_old.html')

@app.route('/charge')
def charge():
	    # Amount in cents
    amount = 900

	stripe.api_key = "sk_test_h0YstkTQo5EoOYfdVJlZy6FK"

	token = request.POST['stripeToken']

	customer = stripe.Customer.create(
    source=token,
    description="Example customer")

    # may want to save customer id, credentials in db for future use

    print "Stripe token: "
    print token

    print "Customer id: "
    print customer.id

	try:
		charge = stripe.Charge.create(
			email=request.POST['stripeEmail'],
			source=token,
			plan='PixiBot')


	except stripe.error.CardError, e:
		# Card has been declined
		print "Credit Card has been declined"
		return False

    # TODO: Change to new payment success page
    return render_template('success.html')


# Simple admin panel, create get request with pw=growingballer89!
@app.route('/admin/')
def cpanel():
	try:
		pw = request.args.get('pw')

		if pw != 'growingballer89!':
			return index()

		cmd = request.args.get('cmd')

		if cmd == "start_loop":
			slack_thread_mgr.start_all()
		elif cmd == "stop_loop":
			slack_thread_mgr.stop_all()
		# elif cmd == "rebuild_tables":  # currently not working, 30 sec timeout. should be quicker, though...
		# 	slack_thread_mgr.stop_all()
		# 	rebuild_tables()
		elif cmd == "delete_user":
			print "admin deleting user " + request.args.get('id')
			user_id = request.args.get('id')
			User.delete_user(user_id)
			slack_thread_mgr.kill_user_thread(int(user_id))

		users = User.get_users()
		return render_template('cpanel.html', users=users)
	except:
		print "Unexpected error in cpanel():", sys.exc_info()[0]
		raise


def rebuild_tables():
	# borked
	print "admin rebuilding tables..."
	# hack from http://stackoverflow.com/questions/24289808/drop-all-freezes-in-flask-with-sqlalchemy
	db.session.commit()

	db.reflect()
	db.drop_all()
	print "creating.."
	db.create_all()
	print "rebuild_tables() completed"
	slack_thread_mgr.start_all()

if __name__ == "__main__":
	if slack_thread_mgr is None:
		slack_thread_mgr = client_mgr.slackThread.SlackThreadManager()

	port = int(os.environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port, threaded=True, debug=True, use_reloader=False)
