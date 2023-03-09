import random
import asyncio
import aiohttp

import discord
from discord.ext import commands
from discord.ext.commands import Bot, Context

from lib.util import random_string

import config

# discord intents and client
intents = discord.Intents.default()
# intents.message_content = True
client = discord.Client(intents=intents)

# say command
async def say(saying, channel):
	async with channel.typing():
		await asyncio.sleep(random.random() * 1)
		await channel.send(saying)
	return

async def typing(channel):
	async with channel.typing():
		await asyncio.sleep(random.random() * 1)
	return

async def upload(file_handle, file_name, channel):
	async with channel.typing():
		await asyncio.sleep(random.random() * 2)
		await channel.send(file=discord.File(file_handle, file_name))

# ON READY
@client.event
async def on_ready():
	# show reboot of bot
	channel = client.get_channel(1067446497253265410)
	await channel.send("-")

	return

# thread update
@client.event
async def on_thread_update(thread):
	print(thread)
	return

# thread create
@client.event
async def on_thread_create(prev_thread, next_thread):
	print(prev_thread, next_thread)
	return

# received a reaction
@client.event
async def on_reaction_add(reaction, user):
	channel = client.get_channel(reaction.message.channel.id)
	print(channel)
	return

# received a plain text query from discord
@client.event
async def on_message(message):
	# check if we are allowed to interact with current channel
	if message.channel.id not in config.allowed_channel_ids:
		return
	
	# if author is the bot, we ignore it from here	 
	if message.author == client.user:
		return

	# commands
	command = message.content.lower().split(" ")[0]
	if command not in config.commands:
		command = "chat"

		# return if not allowed general chat in channel
		if message.channel.id not in config.chat_channel_ids:
			return
	else:
		command = command.strip("!")

	# create a basic document to update as we go
	document = {
		"document_id": random_string(13),
		"message_id": message.id,
		"plain": message.content.strip("!"),
		"command": command,
		"author": message.author.name,
		"channel": message.channel.name
	}

	# authenticate
	url = config.endpoints_url + "/%s" % command
	auth = aiohttp.BasicAuth(
		config.basic_auth_username,
		config.basic_auth_password
	)

	try:
		await typing(message.channel)
		async with aiohttp.ClientSession() as session:
			async with session.post(url, auth=auth, json=document) as resp:
				assert resp.status == 200
				response = await resp.json()

				# print(response)
				await say(response.get('answer'), message.channel)

				if response.get('url_results', []):
					for result in response.get('url_results', []):
						embed = discord.Embed(
							title = result.get('title', ""),
							url = result.get('url'), 
							description = result.get('description'), 
							color = discord.Color.blue()
						)
						try:
							await typing(message.channel)
							await message.channel.send(embed = embed)
						except:
							pass

				if response.get('example', ""):
					await say("```%s```" % response.get('example'), message.channel)

	except Exception as ex:
		await say("My endpoint handlers for !%s are offline. Standby." % command, message.channel)
		print(ex)

	return

# entry point
client.run(config.discord_token)
