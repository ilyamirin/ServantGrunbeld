import os
import socket
import pickle
import string
from struct import pack, unpack

import numpy as np

from numpy.linalg import norm

from . import Tasks
from ProjectUtils.Microphone import MicrophoneRecorder, AUTO_DURATION_LIMIT, AUTO_SILENCE_LIMIT


class IdentifierClient:
	def __init__(self, address: tuple, chunkSize=4096):
		self.microphone = MicrophoneRecorder()

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect(address)

		self.chunkSize = chunkSize


	def _handleResponse(self, response):
		status = response.get("status")

		if status == 500:
			message = response.get("message")
			print(f"Request failed with message: {message}")

			result = None

		elif status == 200:
			print("Task has been successfully finished")
			result = response.get("results")

		else:
			raise ValueError

		return result


	def _getResponse(self):
		response = self.socket.recv(8)
		length = unpack(">Q", response)

		response = b""
		while len(response) < length[0]:
			response += self.socket.recv(self.chunkSize)

		print("Received request from server, unpickling it")

		response = pickle.loads(response)

		return response


	def _packRequest(self, request):
		request = pickle.dumps(request)
		request = pack(">Q", len(request)) + request

		return request


	def _getEmbedding(self, utterance):
		request = {
			"task": Tasks._getEmbedding,
			"utterance": utterance
		}

		request = self._packRequest(request)
		self.socket.sendall(request)

		response = self._getResponse()

		embedding = self._handleResponse(response)

		return embedding


	def _getEmbeddingFromFile(self, file):
		with open(file, "rb") as file:
			audio = file.read()

		request = {
			"task": Tasks._getEmbeddingFromFile,
			"file": audio
		}

		request = self._packRequest(request)
		self.socket.sendall(request)

		response = self._getResponse()

		embedding = self._handleResponse(response)

		return embedding


	@staticmethod
	def _cosineSimilarity(vector1, vector2):
		return 1 - np.inner(vector1, vector2) / (norm(vector1) * norm(vector2))


	def _checkIncomingName(self, name):
		request = {
			"task": Tasks._checkIncomingName,
			"name": name
		}

		request = self._packRequest(request)
		self.socket.sendall(request)

		response = self._getResponse()

		name = self._handleResponse(response)

		return name


	@staticmethod
	def _checkOutgoingName(name):
		name = name.split("/")

		if name[-1] in string.digits:
			name = name[:-1]

		return " ".join(name)


	def enroll(self, name, vector):
		request = {
			"task": Tasks.enroll,
			"name": name,
			"vector": vector
		}

		request = self._packRequest(request)
		self.socket.sendall(request)

		response = self._getResponse()

		self._handleResponse(response)


	def enrollFromMicrophone(self, name):
		with self.microphone as micro:
			audio = micro.recordManual()

		request = {
			"task": Tasks.enrollFromFile,
			"name": name,
			"file": audio
		}

		request = self._packRequest(request)
		self.socket.sendall(request)

		response = self._getResponse()

		self._handleResponse(response)


	def enrollFromFile(self, file, name):
		with open(file, "rb") as file:
			audio = file.read()

		request = {
			"task": Tasks.enrollFromFile,
			"name": name,
			"file": audio
		}

		request = self._packRequest(request)
		self.socket.sendall(request)

		response = self._getResponse()

		self._handleResponse(response)


	def enrollFromFolder(self, name, folder):
		files = [f for f in os.listdir(folder) if f.lower().endswith(".wav")]

		vector = []
		for file in files:
			embedding = self._getEmbeddingFromFile(os.path.join(folder, file))

			if embedding:
				vector.append(embedding)

		vector = np.average(vector, axis=0)

		self.enroll(name, vector)


	def identify(self, vector, unknownThreshold=0.3):
		request = {
			"task": Tasks.identify,
			"unknownThreshold": unknownThreshold,
			"vector": vector
		}

		request = self._packRequest(request)
		self.socket.sendall(request)

		response = self._getResponse()

		results = self._handleResponse(response)

		if results:
			name, scores = results
		else:
			name, scores = None, None

		return name, scores


	def identifyViaFile(self, filepath, unknownThreshold=0.3):
		from io import BytesIO

		with open(filepath, "rb") as file:
			audio = BytesIO(file.read())

		request = {
			"task": Tasks.identifyViaFile,
			"unknownThreshold": unknownThreshold,
			"file": audio
		}

		request = self._packRequest(request)
		self.socket.sendall(request)

		response = self._getResponse()

		results = self._handleResponse(response)

		if results:
			name, scores = results
		else:
			name, scores = None, None

		return name, scores


	def identifyViaMicrophone(self, unknownThreshold=0.3):
		with self.microphone as micro:
			audio = micro.recordAuto(mode=AUTO_SILENCE_LIMIT, threshold=20, addSilence=False)

		request = {
			"task": Tasks.identifyViaFile,
			"unknownThreshold": unknownThreshold,
			"file": audio
		}

		request = self._packRequest(request)
		self.socket.sendall(request)

		response = self._getResponse()
		results = self._handleResponse(response)

		if results:
			name, scores = results
		else:
			name, scores = None, None

		return name, scores