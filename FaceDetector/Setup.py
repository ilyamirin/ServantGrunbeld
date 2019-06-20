import os, sys
import subprocess
import urllib.request

from colorama import Fore, Style

_curPath = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_curPath, ".."))

from SetupTools import requireAnswer, installPackage, checkPIP

sys.path.pop()


class RestrictedVersion(Exception):
	pass


if not "PYCHARM_HOSTED" in os.environ:
	import colorama
	colorama.init()


def checkCuda():
	allowedCudaVersions = [101, 100, 92, 90, 80]

	print(Fore.LIGHTBLUE_EX + "Checking CUDA ..." + Style.RESET_ALL)

	try:
		versionFull = subprocess.getoutput("nvcc --version").split()[-1]
		print(Fore.LIGHTGREEN_EX + "CUDA '%s' is found" % versionFull + Style.RESET_ALL)
		version = "".join(versionFull.split(".")[:2]).replace("V", "")

		if int(version) not in allowedCudaVersions:
			raise RestrictedVersion

	except RestrictedVersion:
		print(Fore.RED + "CUDA version {} is not suitable for mxnet installation:\n".
		      format(versionFull) + Style.RESET_ALL)
		version = None

	except Exception as e:
		print(Fore.RED + "CUDA library is not found with error:\n" + Style.RESET_ALL + str(e))
		version = None

	return version


def getMXNetVersion():
	cudaVersion = checkCuda()

	if cudaVersion is None:
		print("MXNet version for cpu will be installed. Proceed? (y/n)")
		answer = requireAnswer()

		if answer in ["y", "yes"]:
			mxnet_ = "mxnet"
		elif answer in ["n", "no"]:
			return

	else:
		print("MXNet version for gpu will be installed. Proceed? {y/n)")
		answer = requireAnswer()

		if answer in ["y", "yes"]:
			mxnet_ = "mxnet-cu{}".format(cudaVersion)
		elif answer in ["n", "no"]:
			return

	return mxnet_


def downloadFile(url, filename):
	def showProgress(count, blockSize, totalSize):
		print("\rDownloading progress {:.2f}%".format(count * blockSize * 100 / totalSize), end="")

	urllib.request.urlretrieve(url, filename, showProgress)


def downloadWeights():
	folder = os.path.join(_curPath, "Data")
	filename = os.path.join(folder, "R50-0000.params")

	print("\nModel weights will be downloaded. Proceed? (y/n)")
	answer = requireAnswer()

	if answer in ["y", "yes"]:
		pass
	elif answer in ["n", "no"]:
		return

	with open(os.path.join(folder, "weightsURL.txt"), "r") as urlf:
		url = urlf.read().strip()

	print(Fore.LIGHTBLUE_EX + "Downloading model weights ..." + Style.RESET_ALL)

	try:
		downloadFile(url, filename)

	except Exception as e:
		print(Fore.RED + "Weights downloading error:\n" + Style.RESET_ALL + str(e))
		return

	print(Fore.LIGHTGREEN_EX + "\nModel weights '%s' has been successfully placed in: " + Style.RESET_ALL + folder)


def setup():
	winPackages = []

	pip = checkPIP()
	installedPackages = subprocess.check_output([pip, "list"]).decode("utf-8").split()

	mxnet_ = getMXNetVersion()

	if mxnet_ is not None:
		installPackage(pip, mxnet_, installedPackages, winPackages)

	downloadWeights()


if __name__ == "__main__":
	setup()