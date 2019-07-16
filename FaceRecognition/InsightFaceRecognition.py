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
import sklearn

from numpy.linalg import norm
from time import time

from FaceDetection.RetinaFaceDetector import RetinaFace
from FaceDetection.Renderers import OpenCVRenderer as renderer
from FaceRecognition.Preprocessing import preprocess
from DataBase import DataBase


class TooManyFaces(Exception):
	pass


class FaceRecognizer:
	def __init__(self, prefix, epoch, database:DataBase, detector:RetinaFace, ctxID=0):
		self.net = self._initEmbedder(prefix, epoch, ctxID)

		self.dataBase = database
		self.detector = detector


	def _initEmbedder(self, prefix, epoch, ctx):
		return 0


	def _getEmbedding(self, face):
		embeddings = self.net.forward(face).cpu().data.numpy()

		embedding = np.average(embeddings, axis=0)

		return embedding


	def _processImageTensor(self, tensor):
		faces, coords = self.detectFaces(tensor)

		if len(faces) > 1:
			raise TooManyFaces
		else:
			faces = faces[0]

		return self._getEmbedding(faces), faces, coords


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
		results = self.detector.process_image(image, resToDict=True)

		faces = preprocess(image, results)

		return faces, results


	def enroll(self, name, vector):
		assert self.dataBase is not None

		self.dataBase.put(name, vector)
		print("User {} has been enrolled".format(name))


	def enrollFromImageTensor(self, image, name):
		embedding, faces, coords = self._processImageTensor(image)

		name = self._checkIncomingName(name)
		self.enroll(name, embedding)

		return faces, coords


	def enrollFromImageFile(self, filepath, name, readMode=1):
		name = filepath if name is None else name

		image = cv2.imread(filepath, readMode)
		self.enrollFromImageTensor(image, name)


	def enrollFromVideoFile(self, filepath, name, show=False):
		cap = cv2.VideoCapture(filepath)

		success, frame = cap.read()
		assert success

		fpsList = []
		fps = 0
		while cap.isOpened():
			ret, frame = cap.read()
			if not ret:
				break
			t1 = time()

			_, attributes = self.enrollFromImageTensor(frame, name)
			boxes, texts = attributes

			if show:
				frame = renderer.drawBoxes(frame, boxes, text=texts, adaptiveToImage=True, occurrence="outer",
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


	def enrollFromCamera(self, webcamID, name, show=False):
		captureSize = (640, 480)

		stream = cv2.VideoCapture(webcamID)

		stream.set(cv2.CAP_PROP_FRAME_WIDTH, captureSize[0])
		stream.set(cv2.CAP_PROP_FRAME_HEIGHT, captureSize[1])

		fpsList = []
		fps = 0
		while True:
			t1 = time()
			grabbed, frame = stream.read()
			if not grabbed:
				break

			_, attributes = self.enrollFromImageTensor(frame, name)
			boxes, texts = attributes

			if show:
				frame = renderer.drawBoxes(frame, boxes, text=texts, adaptiveToImage=True, occurrence="outer",
				                           fillTextBox=False)

				cv2.namedWindow("Enrollment", cv2.WINDOW_NORMAL)
				cv2.imshow("Enrollment", frame)

			fpsList.append(time() - t1)
			if len(fpsList) == 10:
				fps = 10 // sum(fpsList)
				fpsList = []

			assert captureSize == frame.shape[:-1][::-1]

			print("\rWebcam stream FPS {}".format(fps), end="")

			if cv2.waitKey(1) & 0xFF == ord('q'):
				break

		print("User {} has been enrolled".format(self._checkIncomingName(name)))


	def enrollFromFolder(self, folder, name, readMode=1):
		files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png", ".jpeg"))]

		vector = []
		for file in files:
			image = cv2.imread(os.path.join(folder, file), readMode)
			embedding, _, _ = self._processImageTensor(image)

			vector.append(embedding)

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


	def identifyViaCamera(self):
		pass


	def identifyViaImageFile(self, filepath):
		pass


	def identifyViaVideoFile(self, filepath):
		pass


def initVideoRecroder(filepath, shape, savepath=None):
	if savepath is None:
		wpath = os.path.join(os.path.dirname(__file__), "Videos")
		savepath = os.path.join(wpath, "detected_{}".format(os.path.basename(filepath)))
		print("{} will be used as save path".format(savepath))

	os.makedirs(savepath, exist_ok=True)

	recorder = cv2.VideoWriter(savepath, cv2.VideoWriter_fourcc(*'DIVX'), 25, shape)
	return recorder


def webCamera(id, queue):
	pass


def videoStream(queue):
	pass


def do_flip(data):
	for idx in range(data.shape[0]):
		data[idx, :, :] = np.fliplr(data[idx, :, :])


def get_model(ctx, image_size, model_str, layer):
	_vec = model_str.split(',')
	assert len(_vec) == 2
	prefix = _vec[0]
	epoch = int(_vec[1])
	print('loading', prefix, epoch)
	sym, arg_params, aux_params = mx.model.load_checkpoint(prefix, epoch)
	all_layers = sym.get_internals()
	sym = all_layers[layer + '_output']
	model = mx.mod.Module(symbol=sym, context=ctx, label_names=None)
	# model.bind(data_shapes=[('data', (args.batch_size, 3, image_size[0], image_size[1]))], label_shapes=[('softmax_label', (args.batch_size,))])
	model.bind(data_shapes=[('data', (1, 3, image_size[0], image_size[1]))])
	model.set_params(arg_params, aux_params)
	return model


class FaceModel:
	def __init__(self, args):
		self.args = args
		ctx = mx.gpu(args.gpu)
		_vec = args.image_size.split(',')
		assert len(_vec) == 2
		image_size = (int(_vec[0]), int(_vec[1]))
		self.model = None
		self.ga_model = None
		if len(args.model) > 0:
			self.model = get_model(ctx, image_size, args.model, 'fc1')
		if len(args.ga_model) > 0:
			self.ga_model = get_model(ctx, image_size, args.ga_model, 'fc1')

		self.threshold = args.threshold
		self.det_minsize = 50
		self.det_threshold = [0.6, 0.7, 0.8]
		# self.det_factor = 0.9
		self.image_size = image_size
		mtcnn_path = os.path.join(os.path.dirname(__file__), 'mtcnn-model')
		if args.det == 0:
			detector = MtcnnDetector(model_folder=mtcnn_path, ctx=ctx, num_worker=1, accurate_landmark=True,
			                         threshold=self.det_threshold)
		else:
			detector = MtcnnDetector(model_folder=mtcnn_path, ctx=ctx, num_worker=1, accurate_landmark=True,
			                         threshold=[0.0, 0.0, 0.2])
		self.detector = detector


	def get_input(self, face_img):
		ret = self.detector.detect_face(face_img, det_type=self.args.det)
		if ret is None:
			return None
		bbox, points = ret
		if bbox.shape[0] == 0:
			return None
		bbox = bbox[0, 0:4]
		points = points[0, :].reshape((2, 5)).T
		# print(bbox)
		# print(points)
		nimg = face_preprocess.preprocess(face_img, bbox, points, image_size='112,112')
		nimg = cv2.cvtColor(nimg, cv2.COLOR_BGR2RGB)
		aligned = np.transpose(nimg, (2, 0, 1))
		return aligned


	def get_feature(self, aligned):
		input_blob = np.expand_dims(aligned, axis=0)
		data = mx.nd.array(input_blob)
		db = mx.io.DataBatch(data=(data,))
		self.model.forward(db, is_train=False)
		embedding = self.model.get_outputs()[0].asnumpy()
		embedding = sklearn.preprocessing.normalize(embedding).flatten()
		return embedding


	def get_ga(self, aligned):
		input_blob = np.expand_dims(aligned, axis=0)
		data = mx.nd.array(input_blob)
		db = mx.io.DataBatch(data=(data,))
		self.ga_model.forward(db, is_train=False)
		ret = self.ga_model.get_outputs()[0].asnumpy()
		g = ret[:, 0:2].flatten()
		gender = np.argmax(g)
		a = ret[:, 2:202].reshape((100, 2))
		a = np.argmax(a, axis=1)
		age = int(sum(a))

		return gender, age
