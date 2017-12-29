import os
import OCRparse
from flask import Flask, render_template, request, redirect
# from flask_mail import Mail
# from flask_mail import Message
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.heroku import Heroku
import json
import sys
import client_mgr
import requests
import stripe
import email_client

app = Flask(__name__)
heroku = Heroku(app)
db = SQLAlchemy(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/mylocaldb'
slack_thread_mgr = None

# Create our database model
# tutorial: http://blog.sahildiwan.com/posts/flask-and-postgresql-app-deployed-on-heroku/
class User(db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	access_token = db.Column(db.String(120), unique=True)
	team_name = db.Column(db.String(120), unique=True)
	bot_access_token = db.Column(db.String(120))
	bot_user_id = db.Column(db.String(120))
	stripe_customer_id = db.Column(db.String(120))
	stripe_customer_email = db.Column(db.String(120))
	processed_cnt = db.Column(db.Integer)
	proc_cnt_since_last_rollover = db.Column(db.Integer)
	subscription_type = db.Column(db.Integer)
	last_check_time = db.Column(db.Integer)
	enabled = db.Column(db.Boolean)
	# user_reg_time = db.Column(db.Integer)

	def __init__(self, access_token, bot_access_token, bot_user_id, team_name):
		self.access_token = access_token
		self.team_name = team_name
		self.processed_cnt = 0
		self.proc_cnt_since_last_rollover = 0
		self.subscription_type = 0  # default, free
		self.last_check_time = 0
		self.bot_access_token = bot_access_token
		self.bot_user_id = bot_user_id
		self.stripe_customer_id = ""
		self.stripe_customer_email = ""
		self.enabled = True

	@staticmethod
	def add_new_user(access_token, bot_access_token, bot_user_id, team_name):
		if not db.session.query(User).filter(User.team_name == team_name).count():
			reg = User(access_token=access_token, bot_access_token=bot_access_token,
						bot_user_id=bot_user_id, team_name=team_name)
			db.session.add(reg)
			db.session.commit()
			reg.onboarding_message()
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

	def is_enabled(self):
		return self.get_obj().enabled

	def set_enabled(self, enabled):
		user = self.get_obj()
		user.enabled = enabled
		db.session.commit()

	def get_usage_relative_to_limit(self):
		user = self.get_obj()
		return user.proc_cnt_since_last_rollover - User.get_usage_limit_for_sub_type(user.subscription_type)

	def inc_processed_cnt(self):
		user = self.get_obj()
		user.processed_cnt += 1
		user.proc_cnt_since_last_rollover += 1
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

	def generate_subscription_url(self):
		user = self.get_obj()
		url = "\n Visit our pricing page through this url to subscribe: "
		url += "https://pixibot.co/?teamname="
		url += str(user.team_name)
		url += "#pricing"
		return url

	def onboarding_message(self):
		user = self.get_obj()
		r = requests.get("https://slack.com/api/auth.test",
                  		params={'token': user.access_token})
		user_id = r.json()["user_id"]
		print(r.json())
		print("LEVEL 1")
		try:
			r = requests.get("https://slack.com/api/im.open",
	                  params={'token': user.bot_access_token,
	                          'user': user_id,
	                          'return_im': True})
			resp = r.json()
			print(resp)
			print("LEVEL 2")
			if resp["ok"]:
				channel = resp["channel"]["id"]
				text = client_mgr.bot.about()
				print(text)
				print("LEVEL 3")
				self.post_message(text, channel)
				print("LEVEL 4")
			return
		except:
			print "Unexpected error in onboarding..."
			raise

	@staticmethod
	def error_check(response):
		if response.status_code != 200:
			print "Error making slack call: " + str(response.status_code) + " " + str(response.reason)
			return False

		if not response.json()["ok"]:
			print "Error making slack call: " + json.dumps(response.json())
			return False

		return True

	@staticmethod
	def get_usage_limit_for_sub_type(sub_type):
		if sub_type == 0:
			return 100
		else:
			return 999999999

	def account_info_str(self):
		user_obj = self.get_obj()
		txt = "\n Team Name = " + user_obj.team_name
		txt += "\n Subscription Type = " + str(user_obj.subscription_type)
		txt += "\n Total Processed = " + str(user_obj.processed_cnt)
		txt += "\n Processed This Month = " + str(user_obj.proc_cnt_since_last_rollover)
		txt += "\n OCR Enabled  =  " + str(user_obj.enabled)
		txt += "\n To Manage Subscription, contact support@pixibot.co"
		return txt

	def to_json(self):
		return json.dumps(self, default=lambda o: o.__dict__,  sort_keys=True, indent=4)

	def __repr__(self):
		"<user(access_token='%s')>" % self.access_token

# add to global context for Jinja
app.add_template_global(User, 'User')


class Analytic(db.Model):
	"""Table used for bot analytics."""

	__tablename__ = "analytics"
	id = db.Column(db.Integer, primary_key=True)
	team_name = db.Column(db.String(120), unique=True)
	team_id = db.Column(db.String(120), unique=True)
	user_id = db.Column(db.String(120)),
	user_row = db.Column(db.Integer)

	def __init__(self, teamname, team_id, user_id, user_row):
		"""Init baby."""
		self.team_name = teamname
		self.team_id = team_id
		self.user_id = user_id
		self.user_row = user_row


	@staticmethod
	def add_new_user(teamname, team_id, user_id, user_row):
		"""Add new team when registered."""
		reg = Analytic(teamname=teamname, team_id=team_id,
						user_id=user_id, user_row=user_row)
		db.session.add(reg)
		db.session.commit()
		print "Team added to analytics table:" + teamname

	@staticmethod
	def get_analytics():
		"""Get all entries in DB."""
		# get dictionary of Users table (keys are row IDs)
		teams = {}
		rows = db.session.query(Analytic).all()
		for row in rows:
			# ID is an integer; it's the row number in the database (0,1,2,3 etc.)
			teams[row.id] = row
		return teams

# add to global context for Jinja
app.add_template_global(Analytic, 'Analytic')


@app.context_processor
def utility_processor():
	def is_slack_thread_active(user_key):
		return slack_thread_mgr.is_service_active(user_key)

	return dict(is_slack_thread_active=is_slack_thread_active)


@app.route('/')
def index():
	print "hit homepage!"
	team_name = ""
	ref_r = ""
	if len(request.args):
		if "teamname" in request.args:
			team_name = request.args['teamname']
		if "ref" in request.args:
			print request.args["ref"]
	return render_template('index_old.html', team=team_name, ref=ref_r)


@app.route('/contact_form', methods=['POST'])
def contact_form():

	data = json.loads(request.data)
	message = "name: " + data["name"] + "\nemail: " + data["email"] + "\nmessage:\n\n" + data["message"]
	email = email_client.EmailClient("basinr@gmail.com")
	email.server_connect("contact form outreach", message)
	return "200"

# This is the first step in on-boarding. No subscription yet.
# For new users, use this route. This does oauth, and saves the access_token and team_name to the DB


@app.route('/signup/')
def signup():

	if len(request.args) == 2:

		# Obtains code from initial oauth request. Only need to do this once per user
		code = request.args['code']

		# print code

		# access_token that needs to be stored for each user
		token_dict = OCRparse.get_access_token(code)

		# print token_dict

		access_token = token_dict["access_token"]
		bot_access_token = token_dict["bot_access_token"]
		bot_user_id = token_dict["bot_user_id"]

		# print "access token: " + access_token
		# print "bot access token: " + bot_access_token
		# print "bot user id: " + bot_user_id

		# get team name
		team_name = OCRparse.get_team_name(bot_access_token)
		# email = OCRparse.get_team_name(bot_access_token)

		message = "New Application Added: " \
			"Team name: " + team_name

		email = email_client.EmailClient("support@pixibot.co")
		email.server_connect("Pixibot: New Application Added", message)

		# add user to db if does not exist
		User.add_new_user(access_token, bot_access_token, bot_user_id, team_name)

		# Add to Analytics Table
		# auth.test to get info
		team_dict = {}
		r = requests.get("https://slack.com/api/auth.test",
							params={'token': bot_access_token})
		if r.status_code == 200:
			r = r.json()
			team_dict['teamname'] = r['team']
			team_dict['team_id'] = r['team_id']
			team_dict['user_id'] = r['user_id']
			team_dict['user_row'] = len(User.get_users())

			# add to analytics DB
			Analytic.add_new_user(team_dict['teamname'], team_dict['team_id'],
								  team_dict['user_id'], team_dict['user_row'])
		else:
			print r.status_code
			print 'Error in adding to analytics db, request for auth.test failed'

		return render_template('success.html')

	return render_template('success.html')


@app.route('/privacy')
def privacy():
	return render_template('privacy.html')


@app.route('/new_user', methods=["POST"])
def new_user():
	if request.method == "POST":
		email = request.form['email']
		team = request.form['team']
		message = "Team Name: " + team + "\nEmail: " + email
		email = email_client.EmailClient("support@pixibot.co")
		email.server_connect("Pixibot: User info inserted...", message)
		return redirect("https://slack.com/oauth/authorize?client_id=13657523393.23587667329&scope=bot")
	else:
		abort(404)


@app.route('/plan_registration', methods=['POST'])
def plan_registration():

	# sk_live_68U3GTILIBijBYW3eF6phodO
	stripe.api_key = "sk_live_68U3GTILIBijBYW3eF6phodO"

	data = json.loads(request.data)

	token = data['token_id']
	_email = data['email']

	team_name = data['team_name']

	customer = stripe.Customer.create(
		source=token,
		description=team_name,
		email=_email,
		plan='pixibot'
	)

	# should only return one user object
	users = db.session.query(User).filter(User.team_name == team_name)

	# save stripe info with associated team & user
	for user in users:
		user.stripe_customer_id = customer.id
		user.stripe_customer_email = _email
		user.subscription_type = 1
		db.session.commit()

	user_msg = "Hi from the Pixibot Team!\n Thank you for subscribing." \
		"Enjoy the product, and if you have any questions at all, " \
		"Please reach out to us at support@pixibot.co.\nSincerely, " \
		"The Pixibot Team"

	record_msg = "Email: " + _email + \
		"Team Name: " + team_name

	email_usr = email_client.EmailClient("basinr@gmail.com")
	email_record = email_client.EmailClient("support@pixibot.co")

	email_usr.server_connect("Successfully Subscribed to Pixibot!", user_msg)
	email_record.server_connect("Pixibot: New Subscription", record_msg)

	return render_template('index_old.html')


# Simple admin panel, create get request with pw=growingballer89!

@app.route('/ronbasin95/')
def cpanel():
	try:
		pw = request.args.get('pw')

		if pw != 'getoutofhereplease':
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


@app.route('/research/')
def research_page():
	try:
		pw = request.args.get('pw')

		if pw != 'growingballer89!':
			return index()

		team_info = {}
		domain_list = {}
		var = 0
		with open('team_info.txt', "r") as json_file:
			for line in json_file:
				data = json.loads(line)
				if "team_name" in data:
					if data["team_name"] not in domain_list:
						domain_list[data["team_name"]] = {'name': data["team_name"],
						                            'email': data["email_domain"],
						                            'domain': data["domain"]}
					team_info[var] = data
				var += 1

		return render_template('research.html', team_info=team_info, domains=domain_list)
	except:
		print "Unexpected error in research():", sys.exc_info()[0]
		raise


def rebuild_tables():
	# borked
	print "admin rebuilding tables..."
	# hack from http://stackoverflow.com/questions/24289808/drop-all-freezes-in-flask-with-sqlalchemy
	db.session.commit()

	db.reflect()
	db.drop_all()
	print "creating..."
	db.create_all()
	print "rebuild_tables() completed"
	slack_thread_mgr.start_all()

if __name__ == "__main__":
	if slack_thread_mgr is None:
		slack_thread_mgr = client_mgr.slackThread.SlackThreadManager()

	port = int(os.environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port, threaded=True, debug=True, use_reloader=False)
