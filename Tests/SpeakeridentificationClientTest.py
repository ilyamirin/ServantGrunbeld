import time

from SpeechIdentification.ServerKit.PytorchIdentificationClient import IdentifierClient


def main():
	with IdentifierClient(('localhost', 7700)) as client:
		while True:
			name, _ = client.identifyViaFile(r"D:\data\Speech\Voices_audio\MySets\Ayagma\ver\ayagma_ver1.wav")
			print(name)

			time.sleep(5)


if __name__ == "__main__":
	main()
