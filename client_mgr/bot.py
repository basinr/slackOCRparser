
def process(user, text):
	if user.bot_user_id not in text:
		return False

	if "help" in text:
		return help_menu()
	elif "start" in text:
		user.set_enabled(True)
		return "OCR enabled!"
	elif "stop" in text:
		user.set_enabled(False)
		return "OCR disabled!"
	elif "account" in text:
		return account_info(user)


def help_menu():
	menu = "\n `start` to enable bot" \
		+ "\n `stop` to disable bot" \
		+ "\n `account` to see account info"

	return menu


def account_info(user):
	return user.account_info_str()
