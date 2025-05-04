import random
import requests
import re

from functools import reduce

class Grind:
	def __init__(self, client):
		self.client = client

	async def send_owo(self):
		if self.client.data.available.selfbot:
			say = random.choice(self.client.data.config.grind['owo']['message'])
			await self.client.data.discord.channel.send(say)
			self.client.logger.info(f"Sent {say}")
			self.client.data.stat.sent_message += 1

	async def send_hunt(self):
		if self.client.data.available.selfbot:
			say = random.choice(self.client.data.config.grind['hunt']['message'])
			await self.client.data.discord.channel.send(f"{self.client.data.discord.prefix}{say}")
			self.client.logger.info(f"Sent {self.client.data.discord.prefix}{say}")
			self.client.data.stat.sent_message += 1

	async def send_battle(self):
		if self.client.data.available.selfbot:
			say = random.choice(self.client.data.config.grind['battle']['message'])
			await self.client.data.discord.channel.send(f"{self.client.data.discord.prefix}{say}")
			self.client.logger.info(f"Sent {self.client.data.discord.prefix}{say}")
			self.client.data.stat.sent_message += 1

	async def send_random_messages(self):
		if self.client.data.available.selfbot:
			random_messages = random.choice(self.client.data.selfbot.random_messages)
			await self.client.data.discord.channel.send(f"`{random_messages}`")
			self.client.logger.info(f"Sent {random_messages[0:30]}...")
			self.client.data.stat.sent_message += 1
