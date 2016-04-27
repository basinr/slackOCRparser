
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
	elif "upgrade" in text:
		return generate_url_subscribe(user)


def help_menu():
	menu = "\n `start` to enable bot" \
		+ "\n `stop` to disable bot" \
		+ "\n `account` to see account info" \
		+ "\n `upgrade` to subscribe to our premium plan" \

	return menu


def account_info(user):
	return user.account_info_str()

def generate_url(user):
	return user.generate_subscription_url()
	
