import os
import sys
import datetime
import random
import openai

import traceback

from string import Template

import config

# AI model call by method name
models = {}
model = lambda f: models.setdefault(f.__name__, f)

def ai(model_name="none", document={}):
	# get the user's API token	
	openai_token = config.openai_token

	if not openai_token:
		# rewrite to match document flow
		document['error'] = "model %s errors with no token." % (model_name)
		document['explain'] = "I encountered an error talking with OpenAI."
		document.pop('template_file', None)
		return document
	else:
		# set token for model to use
		document['openai_token'] = openai_token

	# call the model
	try:
		document = models[model_name](document)
		return document

	except Exception as ex:
		if config.dev == "True":
			print(traceback.format_exc())

		document['error'] = "model %s errors with no token." % (model_name)
		document['explain'] = "I encountered an error talking with my AI handler."
		document.pop('template_file', None)
		return document


# helper functions
# ================

# load template
def load_template(name="default"):
	# file path
	lib_path = os.path.dirname(__file__)
	file_path = "templates/%s.txt" % name

	try:
		with open(file_path, 'r') as f:
			template = Template(f.read())
	except Exception as ex:
		print(ex)
		print("exception in loading template")
		template = None

	return template
	
# gpt3 dense vectors
def gpt3_embedding(content, engine='text-similarity-ada-001'):
	content = content.encode(encoding='ASCII',errors='ignore').decode()
	response = openai.Embedding.create(input=content,engine=engine)
	vector = response['data'][0]['embedding']  # this is a normal list
	return vector

# completion
def gpt3_completion(prompt, temperature=0.95, max_tokens=256, top_p=1, fp=0, pp=0):
	try:
		# call to OpenAI completions
		response = openai.Completion.create(
		  model = "text-davinci-003",
		  prompt = prompt,
		  temperature = temperature,
		  max_tokens = max_tokens,
		  top_p = top_p,
		  frequency_penalty = fp,
		  presence_penalty = pp
		)

		answer = response['choices'][0]['text']
	except Exception as ex:
		answer = "Call to OpenAI completion failed: %s" % ex

	return answer


# model functions
# ===============

# reboot noises
@model
def reboot(document, template_file="reboot"):
	# load openai key then drop it from the document
	openai.api_key = document.get('openai_token')
	document.pop('openai_token', None)

	template = load_template(template_file)
	prompt = template.substitute()

	document['answer'] = "Rebooting...%s" % gpt3_completion(prompt, temperature=0.45, max_tokens=30).strip("\n")
	return document

@model
def query(document):
	# load openai key then drop it from the document
	openai.api_key = document.get('openai_token')
	document.pop('openai_token', None)

	# get the template file to use
	template_file = document.get('template_file', "first_pass")

	# random number for ids
	document['random'] = int(random.random()*1000000000)
	
	print(document)
	# substitute things
	template = load_template(template_file)
	prompt = template.substitute(document)
	print(prompt)
	# ask GPT-3 for an answer
	answer = gpt3_completion(prompt)
	print(answer)
	try:
		answer_dict = eval('{%s' % (answer.strip("\n").strip(" ").replace("\n", "")))
		document = {**document, **answer_dict}
	except Exception as ex:
		# bad sql
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print("=============EVAL==============")
		print(exc_type, exc_obj, exc_tb)
		print("===============================")
		document['explain'] = "I had problems returning a response. %s" % ex
		document['is_sql'] = False

	return document

@model
def feedback(document, template_file="sql_feedback"):
	openai.api_key = document.get('openai_token')

	prompt_data = {
		"plain": document.get('plain'),
		"author": document.get('author'),
		"tables": document.get('tables'),
		"error": document.get('error'),
		"sql": document.get('sql'),
		"rand_number": int(random.random()*1000000000)
	}

	template = load_template(template_file)
	prompt = template.substitute(prompt_data)
	print(prompt)

	answer = gpt3_completion(prompt)
	print(answer)
	try:
		answer_dict = eval('{%s' % (answer.strip("\n").strip(" ")))
	except:
		print("Exception with eval'ing answer!")
		print("===============================")
		answer_dict = {"explain": "I had problems building a response.", "is_sql": "False"}

	return answer_dict

@model
def response(document, template_file="response"):
	openai.api_key = document.get('openai_token')

	prompt_data = {
		"plain": document.get('plain'),
		"author": document.get('author'),
		"result": document.get('result'),
		"sql": document.get('sql')
	}


	template = load_template(template_file)
	prompt = template.substitute(prompt_data)
	print(prompt)
	answer = gpt3_completion(prompt)
	print(answer)

	return answer