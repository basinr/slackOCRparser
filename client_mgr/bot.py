
def process(bot_user_id, text):
	if bot_user_id not in text:
		return False

	if text == "help":
		return help_menu()
	elif text == "start":
		return "OCR enabled!"
	elif text == "stop":
		return "OCR disabled!"
	elif text == "account":
		return "account info TODO"


def help_menu():
	menu = "\n `start` to enable bot" \
		+ "\n `stop` to disable bot" \
		+ "\n `account` to see account info"

	return menu
