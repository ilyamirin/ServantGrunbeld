import os
import io

import numpy as np
from numpy.linalg import norm

import torch

from audio import preprocess_file
from Model import SpeakerEncoder
from DataBase import DataBase

from Identification import SpeakerIdentifier


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


	def _checkPresence(self, name):
		pass


	def _cosineSimilarity(self, vector1, vector2):
		return 1 - np.inner(vector1, vector2) / (norm(vector1) * norm(vector2))


	def identify(self, vector):
		assert self.dataBase is not None

		scores = {}

		minScore = 1
		result = None
		for name in self.dataBase:
			value = self.dataBase[name][:]

			score = self._cosineSimilarity(vector, value)
			# score = np.sum(np.square(np.subtract(vector, value)), 0)

			scores[name] = score
			# scores[name + "_dist"] = np.sum(np.square(np.subtract(vector, value)), 0)

			result = name if score < minScore else result
			minScore = score if score < minScore else minScore

		return result, scores


	def identifyViaMicrophone(self):
		with self.microphone as micro:
			audio = micro.recordAuto(addSilence=False)

		results, scores = self.identifyViaFile(audio)

		return results, scores


	def identifyViaFile(self, filepath):
		results, scores = self.identify(self._getEmbeddingFromFile(filepath))

		return results, scores


	def enroll(self, name, vector, rewrite=False):
		assert self.dataBase is not None

		if not rewrite:
			vectorOld = self.dataBase.get(name, 0)
			vector = np.average(np.array((vector, vectorOld)), axis=0)

		self.dataBase.put(name, vector)
		print("User {} has been enrolled".format(name))


	def enrollFromMicrophone(self, name=None):
		with self.microphone as micro:
			audio = micro.recordManual()

		embedding = self._getEmbeddingFromFile(audio)
		self.enroll(name, embedding)


	def enrollFromFolder(self, name, folder):
		files = [f for f in os.listdir(folder) if f.lower().endswith(".wav")]

		vector = []
		for file in files:
			embeddings = self._getEmbeddingFromFile(file)

			vector.append(embeddings)

		vector = np.average(vector, axis=0)

		self.enroll(name, vector)


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
	dataBase = DataBase(
		filepath=r"./Temp/users_extended.hdf",
		showBase=True
	)

	embedder = Identifier(
		modelpath=r"D:\data\Speech\TIMIT\speech_id_checkpoint\pretrained.pt",
		dataBase=dataBase
	)

	# enrollAuto(embedder, r"D:\data\Speech\Voices_audio\MySets")
	identifyAuto(embedder, r"D:\data\Speech\Voices_audio\MySets")

	# enroll(embedder, usersEnr)
	#
	# results = embedder.identifyPartials(r"D:\data\Speech\Voices_audio\MySets\alina\ver\alina_ver1.wav")
	# print(results)

	# identify(embedder, usersVer)


if __name__ == "__main__":
	main()