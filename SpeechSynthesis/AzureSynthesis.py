import os
import requests
import time

from xml.etree import ElementTree

from AudioPlayer import Player

try:
	from .Config import AzureCredentials, AzureConfig
	from .SynthesisModule import Synthesizer
except ImportError:
	from Config import AzureCredentials, AzureConfig
	from SynthesisModule import Synthesizer


class AzureSynthesizer(Synthesizer):
	def __init__(self, key=AzureCredentials.SUBSCRIPTION_KEY, region=AzureCredentials.SERVICE_REGION,
	             language=AzureConfig.LANG_RUS):

		super().__init__(language=language)

		self.key = key
		self.region = region

		self.language = language

		self.token = None

		self.voices = {}

		self.REST = {
			"base": AzureConfig.REST_BASE_URL,
			"path": AzureConfig.REST_PATH,
			"voices": AzureConfig.VOICES_PATH
		}

		self.player = Player()

		self._getToken()
		self._getVoices()


	def _getToken(self):
		fetch_token_url = "https://{}.api.cognitive.microsoft.com/sts/v1.0/issueToken".format(self.region)

		headers = {
			"Ocp-Apim-Subscription-Key": self.key
		}

		response = requests.post(fetch_token_url, headers=headers)
		self.token = str(response.text)


	def _getVoices(self):
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
				# TODO предусмотреть случай пустой аудиодорожки
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