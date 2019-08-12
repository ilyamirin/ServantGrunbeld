import os, sys
import cv2

from base64 import b64encode
from pickle import dumps

from django.contrib import admin

from .models import User, Feature, ProfessionalInfo
from django.conf import settings


def _initRecognizer():
	# указываем абсолютный путь к папке, содержащей модуль FaceRecognition
	sys.path.append(r"D:\git_projects\FEFU\PipeleneDraft")
	from FaceRecognition.InsightFaceRecognition import RetinaFace, FaceRecognizer, DetectorConfig, RecognizerConfig
	sys.path.pop()

	os.environ.setdefault("MXNET_CUDNN_AUTOTUNE_DEFAULT", "0")
	detector = RetinaFace(
		prefix=DetectorConfig.PREFIX,
		epoch=DetectorConfig.EPOCH
	)

	recognizer = FaceRecognizer(
		prefix=RecognizerConfig.PREFIX,
		epoch=RecognizerConfig.EPOCH,
		dataBase=None,
		detector=detector
	)

	return recognizer


class FeaturesInline(admin.StackedInline):
	model = Feature
	radio_fields = {"gender": admin.HORIZONTAL}


class ProfessionalInfoInline(admin.StackedInline):
	model = ProfessionalInfo


@admin.register(User)
class UsersAdmin(admin.ModelAdmin):
	recognizer = None

	model = User

	userFieldSet = (
		"id",
		"name",
		"surname",
		"patronymic"
	)

	professionalInfoFieldSet = (
		"company",
		"position"
	)

	date_hierarchy = "registered"

	readonly_fields = ["showPhoto"]

	fields = ("showPhoto", "photo") + userFieldSet[1:]
	search_fields = (userFieldSet[1:] + ("professionalinfo__company", "professionalinfo__position"))

	list_display = (userFieldSet + ("age", "country", "hasPhoto", "hasEmbedding"))
	list_filter = (userFieldSet[1:] + ("professionalinfo__company", "professionalinfo__country"))
	list_per_page = 20

	inlines = [
		FeaturesInline,
		ProfessionalInfoInline
	]


	def age(self, obj):
		return obj.feature.age


	def country(self, obj):
		return obj.professionalinfo.country


	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)

		# высчитываем эмбеддинг, когда мы добавляем картинку к профилю пользователя
		# TODO: эмбеддинг не пересчитывается при загрузке другой фотографии для пользователя
		if not obj.hasEmbedding() and obj.photo.url is not None:
			if self.recognizer is None:
				# вынуждденная мера из-за приколов джанго; первый расчёт после запуска сервера будет долгим
				self.recognizer = _initRecognizer()

			path = os.path.join(settings.MEDIA_ROOT, os.path.split(obj.photo.url)[-1])
			embedding = self.getEmbedding(path)

			obj.embedding.vector = b64encode(dumps(embedding))
			obj.embedding.count = 1
			obj.embedding.save()


	def getEmbedding(self, path):
		image = cv2.imread(path, 1)

		embedding, _, _ = self.recognizer._processImageTensor(image)
		return embedding