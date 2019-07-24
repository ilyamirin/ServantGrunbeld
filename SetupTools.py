import sys, subprocess


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


def installPackage(pip, package, installedPackages, manualList, **options):
	version = options.get("version", None)
	proxy = options.get("proxy", None)
	url = options.get("url", None)

	package = package if version is None else "{}=={}".format(package, version)

	if proxy is None:
		command = [pip, "install", package]
	else:
		command = [pip, "install", "--proxy", proxy, package]

	if url:
		command[-1] = url

	if not package in installedPackages:
		if "linux" in sys.platform or (sys.platform == "win32" and package not in manualList):
			try:
				print("Executing: " + " ".join(command))
				subprocess.call(command)

			except subprocess.CalledProcessError as e:
				print("Package '%s' installation error:\n" + e.output.decode("utf-8"))

				print("Exiting ...")
				sys.exit(1)

		elif sys.platform == "win32":
			print("Manually download and install package '%s' on Windows from %s" %
			      (package, "http://www.lfd.uci.edu/~gohlke/pythonlibs/#%s" % package))

			print("Exiting ...")
			sys.exit(1)

		else:
			raise RuntimeError("Unsupported platform for installer")
	else:
		print(f"Package {package} is already installed, continuing ...", end="\n")