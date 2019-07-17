try:
    from .Config import AimlCompanionConfig as CFG
except ImportError:
    from Config import AimlCompanionConfig as CFG
import json
import sys
import socket
from time import sleep
import subprocess


class AimlCompanion:
    def __init__(self, start_server=False):
        self.aiml_socket = None
        self.aiml_connected = False
        if start_server:
            self._startServer()

    def _startServer(self):
        if not self.aiml_connected:
            subprocess.call(
                f"{CFG.SCRIPT_SHELL} {CFG.SCRIPT_PATH}",
                stdout=sys.stdout, stderr=sys.stderr, shell=True
            )

    def send(self, question, userid='anon'):
        if not self.aiml_connected and not self.connectToAiml():
            print("AIML server not found", flush=True, file=sys.stderr)
            return None
        query = {
            "userid": userid,
            "question": question
        }
        self.aiml_socket.send(json.dumps(query).encode())
        answer = self.aiml_socket.recv(CFG.TCP_BUFFER_LEN).decode('utf-8')
        data = json.loads(answer)
        if self.aiml_connected:
            self.aiml_connected = False
            self.aiml_socket.close()
        return data['answer']['text'] if data['result'] == "OK" else None

    def connectToAiml(self, timeout=1, attempts=3, timeout_increment=1):
        self.aiml_connected = False
        self.aiml_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while not self.aiml_connected and attempts > 0:
            attempts -= 1
            timeout_, timedelta = timeout, 0.1
            timeout += timeout_increment
            self.aiml_connected = self.aiml_socket.connect_ex((CFG.HOST, CFG.PORT)) == 0
            while not self.aiml_connected and timeout_ > 0:
                timeout_ -= timedelta
                sleep(timedelta)
                self.aiml_connected = self.aiml_socket.connect_ex((CFG.HOST, CFG.PORT)) == 0
        return self.aiml_connected


def test():
    companion = AimlCompanion(start_server=True)

    print("Ready to chat")
    while True:
        text = input()
        result = companion.send(text)
        print(result)


if __name__ == "__main__":
    test()
