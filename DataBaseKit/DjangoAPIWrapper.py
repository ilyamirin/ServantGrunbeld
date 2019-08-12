import os, sys
import django

from base64 import b64decode, b64encode
from pickle import dumps, loads

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DataBase.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class EmbeddingNotExist(Exception):
	pass


class DataBase:
	def __init__(self, dbname=None, user=None, password=None):
		self.type = "django"

		from django.conf import settings

		dbsettings = settings.DATABASES["default"]
		settings.DATABASES = {
				'default': {
					'ENGINE': 'mysql.connector.django',
					'NAME': '{}'.format(dbname if dbname is not None else dbsettings["NAME"]),
					'USER': '{}'.format(user if user is not None else dbsettings["USER"]),
					'PASSWORD': '{}'.format(password if password is not None else dbsettings["PASSWORD"])
				}
			}

		django.setup()

		global User, Embedding
		try:
			from .DBManager.models import User
			from .DBManager.models import Embedding
		except ModuleNotFoundError:
			from DBManager.models import User
			from DBManager.models import Embedding
		except RuntimeError:
			from DBManager.models import User
			from DBManager.models import Embedding

	def __iter__(self):
		users = User.objects.all()
		users = (
			{
				"id": u.id,
				"name": u.name,
				"surname": u.surname,
				"patronymic": u.patronymic
			}
			for u in users if u.hasEmbedding()
		)

		return iter(users)


	@staticmethod
	def checkIncomingName(name, addIndex=False):
		return name


	@staticmethod
	def checkOutgoingName(name):
		return name


	@staticmethod
	def get(user, vector=None):
		id_ = user.get("id")

		try:
			embedding = User.objects.get(id=id_).embedding
			vector = embedding.vector
			if vector is None:
				raise EmbeddingNotExist
			vector = loads(b64decode(vector))
		except EmbeddingNotExist:
			print(f"User with index {id_} does not have embedding")
		except Exception as e:
			print(e)

		return vector


	@staticmethod
	def put(vector, name:str, count:int=1, surname:str=None, patronymic:str=None):
		user = User(name=name, surname=surname, patronymic=patronymic)
		user.save()

		user.embedding.vector = b64encode(dumps(vector))
		user.embedding.count = count
		user.embedding.save()

		print(f"User {user} has been successfully added to base with index {user.id}")


	@staticmethod
	def update(vector, name:str=None, count:int=1, surname:str=None, patronymic:str=None, id_:int=None):
		info = {}

		if name:
			info["name"] = name
		if surname:
			info["surname"] = surname
		if patronymic:
			info["patronymic"] = patronymic
		if id_:
			info["id"] = id_
		else:
			print("Nothing to update")
			return

		try:
			user = User.objects.get(**info)
		except MultipleObjectsReturned:
			print("Result with passed arguments  is ambiguous, try to pass index")
			return
		except ObjectDoesNotExist:
			print("Object with passed arguments does not exist")
			return

		oldVector = loads(b64decode(user.embedding.vector))
		oldCount = user.embedding.count

		vector = ((oldVector * oldCount) + (vector * count)) / (oldCount + count)
		vector = b64encode(dumps(vector))

		user.embedding.vector = vector
		user.embedding.count = count + oldCount
		user.embedding.save()

		print(f"User {user} with index {user.id} has been successfully updated")


def main():
	db = DataBase(
		dbname="django_experimental",
		user="root",
		password="FEFUdatabase"
	)

	db.get(user={"id":3})


if __name__ == "__main__":
	main()
