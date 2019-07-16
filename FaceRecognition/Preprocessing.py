import cv2
import numpy as np
from skimage import transform as trans


def preprocessFace(image, landmarks):
	image_size = (112, 112)

	src = np.array([
		[38.2946, 51.6963],
		[73.5318, 51.5014],
		[56.0252, 71.7366],
		[41.5493, 92.3655],
		[70.7299, 92.2041]], dtype=np.float32)

	dst = landmarks.astype(np.float32)

	tform = trans.SimilarityTransform()
	tform.estimate(dst, src)
	M = tform.params[0:2, :]

	warped = cv2.warpAffine(image, M, (image_size[1], image_size[0]), borderValue=0.0)

	# cv2.imshow("file", warped)
	# cv2.waitKey(0)

	warped = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)

	return np.transpose(warped, (2, 0, 1))
