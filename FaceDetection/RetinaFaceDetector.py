import cv2
import numpy as np

import mxnet as mx
from mxnet import ndarray as nd

try:
	from .Utils.Preprocessing import preprocess
	from .Utils.Postprocessing import clipBoxes, generateAnchorsFPN, anchorsPlane, nms
except ImportError:
	from Utils.Preprocessing import preprocess
	from Utils.Postprocessing import clipBoxes, generateAnchorsFPN, anchorsPlane, nms


class TensorSizeError(Exception):
	pass


class RetinaFace:
	def __init__(self, prefix, epoch, ctxID=0):
		self.ctxID = ctxID

		if self.ctxID >= 0:
			self.ctx = mx.gpu(ctxID)
		else:
			self.ctx = mx.cpu()

		self._featStrideFPN = [32, 16, 8]
		self.keysFPN = ['stride%s' % s for s in self._featStrideFPN]

		self._anchorsFPN = self._createAnchorsFPN(self.keysFPN)
		self._numAnchors = dict(zip(self.keysFPN, [anchors.shape[0] for anchors in self._anchorsFPN.values()]))

		self.model = self._initNet(prefix, epoch)


	def _initNet(self, prefix, epoch):
		inshape = (640, 640)

		print("Please wait until detector is ready")

		sym, arg_params, aux_params = mx.model.load_checkpoint(prefix, epoch)
		model = mx.mod.Module(symbol=sym, context=self.ctx, label_names=None)
		model.bind(data_shapes=[('data', (1, 3, inshape[0], inshape[1]))], for_training=False)
		model.set_params(arg_params, aux_params)

		print("Detector has been initialized")

		return model


	@staticmethod
	def _createAnchorsFPN(keys):
		anchorCfg = {
			'32': {'SCALES': (32, 16), 'BASE_SIZE': 16, 'RATIOS': (1.,), 'ALLOWED_BORDER': 9999},
			'16': {'SCALES': (8, 4), 'BASE_SIZE': 16, 'RATIOS': (1.,), 'ALLOWED_BORDER': 9999},
			'8': {'SCALES': (2, 1), 'BASE_SIZE': 16, 'RATIOS': (1.,), 'ALLOWED_BORDER': 9999},
		}

		anchorsFPN = dict(zip(keys, generateAnchorsFPN(cfg=anchorCfg, denseAnchor=False)))
		anchorsFPN = {k: value.astype(np.float32) for k, value in anchorsFPN.items()}

		return anchorsFPN


	def _getAnchors(self, stride, mapShape):
		key = 'stride{}'.format(stride)
		numOfAnchors = self._numAnchors[key]

		height, width = mapShape
		mapArea = height * width

		anchorsFPN = self._anchorsFPN[key]
		anchors = anchorsPlane(height, width, stride, anchorsFPN)

		anchors = anchors.reshape((numOfAnchors * mapArea, 4))

		return anchors


	def _getBoxes(self, bboxDeltas, stride, mapShape, anchors, inputShape, ratio):
		key = 'stride{}'.format(stride)
		numOfAnchors = self._numAnchors[key]

		bboxDeltas = self._clipPad(bboxDeltas, mapShape)

		bboxDeltas = bboxDeltas.transpose((0, 2, 3, 1))
		bboxPredLen = bboxDeltas.shape[3] // numOfAnchors

		bboxDeltas = bboxDeltas.reshape((-1, bboxPredLen))

		proposals = self._calculateBoxes(anchors, bboxDeltas)
		proposals = clipBoxes(proposals, inputShape)

		proposals[:, 0:4] /= ratio

		return proposals


	def _getScores(self, scores, stride, mapShape):
		key = 'stride{}'.format(stride)
		numOfAnchors = self._numAnchors[key]

		scores = scores[:, numOfAnchors:, :, :]

		scores = self._clipPad(scores, mapShape)
		scores = scores.transpose((0, 2, 3, 1)).reshape((-1, 1))

		return scores


	def _getLandmarks(self, landmarksDeltas, stride, mapShape, anchors, ratio):
		key = 'stride{}'.format(stride)
		numOfAnchors = self._numAnchors[key]

		landmarksDeltas = self._clipPad(landmarksDeltas, mapShape)
		landmarkPredLen = landmarksDeltas.shape[1] // numOfAnchors
		landmarksDeltas = landmarksDeltas.transpose((0, 2, 3, 1)).reshape((-1, 5, landmarkPredLen // 5))

		landmarks = self._calculateLandmarks(anchors, landmarksDeltas)

		landmarks[:, :, 0:2] /= ratio

		return landmarks


	def process_image(self, image, maxSize=640, scoreThreshold=0.5, nmsThreshold=0.4, useLandmarks=True,
	                  alignment=False, resToDict=False):

		proposalsList = []
		scoresList = []
		landmarksList = []

		imTensor, ratio = preprocess(image, maxSize, alignment)
		inputShape = imTensor.shape[2:]
		data = nd.array(imTensor)
		db = mx.io.DataBatch(data=(data,), provide_data=[('data', data.shape)])

		self.model.forward(db, is_train=False)
		netOut = self.model.get_outputs()

		for idx, s in enumerate(self._featStrideFPN):
			idx *= 3
			stride = int(s)
			mapShape = netOut[idx].shape[2:]

			anchors = self._getAnchors(mapShape=mapShape, stride=stride)

			scores = self._getScores(scores=netOut[idx].asnumpy(), stride=stride, mapShape=mapShape)
			proposals = self._getBoxes(bboxDeltas=netOut[idx + 1].asnumpy(), stride=stride, mapShape=mapShape,
			                           anchors=anchors, inputShape=inputShape, ratio=ratio)

			scoresRavel = scores.ravel()
			order = np.where(scoresRavel >= scoreThreshold)[0]

			proposals = proposals[order, :]
			scores = scores[order]

			scoresList.append(scores)
			proposalsList.append(proposals)

			if useLandmarks:
				landmarks = self._getLandmarks(landmarksDeltas=netOut[idx + 2].asnumpy(), stride=stride,
				                               mapShape=mapShape, anchors=anchors, ratio=ratio)
				landmarks = landmarks[order, :]
				landmarksList.append(landmarks)

		proposals = np.vstack(proposalsList)
		scores = np.vstack(scoresList)

		scoresRavel = scores.ravel()
		order = scoresRavel.argsort()[::-1]

		proposals = proposals[order, :]
		scores = scores[order]

		preDet = np.hstack((proposals[:, 0:4], scores)).astype(np.float32, copy=False)

		keep = nms(preDet, nmsThreshold)

		proposals = proposals[keep, :]
		scores = scores[keep]

		proposals[:, (0, 1, 2, 3)] = proposals[:, (1, 0, 3, 2)]

		if useLandmarks:
			landmarks = np.vstack(landmarksList)
			landmarks = landmarks[order].astype(np.float32, copy=False)
			landmarks = landmarks[keep]
		else:
			landmarks = None

		return self.wrapInDict(proposals, scores, landmarks) if resToDict else (proposals, scores, landmarks)


	@staticmethod
	def wrapInDict(proposals, scores, landmarks=None):
		results = {
			"boxes": proposals,
			"text": ["face {:.2f}".format(s[0]) for s in scores],
			"keypoints": landmarks
		}

		return results


	@staticmethod
	def _clipPad(tensor, pad_shape):
		"""
		Clip boxes of the pad area.
		:param tensor: [n, c, H, W]
		:param pad_shape: [h, w]
		:return: [n, c, h, w]
		"""
		H, W = tensor.shape[2:]
		h, w = pad_shape

		if h < H or w < W:
			tensor = tensor[:, :, :h, :w].copy()

		return tensor


	@staticmethod
	def _calculateBoxes(boxes, boxDeltas):
		"""
		Transform the set of class-agnostic boxes into class-specific boxes
		by applying the predicted offsets (box_deltas)
		:param boxes: !important [N 4]
		:param boxDeltas: [N, 4 * num_classes]
		:return: [N 4 * num_classes]
		"""
		if boxes.shape[0] == 0:
			return np.zeros((0, boxDeltas.shape[1]))

		boxes = boxes.astype(np.float, copy=False)
		widths = boxes[:, 2] - boxes[:, 0] + 1.0
		heights = boxes[:, 3] - boxes[:, 1] + 1.0
		ctrX = boxes[:, 0] + 0.5 * (widths - 1.0)
		ctrY = boxes[:, 1] + 0.5 * (heights - 1.0)

		dx = boxDeltas[:, 0:1]
		dy = boxDeltas[:, 1:2]
		dw = boxDeltas[:, 2:3]
		dh = boxDeltas[:, 3:4]

		predCtrX = dx * widths[:, np.newaxis] + ctrX[:, np.newaxis]
		predCtrY = dy * heights[:, np.newaxis] + ctrY[:, np.newaxis]
		predW = np.exp(dw) * widths[:, np.newaxis]
		predH = np.exp(dh) * heights[:, np.newaxis]

		predBoxes = np.zeros(boxDeltas.shape)
		# x1
		predBoxes[:, 0:1] = predCtrX - 0.5 * (predW - 1.0)
		# y1
		predBoxes[:, 1:2] = predCtrY - 0.5 * (predH - 1.0)
		# x2
		predBoxes[:, 2:3] = predCtrX + 0.5 * (predW - 1.0)
		# y2
		predBoxes[:, 3:4] = predCtrY + 0.5 * (predH - 1.0)

		if boxDeltas.shape[1] > 4:
			predBoxes[:, 4:] = boxDeltas[:, 4:]

		return predBoxes


	@staticmethod
	def _calculateLandmarks(boxes, landmarksDeltas):
		if boxes.shape[0] == 0:
			return np.zeros((0, landmarksDeltas.shape[1]))

		boxes = boxes.astype(np.float, copy=False)

		widths = boxes[:, 2] - boxes[:, 0] + 1.0
		heights = boxes[:, 3] - boxes[:, 1] + 1.0
		ctrX = boxes[:, 0] + 0.5 * (widths - 1.0)
		ctrY = boxes[:, 1] + 0.5 * (heights - 1.0)

		pred = landmarksDeltas.copy()
		for i in range(5):
			pred[:, i, 0] = landmarksDeltas[:, i, 0] * widths + ctrX
			pred[:, i, 1] = landmarksDeltas[:, i, 1] * heights + ctrY

		return pred


def inferenceSpeedTest(detector: RetinaFace, image, maxSize=640):
	from time import time

	count = 11
	t_sum = 0
	for c in range(count):
		t1 = time()
		detector.process_image(image, maxSize=maxSize)
		if c != 0:
			t_sum += time() - t1

	print("Inference time with max image size {} is {}".format(maxSize, t_sum / 10))


def test():
	from ProjectUtils.Renderers import OpenCVRenderer as rnd
	try:
		from .Config import DetectorConfig
	except ImportError:
		from Config import DetectorConfig

	detector = RetinaFace(
		prefix=DetectorConfig.PREFIX,
		epoch=DetectorConfig.EPOCH,
		ctxID=DetectorConfig.CTX_ID
	)

	image = cv2.imread("./Data/example1.png")

	inferenceSpeedTest(detector, image, maxSize=720)

	results = detector.process_image(image, maxSize=720, resToDict=True)
	rnd.drawBoxes(image, **results, occurrence=rnd.Position.OUTER)
	rnd.show(image)


if __name__ == "__main__":
	test()