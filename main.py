import os
import json

from flask import Flask, render_template
from flask_basicauth import BasicAuth

import config

# slothbot services app
app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = config.basic_auth_username
app.config['BASIC_AUTH_PASSWORD'] = config.basic_auth_password

# add basic auth to endpoints
basic_auth = BasicAuth(app)

@app.route('/chat')
@basic_auth.required
def chat():
	import openai


	print(completion)
	return completion
	
@app.route('/status')

@app.route('/secret')
@basic_auth.required
def secret_view():
    return render_template('secret.html')

if __name__ == '__main__':
	# This is used when running locally.
	# app.run(host='127.0.0.1', port=8000, debug=True)
	app.run(host='localhost', port=8000, debug=True)
	dev = True