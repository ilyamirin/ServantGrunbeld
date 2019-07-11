import os
import h5py

import numpy as np


class DataBase:
	def __init__(self, filepath, showBase=True, locked=False):
		self.filepath = filepath
		self._checkFileExistence(filepath)

		self.base = None
		if showBase:
			self.base = self._showBase()

		self.locked = locked


	def __enter__(self):
		self.base = self._showBase()
		return self


	def __exit__(self, type_, val, tb):
		del self


	def __iter__(self):
		return iter(self.keys())


	def __getitem__(self, item):
		if self.base is not None:
			return self._getNested(self.base, item)
		else:
			with self._open(self.filepath, "r") as file:
				return file[item][:]


	def __len__(self):
		return len(self.keys())


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


	@staticmethod
	def _getFullKeys(base, keys=None, keyString=None):
		keys = [] if keys is None else keys

		if keyString is not None and (isinstance(base, np.ndarray) or isinstance(base, h5py.Dataset)):
			keys.append(keyString)
		else:
			for key in base.keys():
				keyStringExtended = f"{keyString}/{key}" if keyString is not None else f"{key}"
				keys = DataBase._getFullKeys(base[key], keys, keyStringExtended)

		return keys


	@staticmethod
	def _putNested(base, keys, value):
		keys = keys.split("/")

		key = keys.pop(0)

		if not keys:
			base[key] = value
		else:
			base[key] = base.get(key, {})
			DataBase._putNested(base[key], "/".join(keys), value)


	@staticmethod
	def _getNested(base, keys):
		keys = keys.split("/")

		key = keys.pop(0)

		if not keys:
			return base[key]
		else:
			return DataBase._getNested(base[key], "/".join(keys))


	def _showBase(self):
		with self._open(self.filepath, "r") as file:
			base = {}
			for key in self.keys():
				self._putNested(base, key, file[key][:])

			return base


	def keys(self):
		if self.base is not None:
			return self._getFullKeys(self.base)
		else:
			with self._open(self.filepath, "r") as file:
				return self._getFullKeys(file)


	def put(self, name, value, shape=(256,)):
		if self.locked:
			raise PermissionError("Data base is locked")

		with self._open(self.filepath, "a") as file:
			try:
				if name in file:
					data = file[name]
					data[...] = value

				else:
					file.create_dataset(name=name, shape=shape, data=value, dtype=np.float32, chunks=True)

				if self.base is not None:
					self._putNested(self.base, name, value)

			except Exception as e:
				print(e)


	def get(self, name, value=None):
		try:
			if self.base is not None:
				return self._getNested(self.base, name)
			else:
				with self._open(self.filepath, "r") as file:
					result = file[name]

					if not isinstance(result, h5py.Dataset):
						raise TypeError

					return result[:]

		except KeyError:
			print("User {} isn't represented in base".format(name))
			return value
		except TypeError:
			print("Variable 'name' must be full and lead to embedding")
			return value


def main():
	db = DataBase(r"D:\git_projects\FEFU\PipeleneDraft\Diarization\Temp\users_test.hdf", showBase=True)

	for key in db:
		print(key)


if __name__ == "__main__":
	main()