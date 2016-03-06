import os
import OCRparse
from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.heroku import Heroku

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/ronjon'
db = SQLAlchemy(app)


# Create our database model
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, email):
        self.email = email

    def __repr__(self):
        return '<E-mail %r>' % self.email


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


@app.route('/cakes/')
def cakes():
	# OCRparse.main("xoxp-13657523393-23584016902-23864788196-fed69d1b0a")

	if len(request.args) == 2:
		code = request.args['code']

		# print code
		token = OCRparse.get_access_token(code)
		print token
		print "#########################"

	# 	print "#######################################error"
	# token: 'xoxp-13657523393-23584016902-24270415890-381512abb5'
		# print token
		# print OCRparse.start(token)
	return render_template('success.html')
	# OCRparse.start('xoxp-13657523393-23584016902-24270415890-381512abb5')
	# 'xoxp-13657523393-23584016902-24270415890-381512abb5' + "####################################"
	# return render_template('index.html')

# @app.route('/cakes/booty/')
# def cakes_booty():
# 	# OCRparse.main("xoxp-13657523393-23584016902-23864788196-fed69d1b0a")
# 	return render_template('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)