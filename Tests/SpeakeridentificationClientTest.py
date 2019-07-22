from SpeechIdentification.ServerKit.PytorchIdentificationClient import IdentifierClient


def main():
	client = IdentifierClient(('localhost', 7700))

	name, _ = client.identifyViaMicrophone()
	print(name)


if __name__ == "__main__":
	main()
