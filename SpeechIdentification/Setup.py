import os, sys
import subprocess
import urllib.request

_curPath = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_curPath, ".."))

from SetupTools import requireAnswer, installPackage, checkPIP

sys.path.pop()


versionsAccordance = {
	"100": "1.1.0",
	"90": "1.1.0",
	"92": "0.4.1",
	"80": "1.0.0"
}


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
		print(f"CUDA version {versionFull} is not suitable for pytorch installation, "
		      f"allowed versions list: {allowedCudaVersions}\n")
		version = None

	except Exception as e:
		print("CUDA library is not found with error:\n" + str(e))
		version = None

	if version.endswith("1"):
		version = version[:-1] + "0"

	return version


def checkPython():
	allowedVersions = [35, 36, 37]

	version = f"{sys.version_info[0]}{sys.version_info[1]}"

	if int(version) not in allowedVersions:
		print(f"Python version {version} is not suitable for pytorch installation, "
		      f"allowed versions list: {allowedVersions}\n")
		return None

	return version


def getPytorchVersion(cudaVersion, pythonVersion, platform):
	torchVersion = versionsAccordance[cudaVersion]

	if cudaVersion is None:
		print("Pytorch version for cpu will be installed. Proceed? (y/n)")
		answer = requireAnswer()

		if answer in ["y", "yes"]:
			prefix = "https://download.pytorch.org/whl/cpu"
			torchVersion = "1.1.0"
		elif answer in ["n", "no"]:
			return

	else:
		print("Pytorch version for gpu will be installed. Proceed? {y/n)")
		answer = requireAnswer()

		if answer in ["y", "yes"]:
			prefix = f"https://download.pytorch.org/whl/cu{cudaVersion}"
		elif answer in ["n", "no"]:
			return

	packages = {
		"torch": f"{prefix}/torch-{torchVersion}-cp{pythonVersion}-cp{pythonVersion}m-{platform}.whl",
		"torchvision": f"{prefix}/torchvision-0.3.0-cp{pythonVersion}-cp{pythonVersion}m-{platform}.whl"
	}

	return packages


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
	filename = "speaker_identification_model.pt"

	print("\nModel weights will be downloaded. Proceed? (y/n)")
	answer = requireAnswer()

	if answer in ["y", "yes"]:
		pass
	elif answer in ["n", "no"]:
		return

	url = "https://www.dropbox.com/s/khlhunvcfhqwl8r/speaker_identification_model.pt?dl=1"

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

	if "linux" in sys.platform:
		platform = "linux_x86_64"
	elif sys.platform == "win32":
		platform = "win_amd64"
	else:
		raise RuntimeError("Unsupported platform for installer")

	cudaVersion = checkCuda()
	pythonVersion = checkPython()

	proxy = setProxy()

	if pythonVersion is not None:
		pip = checkPIP()
		installedPackages = subprocess.check_output([pip, "list"]).decode("utf-8").split()

		packages = getPytorchVersion(cudaVersion, pythonVersion, platform)

		if packages:
			for package, url in packages.items():
				installPackage(pip, package, installedPackages, winPackages, proxy=proxy, url=url)

	downloadWeights()


if __name__ == "__main__":
	setup()