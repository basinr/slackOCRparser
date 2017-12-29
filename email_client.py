import smtplib
import const
from email.mime.text import MIMEText


class EmailClient:
	def __init__(self, _send_to):
		self.user_name = "support@pixibot.co"
		self.password = "B00tyshortz9191"
		self.send_to = _send_to
		self.server = None

	def server_connect(self, subject, message):
		try:
			self.server = smtplib.SMTP("mail.privateemail.com", 587)
			self.server.ehlo()
			self.server.starttls()
			self.server.login(self.user_name, self.password)

			msg = MIMEText(message)
			msg['Subject'] = subject
			msg['From'] = self.user_name
			msg['To'] = self.send_to

			self.server.sendmail(self.user_name, self.send_to, msg.as_string())
			print "Email sent!"
			self.server.close()
		except:
			print "Something went wrong in sending an email to " + self.send_to

	def application_added(self):
		subject = "Pixibot for Slack Application Added"
		self.server_connect(subject, const.APPLICATION_ADDED)

	def subscription_created(self):
		subject = 'Pixibot Subscription Confirmation'
		self.server_connect(subject, const.SUPPORT_EMAIL)

	def subscription_renewal(self):
		subject = "Pixibot for Slack Account Renewal Notice"
		self.server_connect(subject, const.SUBSCRIPTION_RENEWAL)
