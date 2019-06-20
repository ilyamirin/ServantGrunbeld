import cv2
import numpy as np


def preprocess(image, maxSize=640, alignment=False):
	height, width = image.shape[:2]

	ratio = min(maxSize / height, maxSize / width)

	if image.ndim == 3:
		image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	elif image.ndim == 2:
		image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
	elif image.ndim == 4:
		image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)

	image = cv2.resize(image, None, None, fx=ratio, fy=ratio, interpolation=cv2.INTER_LINEAR).astype(np.float32)

	if alignment:
		if height % 32 == 0:
			h = height
		else:
			h = (height // 32 + 1) * 32
		if width % 32 == 0:
			w = width
		else:
			w = (width // 32 + 1) * 32

		imTensor = np.zeros((h, w, 3), dtype=np.float32)
		imTensor[0:height, 0:width, :] = image
	else:
		imTensor = image

	imTensor = np.moveaxis(imTensor, 2, 0)[np.newaxis, ...]

	return imTensor, ratio