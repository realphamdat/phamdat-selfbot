import asyncio
import time
import datetime
import re

class Daily:
	def __init__(self, client):
		self.client = client

	def reset_time(self):
		if self.client.data.config.claim_daily['mode'] and self.client.data.cooldown.reset != 0:
			reset_time = self.client.data.cooldown.reset
		else:
			reset_time = datetime.datetime.now(datetime.UTC).replace(hour = int(self.client.data.config.claim_daily['reset_UTC_time']['hour']), minute = int(self.client.data.config.claim_daily['reset_UTC_time']['minute']), second = int(self.client.data.config.claim_daily['reset_UTC_time']['second']), microsecond = int(self.client.data.config.claim_daily['reset_UTC_time']['microsecond']))
			if datetime.datetime.now(datetime.UTC) < reset_time:
				reset_time = reset_time - datetime.timedelta(days = 1)
			reset_time = (reset_time - datetime.datetime.now(datetime.UTC)).seconds + 30
		return(reset_time)

	async def claim_daily(self):
		if self.client.data.available.selfbot and int(self.client.data.cooldown.daily) - time.time() <= 0:
			await self.client.data.discord.channel.send(f"{self.client.data.discord.prefix}daily")
			self.client.logger.info(f"Sent {self.client.data.discord.prefix}daily")
			self.client.data.stat.sent_message += 1
			try:
				daily_message = await self.client.wait_for("message", check = lambda message: self.client.others.message(message, True, True, [str(self.client.data.discord.nickname)], ['next daily', 'Nu']), timeout = 10)
				time_data = re.findall(r'(\d+)H|(\d+)M|(\d+)S', daily_message.content.split('!')[-1].strip())
				next_daily = [int(time_data[0][0]) if time_data[0][0] else 0, int(time_data[1][1]) if time_data[1][1] else 0, int(time_data[2][2]) if time_data[2][2] else 0]
				daily_again = next_daily[0] * 3600 + next_daily[1] * 60 + next_daily[2]
				self.client.data.cooldown.reset = daily_again
				self.client.data.cooldown.daily = daily_again + time.time()
				if "next daily" in daily_message.content:
					self.client.logger.info(f"Claimed daily ({datetime.timedelta(seconds = daily_again)})")
				elif "Nu" in daily_message.content:
					self.client.logger.info(f"Couldn't claim daily ({datetime.timedelta(seconds = daily_again)})")
			except asyncio.TimeoutError:
				self.client.logger.error(f"Couldn't get claim daily message")