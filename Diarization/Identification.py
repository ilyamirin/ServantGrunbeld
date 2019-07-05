from Microphone import MicrophoneRecorder


class SpeakerIdentifier:
	def __init__(self):
		self.microphone = MicrophoneRecorder()


	def identify(self, vector):
		raise NotImplementedError


	def identifyViaMicrophone(self):
		raise NotImplementedError


	def identifyViaFile(self, filepath):
		raise NotImplementedError


	def enroll(self, name, vector):
		raise NotImplementedError


	def enrollFromMicrophone(self):
		pass


	def enrollFromFolder(self, name, folder):
		raise NotImplementedError