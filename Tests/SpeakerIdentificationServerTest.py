from SpeechIdentification.ServerKit.PytorchIdentificationServer import IdentifierServer


def main():
	server = IdentifierServer(
		address=('localhost', 7700)
	)

	server.run()


if __name__ == "__main__":
	main()