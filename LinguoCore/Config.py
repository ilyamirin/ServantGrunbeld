class CompanionConfig:
	NANOSEM_URL_INIT = 'https://biz.nanosemantics.ru/api/bat/nkd/json/Chat.init'
	NANOSEM_URL_REQ = 'https://biz.nanosemantics.ru/api/bat/nkd/json/Chat.request'

	BLOND = "blond"
	GOPNIK = "gopnik"

	GOPNIK_UUID = "46af8cb7-dbd8-476e-8bc3-03128d696ecf"
	GOPNIK_PUBKEY = "727552EB41E467C932DD80490FD69A52"

	BLOND_UUID = "4e9082d3-ce7a-40c8-a2a5-7ac9248e42df"
	BLOND_PUBKEY = "D3351F5642D2442E9C430CF9792AAAB0"


class AimlCompanionConfig:
	from platform import system as OS
	import os

	PORT = 8080
	HOST = "127.0.0.1"
	TCP_BUFFER_LEN = 16384
	SCRIPT_FILE = "NosferatuZodd-tcp.bat" if OS() == "Windows" else "NosferatuZodd-tcp.sh &"
	SCRIPT_PATH = os.path.join(".", "NosferatuZodd", "scripts", "windows" if OS() == "Windows" else "xnix", SCRIPT_FILE)
	SCRIPT_SHELL = "start" if OS() == "Windows" else "sh"
