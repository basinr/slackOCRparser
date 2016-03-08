import os
import OCRparse
from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.heroku import Heroku

app = Flask(__name__)

# Use only when deploying locally, i think
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/ronjon'
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
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

# Stolen from a tutorial: http://blog.sahildiwan.com/posts/flask-and-postgresql-app-deployed-on-heroku/
# @app.route('/prereg', methods=['POST'])
# def prereg():
#     token = None
#     if request.method == 'POST':
#         token = request.form['token']
#         # Check that email does not already exist (not a great query, but works)
#         if not db.session.query(User).filter(User.access_token == token).count():
#             reg = User(token)
#             db.session.add(reg)
#             db.session.commit()
#             return render_template('success.html')
#     return render_template('index.html')

# takes the access_tokens from the database, and inserts them into a list that is then returned
def db_to_list():
	lst = []
	rows = db.session.query(User).all()
	for row in rows:
		lst.append(row.access_token)
	return lst

@app.route('/')
def index():
	return render_template('index.html')

# @app.route('/davay')
# def begin():
# 	print OCRparse.alt_start(db_to_list())
# 	return render_template('index.html')

# For new users, use this route. This does oauth, and saves the access_token to the DB
@app.route('/cakes/')
def cakes():
	if len(request.args) == 2:
		# Obtains code from initial oauth request. Only need to do this once per user
		code = request.args['code']

		# access_token that needs to be stored for each user
		token = OCRparse.get_access_token(code)

		# add token to db if does not exist
		# if not db.session.query(User).filter(User.access_token == token).count():
		# 	reg = User(access_token)
		# 	db.session.add(reg)
		# 	db.session.commit()


		print OCRparse.start(token)
	print OCRparse.start('xoxp-24674298112-24672378661-24674834576-80d28c0be8')
	return render_template('success.html')


# @app.route('/cakes/booty/')
# def cakes_booty():
# 	# OCRparse.main("xoxp-13657523393-23584016902-23864788196-fed69d1b0a")
# 	return render_template('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)