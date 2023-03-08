import os
import json
import time

from flask import Flask, render_template, make_response, request
from flask_basicauth import BasicAuth

from lib.ai import ai

import config

from lib.database import featurebase_tables_schema

# slothbot services app
app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = config.basic_auth_username
app.config['BASIC_AUTH_PASSWORD'] = config.basic_auth_password

# add basic auth to endpoints
basic_auth = BasicAuth(app)

@app.route('/chat', methods=['POST'])
@basic_auth.required
def chat():
	document = request.json
	document = ai("chat", document)
	return make_response(document)

@app.route('/help', methods=['POST'])
@basic_auth.required
def help():
	document = request.json
	document = ai("help", document)
	return make_response(document)

@app.route('/dream', methods=['POST'])
@basic_auth.required
def dream():
	document = request.json
	ai("dream", document)
	return make_response(document)

@app.route('/support', methods=['POST'])
@basic_auth.required
def support():
	document = request.json
	ai("support", document)
	return make_response(document)

@app.route('/query', methods=['POST'])
@basic_auth.required
def query():
	document = request.json
	return make_response(document)
	
@app.route('/status', methods=['POST'])
@basic_auth.required
def status():
	document = request.json
	return make_response(document)

@app.route('/graph', methods=['POST'])
@basic_auth.required
def graph():
	document = request.json
	document['answer'] = "I would generate a graph from SQL."
	return make_response(document)

@app.route('/log', methods=['POST'])
@basic_auth.required
def log():
	document = request.json
	return make_response(document)

@app.route('/feedback', methods=['POST'])
@basic_auth.required
def feedback():
	document = request.json
	return make_response(document)

if __name__ == '__main__':
	# This is used when running locally.
	# app.run(host='127.0.0.1', port=8000, debug=True)
	app.run(host='localhost', port=8000, debug=True)
	dev = True