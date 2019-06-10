import os, sys
import requests
import time

from xml.etree import ElementTree

currpath = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(currpath, ".."))

from AudioPlayer import Player
import SpeechSynthesis.Config as CFG

sys.path.pop()


class AzureSynthesizer:
	def __init__(self, key=CFG.SUBSCRIPTION_KEY, region=CFG.SERVICE_REGION, language=CFG.RUS):
		self.key = key
		self.region = region

		self.language = language

		self.token = None

		self.voices = {}

		self.REST = {
			"base": CFG.REST_BASE_URL,
			"path": CFG.REST_PATH,
			"voices": CFG.VOICES_PATH
		}

		self.player = Player()

		self.__getToken()
		self.__getVoices()


	def __getToken(self):
		fetch_token_url = "https://{}.api.cognitive.microsoft.com/sts/v1.0/issueToken".format(self.region)

		headers = {
			"Ocp-Apim-Subscription-Key": self.key
		}

		response = requests.post(fetch_token_url, headers=headers)
		self.token = str(response.text)


	def __getVoices(self):
		fullUrl = "{}/{}".format(self.REST["base"], self.REST["voices"])

		headers = {
			"Authorization": "Bearer " + self.token
		}
		response = requests.get(fullUrl, headers=headers)

		if response.status_code == 200:
			self.voices = response.json()
			self.voices = [k for k in response.json() if k["Locale"] == self.language]
			self.voices = ["-".join(value["ShortName"].split("-")[2:]) for value in self.voices]
		else:
			print("\nStatus code: " + str(
				response.status_code) + "\nSomething went wrong. Check your subscription key and headers.\n")


	def audioToFile(self, content, wpath, fileName):
		wpath = "./Temp" if wpath is None else wpath
		fileName = "sample-{}.wav".format(time.strftime("%Y%m%d-%H%M")) if fileName is None else fileName

		assert isinstance(wpath, str)
		assert isinstance(fileName, str) and fileName.endswith("./wav")

		with open(os.path.join(wpath, fileName), "wb") as audio:
			audio.write(content)


	def process(self, text, voiceIdx=0, play=True, toFile=False, **params):
		wpath = params.get("wpath", None)
		fileName = params.get("fileName", None)

		if text == "":
			print("There is no text to make synthesis")
			return

		fullUrl = "{}/{}".format(self.REST["base"], self.REST["path"])

		headers = {
			"Authorization": "Bearer " + self.token,
			"Content-Type": "application/ssml+xml",
			"X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm",
			"User-Agent": "SpeechProcessing"
		}

		xml_body = ElementTree.Element("speak", version="1.0")
		xml_body.set("{http://www.w3.org/XML/1998/namespace}lang", self.language)
		
		voice = ElementTree.SubElement(xml_body, "voice")
		voice.set("{http://www.w3.org/XML/1998/namespace}lang", self.language)
		voice.set("name", "Microsoft Server Speech Text to Speech Voice "
		                  "({}, {})".format(self.language, self.voices[voiceIdx]))
		voice.text = text
		
		body = ElementTree.tostring(xml_body)

		response = requests.post(fullUrl, headers=headers, data=body)

		if response.status_code == 200:
			result = response.content
			if play:
				self.player.playAudio(result)
			if toFile:
				self.audioToFile(result, wpath, fileName)
		else:
			print("\nStatus code: " + str(
				response.status_code) + "\nSomething went wrong. Check your subscription key and headers.\n")

			return

		return result


def test():
	synthesizer = AzureSynthesizer()

	attempts = 3

	print("Here you go")
	for _ in range(attempts):
		text = input()
		synthesizer.process(text)


if __name__ == "__main__":
	test()