import os
import json
import sys
import time
import random

import discord, openai
from discord.ext import commands
from discord.ext.commands import Bot, Context

import config

from ai import ai
from database import featurebase_tables, featurebase_query
from database import weaviate

from prettytable import PrettyTable

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
	document = ai(model_name="reboot", document={})

	await channel.send(document.get("answer", "Rebooting.."))

	# test FeatureBase connection
	tables = featurebase_tables()
	_tables = []

	for table in tables:
		_tables.append(table.get('name'))

	if not tables:
		await channel.send("Couldn't query FeatureBase for tables.")
	else:
		await channel.send("%s tables availabe via FeatureBase:" % len(tables))
		await channel.send(_tables)

	# connect to weaviate and ensure schema exists
	try:
		weaviate_client = weaviate.Client("http://localhost:8080")

		# reset weaviate
		# weaviate_client.schema.delete_all()

		# make schema if not avaialble
		if not weaviate_client.schema.contains():
			dir_path = os.path.dirname(os.path.realpath(__file__))
			schema_file = os.path.join(dir_path, "weaviate_schema.json")
			weaviate_client.schema.create(schema_file)
		
		await channel.send("Connected to Weaviate instance.")

	except Exception as ex:
		# show vector database connection error
		await channel.send("Can't connect to a Weaviate instance.")
		await channel.send(ex)

	return


@client.event
async def on_message(message):
	# log discord message
	# log_discord(message)

	# if author is the bot, we ignore it	 
	if message.author == client.user:
		return

	if "slothbot" in message.content.lower() :

		# create document
		document = {
			"plain": message.content,
			"author": message.author.name,
			"tables": featurebase_tables(),
			"template_file": "first_pass"
		}

		# process the request, 3 passes max
		max_pass = 3
		for x in range(0, max_pass):
			document = ai("query", document)

			# run until we get SQL, or an explaination/answer
			if document.get('is_sql', 'False') != 'False':
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
					await message.channel.send(document.get('explain'))
					await message.channel.send(document.get('sql'))
					await message.channel.send(table_string)
				
					break

				else:
					await message.channel.send(document.get('explain'))

					break
		
			else:
				await message.channel.send(document.get("explain"))
				break

			# failback
			time.sleep(3)
			x = x + 1
			if x > 2:
				break

			if not document.get('template_file'):
				await message.channel.send(document.get("explain"))
				break


		"""

		answer_dict = ai("sql", document)

		document = {**document, **answer_dict}
 
		# not working
		data_uuid = weaviate_update(document)

		# got a SQL query back
		if document.get("is_sql", False) and document.get("is_sql").lower() == "true":
			try:
				query = document.get("sql")
				result = requests.post(url, data=query.encode('utf-8'), headers={'Content-Type': 'text/plain'}).json()
			except Exception as bullshit:
				# bad sql
				exc_type, exc_obj, exc_tb = sys.exc_info()
				await message.channel.send("(╯°□°)╯︵ ┻━┻")
				await message.channel.send("%s: %s" % (exc_tb.tb_lineno, bullshit))

			# got an answer from featurebase
			if result.get('error', ""):
				document.setdefault("error", result.get('error', ""))
				answer_dict = ai("sql_feedback", document)
				document = {**document, **answer_dict}

				try:
					query = document.get("sql")
					result = requests.post(url, data=query.encode('utf-8'), headers={'Content-Type': 'text/plain'}).json()
				except Exception as bullshit:
					# bad sql
					exc_type, exc_obj, exc_tb = sys.exc_info()
					await message.channel.send("(╯°□°)╯︵ ┻━┻")
					await message.channel.send("%s: %s" % (exc_tb.tb_lineno, bullshit))


			elif result.get('data', []):
				print(result.get('data'))
				answer_dict = ai("response", document)


				for bits in _result["data"]:
					try:
						# await message.channel.send(bits)
						pass
					except Exception as bullshit:
						exc_type, exc_obj, exc_tb = sys.exc_info()
						await message.channel.send("%s: %s" % (exc_tb.tb_lineno, bullshit))
				await message.channel.send(ai("response", document={"query": message.content,"result": _result['data'], "user": message.author.name, "sql": query}))

			else:
				await message.channel.send(result)
		else:
			if document.get("explain") != "":
				await message.channel.send(document.get("explain"))

			else:
				answer = "Unfortunately, when I thought about this I have nothing to say."
				await message.channel.send(answer)
		"""

# entry
client.run(config.discord_token)

