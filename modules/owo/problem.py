import discord

class Problem:
	def __init__(self, client):
		self.client = client
	
	async def banned(self, message):
		if self.client.others.message(message, True, False, ['You have been banned'], []) and (str(self.client.user.name) in message.content or message.channel.id == self.client.bot.dm_channel.id):
			await self.client.notification.notify()
			self.client.logger.warning(f"!!! You have been banned !!!")
			await self.client.webhook.send(
				content = self.client.data.discord.mention,
				title = "🔨 YOU HAVE BEEN BANNED 🔨",
				description = f"{self.client.data.config.emoji['arrow']}{message.jump_url}",
				color = discord.Colour.random()
			)
			self.client.data.available.selfbot = False

	async def no_cowoncy(self, message):
		if self.client.others.message(message, True, False, [str(self.client.data.discord.nickname), 'don\'t have enough cowoncy!'], []) and not "you silly hooman" in message.content:
			await self.client.notification.notify()
			self.client.logger.warning(f"!!! Ran out of cowoncy !!!")
			await self.client.webhook.send(
				content = self.client.data.discord.mention,
				title = "💸 RAN OUT OF COWONCY 💸",
				description = f"{self.client.data.config.emoji['arrow']}{message.jump_url}",
				color = discord.Colour.random()
			)
			self.client.data.available.selfbot = False