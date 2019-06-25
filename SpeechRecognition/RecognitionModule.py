class Recognizer:
	def __init__(self, language):
		self.language = language


	def processAudio(self, record):
		raise NotImplementedError


	def processAudioFile(self, file):
		raise NotImplementedError


	def processMicrophone(self):
		raise NotImplementedError