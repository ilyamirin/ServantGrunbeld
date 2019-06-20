class AzureCredentials:
	SUBSCRIPTION_KEY = "d7d1ad91f1fb4f54b9bda4345c2c0614"
	SERVICE_REGION = "francecentral"


class AzureConfig:
	RESPONSE_DETAILED = "detailed"
	RESPONSE_SIMPLE = "simple"

	LANG_RUS = "ru-RU"

	REST_PATH = "speech/recognition/conversation/cognitiveservices/v1"
	REST_BASE_URL = "https://{}.stt.speech.microsoft.com".format(AzureCredentials.SERVICE_REGION)
