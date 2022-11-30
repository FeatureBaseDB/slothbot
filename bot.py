import os
import json

import discord
from discord.ext import commands
from discord.ext.commands import Bot, Context

import OpenAi

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready() -> None:
	print(f'We have logged in as {client.user.name}')

@client.event
async def on_message(message):
	print("message-->", message)
	print("message content-->", message.content)
	print("message attachments-->", message.attachments)
	print("message id", message.author.id)
	print("name", message.author.name)
	print("discriminator", message.author.discriminator)
	
	if message.content.startswith('<@10382578170> '):
		print(message.content)
		 
	if message.author == client.user:
		return

	if "slothbot" in message.content.lower():
		answer = OpenAi.ask(message.content, "")
		if answer != "":
			print(answer)
			await message.channel.send(answer)
		else:
			answer = OpenAi.ask("Unfortunately, when we asked the bot this, it had nothing to say.", "")
			await message.channel.send(answer)

client.run("")
