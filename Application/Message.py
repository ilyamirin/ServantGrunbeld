import time
import pickle


class Message:
    AUDIO_CHUNK = 0
    VIDEO_FRAME = 1
    SUBSCRIBE = 2
    RECOGNIZED_SPEECH = 3
    RECOGNIZED_FACE_ROI = 4
    BOT_ANSWER = 5
    ROBOVOICE = 6

    def __init__(self, timestamp=None, type_=None, data=None, device_id=None):
        self.type = type_
        self.data = data
        self.timestamp = timestamp if timestamp else time.time()
        self.device_id = device_id

    def dumps(self):
        return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def loads(data: bytes):  # невозможно аннотировать возвращаемый тип в текущем классе, если тип и есть текущий класс
        return pickle.loads(data)
