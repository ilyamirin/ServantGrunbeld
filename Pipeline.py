from SpeechRecognition.AzureRecognition import AzureRecognizer
from SpeechSynthesis.AzureSynthesis import AzureSynthesizer
from LinguoCore.Companion import Companion


def main():
	recognizer = AzureRecognizer()
	print("Recognizer is ready")

	linguoCore = Companion()
	print("Companion is ready to chat")

	synthesizer = AzureSynthesizer()
	print("Synthesizer is ready")

	print("Here you go")
	attempts = 3
	for _ in range(attempts):
		text = recognizer.processMicrophoneREST()
		response = linguoCore.send(text)
		synthesizer.process(response, voiceIdx=0)

	print()
	linguoCore.printDialog()


if __name__ == "__main__":
	main()