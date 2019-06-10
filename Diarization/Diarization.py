from Microphone import MicrophoneRecorder


class BadFileFormat(Exception):
	pass


class Diarizatorr:
	def __init__(self):
		self.microphone = MicrophoneRecorder()


	def processMicrophone(self):
		self.microphone.initPipe()
		record = self.microphone.record()

		result = self.processAudioFile(record)

		return result


	def processAudioFile(self, record):
		# диаризируем и, по идее, получаем лист сегментированных дорожек

		result = [None, None]

		return result