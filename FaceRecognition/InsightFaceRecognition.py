from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os
import string
import numpy as np
import mxnet as mx
import random
import cv2

from sklearn.preprocessing import normalize
from multiprocessing import Process, Queue
from _thread import start_new_thread
from numpy.linalg import norm
from time import time

from FaceDetection.RetinaFaceDetector import RetinaFace
from FaceDetection.Renderers import OpenCVRenderer as renderer
from FaceRecognition.Preprocessing import preprocessFace
from DataBase import DataBase


class TooManyFaces(Exception):
	pass


class FaceRecognizer:
	def __init__(self, prefix, epoch, dataBase:DataBase, detector:RetinaFace, ctxID=0):
		self.net = self._initEmbedder(prefix, epoch, ctxID)

		self.dataBase = dataBase
		self.detector = detector


	def _initEmbedder(self, prefix, epoch, ctx, shape=(112, 112), layer="fc1"):
		if ctx >= 0:
			ctx = mx.gpu(ctx)
		else:
			ctx = mx.cpu()

		sym, arg_params, aux_params = mx.model.load_checkpoint(prefix, epoch)
		all_layers = sym.get_internals()
		sym = all_layers[layer + '_output']

		model = mx.mod.Module(symbol=sym, context=ctx, label_names=None)

		model.bind(data_shapes=[('data', (1, 3) + shape)])
		model.set_params(arg_params, aux_params)

		return model


	def _getEmbedding(self, face):
		input_blob = np.expand_dims(face, axis=0)
		data = mx.nd.array(input_blob)
		db = mx.io.DataBatch(data=(data,))
		self.net.forward(db, is_train=False)
		embedding = self.net.get_outputs()[0].asnumpy()
		embedding = normalize(embedding).flatten()

		return embedding


	def _processImageTensor(self, tensor, enrollment=False):
		faces, boxes, landmarks = self.detectFaces(tensor)

		if enrollment and len(faces) > 1:
			raise TooManyFaces

		embeddings = [self._getEmbedding(face) for face in faces]

		return embeddings, boxes, landmarks


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


	def detectFaces(self, image):
		results = self.detector.process_image(image)

		boxes = results[0].astype(np.int32)
		landmarks = results[-1]

		faces = []
		for idx in range(len(boxes)):
			faces.append(preprocessFace(image, boxes[idx], landmarks[idx]))

		return faces, boxes, landmarks


	def enroll(self, name, vector):
		assert self.dataBase is not None

		self.dataBase.put(name, vector)
		print("User {} has been enrolled".format(name))


	def enrollFromImageTensor(self, image, name):
		embeddings, boxes, landmarks = self._processImageTensor(image, enrollment=True)

		name = self._checkIncomingName(name)
		self.enroll(name, embeddings)

		return boxes, landmarks


	def enrollFromImageFile(self, filepath, name, readMode=1):
		image = cv2.imread(filepath, readMode)
		self.enrollFromImageTensor(image, name)


	def enrollFromVideoFile(self, filepath, name, show=False):
		videoQueue = Queue()
		start_new_thread(videoStream, (filepath, videoQueue))

		fpsList = []
		while True:
			t1 = time()

			frame = videoQueue.get()

			boxes, landmarks = self.enrollFromImageTensor(frame, name)

			if show:
				frame = renderer.drawBoxes(frame, boxes, text=name, adaptiveToImage=True, occurrence="outer",
				                           fillTextBox=False)

				cv2.namedWindow("Enrollment", cv2.WINDOW_NORMAL)
				cv2.imshow("Enrollment", frame)

			if cv2.waitKey(1) & 0xFF == ord('q'):
				break

			fpsList.append(time() - t1)
			if len(fpsList) == 10:
				fps = 10 // sum(fpsList)
				fpsList = []

				print("\rVideo stream FPS {}".format(fps), end="")

		print("User {} has been enrolled".format(self._checkIncomingName(name)))


	def enrollFromCamera(self, webcamID, name, show=False):
		cameraQueue = Queue()
		start_new_thread(webCamera, (webcamID, cameraQueue))

		fpsList = []
		while True:
			t1 = time()
			frame = cameraQueue.get()

			boxes, landmarks = self.enrollFromImageTensor(frame, name)

			if show:
				frame = renderer.drawBoxes(frame, boxes, text=name, adaptiveToImage=True, occurrence="outer",
				                           fillTextBox=False)

				cv2.namedWindow("Enrollment", cv2.WINDOW_NORMAL)
				cv2.imshow("Enrollment", frame)

			if cv2.waitKey(1) & 0xFF == ord('q'):
				break

			fpsList.append(time() - t1)
			if len(fpsList) == 10:
				fps = 10 // sum(fpsList)
				fpsList = []

				print("\rWebcam stream FPS {}".format(fps), end="")

		print("User {} has been enrolled".format(self._checkIncomingName(name)))


	def enrollFromFolder(self, folder, name, readMode=1):
		files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png", ".jpeg"))]

		vector = []
		for file in files:
			image = cv2.imread(os.path.join(folder, file), readMode)
			embeddings, _, _ = self._processImageTensor(image)

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


	def identifyViaCamera(self, webcamID):
		cameraQueue = Queue()
		start_new_thread(webCamera, (webcamID, cameraQueue))
		captureSize = (640, 480)

		fpsList = []
		while True:
			t1 = time()
			try:
				frame = cameraQueue.get_nowait()

				embeddings, boxes, landmarks = self._processImageTensor(frame)

				users = []
				for embed in embeddings:
					result, scores = self.identify(embed)
					users.append(result)

				frame = renderer.drawBoxes(frame, boxes, text=users, adaptiveToImage=True, occurrence="outer",
				                           fillTextBox=False)

				cv2.namedWindow("Enrollment", cv2.WINDOW_NORMAL)
				cv2.imshow("Enrollment", frame)

				if cv2.waitKey(1) & 0xFF == ord('q'):
					break
			except:
				pass


	def identifyViaVideoFile(self, filepath):
		videoQueue = Queue()
		start_new_thread(videoStream, (filepath, videoQueue))

		fpsList = []
		while True:
			t1 = time()
			frame = videoQueue.get()

			embeddings, boxes, landmarks = self._processImageTensor(frame)
			result, scores = self.identify(embeddings)

		# return result, scores


	def identifyViaImageFile(self, filepath, readMode=1):
		image = cv2.imread(filepath, readMode)

		embeddings, boxes, landmarks = self._processImageTensor(image)

		users = []
		for idx, embed in enumerate(embeddings):
			result, scores = self.identify(embed)

			users.append({
				"name": result,
				"scores": scores,
				"coords": boxes[idx],
				"keypoints": landmarks[idx]
			})

		return users


def initVideoRecroder(filepath, shape, savepath=None):
	if savepath is None:
		wpath = os.path.join(os.path.dirname(__file__), "Videos")
		savepath = os.path.join(wpath, "detected_{}".format(os.path.basename(filepath)))
		print("{} will be used as save path".format(savepath))

	os.makedirs(savepath, exist_ok=True)

	recorder = cv2.VideoWriter(savepath, cv2.VideoWriter_fourcc(*'DIVX'), 25, shape)
	return recorder


def webCamera(webcamID, queue:Queue):
	captureSize = (640, 480)

	stream = cv2.VideoCapture(webcamID)

	stream.set(cv2.CAP_PROP_FRAME_WIDTH, captureSize[0])
	stream.set(cv2.CAP_PROP_FRAME_HEIGHT, captureSize[1])

	while True:
		grabbed, frame = stream.read()
		if not grabbed:
			break

		queue.put(frame)

		assert captureSize == frame.shape[:-1][::-1]

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break


def videoStream(filepath, queue):
	cap = cv2.VideoCapture(filepath)

	success, frame = cap.read()
	assert success

	while cap.isOpened():
		ret, frame = cap.read()
		if not ret:
			break

		queue.put(frame)

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break


def enroll(recognizer:FaceRecognizer, users):
	for name, folder in users.items():
		recognizer.enrollFromFolder(folder, name)


def identify(recognizer:FaceRecognizer, users):
	for name, folder in users.items():
		for file in os.listdir(folder):
			users = recognizer.identifyViaImageFile(os.path.join(folder, file))
			for usr in users:
				print("File {}\nTRUE {}\tPREDICTION {}\nscores: {}\n".format(file, name,
				                                                             usr.get("name"), usr.get("scores")))


def main():
	usersEnroll = {
		"Anton": r"D:\data\Faces\MySets\Anton\enr",
		"Alina": r"D:\data\Faces\MySets\Alina\enr",
		"Tanya": r"D:\data\Faces\MySets\Tanya\enr"
	}

	usersIdentify = {
		"Anton": r"D:\data\Faces\MySets\Anton\ver",
		"Alina": r"D:\data\Faces\MySets\Alina\ver",
		"Tanya": r"D:\data\Faces\MySets\Tanya\ver"
	}

	dataBase = DataBase(
		filepath="./Temp/users_face.hdf"
	)

	detector = RetinaFace(
		prefix=r"D:\git_projects\FEFU\PipeleneDraft\FaceDetection\Data\R50",
		epoch=0
	)

	recognizer = FaceRecognizer(
		prefix=r"D:\git_projects\FEFU\PipeleneDraft\FaceRecognition\Data\model",
		epoch=0,
		dataBase=dataBase,
		detector=detector
	)

	# enroll(recognizer, usersEnroll)
	# identify(recognizer, usersIdentify)
	recognizer.identifyViaCamera(0)

if __name__ == "__main__":
	main()