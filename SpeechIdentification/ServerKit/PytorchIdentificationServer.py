import socket
import pickle
from struct import pack, unpack

from . import Tasks
from SpeechIdentification.PytorchIdentification import Identifier


class IdentifierServer(Identifier):
	def __init__(self, modelpath, dataBase, address:tuple, clientsLimit=3, chunkSize=4096):
		super().__init__(modelpath, dataBase)

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind(address)
		self.socket.listen(clientsLimit)

		self.chunkSize = chunkSize

		self.running = False


	def _getRequest(self, clientSocket):
		request = clientSocket.recv(8)
		length = unpack(">Q", request)

		request = b""
		while len(request) < length[0]:
			request += clientSocket.recv(self.chunkSize)

		print("Received request from client {}, unpickling it".
		      format(":".join(str(i) for i in (clientSocket.getsockname()))))

		request = pickle.loads(request)

		return request


	def _packResponse(self, response):
		response = pickle.dumps(response)
		response = pack(">Q", len(response)) + response

		return response


	def handleRequest(self, requestDict):
		task = requestDict.get("task")

		name = requestDict.get("name", "Unknown")
		results = None

		if task == Tasks.enroll:
			vector = requestDict.get("vector")
			self.enroll(name, vector)

		elif task == Tasks.enrollFromFile:
			file = requestDict.get("file")

			self.enrollFromFile(file, name)

		elif task == Tasks.identifyViaFile:
			file = requestDict.get("file")
			threshold = requestDict.get("unknownThreshold", 0.4)

			results = self.identifyViaFile(file, threshold)

		elif task == Tasks._getEmbedding:
			utterance = requestDict.get("utterance")
			results = self._getEmbedding(utterance)

		elif task == Tasks._getEmbeddingFromFile:
			file = requestDict.get("file")

			results = self._getEmbeddingFromFile(file)

		elif task == Tasks._checkIncomingName:
			results = self._checkIncomingName(name)

		else:
			raise NotImplementedError

		return results


	def run(self):
		self.running = True

		print("Server running at {}".format(":".join(str(i) for i in (self.socket.getsockname()))))
		while self.running:
			self.socket.settimeout(1)

			try:
				clientSocket, clientAddress = self.socket.accept()
			except:
				clientSocket = None

			if clientSocket:
				try:
					request = self._getRequest(clientSocket)

					results = self.handleRequest(request)

					response = {
						"status": 200,
						"results": results
					}

				except Exception as e:
					response = {
						"status": 500,
						"message": e
					}

				finally:
					try:
						response = self._packResponse(response)
						clientSocket.sendall(response)
					except Exception as e:
						print(e)