import os
import numpy as np
import mxnet as mx
import cv2

from numpy.linalg import norm

from ProjectUtils.Renderers import OpenCVRenderer as renderer
from DataBaseKit.DataBaseHDF import DataBase as DBHDF
from DataBaseKit.DjangoAPIWrapper import DataBase as DBDjango
from FaceDetection.RetinaFaceDetector import RetinaFace
from FaceDetection.Config import DetectorConfig

try:
	from .Preprocessing import preprocessFace
	from .Config import RecognizerConfig
except ImportError:
	from Preprocessing import preprocessFace
	from Config import RecognizerConfig


class TooManyFaces(Exception):
	pass


class FaceRecognizer:
	def __init__(self, prefix, epoch, dataBase, detector:RetinaFace, ctxID=0):
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


	def _getEmbedding(self, faces):
		data = mx.nd.array(faces)
		db = mx.io.DataBatch(data=(data,))
		self.net.forward(db, is_train=False)
		embeddings = self.net.get_outputs()[0].asnumpy()

		return embeddings


	def _processImageTensor(self, tensor, enrollment=False):
		faces, boxes, landmarks = self.detectFaces(tensor)

		if enrollment and len(faces) > 1:
			raise TooManyFaces

		embeddings = self._getEmbedding(np.array(faces))
		# embeddings = [self._getEmbedding(face) for face in faces]

		return embeddings, boxes, landmarks


	@staticmethod
	def cosineSimilarity(vector1, vector2):
		return 1 - np.inner(vector1, vector2) / (norm(vector1) * norm(vector2))


	@staticmethod
	def distance(vector1, vector2):
		diff = np.subtract(norm(vector1), norm(vector2))
		dist = np.sum(np.square(diff), 0)

		return dist


	def detectFaces(self, image):
		results = self.detector.process_image(image)

		boxes = results[0].astype(np.int32)
		landmarks = results[-1]

		faces = []
		for idx in range(len(boxes)):
			faces.append(preprocessFace(image, landmarks[idx]))

		return faces, boxes, landmarks


	def enroll(self, vector, name, **kwargs):
		assert self.dataBase is not None

		if kwargs.pop("update", False):
			name = self.dataBase.checkIncomingName(name)
			self.dataBase.update(vector, name, **kwargs)
		else:
			name = self.dataBase.checkIncomingName(name, addIndex=True)
			self.dataBase.put(vector, name, **kwargs)


	def enrollFromImageTensor(self, image, name, **kwargs):
		kwargs["count"] = 1

		embeddings, boxes, landmarks = self._processImageTensor(image, enrollment=True)

		self.enroll(embeddings[0], name, **kwargs)

		return boxes, landmarks


	def enrollFromImageFile(self, filepath, name, readMode=1, **kwargs):
		image = cv2.imread(filepath, readMode)
		self.enrollFromImageTensor(image, name, **kwargs)


	def _enrollVideoStream(self, frame, name, container:list, show, windowName):
		embedding, boxes, landmarks = self._processImageTensor(frame, enrollment=True)
		container.append(embedding[0])

		if show:
			frame = renderer.drawBoxes(frame, boxes, text=name, adaptiveToImage=True, occurrence="outer",
			                           fillTextBox=False)

			cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)
			cv2.imshow(windowName, frame)


	def enrollFromVideoFile(self, filepath, name, show=False, windowName="Video enrollment", **kwargs):
		container = []
		videoStream(filepath, self._enrollVideoStream, name=name, container=container, show=show, windowName=windowName)

		kwargs["count"] = len(container)
		container = np.average(np.array(container), axis=0)
		self.enroll(container, name, **kwargs)

		print("User {} has been enrolled".format(self.dataBase.checkIncomingName(name)))


	def enrollFromCamera(self, webcamID, name, show=False, windowName="Video enrollment", **kwargs):
		container = []
		webCamera(webcamID, self._enrollVideoStream, framesLimit=50, name=name, container=container, show=show,
		                      windowName=windowName)

		kwargs["count"] = len(container)
		container = np.average(np.array(container), axis=0)
		self.enroll(container, name, **kwargs)

		print("User {} has been enrolled".format(self.dataBase.checkIncomingName(name)))


	def enrollFromFolder(self, folder, name, readMode=1, **kwargs):
		files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png", ".jpeg"))]

		vector = []
		for file in files:
			image = cv2.imread(os.path.join(folder, file), readMode)
			embeddings, _, _ = self._processImageTensor(image)

			vector.append(np.ravel(embeddings))

		kwargs["count"] = len(vector)
		vector = np.average(vector, axis=0)

		self.enroll(vector, name, **kwargs)


	def identify(self, vector, unknownThreshold=0.5):
		assert self.dataBase is not None

		scores = {}

		minScore = 1
		result = "Unknown"
		for user in self.dataBase:
			value = self.dataBase.get(user)

			if self.dataBase.type == "django":
				user = [i for i in [user["surname"], user["name"], user["patronymic"]] if i]
				user = " ".join(user)

			score = self.cosineSimilarity(vector, value)
			# score = self._distance(vector, value)
			# score = np.sum(np.square(np.subtract(vector, value)), 0)

			scores[user] = score
			# scores[name + "_dist"] = np.sum(np.square(np.subtract(vector, value)), 0)

			result = user if (score < minScore and score < unknownThreshold) else result
			minScore = score if score < minScore else minScore

		result = self.dataBase.checkOutgoingName(result)

		return result, scores


	def _identifyVideoStream(self, frame, show, windowName):
		embeddings, boxes, landmarks = self._processImageTensor(frame)

		users = []
		for embed in embeddings:
			result, scores = self.identify(embed)
			users.append(result)

		if show:
			frame = renderer.drawBoxes(frame, boxes, text=users, adaptiveToImage=True, occurrence="outer",
			                           fillTextBox=False)

			cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)
			cv2.imshow(windowName, frame)


	def identifyViaCamera(self, webcamID, show=True, windowName="Video identification"):
		webCamera(webcamID, self._identifyVideoStream, show=show, windowName=windowName)


	def identifyViaVideoFile(self, filepath, show=True, windowName="Video identification"):
		videoStream(filepath, self._identifyVideoStream, show=show, windowName=windowName)


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


def webCamera(webcamID, action, framesLimit=None, **kwargs):
	framesLimit = float("inf") if framesLimit is None else framesLimit

	captureSize = (640, 480)

	stream = cv2.VideoCapture(webcamID)

	stream.set(cv2.CAP_PROP_FRAME_WIDTH, captureSize[0])
	stream.set(cv2.CAP_PROP_FRAME_HEIGHT, captureSize[1])

	frameIdx = 0
	while frameIdx < framesLimit:
		grabbed, frame = stream.read()
		if not grabbed:
			break

		action(frame, **kwargs)

		assert captureSize == frame.shape[:-1][::-1]

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

		frameIdx += 1

	cv2.destroyWindow(kwargs.get("windowName", ""))


def videoStream(filepath, action, **kwargs):
	cap = cv2.VideoCapture(filepath)

	captureSize = (640, 480)

	cap.set(cv2.CAP_PROP_FRAME_WIDTH, captureSize[0])
	cap.set(cv2.CAP_PROP_FRAME_HEIGHT, captureSize[1])

	success, frame = cap.read()
	assert success

	while cap.isOpened():
		ret, frame = cap.read()
		if not ret:
			break

		action(frame, **kwargs)

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

	cv2.destroyWindow(kwargs.get("windowName", ""))


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


def enrollAuto(embedder:FaceRecognizer, usersPath):
	for usrFolder in os.listdir(usersPath):
		if not os.path.isdir(os.path.join(usersPath, usrFolder)):
			continue

		name = usrFolder.split("_")[0]
		enrFolder = os.path.join(usersPath, usrFolder, "enr")

		embedder.enrollFromFolder(enrFolder, name)


def identifyAuto(embedder:FaceRecognizer, usersPath):
	for usrFolder in os.listdir(usersPath):
		if not os.path.isdir(os.path.join(usersPath, usrFolder)):
			continue

		name = usrFolder.split("_")[0]
		verFolder = os.path.join(usersPath, usrFolder, "ver")

		for file in os.listdir(verFolder):
			users = embedder.identifyViaImageFile(os.path.join(verFolder, file))

			for idx, usr in enumerate(users):
				print("File {}\nTRUE {}\tPREDICTION {}\nscores: {}\n".format(file, name,
				                                                             usr.get("name"), usr.get("scores")))
				image = cv2.imread(os.path.join(verFolder, file))
				renderer.drawBoxes(image, boxes=[usr.get("coords")], text=usr.get("name"))
				# renderer.show(image)
				renderer.save(image, r"D:\data\Faces\Results", "{}_{}".format(idx, file))


def main():
	# dataBase = DBHDF(
	# 	filepath=RecognizerConfig.DATA_BASE_PATH
	# )

	os.environ["DJANGO_SETTINGS_MODULE"] = "DataBaseKit.DataBase.settings"
	dataBase = DBDjango(password="FEFUdatabase")

	detector = RetinaFace(
		prefix=DetectorConfig.PREFIX,
		epoch=DetectorConfig.EPOCH
	)

	recognizer = FaceRecognizer(
		prefix=RecognizerConfig.PREFIX,
		epoch=RecognizerConfig.EPOCH,
		dataBase=dataBase,
		detector=detector
	)

	# recognizer.enrollFromImageFile(r"D:\data\Faces\MySets\Anton\enr\0002.JPG", name="Anton", surname="Drobyshev")
	recognizer.identifyViaImageFile(filepath=r"D:\data\Faces\Demo\Dmitriy_Sukhoverov\ver\2-z14-180f2ff2-a3f5-40b6-9d36-e66acecce680.jpg")

	# enrollAuto(recognizer, r"D:\data\Faces\MySets")
	# identifyAuto(recognizer, r"D:\data\Faces\MySets")
	# recognizer.identifyViaImageFile(r"D:\data\Faces\Results\Unknown_1.png")
	# recognizer.identifyViaVideoFile(filepath=r"D:\data\Faces\Friends\FRIENDS - Season 6 Intro A [HD].mp4")

	# enroll(recognizer, usersEnroll)
	# identify(recognizer, usersIdentify)
	# recognizer.enrollFromCamera(0, "Anton", show=True)
	recognizer.identifyViaCamera(0)
	# recognizer.identifyViaVideoFile(r"D:\data\Faces\Demo.avi")


if __name__ == "__main__":
	main()