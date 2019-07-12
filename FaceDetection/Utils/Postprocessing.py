import numpy as np


def clipBoxes(boxes, imShape):
	"""
	Clip boxes to image boundaries.
	:param boxes: [N, 4* num_classes]
	:param imShape: tuple of 2
	:return: [N, 4* num_classes]
	"""
	# x1 >= 0
	boxes[:, 0::4] = np.maximum(np.minimum(boxes[:, 0::4], imShape[1] - 1), 0)
	# y1 >= 0
	boxes[:, 1::4] = np.maximum(np.minimum(boxes[:, 1::4], imShape[0] - 1), 0)
	# x2 < im_shape[1]
	boxes[:, 2::4] = np.maximum(np.minimum(boxes[:, 2::4], imShape[1] - 1), 0)
	# y2 < im_shape[0]
	boxes[:, 3::4] = np.maximum(np.minimum(boxes[:, 3::4], imShape[0] - 1), 0)

	return boxes


def nms(dets, thresh):
	"""
	greedily select boxes with high confidence and overlap with current maximum <= thresh
	rule out overlap >= thresh
	:param dets: [[x1, y1, x2, y2 score]]
	:param thresh: retain overlap < thresh
	:return: indexes to keep
	"""
	x1 = dets[:, 0]
	y1 = dets[:, 1]
	x2 = dets[:, 2]
	y2 = dets[:, 3]
	scores = dets[:, 4]

	areas = (x2 - x1 + 1) * (y2 - y1 + 1)
	order = scores.argsort()[::-1]

	keep = []
	while order.size > 0:
		i = order[0]
		keep.append(i)
		xx1 = np.maximum(x1[i], x1[order[1:]])
		yy1 = np.maximum(y1[i], y1[order[1:]])
		xx2 = np.minimum(x2[i], x2[order[1:]])
		yy2 = np.minimum(y2[i], y2[order[1:]])

		w = np.maximum(0.0, xx2 - xx1 + 1)
		h = np.maximum(0.0, yy2 - yy1 + 1)
		inter = w * h
		ovr = inter / (areas[i] + areas[order[1:]] - inter)

		inds = np.where(ovr <= thresh)[0]
		order = order[inds + 1]

	return keep


def anchorsPlane(height, width, stride, baseAnchors):
	gridX = np.tile(np.reshape(np.arange(width), [1, -1, 1, 1]), [height, 1, 1, 1])
	gridY = np.tile(np.reshape(np.arange(height), [-1, 1, 1, 1]), [1, width, 1, 1])

	grid = np.concatenate([gridX, gridY, gridX, gridY], axis=-1)
	allAnchors = grid * stride + baseAnchors

	return allAnchors


def generateAnchors(baseSize=16, ratios=None, scales=None, stride=16, denseAnchor=False):
	"""
	Generate anchor (reference) windows by enumerating aspect ratios X
	scales wrt a reference (0, 0, 15, 15) window.
	"""
	ratios = [0.5, 1, 2] if ratios is None else ratios
	scales = 2 ** np.arange(3, 6) if scales is None else scales

	baseAnchor = np.array([1, 1, baseSize, baseSize]) - 1
	ratioAnchors = _ratioEnum(baseAnchor, ratios)
	anchors = np.vstack([_scaleEnum(ratioAnchors[i, :], scales) for i in range(ratioAnchors.shape[0])])

	if denseAnchor:
		assert stride % 2 == 0
		anchors2 = anchors.copy()
		anchors2[:, :] += int(stride / 2)
		anchors = np.vstack((anchors, anchors2))

	return anchors


def generateAnchorsFPN(cfg, denseAnchor=False):
	# assert(False)
	"""
	Generate anchor (reference) windows by enumerating aspect ratios X
	scales wrt a reference (0, 0, 15, 15) window.
	"""

	featStrideRPN = []
	for k in cfg:
		featStrideRPN.append(int(k))

	featStrideRPN = sorted(featStrideRPN, reverse=True)

	anchors = []
	for k in featStrideRPN:
		v = cfg[str(k)]
		bs = v['BASE_SIZE']
		ratios = np.array(v['RATIOS'])
		scales = np.array(v['SCALES'])
		stride = int(k)

		r = generateAnchors(bs, ratios, scales, stride, denseAnchor)

		anchors.append(r)

	return anchors


def _whctrs(anchor):
	"""
	Return width, height, x center, and y center for an anchor (window).
	"""

	w = anchor[2] - anchor[0] + 1
	h = anchor[3] - anchor[1] + 1

	xCtr = anchor[0] + 0.5 * (w - 1)
	yCtr = anchor[1] + 0.5 * (h - 1)

	return w, h, xCtr, yCtr


def _mkanchors(ws, hs, xCtr, yCtr):
	"""
	Given a vector of widths (ws) and heights (hs) around a center
	(x_ctr, y_ctr), output a set of anchors (windows).
	"""

	ws = ws[:, np.newaxis]
	hs = hs[:, np.newaxis]
	anchors = np.hstack((xCtr - 0.5 * (ws - 1),
	                     yCtr - 0.5 * (hs - 1),
	                     xCtr + 0.5 * (ws - 1),
	                     yCtr + 0.5 * (hs - 1)))

	return anchors


def _ratioEnum(anchor, ratios):
	"""
	Enumerate a set of anchors for each aspect ratio wrt an anchor.
	"""

	w, h, xCtr, yCtr = _whctrs(anchor)
	size = w * h
	sizeRatios = size / ratios
	ws = np.round(np.sqrt(sizeRatios))
	hs = np.round(ws * ratios)
	anchors = _mkanchors(ws, hs, xCtr, yCtr)

	return anchors


def _scaleEnum(anchor, scales):
	"""
	Enumerate a set of anchors for each scale wrt an anchor.
	"""
	w, h, xCtr, yCtr = _whctrs(anchor)
	ws = w * scales
	hs = h * scales
	anchors = _mkanchors(ws, hs, xCtr, yCtr)

	return anchors