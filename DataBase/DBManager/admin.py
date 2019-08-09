from django.contrib import admin

from .models import User, Feature, ProfessionalInfo


class FeaturesInline(admin.StackedInline):
	model = Feature
	radio_fields = {"gender": admin.HORIZONTAL}


class ProfessionalInfoInline(admin.StackedInline):
	model = ProfessionalInfo


class UsersAdmin(admin.ModelAdmin):
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

	search_fields = (userFieldSet[1:] + ("feature__age", "professionalinfo__company", "professionalinfo__position"))

	list_display = (userFieldSet + ("age", "country", "hasEmbedding"))
	list_filter = (userFieldSet[1:] + ("feature__age", "professionalinfo__company", "professionalinfo__country"))
	list_per_page = 20

	inlines = [
		FeaturesInline,
		ProfessionalInfoInline
	]


	def age(self, obj):
		return obj.feature.age


	def country(self, obj):
		return obj.professionalinfo.country


admin.site.register(User, UsersAdmin)
