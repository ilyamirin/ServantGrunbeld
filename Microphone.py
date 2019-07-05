import os
import io

from sys import byteorder
from array import array
from struct import pack
from _thread import start_new_thread

import pyaudio
import wave


AUTO_SILENCE_LIMIT = "silent_counting"
AUTO_DURATION_LIMIT = "duration_limit"
MANUAL_KEYBOARD = "keyboard"



class MicrophoneRecorder:
	def __init__(self, audioFormat=pyaudio.paInt16, chunkSize=1024, rate=16000, silenceThreshold=500, initPipe=False,
	             name="your_microphone"):

		self.format = audioFormat
		self.chunkSize = chunkSize
		self.rate = rate

		self.silenceThreshold = silenceThreshold

		self.maximum = 16384

		self.pipe = None
		self.pipeIsOpened = False

		self.name = name

		if initPipe:
			self.initPipe()


	def __enter__(self):
		self.initPipe()
		return self


	def __exit__(self, type, val, traceback):
		self.terminatePipe()


	def initPipe(self):
		self.pipe = pyaudio.PyAudio()
		self.pipeIsOpened = True


	def terminatePipe(self):
		self.pipe.terminate()
		self.pipeIsOpened = False


	def _isSilent(self, soundData):
		return max(soundData) < self.silenceThreshold


	def _normalize(self, soundData):
		if len(soundData) == 0:
			print("Warning! Record is empty")
			return soundData

		ratios = float(self.maximum) / max(abs(i) for i in soundData)

		soundData = [int(i * ratios) for i in soundData]

		return soundData


	def _trim(self, soundData):
		for idx, value in enumerate(soundData):
			if abs(value) > self.silenceThreshold:
				soundData = soundData[idx:]
				break

		return soundData


	def _trimWrapper(self, soundData):
		# Trim to the left
		soundData = self._trim(soundData)

		# Trim to the right
		soundData.reverse()
		soundData = self._trim(soundData)
		soundData.reverse()

		return soundData


	def _addSilence(self, soundData, seconds):
		r = array("h", [0 for _ in range(int(seconds * self.rate))])
		r.extend(soundData)
		r.extend([0 for _ in range(int(seconds * self.rate))])
		return r


	def recordVoice(self, stream, record, mode, **kwargs):
		threshold = kwargs.get("threshold", None)

		soundStarted = False
		doRecord = True
		silentFrames = 0

		while doRecord:
			soundData = array("h", stream.read(self.chunkSize))
			if byteorder == "big":
				soundData.byteswap()

			silent = self._isSilent(soundData)

			if not silent:
				if not soundStarted:
					soundStarted = True
				else:
					record.extend(soundData)
					silentFrames = 0
			elif silent and soundStarted:
				silentFrames += 1

			if mode == MANUAL_KEYBOARD:
				doRecord = not threshold
			elif mode == AUTO_SILENCE_LIMIT:
				doRecord = silentFrames < threshold
			elif mode == AUTO_DURATION_LIMIT:
				doRecord = len(record) / self.rate < threshold
			else:
				raise ValueError


	def recordManual(self, toFile=False, wpath="./Temp", fileName="new_record.wav", normalize=True, trim=True,
	                 addSilence=True):

		if not self.pipeIsOpened:
			self.initPipe()

		stream = self.pipe.open(format=self.format, channels=1, rate=self.rate,
			                        input=True, output=True, frames_per_buffer=self.chunkSize)

		record = array("h")

		print("Press 'Enter' in command prompt to start (press 'Enter' in command prompt again to finish)")
		input()

		print("started... ", end="")

		aList = []
		start_new_thread(function=inputThread, args=(aList,))
		self.recordVoice(stream, record, MANUAL_KEYBOARD, threshold=aList)

		print("stopped")

		sampleWidth = self.pipe.get_sample_size(self.format)
		stream.stop_stream()
		stream.close()

		record = self._normalize(record) if normalize else record
		record = self._trimWrapper(record) if trim else record
		record = self._addSilence(record, 0.5) if addSilence else record

		wav = self.convertToWAV(sampleWidth, record)

		if toFile:
			self.recordToFile(wav, wpath, fileName)

		self.terminatePipe()

		return wav


	def recordAuto(self, mode=AUTO_SILENCE_LIMIT, threshold=20, toFile=False, wpath="./Temp", fileName="new_record.wav",
	               normalize=True, trim=True, addSilence=True):

		if not self.pipeIsOpened:
			self.initPipe()

		stream = self.pipe.open(format=self.format, channels=1, rate=self.rate,
		                        input=True, output=True, frames_per_buffer=self.chunkSize)

		record = array("h")

		print("recording...", end="")
		self.recordVoice(stream, record, mode, threshold=threshold)
		print("stop")

		sampleWidth = self.pipe.get_sample_size(self.format)
		stream.stop_stream()
		stream.close()

		record = self._normalize(record) if normalize else record
		record = self._trimWrapper(record) if trim else record
		record = self._addSilence(record, 0.5) if addSilence else record

		wav = self.convertToWAV(sampleWidth, record)

		if toFile:
			self.recordToFile(wav, wpath, fileName)

		self.terminatePipe()

		return wav


	def convertToWAV(self, width, data):
		tempFile = io.BytesIO()

		data = pack("<" + ("h" * len(data)), *data)

		with wave.open(tempFile, "wb") as tempInput:
			tempInput.setnchannels(1)
			tempInput.setsampwidth(width)
			tempInput.setframerate(self.rate)
			tempInput.writeframes(data)

		tempFile.seek(0)

		return tempFile.read()


	def recordToFile(self, data, wpath, fname):
		os.makedirs(wpath, exist_ok=True)
		fname = fname if fname.endswith(".wav") else "{}.wav".format(fname)

		fullPath = os.path.join(wpath, fname)

		with open(fullPath, "wb") as wf:
			wf.write(data)


def inputThread(aList):
	a = input()
	aList.append(a)


def main():
	with MicrophoneRecorder() as microphone:
		microphone.recordAuto(mode=AUTO_DURATION_LIMIT, threshold=15, toFile=True)

	# microphone.recordManual(toFile=True)


if __name__ == "__main__":
	main()
