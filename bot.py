import os
import json

import discord, openai
from discord.ext import commands
from discord.ext.commands import Bot, Context

import requests
from string import Template

import random

import config

intents = discord.Intents.default()
# print(dir(intents))
# intents.message_content = True
client = discord.Client(intents=intents)

url = 'http://localhost:10101/sql'

def load_template(name="default"):
		lib_path = os.path.dirname(__file__)
		file_path = "templates/%s.txt" % name

		try:
			with open(os.path.join(lib_path, file_path), 'r') as f:
				template = Template(f.read())
		except:
			template = None

		return template

def ai(message, user, tables):
	openai.api_key = config.openai_token

	query = {"message": message, "user": user, "tables": tables, "rand_number": int(random.random()*1000000000)}
	template = load_template('ai')
	prompt = template.substitute(query)
	print(prompt)
	response = openai.Completion.create(
	  model="text-davinci-003",
	  prompt=prompt,
	  temperature=0.7,
	  max_tokens=256,
	  top_p=1,
	  frequency_penalty=0,
	  presence_penalty=0
	)

	answer = response['choices'][0]['text']
	print(answer)
	#python_dict = eval('{"explain": %s' % answer)

	#print(python_dict)
	#return make_response({"q": q, "data": python_dict})
	return(answer)

@client.event
async def on_ready() -> None:
	print(f'We have logged in as {client.user.name}')

@client.event
async def on_message(message):
	print("message-->", message)
	# print("message content-->", message.content)
	# print("message attachments-->", message.attachments)
	# print("message id", message.author.id)
	# print("name", message.author.name)
	# print("discriminator", message.author.discriminator)

	# get current tables
	result = requests.get('http://localhost:10101/index')
	tables = result.json().get("indexes")
	tables_string = ""
	for table in tables:
		query = "show create table %s" % table.get("name")
		result_create = requests.post(url, data=query.encode('utf-8'), headers={'Content-Type': 'text/plain'})
		tables_string = tables_string + result_create.json().get("data")[0][0] + "\n"

	if message.content.startswith('<@10382578170> '):
		pass
		# print(message.content)
			 
	if message.author == client.user:
		return

	if "slothbot" in message.content.lower():
		"""
		message.channel.send({
			files: [{
				attachment: "/static/fig1.png",
				name: "fig1.png"
			}]
		});
		"""

		answer = query = ai(message.content, message.author.name, tables_string)
		
		answer_dict = eval('{"user": %s' % answer.strip("\n").strip(" "))

		if answer_dict.get("is_sql"):
			query = answer_dict.get("sql")
			result = requests.post(url, data=query.encode('utf-8'), headers={'Content-Type': 'text/plain'})
			_result = result.json()

		if answer_dict.get("answer") != "":
			await message.channel.send(answer_dict.get("answer"))
		else:
			answer = "Unfortunately, when I thought about this I have nothing to say."
			await message.channel.send(answer)
		
		try:
			if _result["data"]:
				for bits in _result["data"]:
					await message.channel.send(bits)
		except:
			pass
			# await message.channel.send(_result)


				


client.run(config.discord_token)