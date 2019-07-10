try:
    from .Config import KaldiConfig
    from .RecognitionModule import Recognizer
except ImportError:
    from Config import KaldiConfig
    from RecognitionModule import Recognizer

from Microphone import MicrophoneRecorder, AUTO_DURATION_LIMIT, AUTO_SILENCE_LIMIT
import socket
import subprocess
import pyaudio


class KaldiRecognizer(Recognizer):
    def processAudio(self, record):
        raise NotImplementedError

    def processAudioFile(self, file):
        raise NotImplementedError

    def processMicrophone(self):
        raise NotImplementedError


class KaldiOnlineRecognizer(Recognizer):
    def __init__(self, language="ru-RU"):
        super().__init__(language)
        self.microphone = MicrophoneRecorder(
            audioFormat=pyaudio.paInt16,
            chunkSize=KaldiConfig.microphone_frames_per_chunk,
            rate=KaldiConfig.samp_freq
        )

    def processAudio(self, record):
        pass

        # send a chunk over tcp socket

    def processAudioFile(self, file):
        raise NotImplementedError

    def processMicrophone(self):
        self.microphone.initPipe()
        record = self.microphone.recordManual()
        result = self.processAudio(record)

    def _processChunk(self, chunk):
        """"""
        pass


def main():
    pass


__all__ = [KaldiOnlineRecognizer]

if __name__ == "__main__":
    main()
