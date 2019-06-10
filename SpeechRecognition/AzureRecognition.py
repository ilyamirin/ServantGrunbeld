import os, sys
import requests

import azure.cognitiveservices.speech as speechsdk


currpath = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(currpath, ".."))

from Microphone import MicrophoneRecorder
import SpeechRecognition.Config as CFG

sys.path.pop()


class BadFileFormat(Exception):
	pass


class AzureRecognizer:
	def __init__(self, key=CFG.SUBSCRIPTION_KEY, region=CFG.SERVICE_REGION, language=CFG.RUS,
	             responseFormat=CFG.DETAILED):
		self.key = key
		self.region = region

		self.language = language
		self.format = responseFormat

		self.recognizer = self.__initRecognizer(self.key, self.region)
		self.microphone = MicrophoneRecorder()

		self.REST = {
			"base": CFG.REST_BASE_URL,
			"path": CFG.REST_PATH
		}


	def __initRecognizer(self, key, region):
		speechConfig = speechsdk.SpeechConfig(subscription=key, region=region,
		                                      speech_recognition_language=self.language)

		recognizer = speechsdk.SpeechRecognizer(speech_config=speechConfig)

		return recognizer


	def __sendRequest(self, data):
		# TODO нужно ограничть длину записи до 10 секунд (требования rest api azure),
		#  либо использовать другой вид запроса
		headers = {
			"Ocp-Apim-Subscription-Key": self.key,
			"Content-type": "audio/wav; codecs=audio/pcm; samplerate=16000",
			"Accept": "application/json"
		}

		fullRequest = "{}/{}?language={}&format={}".format(self.REST["base"], self.REST["path"],
		                                                   self.language, self.format)
		response = requests.post(fullRequest, headers=headers, data=data)

		return response


	def _handleResponseREST(self, code):
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


	def processMicrophoneSDK(self):
		return self.recognizer.recognize_once()


	def processAudio(self, record):
		if not isinstance(record, bytes):
		#TODO у аудио-дорожки должны быть определённые характеристики: битрейт и кодек
			raise TypeError("Method takes either sound bytearray or .wav file")

		response = self.__sendRequest(record)
		self._handleResponseREST(response.status_code)

		result = response.json().get("NBest", "")
		if result != "":
			result = result[0]["Display"]

		return result


	def processMicrophoneREST(self):
		self.microphone.initPipe()
		record = self.microphone.record()

		result = self.processAudio(record)

		return result


	def processAudioFile(self, record):
		if not record.endswith(".wav"):
			raise BadFileFormat("File format has to be .wav")

		with open(record, "rb") as rec:
			record = rec.read()

		result = self.processAudio(record)

		return result


	def handleResponseSDK(self, result):
		if result.reason == speechsdk.ResultReason.RecognizedSpeech:
			print("Recognized: {}".format(result.text))
		elif result.reason == speechsdk.ResultReason.NoMatch:
			print("No speech could be recognized: {}".format(result.no_match_details))
		elif result.reason == speechsdk.ResultReason.Canceled:
			cancellation_details = result.cancellation_details
			print("Speech Recognition canceled: {}".format(cancellation_details.reason))
			if cancellation_details.reason == speechsdk.CancellationReason.Error:
				print("Error details: {}".format(cancellation_details.error_details))


def testAzureSDK(recognizer):
	attempts = 3

	print("Here you go")
	for _ in range(attempts):
		result = recognizer.processMicrophoneSDK()
		recognizer.handleResponseSDK(result)


def testAzureREST(recognizer):
	attempts = 3

	print("Here you go")
	for _ in range(attempts):
		result = recognizer.processMicrophoneREST()
		print("Recognized:", result)


def main():
	recognizer = AzureRecognizer()

	testAzureSDK(recognizer)
	testAzureREST(recognizer)
	# result = recognizer.processAudioFile(r"D:\git_projects\FEFU\AssistantPipeline\Temp\new_record.wav")
	# print(result)


if __name__ == "__main__":
	main()