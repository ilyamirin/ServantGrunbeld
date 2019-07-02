import os
import io

from sys import byteorder
from array import array
from struct import pack
from _thread import start_new_thread

import pyaudio
import wave


class MicrophoneRecorder:
	def __init__(self, audioFormat=pyaudio.paInt16, chunkSize=1024, rate=16000, silenceThreshold=500, initPipe=False,
	             name="your_microphone"):

		self.format = audioFormat
		self.chunkSize = chunkSize
		self.rate = rate

		self.silenceThreshold = silenceThreshold
		self.silentFramesThreshold = 20

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
		"Returns 'True' if below the 'silent' threshold"
		return max(soundData) < self.silenceThreshold


	def _normalize(self, soundData):
		"Average the volume out"
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
		"Trim the blank spots at the start and end"
		# Trim to the left
		soundData = self._trim(soundData)

		# Trim to the right
		soundData.reverse()
		soundData = self._trim(soundData)
		soundData.reverse()

		return soundData


	def _addSilence(self, soundData, seconds):
		"Add silence to the start and end of 'soundData' of length 'seconds' (float)"
		r = array("h", [0 for _ in range(int(seconds * self.rate))])
		r.extend(soundData)
		r.extend([0 for _ in range(int(seconds * self.rate))])
		return r


	def recordVoice(self, stream, record, check: list=None):
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

			if check is not None:
				doRecord = not check
			else:
				doRecord = silentFrames < self.silentFramesThreshold


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
		self.recordVoice(stream, record, aList)

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


	def recordAuto(self, toFile=False, wpath="./Temp", fileName="new_record.wav", normalize=True, trim=True,
	               addSilence=True):
		"""
		Record a word or words from the microphone and
		return the data as an array of signed shorts.

		Normalizes the audio, trims silence from the
		start and end, and pads with 0.5 seconds of
		blank sound to make sure VLC et al can play
		it without getting chopped off.
		"""

		if not self.pipeIsOpened:
			self.initPipe()

		stream = self.pipe.open(format=self.format, channels=1, rate=self.rate,
		                        input=True, output=True, frames_per_buffer=self.chunkSize)

		record = array("h")

		print("recording...", end="")
		self.recordVoice(stream, record)
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
		"Records from the microphone and outputs the resulting data to 'path'"
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
		microphone.recordAuto(toFile=True)

	microphone.recordManual(toFile=True)


if __name__ == "__main__":
	main()
