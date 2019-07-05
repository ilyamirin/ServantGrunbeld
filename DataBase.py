import os
import h5py

import numpy as np


class DataBase:
	def __init__(self, filepath, showBase=True):
		self.filepath = filepath
		self._checkFileExistence(filepath)

		self.base = self._showBase() if showBase else None


	def __enter__(self):
		self.base = self._showBase()
		return self


	def __exit__(self, type, val, tb):
		del self


	def __iter__(self):
		if self.base is not None:
			return iter(self.base)
		else:
			with self._open(self.filepath, "r") as file:
				return iter(list(file.keys()))


	def __getitem__(self, item):
		if self.base is not None:
			return self.base[item]
		else:
			with self._open(self.filepath, "r") as file:
				return file[item][:]


	@staticmethod
	def _checkFileExistence(filepath):
		if not os.path.exists(filepath):
			os.makedirs(os.path.dirname(filepath), exist_ok=True)
			print("File {} doesn't exist, creating it".format(filepath))
			file = DataBase._open(filepath, "w")
			file.close()


	@staticmethod
	def _open(filepath, mode):
		return h5py.File(filepath, mode)


	def _showBase(self):
		with self._open(self.filepath, "r") as file:
			return {name:file[name][:] for name in file.keys()}


	def put(self, name, value):
		with self._open(self.filepath, "a") as file:
			try:
				if name in file:
					data = file[name]
					data[...] = value

				else:
					file.create_dataset(name=name, shape=(256,), data=value, dtype=np.float32, chunks=True)

				if self.base is not None:
					self.base[name] = value

			except Exception as e:
				print(e)


	def get(self, name):
		try:
			if self.base is not None:
				return self.base[name]
			else:
				with self._open(self.filepath, "r") as file:
					return file[name][:]
		except KeyError:
			print("No such user in base")