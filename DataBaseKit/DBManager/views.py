from django.http import HttpResponse


def image(request):
	return HttpResponse("You're looking at image.")
