import io

import pyaudio
import wave


class BadFileFormat(Exception):
	pass


class Player:
	def __init__(self, chunkSize=1024, initPipe=False):
		self.chunkSize = chunkSize
		self.pipe = None

		self.pipeIsOpened = False

		if initPipe:
			self.initPipe()


	def initPipe(self):
		self.pipe = pyaudio.PyAudio()
		self.pipeIsOpened = True


	def terminatePipe(self):
		self.pipe.terminate()
		self.pipeIsOpened = False


	def playAudioFile(self, file):
		if not file.endswith(".wav"):
			raise BadFileFormat("File format has to be .wav")

		audio = wave.open(file, "rb")

		self.playAudio(audio, opened=True)

		audio.close()


	def playAudio(self, audio, opened=False):
		if not self.pipeIsOpened:
			self.initPipe()

		if not opened:
			tempFile = io.BytesIO(audio)
			audio = wave.open(tempFile, "rb")

		stream = self.pipe.open(
			format=self.pipe.get_format_from_width(audio.getsampwidth()),
			channels=audio.getnchannels(),
			rate=audio.getframerate(),
			output=True
		)

		data = audio.readframes(self.chunkSize)

		while data:
			stream.write(data)
			data = audio.readframes(self.chunkSize)

		stream.stop_stream()
		stream.close()

		self.terminatePipe()


def test():
	player = Player()
	player.playAudioFile(r"D:\git_projects\FEFU\AssistantPipeline\Temp\new_record.wav")


def testTandem():
	from Microphone import MicrophoneRecorder
	microphone = MicrophoneRecorder()
	player = Player()

	print("Please speak")
	player.playAudio(microphone.record())


if __name__ == "__main__":
	test()