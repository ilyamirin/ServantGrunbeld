import os
import string

import numpy as np

from numpy.linalg import norm

import torch

from ProjectUtils.DataBase import DataBase
from ProjectUtils.Microphone import AUTO_DURATION_LIMIT

try:
	from .Identification import SpeakerIdentifier
	from .AudioPreprocessing import preprocess_file
	from .Model import SpeakerEncoder
except ImportError:
	from Identification import SpeakerIdentifier
	from AudioPreprocessing import preprocess_file
	from Model import SpeakerEncoder


class Identifier(SpeakerIdentifier):
	def __init__(self, modelpath, dataBase:DataBase=None):
		super().__init__()

		self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
		self.net = self._initEmbedder(modelpath)

		self.dataBase = dataBase


	def _initEmbedder(self, modelpath):
		net = SpeakerEncoder(self.device, torch.device("cpu"))
		checkpoint = torch.load(modelpath)

		if modelpath.endswith(".pt"):
			checkpoint = checkpoint["model_state"]

		net.load_state_dict(checkpoint)
		net.eval()

		return net


	def _getEmbedding(self, utterance):
		embeddings = self.net.forward(utterance).cpu().data.numpy()

		embedding = np.average(embeddings, axis=0)

		return embedding


	def _getEmbeddingFromFile(self, file):
		audio = preprocess_file(file)
		audio = torch.from_numpy(audio).to(self.device)

		return self._getEmbedding(audio)


	@staticmethod
	def _cosineSimilarity(vector1, vector2):
		return 1 - np.inner(vector1, vector2) / (norm(vector1) * norm(vector2))


	def _checkIncomingName(self, name):
		name = name.split("/")

		if not name[-1] in string.digits and len(name) == 1:
			name = [name[-1], str(len(self.dataBase.get("/".join(name), {})))]

		return "/".join(name)


	def _checkOutgouingName(self, name):
		name = name.split("/")

		if name[-1] in string.digits:
			name = name[:-1]

		return " ".join(name)


	def enroll(self, name, vector):
		assert self.dataBase is not None

		self.dataBase.put(name, vector)
		print("User {} has been enrolled".format(name))


	def enrollFromMicrophone(self, name):
		with self.microphone as micro:
			audio = micro.recordManual()

		embedding = self._getEmbeddingFromFile(audio)

		name = self._checkIncomingName(name)
		self.enroll(name, embedding)


	def enrollFromFolder(self, name, folder):
		files = [f for f in os.listdir(folder) if f.lower().endswith(".wav")]

		vector = []
		for file in files:
			embeddings = self._getEmbeddingFromFile(os.path.join(folder, file))

			vector.append(embeddings)

		vector = np.average(vector, axis=0)

		name = self._checkIncomingName(name)
		self.enroll(name, vector)


	def identify(self, vector, unknownThreshold=0.4):
		assert self.dataBase is not None

		scores = {}

		minScore = 1
		result = "Unknown"
		for name in self.dataBase:
			value = self.dataBase.get(name)

			score = self._cosineSimilarity(vector, value)
			# score = np.sum(np.square(np.subtract(vector, value)), 0)

			scores[name] = score
			# scores[name + "_dist"] = np.sum(np.square(np.subtract(vector, value)), 0)

			result = name if (score < minScore and score < unknownThreshold) else result
			minScore = score if score < minScore else minScore

		return result, scores


	def identifyViaMicrophone(self):
		with self.microphone as micro:
			audio = micro.recordAuto(mode=AUTO_DURATION_LIMIT, threshold=8, addSilence=False)

		results, scores = self.identifyViaFile(audio)
		results = self._checkOutgouingName(results)

		return results, scores


	def identifyViaFile(self, filepath):
		results, scores = self.identify(self._getEmbeddingFromFile(filepath))
		results = self._checkOutgouingName(results)

		return results, scores


def enroll(embedder:Identifier, userDict):
	for name, folder in userDict.items():
		embedder.enrollFromFolder(name, folder)


def identify(embedder:Identifier, userDict):
	for name, folder in userDict.items():
		for file in os.listdir(folder):
			result, scores = embedder.identifyViaFile(os.path.join(folder, file))

			print("File {} result: {}\nscores: {}".format(file, result, scores))


def enrollAuto(embedder:Identifier, usersPath):
	for usrFolder in os.listdir(usersPath):
		name = usrFolder.split("_")[0]
		enrFolder = os.path.join(usersPath, usrFolder, "enr")

		embedder.enrollFromFolder(name, enrFolder)


def identifyAuto(embedder:Identifier, usersPath):
	for usrFolder in os.listdir(usersPath):
		name = usrFolder.split("_")[0]
		verFolder = os.path.join(usersPath, usrFolder, "ver")

		for file in os.listdir(verFolder):
			result, scores = embedder.identifyViaFile(os.path.join(verFolder, file))
			print("File {}\nTRUE {}\tPREDICTION {}\nscores: {}\n".format(file, name, result, scores))



def main():
	usersEnr = {
		"Anton/Drobyshev": r"D:\data\Speech\Voices_audio\MySets\Anton_Drobyshev\enr",
		"Alina/Bazarbaeva": r"D:\data\Speech\Voices_audio\MySets\Alina_Bazarbaeva\enr",
		"Tanya/Yan": r"D:\data\Speech\Voices_audio\MySets\Tanya_Ian\enr",
		"Ilya/Mirin": r"D:\data\Speech\Voices_audio\MySets\Ilya_Mirin\enr"
	}

	usersVer = {
		"Anton/Drobyshev": r"D:\data\Speech\Voices_audio\MySets\Anton_Drobyshev\ver",
		"Alina/Bazarbaeva": r"D:\data\Speech\Voices_audio\MySets\Alina_Bazarbaeva\ver",
		"Tanya/Yan": r"D:\data\Speech\Voices_audio\MySets\Tanya_Ian\ver",
		"Ilya/Mirin": r"D:\data\Speech\Voices_audio\MySets\Ilya_Mirin\ver"
	}

	dataBase = DataBase(
		filepath=r"./Temp/users_new_base.hdf",
		showBase=True
	)

	embedder = Identifier(
		modelpath=r"D:\data\Speech\TIMIT\speech_id_checkpoint\pretrained.pt",
		dataBase=dataBase
	)

	# enrollAuto(embedder, r"D:\data\Speech\Voices_audio\MySets")
	# identifyAuto(embedder, r"D:\data\Speech\Voices_audio\MySets")

	result, _ = embedder.identifyViaMicrophone()
	print(result)

	# enroll(embedder, usersEnr)
	#
	# results = embedder.identifyPartials(r"D:\data\Speech\Voices_audio\MySets\alina\ver\alina_ver1.wav")
	# print(results)

	# identify(embedder, usersVer)


if __name__ == "__main__":
	main()