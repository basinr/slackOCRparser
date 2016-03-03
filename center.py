import os
import OCRparse
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/cakes/')
def cakes():
	# OCRparse.main("xoxp-13657523393-23584016902-23864788196-fed69d1b0a")
	code = request.args['code']
	return render_template('index.html')



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)