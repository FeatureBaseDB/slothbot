import os
import json
import sys
import time
import random
import string

import discord, openai
from discord.ext import commands
from discord.ext.commands import Bot, Context

import config

from ai import ai
from database import featurebase_tables_schema, featurebase_tables_string, featurebase_query
from database import weaviate_update, weaviate_query, weaviate_delete

import weaviate

from prettytable import PrettyTable

# random words
from random_word import RandomWords
r = RandomWords()

def random_string(size=6, chars=string.ascii_letters + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

# discord intents
intents = discord.Intents.default()
# intents.message_content = True
client = discord.Client(intents=intents)

# discord log
def log_discord(message):
	print("message-->", message)
	# print("message content-->", message.content)
	# print("message attachments-->", message.attachments)
	# print("message id", message.author.id)
	# print("name", message.author.name)
	# print("discriminator", message.author.discriminator)


# ON READY
@client.event
async def on_ready():
	# show reboot of bot
	channel = client.get_channel(1067446497253265410)

	# test FeatureBase connection
	_tables = featurebase_tables_string()

	await channel.send("-")

	if not _tables:
		await channel.send("Couldn't query FeatureBase for tables.")
	else:
		await channel.send("%s tables availabe via FeatureBase: %s" % (len(_tables.split(",")), _tables))

	# connect to weaviate and ensure schema exists
	try:
		weaviate_client = weaviate.Client("http://localhost:8080")

		# Need to reset Weaviate?
		# weaviate_client.schema.delete_all()

		# make schemas if none found
		if not weaviate_client.schema.contains():
			dir_path = os.path.dirname(os.path.realpath(__file__))
			schema_file = os.path.join(dir_path, "weaviate_schema.json")
			weaviate_client.schema.create(schema_file)
		
		await channel.send("Connected to Weaviate instance.")

	except Exception as ex:
		# show vector database connection error
		await channel.send("Can't connect to a Weaviate instance.")
		print(ex)

	return

# received a reaction
# we use this to move the document to the next step in the pipeline
@client.event
async def on_reaction_add(reaction, user):
	channel = client.get_channel(reaction.message.channel.id)
	if reaction.message.channel.id == 1067446497253265410:
		if "uuid:" in reaction.message.content:
			uuid = reaction.message.content.split("uuid: ")[1]
			weaviate_delete(uuid, "Intent")
			await channel.send("Deleted document %s from Weaviate." % uuid)
			return

		await channel.send("Standby...running query.")

		document = {"concepts": [reaction.message.content]}
		result = weaviate_query(document, "Intent", 0.2)

		# refactor
		# run until we get SQL, or an explaination/answer
		if document.get('is_sql', False) != False:
			document = featurebase_query(document)

			if document.get('data', []) != []:
				table_name = document.get('table')
				table = featurebase_tables(table_name)[0]

				_field_names = []
				for field in table.get('fields'):
					_field_names.append(field.get('name'))

				pretty_table = PrettyTable()
				pretty_table.field_names = _field_names

				for entry in document.get('data'):
					pretty_table.add_row(entry)

				table_string = "```\n%s\n```" % pretty_table
				await channel.send(document.get('explain'))
				await channel.send(document.get('sql'))
				await channel.send(table_string)

			else:
				await channel.send("It goes without saying, we have to be here.")
				await channel.send(document.get('explain'))

	return

# received a plain query from the user
@client.event
async def on_message(message):
	# log discord message
	# log_discord(message)

	# if author is the bot, we ignore it	 
	if message.author == client.user:
		return

	# stop bot from interactions in most channels
	# use #offtopic and #bot-dev only
	# allows op to interact everywhere
	if message.channel.id not in [1067446497253265410, 1038459042345001061]:
		if "slothbot" in message.content.lower():
			if message.author.name != "Kord" and message.author != client.user:
				await message.channel.send("Sorry %s, I can't work in here. See the #bot-dev channel!" % message.author.name)
				return

	if message.content.lower().startswith("delete ") and message.author.name == "Kord":
		uuid = message.content.split(" ")[1]
		weaviate_delete(uuid, "Intent")
		await message.channel.send("Deleted document %s from Weaviate." % uuid)
		return

	# test message content for json
	try:
		document = json.loads(message.content)
		if document.get('sql', False):
			use_sql = True
		else:
			use_sql = False

		if document.get('type_of_chart', False):
			use_chart = True
		else:
			use_chart = False

		intent_document = {
			"author": message.author.name,
			"plain": document.get('plain'),
			"explain": document.get('explain'),
			"sql": document.get('sql'),
			"table": document.get('table'),
			"display_type": document.get('display_type')				
		} 
		data_uuid = weaviate_update(intent_document, "Intent")
		await message.channel.send("Document inserted into Weaviate with uuid: %s" % data_uuid)

	except:
		pass

	# who wants dallE?
	# creates images from a prompt
	if message.content.lower().startswith("dream "):
		# create document
		document = {
			"plain": message.content,
			"author": message.author.name
		}
		url = ai("dream", document)
		await message.channel.send(url)
		return

	# graph bot prototype
	if "graphbot" in message.content.lower():
		import plotly.express as px
		import plotly.figure_factory as ff
		import numpy as np
		x1,y1 = np.meshgrid(np.arange(0, 2, .2), np.arange(0, 2, .2))
		u1 = np.cos(x1)*y1
		v1 = np.sin(x1)*y1

		fig = ff.create_quiver(x1, y1, u1, v1)

		filename = "static/%s.png" % random_string(6)
		fig.write_image(filename)
		
		picture = discord.File(filename)
		await message.channel.send(file=picture)
		
		return

	# graph bot prototype
	if message.content.lower().startswith("help "):
		# create document
		document = {
			"plain": message.content,
			"author": message.author.name
		}
		result = ai("help", document)
		await message.channel.send(result.get("explain"))

		return

	# someone is addressing slothbot, so respond
	if "slothbot" in message.content.lower():
		# create document
		document = {
			"plain": message.content,
			"author": message.author.name,
			"tables_schema": featurebase_tables_schema(),
			"tables": featurebase_tables_string(),
		}

		# retreive document results from AI
		document = ai("query", document)


		await message.channel.send(document.get("explain"))

		print(document)
		if document.get("sql") and document.get('table'):
			document = featurebase_query(document)

			if document.get('error', False):
				await message.channel.send("Got an answer, but no data.")
				await message.channel.send(document.get("explain"))
				await message.channel.send(document.get("error"))
			elif document.get('data', []):
				await message.channel.send(document.get('data'))


		# create a history document and send to weaviate
		intent = {
			"author": document.get('author'),
			"plain": document.get('plain'),
			"explain": document.get('explain'),
			"sql": document.get('sql'),
			"table": document.get('table'),
			"display_type": document.get('display_type')				
		}

		data_uuid = weaviate_update(intent, "Intent")
		await message.channel.send("Document inserted into Weaviate with uuid: %s" % data_uuid)


	return

# entry point
client.run(config.discord_token)

