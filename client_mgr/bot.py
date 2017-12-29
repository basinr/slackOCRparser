
def process(user, text, dm=False):
	if user.bot_user_id not in text and not dm:
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
		return subscribe_url(user)
	elif "about" in text:
		return about()
	else:
		return help_menu()

def help_menu():
	greeting = "Hey there! Here's a help menu to get you started:\n"
	menu = "\n `@pixibot account` to see account info" \
		+ "\n `@pixibot upgrade` to subscribe to our premium plan" \
		+ "\n `@pixibot about` to get started with using pixibot\n" \
		+ "\n Visit www.pixibot.co/#contact, or email support@pixibot.co directly for support\n\n"

	salutation = "We would love to hear any feedback you might have on pixibot. Please reach out to me, Ronnie, the founder, at basinr@gmail.com with any feedback or suggestions!"

	return greeting + menu + salutation

def about():
	greeting = "Hi! Pixibot makes it possible to search the text of images you post in public slack channels\n"
	greeting2 = "Here's how it works:\n"
	options = "\n1. Invite pixibot to a public channel with `/invite @pixibot`" \
			+ "\n2. Post a JPG/PNG file (e.g. a screenshot)" \
			+ "\n3. pixibot will comment on your file with your image's text!\n\n"
	help_msg = "When in doubt, type `@pixibot help` for a full menu of options\n\n"
	salutation = "We would love to hear any feedback you might have on pixibot. Please reach out to me, Ronnie, the founder, at `basinr@gmail.com` with any feedback or suggestions!"

	return greeting + greeting2 + options + help_msg + salutation

def account_info(user):
	return user.account_info_str()


def subscribe_url(user):
	return user.generate_subscription_url()
