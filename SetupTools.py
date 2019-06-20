import sys, subprocess

from colorama import Fore, Style


def requireAnswer():
	answer = input().lower()

	while answer not in ["y", "n", "yes", "no"]:
		print("(y/n)")
		answer = requireAnswer()

	return answer


def checkPIP():
	usePip = "pip3"

	try:
		subprocess.check_output([usePip])
	except subprocess.CalledProcessError:
		usePip = "pip"

	return usePip


def installPackage(pip, package, installedPackages, manualList):
	if not package in installedPackages:
		if "linux" in sys.platform or (sys.platform == "win32" and package not in manualList):
			try:
				print(Fore.LIGHTBLUE_EX + "Installing package %s ..." % package + Style.RESET_ALL)
				result = subprocess.check_output([pip, "install", package])

				print(Fore.LIGHTGREEN_EX + "Package '%s' installation complete: "
				      % package + Style.RESET_ALL + str(result))

			except subprocess.CalledProcessError as e:
				print(Fore.RED + "Package '%s' installation error:\n" + Style.RESET_ALL + e.output.decode("utf-8"))

				print("Exiting ...")
				sys.exit(1)

		elif sys.platform == "win32":
			print(Fore.LIGHTBLUE_EX + "Manually download and install package '%s' on Windows from %s" %
			      (package, "http://www.lfd.uci.edu/~gohlke/pythonlibs/#%s" % package) + Style.RESET_ALL)

			print("Exiting ...")
			sys.exit(1)

		else:
			raise RuntimeError("Unsupported platform for installer")
	else:
		print(Fore.LIGHTGREEN_EX + "Package '%s' is already installed" % package + Style.RESET_ALL)
		print("Continuing ...", end="\n\n")