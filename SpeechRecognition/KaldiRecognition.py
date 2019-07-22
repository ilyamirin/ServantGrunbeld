try:
    from .Config import KaldiConfig
    from .RecognitionModule import Recognizer
except ImportError:
    from Config import KaldiConfig
    from RecognitionModule import Recognizer

from ProjectUtils.Microphone import MicrophoneRecorder
import socket
import sys
import subprocess
import pyaudio
from time import sleep
import wave
import json
import datetime


class KaldiOnlineRecognizer(Recognizer):
    def __init__(self, language="ru-RU"):
        super().__init__(language)
        self.handle_intermediate = []
        self.handle_final = []
        self.kaldi_socket = None
        self.connected = False
        self.record = []

    def start(self, script_name="tcp-decode.sh", timeout=1, attempts=3, timeout_increment=1):
        """Запуск ехешника сейчас захардкожен в скрипте"""

        self.kaldi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.kaldi_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.connected = False
        while not self.connected and attempts > 0:
            attempts -= 1
            timeout_, timedelta = timeout, 0.1
            timeout += timeout_increment
            self.connected = self.kaldi_socket.connect_ex((KaldiConfig.host, KaldiConfig.port)) == 0
            while not self.connected and timeout_ > 0:
                timeout_ -= timedelta
                sleep(timedelta)
                self.connected = self.kaldi_socket.connect_ex((KaldiConfig.host, KaldiConfig.port)) == 0
            if not self.connected:
                subprocess.call(
                    f"sh {script_name} --port-num={KaldiConfig.port} --read-timeout=-1 &",
                    stdout=sys.stdout, stderr=sys.stderr, shell=True
                )
        if not self.connected:
            raise RuntimeError("Не удалось запустить распознаватель")
        print("Говорите...", flush=True)

    def stop(self):
        pass

    def runLoop(self):
        sentence = []
        self.record = []
        while True:
            data = self.kaldi_socket.recv(1)
            sentence.append(data)
            if sentence and sentence[-1] == b'\r':
                for func in self.handle_intermediate:
                    func(b"".join(sentence).decode("utf-8"))
                sentence = []
            if not data or sentence and sentence[-1] == b'\n':
                self.stop()
                for func in self.handle_final:
                    func(b"".join(sentence).decode("utf-8"))
                break

    def processAudio(self, record):
        # send a chunk over tcp socket
        pass

    def processAudioFile(self, file):
        raise NotImplementedError

    def processMicrophone(self):
        raise NotImplementedError
        # record = self.microphone.recordManual()
        # result = self.processAudio(record)

    def sendChunk(self, data):
        # src/online2bin/online2-tcp-nnet3-decode-faster
        # печатает \r в конце каждой lattice
        # \n в конце feature pipeline
        self.record.extend(data)
        """Скормить огрызок распознавалке"""
        if self.kaldi_socket is not None and self.connected:
            self.kaldi_socket.send(data)

    def recv(self, bufsize=1024):
        return self.kaldi_socket.recv(bufsize)

    def registerIntermediateRecognitionHandler(self, callback):
        self.handle_intermediate.append(callback)

    def registerFinalRecognitionHandler(self, callback):
        self.handle_final.append(callback)


class PyAudioHelper:
    def __init__(self, recognizer):
        self.recognizer = recognizer
        self.session_running = False
        self.mic = MicrophoneRecorder(
            chunkSize=KaldiConfig.chunk_length,
            rate=KaldiConfig.samp_freq,
        )

    def streamCallback(self, in_data, frame_count, time_info, status):
        self.recognizer.sendChunk(in_data)
        return in_data, pyaudio.paContinue if self.session_running else pyaudio.paComplete

    def handleIntermediate(self, text):
        if text is None:
            return
        text = text.strip()
        if text == "":
            return
        print(text)
        sys.stdout.flush()

    def handleFinal(self, text):
        if text is None:
            return
        text = text.strip()
        if text == "":
            return
        print(f"— {text}")
        sys.stdout.flush()
        file = wave.open(f"./records/record{datetime.datetime.now()}.wav", 'wb')
        file.setnchannels(1)
        file.setsampwidth(self.mic.getSampleSize())
        file.setframerate(KaldiConfig.samp_freq)
        file.writeframes(bytearray(self.recognizer.record))
        file.close()
        # answer = self.talk(text)
        # print(f"— {answer.strip() if answer else '...'}\n")

    def startStream(self):
        self.session_running = True
        # start_stream микрофона запускает асинхронное прослушивание
        self.mic.startStream(callback=self.streamCallback)
        # recognizer.start запускает блокирующий цикл.
        # запуск самой распознавалки занимает время, к тому же занимает целый порт,
        # поэтому каждый запуск/остановка распознавалки должна соответствовать сессии целиком.
        # внутри одной сессии контекст обнуляется между предложениями (опр. продолжительными паузами)
        self.recognizer.start()

    def stopStream(self):
        self.session_running = False
        self.recognizer.stop()
        self.mic.stopStream()


def main():
    recognizer = KaldiOnlineRecognizer()
    pyh = PyAudioHelper(recognizer)
    recognizer.registerIntermediateRecognitionHandler(pyh.handleIntermediate)
    recognizer.registerFinalRecognitionHandler(pyh.handleFinal)
    while True:
        pyh.startStream()
        pyh.stopStream()


__all__ = [KaldiOnlineRecognizer]

if __name__ == "__main__":
    main()
