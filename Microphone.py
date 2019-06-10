import os
import io

from sys import byteorder
from array import array
from struct import pack

import pyaudio
import wave


class MicrophoneRecorder:
	def __init__(self, format=pyaudio.paInt16, chunkSize=1024, rate=16000, silenceThreshold=500, initPipe=False):
		self.format = format
		self.chunkSize = chunkSize
		self.rate = rate

		self.silenceThreshold = silenceThreshold
		self.silentFramesThreshold = 20

		self.maximum = 16384

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


	def __isSilent(self, soundData):
		"Returns 'True' if below the 'silent' threshold"
		return max(soundData) < self.silenceThreshold


	def __normalize(self, soundData):
		"Average the volume out"
		ratios = float(self.maximum) / max(abs(i) for i in soundData)

		r = array("h")
		for i in soundData:
			r.append(int(i * ratios))
		return r


	def __trim(self, soundData):
		soundStarted = False
		r = array("h")

		for i in soundData:
			if not soundStarted and abs(i) > self.silenceThreshold:
				soundStarted = True
				r.append(i)

			elif soundStarted:
				r.append(i)
		return r


	def __trimWrapper(self, soundData):
		"Trim the blank spots at the start and end"
		# Trim to the left
		soundData = self.__trim(soundData)

		# Trim to the right
		soundData.reverse()
		soundData = self.__trim(soundData)
		soundData.reverse()

		return soundData


	def __addSilence(self, soundData, seconds):
		"Add silence to the start and end of 'soundData' of length 'seconds' (float)"
		r = array("h", [0 for _ in range(int(seconds * self.rate))])
		r.extend(soundData)
		r.extend([0 for _ in range(int(seconds * self.rate))])
		return r


	def record(self, toFile=False, **params):
		"""
		Record a word or words from the microphone and
		return the data as an array of signed shorts.

		Normalizes the audio, trims silence from the
		start and end, and pads with 0.5 seconds of
		blank sound to make sure VLC et al can play
		it without getting chopped off.
		"""
		wpath = params.get("wpath", "./Temp")
		fileName = params.get("fileName", "new_record.wav")

		if not self.pipeIsOpened:
			self.initPipe()

		stream = self.pipe.open(format=self.format, channels=1, rate=self.rate,
		                        input=True, output=True, frames_per_buffer=self.chunkSize)

		silentFrames = 0
		soundStarted = False

		record = array("h")

		print("recording...", end="")
		while True:
			# little endian, signed short
			soundData = array("h", stream.read(self.chunkSize))
			if byteorder == "big":
				soundData.byteswap()
			record.extend(soundData)

			silent = self.__isSilent(soundData)

			if silent and soundStarted:
				# print("\rNumber of silent frames: {}".format(silentFrames), end="")
				silentFrames += 1
			elif not silent and not soundStarted:
				soundStarted = True

			if soundStarted and silentFrames > self.silentFramesThreshold:
				break

		print("stop")

		sampleWidth = self.pipe.get_sample_size(self.format)
		stream.stop_stream()
		stream.close()

		record = self.__normalize(record)
		record = self.__trim(record)
		record = self.__addSilence(record, 0.5)

		wav = self.convertToWAV(sampleWidth, record)

		if toFile:
			self.recordToFile(wav, sampleWidth, wpath, fileName)

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


	def recordToFile(self, data, width, wpath, fname):
		"Records from the microphone and outputs the resulting data to 'path'"
		os.makedirs(wpath, exist_ok=True)
		fname = fname if fname.endswith(".wav") else "{}.wav".format(fname)

		fullPath = os.path.join(wpath, fname)

		with open(fullPath, "wb") as wf:
			wf.write(data)


def main():
	microphone = MicrophoneRecorder()
	microphone.initPipe()
	microphone.record(toFile=True)


if __name__ == "__main__":
	main()
