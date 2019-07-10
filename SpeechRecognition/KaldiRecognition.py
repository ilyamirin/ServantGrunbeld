try:
    from .Config import KaldiConfig
    from .RecognitionModule import Recognizer
except ImportError:
    from Config import KaldiConfig
    from RecognitionModule import Recognizer

from Microphone import MicrophoneRecorder, AUTO_DURATION_LIMIT, AUTO_SILENCE_LIMIT
import socket
import sys
import subprocess
import pyaudio
import asyncio
from time import sleep


class KaldiOnlineRecognizer(Recognizer):
    def __init__(self, language="ru-RU"):
        super().__init__(language)
        self.handleIntermediate = lambda *args, **kwargs: None
        self.handleFinal = lambda *args, **kwargs: None
        self.kaldi_socket = None
        self.connected = False

    def start(self, script_name="tcp-decode.sh", timeout=10):
        """Запуск ехешника со ВСЕМИ параметрами сейчас захардкожен в скрипте"""
        res = subprocess.call(
            f"sh {script_name} --port-num={KaldiConfig.port} --read-timeout=-1 &",
            stdout=sys.stdout, stderr=sys.stderr, shell=True)
        if res != 0:
            raise RuntimeError(f"Не удалось запустить распознаватель. Код ошибки: {res}")
        self.kaldi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.kaldi_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        timedelta = 0.1
        while self.kaldi_socket.connect_ex((KaldiConfig.host, KaldiConfig.port)) != 0 and timeout > 0:
            timeout -= timedelta
            sleep(timedelta)
        self.connected = True
        data = []
        while True:
            data.append(self.kaldi_socket.recv(1))
            if data[-1] == b'\r' or data[-1] == b'\n':
                self.handleIntermediate((b"".join(data)).decode("utf-8"))
                data = []

    def stop(self):
        pass

    def processAudio(self, record):
        # send a chunk over tcp socket
        pass

    def processAudioFile(self, file):
        raise NotImplementedError

    def processMicrophone(self):
        raise NotImplementedError
        # record = self.microphone.recordManual()
        # result = self.processAudio(record)

    def processChunk(self, data):
        # src/online2bin/online2-tcp-nnet3-decode-faster
        # печатает \r в конце каждой lattice
        # \n в конце feature pipeline
        """Скормить огрызок распознавалке"""
        if self.kaldi_socket is not None and self.connected:
            self.kaldi_socket.send(data)

    def registerIntermediateRecognitionHandler(self, callback):
        self.handleIntermediate = callback

    def registerFinalRecognitionHandler(self, callback):
        self.handleFinal = callback


class PyAudioHelper:
    def __init__(self, recognizer, microphone):
        self.recognizer = recognizer
        self.mic = microphone
        self.session_running = False
        self.mic_stream = microphone.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=KaldiConfig.samp_freq,
            input=True,
            output=True,
            frames_per_buffer=KaldiConfig.chunk_length,
            stream_callback=self.streamCallback
        )

    def streamCallback(self, in_data, frame_count, time_info, status):
        self.recognizer.processChunk(in_data)
        return in_data, pyaudio.paContinue if self.session_running else pyaudio.paComplete

    def handleIntermediate(self, text):
        print(text)
        sys.stdout.flush()


    def handleFinal(self, text):
        print(text, '\n')
        sys.stdout.flush()

    def startStream(self):
        print("pa_helper: stream started")
        self.session_running = True
        self.mic_stream.start_stream()
        self.recognizer.start()

    def stopStream(self):
        self.session_running = False
        self.recognizer.stop()
        self.mic_stream.stop_stream()
        self.mic_stream.close()
        print("pa_helper: stream finished")


def main():
    recognizer = KaldiOnlineRecognizer()
    microphone = pyaudio.PyAudio()
    pyh = PyAudioHelper(recognizer, microphone)
    recognizer.registerIntermediateRecognitionHandler(pyh.handleIntermediate)
    recognizer.registerFinalRecognitionHandler(pyh.handleFinal)
    pyh.startStream()
    pyh.stopStream()


__all__ = [KaldiOnlineRecognizer]

if __name__ == "__main__":
    main()
