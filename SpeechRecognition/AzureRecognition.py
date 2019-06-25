import requests

try:
	import azure.cognitiveservices.speech as speechsdk
	hasAzureSDK = True
except ImportError:
	hasAzureSDK = False

from Microphone import MicrophoneRecorder

try:
	from .Config import AzureCredentials, AzureConfig
	from .RecognitionModule import Recognizer
except ImportError:
	from Config import AzureCredentials, AzureConfig
	from RecognitionModule import Recognizer


class BadFileFormat(Exception):
	pass


class PackageIsNotInstalled(Exception):
	pass


class AzureRecognizer(Recognizer):
	def __init__(self, key=AzureCredentials.SUBSCRIPTION_KEY, region=AzureCredentials.SERVICE_REGION,
	             language=AzureConfig.LANG_RUS, responseFormat=AzureConfig.RESPONSE_DETAILED):

		super().__init__(language=language)

		self.key = key
		self.region = region

		self.format = responseFormat

		self.recognizer = self._initRecognizer(self.key, self.region)
		self.microphone = MicrophoneRecorder()

		self.REST = {
			"base": AzureConfig.REST_BASE_URL,
			"path": AzureConfig.REST_PATH
		}


	def _initRecognizer(self, key, region):
		speechConfig = speechsdk.SpeechConfig(subscription=key, region=region,
		                                      speech_recognition_language=self.language)

		recognizer = speechsdk.SpeechRecognizer(speech_config=speechConfig)

		return recognizer


	def _sendRequest(self, data):
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


	def processAudio(self, record):
		if not isinstance(record, bytes):
		#TODO у аудио-дорожки должны быть определённые характеристики: битрейт и кодек
			raise TypeError("Method takes either sound bytearray or .wav file")

		response = self._sendRequest(record)
		self._handleResponseREST(response.status_code)

		result = response.json().get("NBest", "")
		if result != "":
			result = result[0]["Display"]

		return result


	def processMicrophoneSDK(self):
		if hasAzureSDK:
			return self.recognizer.recognize_once()
		else:
			raise PackageIsNotInstalled("Azure cognitive speech SDK is not installed")


	def processMicrophone(self):
		self.microphone.initPipe()
		record = self.microphone.record()

		result = self.processAudio(record)

		return result


	def processAudioFile(self, file):
		if not file.endswith(".wav"):
			raise BadFileFormat("File format has to be .wav")

		with open(file, "rb") as rec:
			file = rec.read()

		result = self.processAudio(file)

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
		result = recognizer.processMicrophone()
		print("Recognized:", result)


def main():
	recognizer = AzureRecognizer()

	# testAzureSDK(recognizer)
	testAzureREST(recognizer)
	# result = recognizer.processAudioFile(r"D:\git_projects\FEFU\AssistantPipeline\Temp\new_record.wav")
	# print(result)


if __name__ == "__main__":
	main()