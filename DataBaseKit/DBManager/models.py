from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe


class User(models.Model):
	userID = models.AutoField(primary_key=True, name="id", editable=False)
	name = models.CharField(max_length=255, name="name", null=False)
	surname = models.CharField(max_length=255, name="surname", blank=True, null=True)
	patronymic = models.CharField(max_length=255, name="patronymic", blank=True, null=True)
	registered = models.DateTimeField(name="registered", default=timezone.now, editable=False)
	modified = models.DateTimeField(name="modified", default=timezone.now)
	photo = models.ImageField(name="photo", null=True, blank=True)

	class Meta(object):
		ordering = ["id"]

	def hasEmbedding(self):
		return self.embedding.vector is not None


	hasEmbedding.boolean = True
	hasEmbedding.short_description = "embedding exists"


	def hasPhoto(self):
		return self.photo is not None


	hasPhoto.boolean = True
	hasPhoto.short_description = "photo uploaded"


	def showPhoto(self):
		if self.photo.url is not None:
			html = """<a href="{src}" target="_blank"><img src="{src}" alt="{title}" 
			style="max-width: 200px; max-height: 200px;" /></a>""".format(src=self.photo.url, title=self)

			return mark_safe(html)

		return "Download photo using button 'Choose File' below"


	showPhoto.short_description = 'Image'


	def save(self, update=False, *args, **kwargs):
		createRelatives = self.id is None

		super().save(*args, **kwargs)
		print("user saved")

		if createRelatives:
			Feature.objects.create(id=self)
			ProfessionalInfo.objects.create(id=self)
			Embedding.objects.create(id=self)
			print("relatives created")


	def __str__(self):
		fields = (i for i in (self.surname, self.name, self.patronymic) if i is not None)
		return " ".join(fields)


class ProfessionalInfo(models.Model):
	userID = models.OneToOneField(
		to="User",
		to_field="id",
		on_delete=models.CASCADE,
		primary_key=True,
		name="id")

	country = models.CharField(max_length=255, name="country", blank=True, null=True)
	company = models.CharField(max_length=255, name="company", blank=True, null=True)
	position = models.CharField(max_length=255, name="position", blank=True, null=True)


class Feature(models.Model):
	genders = (
		("male", "male"),
		("female", "female")
	)

	userID = models.OneToOneField(
		to="User",
		to_field="id",
		on_delete=models.CASCADE,
		primary_key=True,
		name="id")

	birthdate = models.DateField(name="birthdate", blank=True, null=True)
	gender = models.CharField(max_length=6, choices=genders, blank=True, null=True)
	height = models.PositiveSmallIntegerField(name="height", blank=True, null=True)
	weight = models.PositiveSmallIntegerField(name="weight", blank=True, null=True)
	nationality = models.CharField(max_length=30, name="nationality", blank=True, null=True)


	def returnAge(self):
		today = timezone.now()
		born = self.birthdate

		if born is None:
			return None

		return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


	age = property(returnAge)


class Embedding(models.Model):
	userID = models.OneToOneField(
		to="User",
		to_field="id",
		on_delete=models.CASCADE,
		primary_key=True,
		name="id")

	vector = models.BinaryField(max_length=4096, name="vector", blank=True, null=True)
	count = models.PositiveSmallIntegerField(name="count", blank=True, null=True)
