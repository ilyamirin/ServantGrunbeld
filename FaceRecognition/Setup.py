import os, sys
import subprocess
import urllib.request

_curPath = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_curPath, ".."))

from SetupTools import requireAnswer, installPackage, checkPIP

sys.path.pop()


class RestrictedVersion(Exception):
	pass


def checkCuda():
	allowedCudaVersions = [101, 100, 92, 91, 90, 80]

	print("Checking CUDA ...")

	try:
		versionFull = subprocess.getoutput("nvcc --version").split()[-1]
		print("CUDA '%s' is found" % versionFull)
		version = "".join(versionFull.split(".")[:2]).replace("V", "")

		if int(version) not in allowedCudaVersions:
			raise RestrictedVersion

	except RestrictedVersion:
		print("CUDA version {} is not suitable for mxnet installation:\n".format(versionFull))
		version = None

	except Exception as e:
		print("CUDA library is not found with error:\n" + str(e))
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


def downloadFile(url, filename, proxy=None):
	def showProgress(count, blockSize, totalSize):
		print("\rDownloading progress {:.2f}%".format(count * blockSize * 100 / totalSize), end="")

	if proxy is not None:
		proxy = urllib.request.ProxyHandler({"http": proxy})
		opener = urllib.request.build_opener(proxy)
		urllib.request.install_opener(opener)

	urllib.request.urlretrieve(url, filename, showProgress)


def downloadWeights(proxy=None):
	folder = os.path.join(_curPath, "Data")
	filename = "face_recognition_model-0000456.params"

	print("\nModel weights will be downloaded. Proceed? (y/n)")
	answer = requireAnswer()

	if answer in ["y", "yes"]:
		pass
	elif answer in ["n", "no"]:
		return

	url = "https://www.dropbox.com/s/m84hve1x76v7vng/face_recognition_model-0000.params?dl=1"

	print("Downloading model weights ...")

	try:
		downloadFile(url, os.path.join(folder, filename), proxy)

	except Exception as e:
		print("Weights downloading error:\n" + str(e))
		return

	print(f"\nModel weights '{filename}' has been successfully placed in {folder}")


def setProxy():
	proxy = "http://proxy.dvfu.ru:3128"

	print(f"\nSet proxy {proxy}? (y/n)")
	answer = requireAnswer()

	if answer in ["y", "yes"]:
		return proxy
	elif answer in ["n", "no"]:
		return


def setup():
	winPackages = []

	pip = checkPIP()
	installedPackages = subprocess.check_output([pip, "list"]).decode("utf-8").split()

	mxnet_ = getMXNetVersion()

	proxy = setProxy()

	if mxnet_ is not None:
		installPackage(pip, mxnet_, installedPackages, winPackages, proxy=proxy)

	downloadWeights(proxy)


if __name__ == "__main__":
	setup()