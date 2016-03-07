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
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, email):
        self.email = email

    def __repr__(self):
        return '<E-mail %r>' % self.email

# Stolen from a tutorial: http://blog.sahildiwan.com/posts/flask-and-postgresql-app-deployed-on-heroku/
@app.route('/prereg', methods=['POST'])
def prereg():
    email = None
    if request.method == 'POST':
        email = request.form['email']
        # Check that email does not already exist (not a great query, but works)
        if not db.session.query(User).filter(User.email == email).count():
            reg = User(email)
            db.session.add(reg)
            db.session.commit()
            return render_template('success.html')
    return render_template('index.html')

@app.route('/')
def index():
    return render_template('index.html')


# The 
@app.route('/cakes/')
def cakes():
	if len(request.args) == 2:
		# Obtains code from initial oauth request. Only need to do this once per user
		code = request.args['code']

		# access_token that needs to be stored for each user
		token = OCRparse.get_access_token(code)

		# print OCRparse.start(token)
	return render_template('success.html')


# @app.route('/cakes/booty/')
# def cakes_booty():
# 	# OCRparse.main("xoxp-13657523393-23584016902-23864788196-fed69d1b0a")
# 	return render_template('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)