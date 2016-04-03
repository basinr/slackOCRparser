
def process(bot_user_id, text):
	if bot_user_id not in text:
		return False

	if "help" in text:
		return help_menu()
	elif "start" in text:
		return "OCR enabled!"
	elif "stop" in text:
		return "OCR disabled!"
	elif "account" in text:
		return "account info TODO"


def help_menu():
	menu = "\n `start` to enable bot" \
		+ "\n `stop` to disable bot" \
		+ "\n `account` to see account info"

	return menu
