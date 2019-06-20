import requests

import hashlib
import json

try:
	from .Config import CompanionConfig as CFG
except ImportError:
	from Config import CompanionConfig as CFG


class Companion:
	def __init__(self, dtype=CFG.GOPNIK, name="new_bot"):
		self.name = name

		self.uuid = None
		self.pubkey = None

		self.cuid = None
		self.sign = None

		self.dialog = []

		self.__intiCore(dtype)


	def __setSign(self):
		self.sign = hashlib.md5((self.uuid + "" + self.pubkey).encode()).hexdigest()


	def __setCuid(self):
		self.__setSign()
		headers = {
			"Content-Type": "application/json",
			"X-ApiKey": self.pubkey
		}

		data = json.dumps({
			"uuid": self.uuid,
			"sign": self.sign
		})

		response = requests.post(CFG.NANOSEM_URL_INIT, headers=headers, data=data)
		self.cuid = response.json()["result"]["cuid"]


	def __intiCore(self, dtype):
		self.uuid = None
		self.pubkey = None

		if dtype == CFG.GOPNIK:
			self.uuid = CFG.GOPNIK_UUID
			self.pubkey = CFG.GOPNIK_PUBKEY
		elif dtype == CFG.BLOND:
			self.uuid = CFG.BLOND_UUID
			self.pubkey = CFG.BLOND_PUBKEY
		else:
			raise TypeError

		self.__setCuid()

		# print("Companion is ready to chat")


	def __responseHandler(self, code):
		if code == 200:
			return
		elif code == 404:
			print("Bad request")
		elif code == 401:
			print("Not authorized")
		elif code == 403:
			print("Access is forbidden")
		elif code == 404:
			print("Not found")


	def printDialog(self):
		for i in self.dialog:
			print(i)


	def send(self, text):
		data = json.dumps({
			"cuid": self.cuid,
			"sign": self.sign,
			"text": text
		})

		headers = {
			"Content-Type": "application/json",
			"X-ApiKey": self.pubkey
		}

		response = requests.post(url=CFG.NANOSEM_URL_REQ, data=data, headers=headers)
		self.__responseHandler(response.status_code)

		response = response.json()["result"]["text"]["value"]

		self.dialog.extend(["YOU: {}".format(text), "BOT: {}".format(response)])

		return response


def test():
	companion = Companion()

	print("Ready to chat")
	while True:
		text = input()
		result = companion.send(text)
		print(result)


if __name__ == "__main__":
	test()