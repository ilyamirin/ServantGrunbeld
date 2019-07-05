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


	def identify(self, vector):
		assert self.dataBase is not None

		scores = {}

		minScore = 1
		result = None
		for name in self.dataBase:
			value = self.dataBase[name][:]

			score = 1 - np.inner(vector, value) / (norm(vector) * norm(value))
			# score = np.sum(np.square(np.subtract(vector, value)), 0)

			scores[name] = score
			# scores[name + "_dist"] = np.sum(np.square(np.subtract(vector, value)), 0)

			result = name if score < minScore else result
			minScore = score if score < minScore else minScore

		return result, scores


	def identifyViaMicrophone(self):
		with self.microphone as micro:
			audio = micro.recordAuto(addSilence=False)

		tempFile = io.BytesIO(audio)

		audio = preprocess_file(tempFile)

		results, scores = self.identify(self._getEmbedding(audio))

		return results


	def identifyViaFile(self, filepath):
		audio = preprocess_file(filepath)

		audio = torch.from_numpy(audio).to(self.device)

		results, scores = self.identify(self._getEmbedding(audio))

		return results, scores


	def enroll(self, name, vector):
		assert self.dataBase is not None

		self.dataBase.put(name, vector)
		print("User {} has been enrolled".format(name))


	def enrollFromMicrophone(self):
		pass


	def enrollFromFolder(self, name, folder):
		files = os.listdir(folder)

		vector = []
		for file in files:
			audio = preprocess_file(os.path.join(folder, file))
			audio = torch.from_numpy(audio).to(self.device)

			embeddings = self._getEmbedding(audio)

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


def main():
	usersEnr = {
		"Anton": r"D:\data\Speech\Voices_audio\MySets\anton\enr",
		"Alina": r"D:\data\Speech\Voices_audio\MySets\alina\enr",
		"Tanya": r"D:\data\Speech\Voices_audio\MySets\tanya\enr",
		"Ilya": r"D:\data\Speech\Voices_audio\MySets\ilya\enr"
	}

	usersVer = {
		"Anton": r"D:\data\Speech\Voices_audio\MySets\anton\ver",
		"Alina": r"D:\data\Speech\Voices_audio\MySets\alina\ver",
		"Tanya": r"D:\data\Speech\Voices_audio\MySets\tanya\ver",
		"Ilya": r"D:\data\Speech\Voices_audio\MySets\ilya\ver"
	}

	dataBase = DataBase(
		filepath=r"./Temp/users.hdf",
		showBase=False
	)

	embedder = Identifier(
		modelpath=r"D:\data\Speech\TIMIT\speech_id_checkpoint\pretrained.pt",
		dataBase=dataBase
	)

	# enroll(embedder, usersEnr)

	# results = embedder.identifyPartials(r"D:\data\Speech\Voices_audio\MySets\alina\ver\alina_ver1.wav")
	# print(results)

	identify(embedder, usersVer)


if __name__ == "__main__":
	main()