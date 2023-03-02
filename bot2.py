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

# discord intents
intents = discord.Intents.default()
# intents.message_content = True
client = discord.Client(intents=intents)


# ON READY
@client.event
async def on_ready():
	# show reboot of bot
	channel = client.get_channel(1067446497253265410)
	await channel.send("-")

	return

# entry point
client.run(config.discord_token)
