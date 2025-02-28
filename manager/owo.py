import json
import inquirer

class OwOManager:
	def __init__(self, directory):
		self.list_filter = lambda x: x.replace("'", "").replace('"', '')
		self.file = directory['owo']['directory']
		with open(directory['template']) as file:
			self.template = json.load(file)['owo']

		self.features = [
			"Select all",
			"Error retry times",
			"Emoji",
			"Notification (Play music)",
			"History (File - Discord)",
			"Command",
			"Sleep after certain time",
			"Detect problem (Banned - No cowoncy)",
			"Captcha (Detect - Solve - Pause)",
			"Get OwO prefix",
			"Check OwO status",
			"Join OwO giveaway",
			"Channel (ID - Mention - Chanllenge)",
			"Vote top.gg (Require chorme)",
			"Claim daily",
			"Do quest",
			"Grind (OwO/UwU - Hunt - Battle - Quote)",
			"Huntbot (Claim - Sumbit - Upgrade)",
			"Use gem (Box - Crate - Flootbox - Glitch)",
			"Sell/Sacrifice animal",
			"Notify caught animal",
			"Gamble (Slot - Coinflip - Blackjack)",
			"Minigame (Pray/Curse - Others)"
		]

	def homepage(self):
		with open(self.file) as file:
			config = json.load(file)
		choices = ['Back', 'Add account', 'Remove account']
		for account in config:
			choices.append(account)
		select = inquirer.list_input("Move ↑↓ and ENTER to select", choices = choices)
		if select == "Back":
			return
		elif select == "Add account":
			self.add_account()
		elif select == "Remove account":
			self.remove_account()
		else:
			self.edit_account(select)
		self.homepage()

	def add_account(self):
		with open(self.file) as file:
			config = json.load(file)
		while True:
				token = input("[!] Enter a discord token: ")
				if not token == "" and not " " in token:
					break
				print("[-] Token mustn't be empty or have spaces")
		account = {token: self.template}
		config.update(account)
		with open(self.file, "w") as file:
			json.dump(config, file, indent = 4)
		print("[+] Added a new account")
		self.edit_account(token, True)

	def remove_account(self):
		with open(self.file) as file:
			config = json.load(file)
		choices = []
		for account in config:
			choices.append(account)
		select = inquirer.checkbox("Move ↑↓ and SPACE to choose, then ENTER to select", choices = choices)
		amount = 0
		for account in select:
			amount += 1
			del config[account]
		with open(self.file, 'w') as file:
			json.dump(config, file, indent = 4)
		if amount > 0:
			print(f"[-] Removed {amount} {'account' if amount == 1 else 'account'}")

	def edit_account(self, token, select_all = False):
		with open(self.file) as file:
			config = json.load(file)

		if not select_all:
			select = inquirer.checkbox("Move ↑↓ and SPACE to choose, then ENTER to select", choices = self.features)
			if "Select all" in select:
				select_all = True

		if select_all or "Error retry times" in select:
			self.error_retry_times(token, config)
			print()

		if select_all or "Emoji" in select:
			self.emoji(token, config)
			print()

		if select_all or "Notification (Play music)" in select:
			self.notification(token, config)
			print()

		if select_all or "History (File - Discord)" in select:
			self.history(token, config)
			print()

		if select_all or "Command" in select:
			self.command(token, config)
			print()

		if select_all or "Sleep after certain time" in select:
			self.sleep(token, config)
			print()

		if select_all or "Detect problem (Banned - No cowoncy)" in select:
			self.problem(token, config)
			print()

		if select_all or "Captcha (Detect - Solve - Pause)" in select:
			self.captcha(token, config)
			print()

		if select_all or "Get OwO prefix" in select:
			self.get_owo_prefix(token, config)
			print()

		if select_all or "Check OwO status" in select:
			self.check_owo_status(token, config)
			print()

		if select_all or "Join OwO giveaway" in select:
			self.join_owo_giveaway(token, config)
			print()

		if select_all or "Channel (ID - Mention - Chanllenge)" in select:
			self.channel(token, config)
			print()

		if select_all or "Vote top.gg (Require chorme)" in select:
			self.vote_topgg(token, config)
			print()

		if select_all or "Claim daily" in select:
			self.claim_daily(token, config)
			print()

		if select_all or "Do quest" in select:
			self.do_quest(token, config)
			print()

		if select_all or "Grind (OwO/UwU - Hunt - Battle - Quote)" in select:
			self.grind(token, config)
			print()

		if select_all or "Huntbot (Claim - Sumbit - Upgrade)" in select:
			self.huntbot(token, config)
			print()

		if select_all or "Use gem (Box - Crate - Flootbox - Glitch)" in select:
			self.use_gem(token, config)
			print()

		if select_all or "Sell/Sacrifice animal" in select:
			self.sell_sacrifice_animal(token, config)
			print()

		if select_all or "Notify caught animal" in select:
			self.notify_caught_animal(token, config)
			print()

		if select_all or "Gamble (Slot - Coinflip - Blackjack)" in select:
			self.gamble(token, config)
			print()

		if select_all or "Minigame (Pray/Curse - Others)" in select:
			self.minigame(token, config)
			print()

		with open(self.file, 'w') as file:
			json.dump(config, file, indent = 4)
		print("[+] Saved!")
	
	def error_retry_times(self, token, config):
		while True:
			try:
				config[token]['error_retry_times'] = int(inquirer.prompt([inquirer.Text("", message = "Enter error retry times", default = config[token]['error_retry_times'])])[""])
				break
			except ValueError:
				print("Must be a number")

	def emoji(self, token, config):
		config[token]['emoji']['arrow'] = inquirer.prompt([inquirer.Text("", message = "Enter arrow emoji", default = config[token]['emoji']['arrow'])])[""]

	def notification(self, token, config):
		config[token]['notification']['play_music']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Play music", default = config[token]['notification']['play_music']['mode'])])[""]
		if config[token]['notification']['play_music']['mode']:
			config[token]['notification']['play_music']['directory'] = inquirer.prompt([inquirer.Text("", message = "Enter directory music", default = config[token]['notification']['play_music']['directory'])])[""]

	def history(self, token, config):
		config[token]['history']['file']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Log history as file", default = config[token]['history']['file']['mode'])])[""]
		if config[token]['history']['file']['mode']:
			config[token]['history']['file']['directory'] = inquirer.prompt([inquirer.Text("", message = "Enter directory file", default = config[token]['history']['file']['directory'])])[""]
		config[token]['history']['discord']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Log history as discord webhook", default = config[token]['history']['discord']['mode'])])[""]
		if config[token]['history']['discord']['mode']:
			while True:
				try:
					config[token]['history']['discord']['target'] = list(map(int, [x.strip() for x in inquirer.prompt([inquirer.Text("", message = "Enter user ID will be notified (Separated by comma)", default = ", ".join(map(str, config[token]['history']['discord']['target'])))])[""].split(",") if x.strip()]))
					break
				except ValueError:
					print("Must be a number")
			config[token]['history']['discord']['webhook_url'] = inquirer.prompt([inquirer.Text("", message = "Enter webhook url", default = config[token]['history']['discord']['webhook_url'])])[""]

	def command(self, token, config):
		config[token]['command']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Selfbot command", default = config[token]['command']['mode'])])[""]
		if config[token]['command']['mode']:
			while True:
				try:
					config[token]['command']['target'] = list(map(int, [x.strip() for x in inquirer.prompt([inquirer.Text("", message = "Enter user ID can use command (Separated by comma)", default = ", ".join(map(str, config[token]['command']['target'])))])[""].split(",") if x.strip()]))
					break
				except ValueError:
					print("Must be a number")

	def sleep(self, token, config):
		config[token]['sleep_after_certain_time']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Sleep after certain time", default = config[token]['sleep_after_certain_time']['mode'])])[""]
		if config[token]['sleep_after_certain_time']['mode']:
			while True:
				try:
					config[token]['sleep_after_certain_time']['sleep']['min'] = int(inquirer.prompt([inquirer.Text("", message = "Enter min sleep time", default = config[token]['sleep_after_certain_time']['sleep']['min'])])[""])
					break
				except ValueError:
					print("Must be a number")
			while True:
				try:
					config[token]['sleep_after_certain_time']['sleep']['max'] = int(inquirer.prompt([inquirer.Text("", message = "Enter max sleep time", default = config[token]['sleep_after_certain_time']['sleep']['max'])])[""])
					break
				except ValueError:
					print("Must be a number")
			while True:
				try:
					config[token]['sleep_after_certain_time']['work']['min'] = int(inquirer.prompt([inquirer.Text("", message = "Enter min work time", default = config[token]['sleep_after_certain_time']['work']['min'])])[""])
					break
				except ValueError:
					print("Must be a number")
			while True:
				try:
					config[token]['sleep_after_certain_time']['work']['max'] = int(inquirer.prompt([inquirer.Text("", message = "Enter max work time", default = config[token]['sleep_after_certain_time']['work']['max'])])[""])
					break
				except ValueError:
					print("Must be a number")

	def problem(self, token, config):
		config[token]['problem']['banned'] = inquirer.prompt([inquirer.Confirm("", message = "Stop when have been banned", default = config[token]['problem']['banned'])])[""]
		config[token]['problem']['no_cowoncy'] = inquirer.prompt([inquirer.Confirm("", message = "Stop when run out of cowoncy", default = config[token]['problem']['no_cowoncy'])])[""]

	def captcha(self, token, config):
		config[token]['captcha']['solve_image_captcha']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Solve image captcha", default = config[token]['captcha']['solve_image_captcha']['mode'])])[""]
		if config[token]['captcha']['solve_image_captcha']['mode']:
			config[token]['captcha']['solve_image_captcha']['attempt'] = int(inquirer.prompt([inquirer.Text("", message = "Enter number of attempts for image captcha", default = config[token]['captcha']['solve_image_captcha']['attempt'])])[""])
			config[token]['captcha']['solve_image_captcha']['sleep_after_solve'] = inquirer.prompt([inquirer.Confirm("", message = "Sleep after solve image captcha", default = config[token]['captcha']['solve_image_captcha']['sleep_after_solve'])])[""]
			config[token]['captcha']['solve_image_captcha']['twocaptcha'] = [x.strip() for x in inquirer.prompt([inquirer.Text("", message = "Enter the image captcha TwoCaptcha API (Separated by comma)", default = ", ".join(map(str, config[token]['captcha']['solve_image_captcha']['twocaptcha'])))])[""].split(",") if x.strip()]
		config[token]['captcha']['solve_hcaptcha']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Solve hcaptcha", default = config[token]['captcha']['solve_hcaptcha']['mode'])])[""]
		if config[token]['captcha']['solve_hcaptcha']['mode']:
			config[token]['captcha']['solve_hcaptcha']['attempt'] = int(inquirer.prompt([inquirer.Text("", message = "Enter number of attempts for hcaptcha", default = config[token]['captcha']['solve_hcaptcha']['attempt'])])[""])
			config[token]['captcha']['solve_hcaptcha']['sleep_after_solve'] = inquirer.prompt([inquirer.Confirm("", message = "Sleep after solve hcaptcha", default = config[token]['captcha']['solve_hcaptcha']['sleep_after_solve'])])[""]
			config[token]['captcha']['solve_hcaptcha']['twocaptcha'] = [x.strip() for x in inquirer.prompt([inquirer.Text("", message = "Enter the hcaptcha TwoCaptcha API (Separated by comma)", default = ", ".join(map(str, config[token]['captcha']['solve_hcaptcha']['twocaptcha'])))])[""].split(",") if x.strip()]
			config[token]['captcha']['pause_if_twocaptcha_balance_is_low']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Pause if TwoCaptcha balance is low", default = config[token]['captcha']['pause_if_twocaptcha_balance_is_low']['mode'])])[""]
		if config[token]['captcha']['pause_if_twocaptcha_balance_is_low']['mode']:
			while True:
				try:
					config[token]['captcha']['pause_if_twocaptcha_balance_is_low']['amount'] = float(inquirer.prompt([inquirer.Text("", message = "Enter minimum amount to pause", default = config[token]['captcha']['pause_if_twocaptcha_balance_is_low']['amount'])])[""])
					break
				except ValueError:
					print("[-] Must be a number")

	def get_owo_prefix(self, token, config):
		config[token]['get_owo_prefix']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Get OwO prefix", default = config[token]['get_owo_prefix']['mode'])])[""]
		if not config[token]['get_owo_prefix']['mode']:
			config[token]['get_owo_prefix']['default'] = inquirer.prompt([inquirer.Text("", message = "Enter OwO prefix as default", default = config[token]['get_owo_prefix']['default'])])[""]

	def check_owo_status(self, token, config):
		config[token]['check_owo_status']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Check OwO status", default = config[token]['check_owo_status']['mode'])])[""]
		if config[token]['check_owo_status']['mode']:
			while True:
				try:
					config[token]['check_owo_status']['wait_time'] = int(inquirer.prompt([inquirer.Text("", message = "Enter time to recheck", default = config[token]['check_owo_status']['wait_time'])])[""])
					break
				except ValueError:
					print("[-] Must be a number")
			config[token]['check_owo_status']['message'] = [x.strip() for x in inquirer.prompt([inquirer.Text("", message = "Enter the command to check (Separated by comma)", default = ", ".join(map(str, config[token]['check_owo_status']['message'])))])[""].split(",") if x.strip()]


	def join_owo_giveaway(self, token, config):
		config[token]['join_owo_giveaway']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Join OwO giveaway", default = config[token]['join_owo_giveaway']['mode'])])[""]
		if config[token]['join_owo_giveaway']['mode']:
			while True:
				try:
					config[token]['join_owo_giveaway']['channel_id_blacklist'] = list(map(int, [x.strip() for x in inquirer.prompt([inquirer.Text("", message = "Enter channel id blacklist (Separated by comma)", default = ", ".join(map(str, config[token]['join_owo_giveaway']['channel_id_blacklist'])))])[""].split(",") if x.strip()]))
					break
				except ValueError:
					print("Must be a number")

	def channel(self, token, config):
		while True:
			try:
				config[token]['channel']['id_list'] = list(map(int, [x.strip() for x in inquirer.prompt([inquirer.Text("", message = "Enter channel id to start (Separated by comma)", default = ", ".join(map(str, config[token]['channel']['id_list'])))])[""].split(",") if x.strip()]))
				break
			except ValueError:
				print("Must be a number")
		config[token]['channel']['change_when_be_mentioned'] = inquirer.prompt([inquirer.Confirm("", message = "Change channel when be mentioned", default = config[token]['channel']['change_when_be_mentioned'])])[""]
		config[token]['channel']['change_when_be_challenged'] = inquirer.prompt([inquirer.Confirm("", message = "Change channel when be challenged", default = config[token]['channel']['change_when_be_challenged'])])[""]

	def vote_topgg(self, token, config):
		config[token]['vote_topgg']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Vote OwO top.gg", default = config[token]['vote_topgg']['mode'])])[""]
		if config[token]['vote_topgg']['mode']:
			config[token]['vote_topgg']['display'] = inquirer.prompt([inquirer.Confirm("", message = "Display progress screen", default = config[token]['vote_topgg']['display'])])[""]

	def claim_daily(self, token, config):
		config[token]['claim_daily']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Claim daily", default = config[token]['claim_daily']['mode'])])[""]
		if config[token]['claim_daily']['mode']:
			for key in ['hour', 'minute', 'second', 'microsecond']:
				while True:
					try:
						config[token]['claim_daily']['reset_UTC_time'][key] = int(inquirer.prompt([inquirer.Text("", message = f"Enter the {key} of reset UTC time", default = str(config[token]['claim_daily']['reset_UTC_time'][key]))])[""])
						break
					except ValueError:
						print("[-] Must be a number")

	def do_quest(self, token, config):
		config[token]['do_quest']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Do quest", default = config[token]['do_quest']['mode'])])[""]
		if config[token]['do_quest']['mode']:
			config[token]['do_quest']['safe'] = inquirer.prompt([inquirer.Confirm("", message = "Safe mode", default = config[token]['do_quest']['safe'])])[""]
			while True:
				try:
					config[token]['do_quest']['channel_id'] = list(map(int, [x.strip() for x in inquirer.prompt([inquirer.Text("", message = "Enter the channel id to do quest (Separated by comma)", default = ", ".join(map(str, config[token]['do_quest']['channel_id'])))])[""].split(",") if x.strip()]))
					break
				except ValueError:
					print("Must be a number")
			config[token]['do_quest']['action'] = [x.strip() for x in inquirer.prompt([inquirer.Text("", message = "Enter the quest action (Separated by comma)", default = ", ".join(map(str, config[token]['do_quest']['action'])))])[""].split(",") if x.strip()]

	def grind(self, token, config):
		config[token]['grind']['owo']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Send OwO/UwU", default = config[token]['grind']['owo']['mode'])])[""]
		if config[token]['grind']['owo']['mode']:
			config[token]['grind']['owo']['message'] = [x.strip() for x in inquirer.prompt([inquirer.Text("", message = "Enter OwO/UwU message (Separated by comma)", default = ", ".join(map(str, config[token]['grind']['owo']['message'])))])[""].split(",") if x.strip()]
		config[token]['grind']['hunt']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Hunt", default = config[token]['grind']['hunt']['mode'])])[""]
		if config[token]['grind']['hunt']['mode']:
			config[token]['grind']['hunt']['message'] = [x.strip() for x in inquirer.prompt([inquirer.Text("", message = "Enter hunt message (Separated by comma)", default = ", ".join(map(str, config[token]['grind']['hunt']['message'])))])[""].split(",") if x.strip()]
		config[token]['grind']['battle']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Battle", default = config[token]['grind']['battle']['mode'])])[""]
		if config[token]['grind']['battle']['mode']:
			config[token]['grind']['battle']['message'] = [x.strip() for x in inquirer.prompt([inquirer.Text("", message = "Enter battle message (Separated by comma)", default = ", ".join(map(str, config[token]['grind']['battle']['message'])))])[""].split(",") if x.strip()]
		config[token]['grind']['quote']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Send quote", default = config[token]['grind']['quote']['mode'])])[""]
		if config[token]['grind']['quote']['mode']:
			config[token]['grind']['quote']['api'] = inquirer.prompt([inquirer.Text("", message = "Quote API", default = config[token]['grind']['quote']['api'])])[""]
			config[token]['grind']['quote']['path'] = inquirer.prompt([inquirer.Text("", message = "Quote API path", default = config[token]['grind']['quote']['path'])])[""]

	def huntbot(self, token, config):
		config[token]['huntbot']['claim_submit'] = inquirer.prompt([inquirer.Confirm("", message = "Claim/Sumbit huntbot", default = config[token]['huntbot']['claim_submit'])])[""]
		if config[token]['huntbot']['claim_submit']:
			config[token]['huntbot']['directory'] = inquirer.prompt([inquirer.Text("", message = "Huntbot solver directory", default = config[token]['huntbot']['directory'])])[""]
			config[token]['huntbot']['upgrade']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Upgrade huntbot", default = config[token]['huntbot']['upgrade']['mode'])])[""]
			if config[token]['huntbot']['upgrade']['mode']:
				config[token]['huntbot']['upgrade']['type'] = inquirer.prompt([inquirer.Text("", message = "Huntbot upgrade type", default = config[token]['huntbot']['upgrade']['type'])])[""]

	def use_gem(self, token, config):
		config[token]['use_gem']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Use gem", default = config[token]['use_gem']['mode'])])[""]
		if config[token]['use_gem']['mode']:
			config[token]['use_gem']['sort'] = inquirer.prompt([inquirer.Text("", message = "Gem sort (max/min)", default = config[token]['use_gem']['sort'])])[""]
			config[token]['use_gem']['star'] = inquirer.prompt([inquirer.Confirm("", message = "Use star gem", default = config[token]['use_gem']['star'])])[""]
			config[token]['use_gem']['open_box'] = inquirer.prompt([inquirer.Confirm("", message = "Open box", default = config[token]['use_gem']['open_box'])])[""]
			config[token]['use_gem']['open_crate'] = inquirer.prompt([inquirer.Confirm("", message = "Open crate", default = config[token]['use_gem']['open_crate'])])[""]
			config[token]['use_gem']['open_flootbox'] = inquirer.prompt([inquirer.Confirm("", message = "Open flootbox", default = config[token]['use_gem']['open_flootbox'])])[""]
		else:
			config[token]['use_gem']['use_gem_when_glitch_available'] = inquirer.prompt([inquirer.Confirm("", message = "Use gem when glitch available", default = config[token]['use_gem']['use_gem_when_glitch_available'])])[""]

	def notify_caught_animal(self, token, config):
		config[token]['notify_caught_animal']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Notify caught animal", default = config[token]['notify_caught_animal']['mode'])])[""]
		if config[token]['notify_caught_animal']['mode']:
			print("Notify caught animal coming soon ...")

	def sell_sacrifice_animal(self, token, config):
		config[token]['sell_sac_animal']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Sell/Sacrifice animal", default = config[token]['sell_sac_animal']['mode'])])[""]
		if config[token]['sell_sac_animal']['mode']:
			config[token]['sell_sac_animal']['type'] = inquirer.prompt([inquirer.Text("", message = "Type", default = config[token]['sell_sac_animal']['type'])])[""]
			config[token]['sell_sac_animal']['rank'] = inquirer.prompt([inquirer.Text("", message = "Rank", default = config[token]['sell_sac_animal']['rank'])])[""]

	def gamble_filter(self, name, data):
		while True:
			try:
				data['bet'] = int(inquirer.prompt([inquirer.Text("", message = f"Enter the amount of cowoncy to start bet {name}", default = data['bet'])])[""])
				break
			except ValueError:
				print("[-] Must be a number")
		while True:
			try:
				data['rate'] = int(inquirer.prompt([inquirer.Text("", message = f"[!] Enter the rate number to multiply when lose on {name}", default = data['rate'])])[""])
				break
			except ValueError:
				print("[-] Must be a number")
		while True:
			try:
				data['max'] = int(inquirer.prompt([inquirer.Text("", message = f"[!] Enter the amount of maximum bet {name}", default = data['max'])])[""])
				break
			except ValueError:
				print("[-] Must be a number")

	def gamble(self, token, config):
		config[token]['gamble']['slot']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Slot", default = config[token]['gamble']['slot']['mode'])])[""]
		if config[token]['gamble']['slot']['mode']:
			self.gamble_filter("slot", config[token]['gamble']['slot'])
		config[token]['gamble']['coinflip']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Coinflip", default = config[token]['gamble']['coinflip']['mode'])])[""]
		if config[token]['gamble']['coinflip']['mode']:
			self.gamble_filter("coinflip", config[token]['gamble']['coinflip'])
		config[token]['gamble']['blackjack']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Blackjack", default = config[token]['gamble']['blackjack']['mode'])])[""]
		if config[token]['gamble']['blackjack']['mode']:
			self.gamble_filter("blackjack", config[token]['gamble']['blackjack'])

	def minigame(self, token, config):
		config[token]['minigame']['pray_curse']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "Pray/Curse", default = config[token]['minigame']['pray_curse']['mode'])])[""]
		if config[token]['minigame']['pray_curse']['mode']:
			config[token]['minigame']['pray_curse']['type'] = inquirer.prompt([inquirer.Text("", message = "Type", default = config[token]['minigame']['pray_curse']['type'])])[""]
			config[token]['minigame']['pray_curse']['target'] = inquirer.prompt([inquirer.Text("", message = "Rank", default = config[token]['minigame']['pray_curse']['target'])])[""]
		config[token]['minigame']['others']['run'] = inquirer.prompt([inquirer.Confirm("", message = "Run", default = config[token]['minigame']['others']['run'])])[""]
		config[token]['minigame']['others']['pup'] = inquirer.prompt([inquirer.Confirm("", message = "Pup", default = config[token]['minigame']['others']['pup'])])[""]
		config[token]['minigame']['others']['piku'] = inquirer.prompt([inquirer.Confirm("", message = "Piku", default = config[token]['minigame']['others']['piku'])])[""]
		config[token]['minigame']['others']['common_ring'] = inquirer.prompt([inquirer.Confirm("", message = "Buy Common ring", default = config[token]['minigame']['others']['common_ring'])])[""]