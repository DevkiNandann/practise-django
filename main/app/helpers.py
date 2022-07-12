from rest_framework.response import Response
import sendgrid
from twilio.rest import Client
import random
from main.settings import TWILIO_AUTH_TOKEN, TWILIO_ACCOUNT_SID, TWILIO_NUMBER
import os
from sendgrid.helpers.mail import Mail, Email, To
from app import constants

def generate_otp() -> str:
    otp = str(random.randint(1000, 9999))
    return otp


class MessageClient:
    """
    Messgae client to send the otp
    """

    def __init__(self):
        self.twilio_number = str(TWILIO_NUMBER)
        self.twilio_client = Client(str(TWILIO_ACCOUNT_SID), str(TWILIO_AUTH_TOKEN))
        self.sg_client = sendgrid.SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        self.send_from = os.environ.get("SEND_FROM")

    def send_message(self, body, to):
        to = constants.COUNTRY_CODE + to
        self.twilio_client.messages.create(body=body, to=to, from_=self.twilio_number)

    def send_mail(self, to, subject, message):
        message = Mail(
            Email(self.send_from),
            To(to),
            subject,
            message,
        )
        try:
            self.sg_client.client.mail.send.post(message.get())
        except Exception as ex:
            print(ex)
