import os
import json
import sys
import time
import random
import string

import asyncio

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

# async think
start_time = time.time()

async def stuff():
	channel = client.get_channel(1067446497253265410)

	async with channel.typing():
		await asyncio.sleep(random.random() * 5)
		await channel.send(ai("meh", {}).get('explain'))

async def think(periodic_function):
	while True:
		await asyncio.gather(
		asyncio.sleep((random.random() * 100)+300),
		periodic_function(),
	)

async def say(saying, channel):
	async with channel.typing():
		await asyncio.sleep(random.random() * 2)
		await channel.send(saying)
	return

# ON READY
@client.event
async def on_ready():
	# show reboot of bot
	channel = client.get_channel(1067446497253265410)

	# test FeatureBase connection
	_tables = featurebase_tables_string()

	if not _tables:
		await channel.send("Couldn't query FeatureBase for tables.")
	else:
		await say("%s table(s) availabe via FeatureBase: %s" % (len(_tables.split(",")), _tables), channel)

	# connect to weaviate and ensure schema exists
	try:
		weaviate_client = weaviate.Client(config.weaviate_url)
		await say("Connected to a Weaviate instance!", channel)
	except:
		await say("Can't connect to a Weaviate instance.", channel)


	# Need to reset Weaviate?
	for weaviate_class in config.weaviate_classes:
		try:
			# weaviate_client.schema.delete_class(weaviate_class)
			pass
		except Exception as ex:
			print(ex)

	schema_path = os.path.dirname(os.path.realpath(__file__))+"/schema"
	schema_list = os.listdir(schema_path)

	for schema in schema_list:
		schema_file = os.path.join(schema_path, schema)
		
		with open(schema_file) as f:
			schema_dict = json.loads(f.read())

			try:
				weaviate_client.schema.create_class(schema_dict)
				print("Created Weaviate class %s" % schema)
				await say("Created Weaviate class from *%s* schema." % schema, channel)

			except Exception as ex:
				# show vector database connection error
				# await say("Weaviate class *%s* exists." % schema, channel)
				print(ex)

	# just thinking
	# task = asyncio.create_task(think(stuff))
	
	return

@client.event
async def on_thread_update(thread):
	print(thread)
	return

@client.event
async def on_thread_create(prev_thread, next_thread):
	print(prev_thread, next_thread)
	return

# received a reaction
# we use this to move the document to the next step in the pipeline
@client.event
async def on_reaction_add(reaction, user):
	channel = client.get_channel(reaction.message.channel.id)

	if reaction.message.channel.id == 1067446497253265410:
		if "uuid:" in reaction.message.content:
			uuid = reaction.message.content.split("uuid: ")[1]
			weaviate_delete(uuid, "FeatureBase")
			await channel.send("Deleted document %s from Weaviate." % uuid)
			return

		await channel.send("Standby...running query.")

		document = {"concepts": [reaction.message.content]}
		result = weaviate_query(document, "Intent", 0.2)

	return

# received a plain text query from discord
@client.event
async def on_message(message):
	# log discord message
	# log_discord(message)

	# log channels
	if message.channel.id in config.support_channel_ids:
		document = {
			"plain": message.content,
			"author": message.author.name,
			"channel": message.channel.name
		}
		data_uuid = weaviate_update(document, "SupportHistory")

	# check if we are allowed to interact with current channel
	if message.channel.id not in config.allowed_channel_ids:
		return
	
	# if author is the bot, we ignore it from here	 
	if message.author == client.user:
		return

	# grab tables and check input for mentions of them
	tables = featurebase_tables_schema()
	tables_schema = []
	for table in tables:
		table_name = table.get('name')
		if table_name in message.content.lower():
			tables_schema = featurebase_tables_schema(table_name)
			break
	
	# ask the AI
	if not tables_schema:
		# try to determine the table
		document['tables'] = featurebase_tables_string()
		table_name = ai("which_database", document).get('table', None)
		print("table was determined to be %s" % table_name)
		if table_name:
			tables_schema = featurebase_tables_schema(table_name)

	# either way, we respond to the prompt template
	if not tables_schema:
		# no table mentioned		
		table_info = "You were unable to determine a FeatureBase table on which to operate. You may still be able to write some SQL queries, but won't have any idea what the table name is if doing selects or inserts."
	else:
		fb_document = featurebase_query({"sql": "SELECT CAST (_id AS int) AS the_id FROM %s ORDER BY the_id desc;" % table_name})
		try:
			next_id = fb_document.get('data')[0][0] + 1
			print(next_id)
			print("================")
		except:
			next_id = 0

		table_info = "You are operating on a table called: %s. If you need an _id for the id field for an INSERT, you can use: %s. The schema for %s is as follows:\n%s" % (table_name, next_id, table_name, tables_schema)

	# someone is addressing slothbot, so respond
	if message.content.lower().startswith("slothbot "):
		# create document
		document = {
			"plain": message.content.lstrip("slothbot "),
			"author": message.author.name,
			"tables_schema": tables_schema,
			"table_info": table_info,
			"tables": featurebase_tables_string(),
		}

		# try to determine the table
		table = ai("which_database", document).get('table', None)

		# retreive document results from AI
		document = ai("query", document)

		# document = ai("process_sql", document)

		# for now, we remove for printing to discord
		document.pop("tables")
		document.pop("tables_schema")
		document.pop("random_id")
		document.pop("sql_samples")
		document.pop("table_info")

		if document.get("explain", "None") != "None":
			await say(document.get("explain"), message.channel)
		if document.get("thoughts", None) not in ["None", None, ""]:
			await say(document.get("thoughts"), message.channel)

		# await say(json.dumps(document), message.channel)
		print("=======TRAIN INFO=========")
		print(json.dumps(document))
		print("==========================")

		# we have something to run to the database
		if document.get("sql") != ";":

			# ACLs, of a type
			access_denied = False
			if message.author.id not in config.admins:
				for blocked in ["drop", "create", "alter", "delete"]:
					if blocked in document.get("sql").lower():
						access_denied = True
						document['error'] = "I'm sorry, but my ACLs prevent that action."
						document['explain'] = "User %s is not allowed to do that." % document.get('author')

			# only run if not denied
			if not access_denied:
				document = featurebase_query(document)

				if document.get('error', False):
					await say(document.get("explain"), message.channel)
					await say(document.get("error"), message.channel)
				elif document.get('data', []):
					if document.get('data', []):
						pass
						# await say(document.get('data'), message.channel)
					else:
						await say("Done.")


				purty = PrettyTable()
				purty_fields = []
				try:
					for field in document.get('schema').get('fields'):
						purty_fields.append(field.get('name'))
				except:
					pass
				purty.field_names = purty_fields
				purty_rows = []
				for row in document.get('data'):
					purty.add_row(row)
				await say("```\n%s\n```" % purty, message.channel)

		# create a history document and send to weaviate
		hints = {
			"author": document.get('author'),
			"plain": document.get('plain'),
			"explain": document.get('explain'),
			"thoughts": document.get('thoughts'),
			"sql": document.get('sql'),
			"table": document.get('table'),
			"display_type": document.get('display_type')				
		}

		data_uuid = weaviate_update(hints, "FeatureBase")
		await message.channel.send("Document inserted into Weaviate with uuid: %s" % data_uuid)

		return

	# provide basic support
	if message.content.lower().startswith("support "):
		# create document
		document = {
			"plain": message.content,
			"author": message.author.name,
			"channel": message.channel.name
		}
		support_document = ai("support", document)

		await message.channel.send(support_document.get('explain'))
		return

	if message.content.lower().startswith("delete ") and message.author.name == "Kord":
		uuid = message.content.split(" ")[1]
		weaviate_delete(uuid, "Intent")
		await message.channel.send("Deleted document %s from Weaviate." % uuid)
		return

	# test message content for json
	try:
		document = json.loads(message.content)

		intent_document = {
			"author": message.author.name,
			"plain": document.get('plain'),
			"explain": document.get('explain'),
			"sql": document.get('sql'),
			"table": document.get('table'),
			"display_type": document.get('display_type')
		}

		if message.author.id not in config.admins:
			await say("%s is not allowed to train the bot. Please contact an admin for assistance." % message.author.name, message.channel)

			raise("User is not allowed to train bot.")

		data_uuid = weaviate_update(intent_document, "FeatureBase")
		await say("Document inserted into Weaviate with uuid: %s" % data_uuid, message.channel)

	except Exception as ex:
		print(ex)

	# who wants dallE?
	# creates images from a prompt
	if message.content.lower().startswith("dream "):
		# create document
		document = {
			"plain": "a sloth and " + message.content,
			"author": message.author.name
		}
		url = ai("dream", document)
		await message.channel.send(url)
		return

	# who wants dallE?
	# creates images from a prompt
	if message.content.lower().startswith("mug "):
		# create document
		document = {
			"plain": "sloth %s" % message.content.strip("mug "),
			"author": message.author.name
		}
		url = ai("dream", document)

		# download image
		import requests

		filename = '%s.jpg' % random_string(8)
		
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


# entry point
client.run(config.discord_token)

