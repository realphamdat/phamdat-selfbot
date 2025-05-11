import os

class Notification:
	def __init__(self, client):
		self.client = client
	
	async def notify(self):
		if self.client.data.config.notification['play_music']['mode']:
			await self.play_music()

	async def play_music(self):
		try:
			os.startfile(os.getcwd() + "/assets/music.mp3")
			self.client.logger.info(f"Played music")
		except Exception as e:
			self.client.logger.error(f"Couldn't play music | {e}")