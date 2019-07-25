import os


class RecognizerConfig:
	_currpath = os.path.dirname(os.path.abspath(__file__))

	PREFIX = os.path.join(_currpath, "Data/face_recognition_model")
	EPOCH = 0
	CTX_ID = 0

	DATA_BASE_PATH = os.path.join(_currpath, "Data/data_base_faces.hdf")