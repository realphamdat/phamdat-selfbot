import json
import inquirer

from manager.owo import OwOManager

class Setup:
	def __init__(self):
		self.file = "setting/config.json"

	def homepage(self):
		with open(self.file) as file:
			config = json.load(file)
		select = inquirer.list_input("Move ↑↓ and ENTER to select", choices = ['API', 'Key', 'Template', 'OwO'])
		if select == "API":
			config['api'] = inquirer.prompt([inquirer.Text("", message = "Enter API", default = config['api'])])[""]
		if select == "Key":
			config['key'] = inquirer.prompt([inquirer.Text("", message = "Enter key", default = config['key'])])[""]
		if select == "Template":
			config['template'] = inquirer.prompt([inquirer.Text("", message = "Enter template", default = config['template'])])[""]
		if select == "OwO":
			self.owo()
		with open(self.file, "w") as file:
			json.dump(config, file, indent = 4)
		print("[+] Saved!")
		self.homepage()

	def owo(self):
		with open(self.file) as file:
			config = json.load(file)
		select = inquirer.list_input("Move ↑↓ and ENTER to select", choices = ['Back', 'Manage', 'Mode', 'Directory'])
		if select == "Back":
			return
		if select == "Manage":
			OwOManager(config).homepage()
		if select == "Mode":
			config['owo']['mode'] = inquirer.prompt([inquirer.Confirm("", message = "OwO mode", default = config['owo']['mode'])])[""]
		if select == "Directory":
			config['owo']['directory'] = inquirer.prompt([inquirer.Text("", message = "Enter OwO directory", default = config['owo']['directory'])])[""]
		with open(self.file, "w") as file:
			json.dump(config, file, indent = 4)
		print("[+] Saved!")
		self.owo()

if __name__ == "__main__":
	Setup().homepage()