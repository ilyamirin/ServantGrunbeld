from SpeechIdentification.ServerKit.PytorchIdentificationServer import IdentifierServer
from SpeechIdentification.Config import RecognizerConfig
from ProjectUtils.DataBase import DataBase


def main():
	dataBase = DataBase(
		filepath=r"D:\git_projects\FEFU\PipeleneDraft\SpeechIdentification\Temp\users_new_base.hdf",
		showBase=True
	)

	server = IdentifierServer(
		modelpath=RecognizerConfig.MODEL_PATH,
		dataBase=dataBase,
		address=('localhost', 7700)
	)

	server.run()


if __name__ == "__main__":
	main()