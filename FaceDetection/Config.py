import os


class DetectorConfig:
	_currpath = os.path.dirname(os.path.abspath(__file__))

	PREFIX = os.path.join(_currpath, "Data/face_detection_model")
	EPOCH = 0
	CTX_ID = 0