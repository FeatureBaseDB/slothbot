import os
import sys
import datetime
import random
import string
import requests

import openai

import traceback

from string import Template

from bs4 import BeautifulSoup

from lib.database import weaviate_schema, weaviate_query, weaviate_update
from lib.database import featurebase_tables_schema

import config

# AI model call by method name
models = {}
model = lambda f: models.setdefault(f.__name__, f)

def ai(model_name="none", document={}):
	# get the user's API token	
	openai_token = config.openai_token
	print("AI in")

	if not openai_token:
		# rewrite to match document flow
		document['error'] = "model %s errors with no token." % (model_name)
		document['explain'] = "I encountered an error talking with OpenAI."
		document['template_file'] = "eject_document"
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

		document['error'] = "model *%s* errors with %s." % (model_name, ex)
		document['explain'] = "I encountered an error talking with my AI handler."
		document['template_file'] = "eject_document"
		return document


# helper functions
# ================

# load template
def load_template(name="default"):
	# file path
	lib_path = os.path.dirname(__file__)
	file_path = "%s/templates/%s.txt" % (lib_path, name)

	try:
		with open(file_path, 'r') as f:
			template = Template(f.read())
	except Exception as ex:
		print(ex)
		print("exception in loading template")
		template = None

	return template


# random strings
def random_string(size=6, chars=string.ascii_letters + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))


# gpt3 dense vectors
def gpt3_embedding(content, engine='text-similarity-ada-001'):
	content = content.encode(encoding='ASCII',errors='ignore').decode()
	response = openai.Embedding.create(input=content,engine=engine)
	vector = response['data'][0]['embedding']  # this is a normal list
	return vector


# gptchat
def gpt_chat(words):
	try:
		completion = openai.ChatCompletion.create(
		  model="gpt-3.5-turbo-0301",
		  messages = [
		    {"role": "user", "content": words}
		  ]
		)
		answer = completion.choices[0].message
	except Exception as ex:
		answer = "Call to OpenAI chat failed: %s" % ex

	return answer


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
		  presence_penalty = pp,
		  timeout = 20
		)

		answer = response['choices'][0]['text']
	except Exception as ex:
		answer = "Call to OpenAI completion failed: %s" % ex

	return answer

def gpt3_dict_completion(prompt, temperature=0.90, max_tokens=256, top_p=1, fp=0, pp=0):
	answer = gpt3_completion(prompt, temperature, max_tokens, top_p, fp, pp)
	
	try:
		print(answer.replace('\n', ""))
		python_dict = eval('{%s' % answer.replace('\n', ""))
	except Exception as ex:
		python_dict = {}
		python_dict['error'] = "Call to OpenAI completion failed: %s" % ex
		python_dict['dict_string'] = answer
		python_dict['answer'] = "An error occurred talking to OpenAI. Try again in a minute."

	return python_dict


# model functions
# ===============

# mirror text for indexing
@model
def mirror(document):
	# load openai key then drop it from the document
	openai.api_key = document.get('openai_token')
	document.pop('openai_token', None)
	document['answer'] = gpt_chat(document.get('words')).get('content', "")

	return document

# chat mode
@model
def chat(document):
	# load openai key then drop it from the document
	openai.api_key = document.get('openai_token')
	document.pop('openai_token', None)

	# memories
	schema = weaviate_schema("memories")
	uuid = weaviate_update(document, "memories")

	entries = weaviate_query(document, "Memories", ["plain"])
	print("===============")
	print(uuid)
	print(schema)
	print(entries)
	print("===============")

	document['content'] = ""
	for i, entry in enumerate(entries):
		document['content'] = document['content'] + entry.get('gpt_fragment') + "\n"
		if i > 10:
			break

	# substitute things
	template = load_template("chat")
	prompt = template.substitute(document)
	print(prompt)
	answer = gpt3_completion(prompt)
	document['answer'] = answer
	return document

# help mode
@model
def help(document):
	# load openai key then drop it from the document
	openai.api_key = document.get('openai_token')
	document.pop('openai_token', None)

	# substitute things
	template = load_template("help")
	prompt = template.substitute(document)

	answer = gpt3_completion(prompt).strip('\n').strip('"')
	document['answer'] = answer
	return document

# help mode
@model
def docs(document):
	# load openai key then drop it from the document
	openai.api_key = document.get('openai_token')
	document.pop('openai_token', None)

	fields = ["url", "title", "sentence"]
	plain = document.get('plain', "")
	concepts = [plain]

	results = weaviate_query(concepts, "Docs", fields)

	# get a list of URLs and titles
	urls = []
	titles = []
	sentences = [] # first use for description

	for i, result in enumerate(results):
		if result.get('url') not in urls:
			urls.append(result.get('url'))
		if result.get('title') not in titles:
			titles.append(result.get('title'))

	# 10 max for now
	document['docs_urls'] = urls[:10]
	document['docs_titles'] = titles[:10]

	# gather new results + build page info
	concepts = []
	for title in document['docs_titles']:
		concepts.append("%s referencing %s" % (document.get('plain', ""), title))

	# run refined query to weaviate to get relevant sentences for the prompt
	fields = ["sentence"]	
	results = weaviate_query(concepts, "Docs", fields)

	texts = ""
	sentences = []
	for result in results:
		if result.get('sentence') not in texts:
			texts = texts + " " + result.get('sentence')
		if result.get('sentence') not in sentences:
			sentences.append(result.get('sentence'))

	document['docs_texts'] = texts[:1500]
	
	# replace with text version of URL list
	document['docs_urls'] = '\n'.join(document.get('docs_urls'))

	# substitute things
	template = load_template("docs")
	prompt = template.substitute(document)

	# query OpenAI
	answer_dict = gpt3_dict_completion(prompt)

	document['answer'] = answer_dict.get('answer', "")

	if answer_dict.get('code') not in ["none", "NONE", "None"]:
		document['code'] = answer_dict.get('code')

	if answer_dict.get('error', ""):
		print(answer_dict.get('error', ""))
		print(answer_dict.get('dict_string', ""))

	# build embedding information
	url_results = []

	# loop over and check URLs returned
	for url in answer_dict.get('urls',[]):
		res = requests.get(url)
		html_page = res.content
		if res.status_code == 200:
			try:
				soup = BeautifulSoup(html_page, 'html.parser')
				title = soup.find('title').text
			except:
				title = "No title"

			# query weaviate one more time for a "description" of the page
			concepts = "%s %s" % (url, title)
			fields = ["sentence"]
			results = weaviate_query(concepts, "Docs", fields)
	
			if results:
				description = "Signup for FeatureBase Cloud today!"
				for result in results:
					if len(result.get('sentence', "")) > 50:
						description = result.get('sentence', "")[:210]
						for letter in result.get('sentence', "")[210:]:
								if letter != " ":
									description = description + letter
								else:
									break
						break
			else:
				description = "No description provided."

			url_results.append(
				{
					"url": url, 
					"title": "%s 🚀" % title,
					"description": "%s..." % description
				}
			)
		res.close()

	document['url_results'] = url_results

	return document


# dream an image
@model
def dream(document):
	# load openai key then drop it from the document
	openai.api_key = document.get('openai_token')
	document.pop('openai_token', None)
	
	response = openai.Image.create(
	    prompt=document.get('plain'),
	    n=1,
	    size="256x256",
	)

	document['answer'] = response["data"][0]["url"]
	
	return document

# uses templates in templates directory
# set template using document key "template_file"
# use of "eject_document" will force a reply to Discord
@model
def query(document):
	# load openai key then drop it from the document
	openai.api_key = document.get('openai_token')
	document.pop('openai_token', None)

	# get the template file to use
	template_file = document.get('template_file', "query")

	# random string for ids
	document['random_id'] = random_string(6)

	# move this to the query
	hints = weaviate_query(
		document,
		"FeatureBase",
		["author", "plain", "explain", "sql", "table", "display_type"]
	)

	# top 10 hints
	_hints = ""
	for index, hint in enumerate(hints):
		if index < 5:
			hint.pop('_additional')
			if hint.get('sql') not in _hints and hint.get('explain') not in _hints:
				_hints = _hints + hint.get('explain') + ": " + hint.get('sql') + "\n"
		else:
			break

	document['sql_samples'] = _hints

	# substitute things
	template = load_template(template_file)
	prompt = template.substitute(document)

	# ask GPT-3 for an answer
	answer = gpt3_completion(prompt)

	# try to eval the result
	try:
		# prepend the completion with a dictionary {
		answer_dict = eval('{%s' % (answer.strip("\n").strip(" ").replace("\n", "")))
		document = {**document, **answer_dict}

	# we failed to eval
	except Exception as ex:
		# bad sql
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print("=============EVAL==============")
		print(exc_type, exc_obj, exc_tb)
		print(ex)
		print(prompt)
		print(answer)
		print("===============================")
		if not document.get('explain', None):
			document['explain'] = "I had problems returning a valid response."

		document['error'] = ex
		document['template_file'] = "eject_document"

	return document

@model
def which_database(document):
	# load openai key then drop it from the document
	openai.api_key = document.get('openai_token')
	document.pop('openai_token', None)

	# get the template file to use
	template_file = document.get('template_file', "which_database")
	
	# substitute things
	template = load_template(template_file)
	prompt = template.substitute(document)

	# ask GPT-3 for an answer
	answer = gpt3_completion(prompt)

	try:
		# prepend the completion with a dictionary {
		answer_dict = eval('{"table": "%s' % (answer.strip("\n").strip(" ").replace("\n", "")))
		document = {**document, **answer_dict}

	# we failed to eval
	except Exception as ex:
		# bad sql
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print("=============EVAL==============")
		print(exc_type, exc_obj, exc_tb)
		print(ex)
		print(prompt)
		print(answer)
		print("===============================")
		document = {}

	return document


# not in use
@model
def support(document, template_file="support"):
	# load openai key then drop it from the document
	openai.api_key = document.get('openai_token')
	document.pop('openai_token', None)

	template = load_template(template_file)

	# no substitutions for this template, yet
	prompt = template.substitute(document)

	document['explain'] = gpt3_completion(prompt, temperature=0.85, max_tokens=256).strip("\n")
	return document


@model
def meh(document, template_file="meh"):
	# load openai key then drop it from the document
	openai.api_key = document.get('openai_token')
	document.pop('openai_token', None)

	template = load_template(template_file)

	# no substitutions for this template, yet
	prompt = template.substitute(document)

	document['explain'] = gpt3_completion(prompt, temperature=0.85, max_tokens=256).strip("\n")
	return document

@model
def process_sql(document):
	# load openai key then drop it from the document
	openai.api_key = document.get('openai_token')
	document.pop('openai_token', None)

	template_file = document.get('template_file', "sql_process")

	# get the schema
	document["schema"] = featurebase_tables_schema(document.get('table'))
	document["id"] = "12345"

	# substitute things
	template = load_template(template_file)
	prompt = template.substitute(document)
	print(prompt)
	answer = gpt3_completion(prompt)
	print(answer)

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

	answer = gpt3_completion(prompt)

	try:
		answer_dict = eval('{%s' % (answer.strip("\n").strip(" ")))
	except:
		print("Exception with eval'ing answer!")
		print("===============================")
		answer_dict = {"explain": "I had problems building a response.", "is_sql": "False"}

	return answer_dict
