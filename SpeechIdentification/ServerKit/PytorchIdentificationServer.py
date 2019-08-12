import socket
import select
import pickle
from struct import pack, unpack

from multiprocessing import Process

from . import Tasks
from DataBaseKit.DataBaseHDF import DataBase
from SpeechIdentification.Config import IdentifierConfig
from SpeechIdentification.PytorchIdentification import Identifier


class IdentifierServer:
	def __init__(self, address: tuple, maxClients=3):
		super().__init__()

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		self.socket.bind(address)
		self.socket.listen(maxClients)

		self.processes = []

		self._running = False


	def _addressAsString(self, address):
		return ":".join((str(i) for i in address))


	def close(self):
		print(f"Closing server socket {self._addressAsString(self.socket.getsockname())}")

		for pr in self.processes:
			pr.stop()
			pr.join()

		if self.socket:
			self.socket.close()
			self.socket = None


	def run(self):
		print(f"Starting a new Identifier server at {self._addressAsString(self.socket.getsockname())}")

		self._running = True
		while self._running:
			self.socket.settimeout(1)
			try:
				clientSocket, clientAddress = self.socket.accept()
			except socket.timeout:
				clientSocket = None

			if clientSocket:
				id_ = len(self.processes)
				clientProcess = IdentifierProcess(clientSocket, self._addressAsString(clientAddress), id_)
				self.processes.append(clientProcess)

				clientProcess.start()

		self.close()


	def stop(self):
		self._running = False


class IdentifierProcess(Process):
	def __init__(self, socket_, address, id_):
		super().__init__()

		self.socket = socket_
		self.address = address

		self.chunkSize = 4096

		self.id = id_

		self._running = False


	def _initHandler(self):
		dataBase = DataBase(
			filepath=r"D:\git_projects\FEFU\PipeleneDraft\SpeechIdentification\Temp\users_new_base.hdf",
		)
		identifier = Identifier(
			modelpath=IdentifierConfig.MODEL_PATH,
			dataBase=dataBase
		)

		return identifier


	def _getRequest(self):
		request = self.socket.recv(8)
		length = unpack(">Q", request)

		request = b""
		while len(request) < length[0]:
			request += self.socket.recv(self.chunkSize)

		print("Process {:7<}\tclient address {}: Received request from client".
			      format(self.id, self.address))

		request = pickle.loads(request)

		return request


	def _packResponse(self, response):
		response = pickle.dumps(response)
		response = pack(">Q", len(response)) + response

		return response


	def _handleRequest(self, request):
		task = request.get("task")

		name = request.get("name", "Unknown")
		results = None

		if task == Tasks.enroll:
			vector = request.get("vector")
			self.handler.enroll(name, vector)

		elif task == Tasks.enrollFromFile:
			file = request.get("file")

			self.handler.enrollFromFile(file, name)

		elif task == Tasks.identifyViaFile:
			file = request.get("file")
			threshold = request.get("unknownThreshold", 0.4)

			results = self.handler.identifyViaFile(file, threshold)

		elif task == Tasks._getEmbedding:
			utterance = request.get("utterance")
			results = self.handler._getEmbedding(utterance)

		elif task == Tasks._getEmbeddingFromFile:
			file = request.get("file")

			results = self.handler._getEmbeddingFromFile(file)

		elif task == Tasks._checkIncomingName:
			results = self.handler._checkIncomingName(name)

		else:
			raise NotImplementedError

		return results


	def _process(self):
		try:
			request = self._getRequest()

			results = self._handleRequest(request)

			response = {
				"status": 200,
				"results": results
			}

		except ConnectionAbortedError:
			print("Process {:7<}\tclient address {}: Connection has been closed by client".
			      format(self.id, self.address))

			self.stop()
			return

		except ConnectionResetError:
			print("Process {:7<}\tclient address {}: Connection has been closed by client".
			      format(self.id, self.address))

			self.stop()
			return

		except Exception as e:
			response = {
				"status": 500,
				"message": e
			}

		finally:
			if self._running:
				response = self._packResponse(response)
				self.socket.sendall(response)

				print("Process {:7<}\tclient address {}: Response has been sent".
				      format(self.id, self.address))

			else:
				return


	def run(self):
		print("Process {:7<}\tclient address {}: Process has started".format(self.id, self.address))

		self.handler = self._initHandler()

		self._running = True
		while self._running:
			if self.socket:
				try:
					readyRead, readyWrite, errors = select.select([self.socket], [self.socket], [], 1)

				except select.error as e:
					print("Process {:7<}\twith client address {}: Process has failed with error\n: {}".
					      format(self.id, self.address, e))

					self.stop()
					return

				if len(readyRead) > 0:
					self._process()

			else:
				print("Process {:7<}\tclient address {}: Client is not connected, can't receive data".
				      format(self.id, self.address))

				self.stop()
		self.close()


	def stop(self):
		self._running = False


	def close(self):
		if self.socket:
			print("Process {:7<}\tclient address {}: Closing connection".
			      format(self.id, self.address))

			self.socket.close()
