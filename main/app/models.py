from datetime import datetime
from django.db import models
from djchoices import DjangoChoices, ChoiceItem
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from app.managers import UserManager



class Users(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=256, null=True)
    last_name = models.CharField(max_length=256, null=True)
    phone_number = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=256)
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(null=True)
    email = models.EmailField()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["is_superuser", "email"]

    objects = UserManager()

    def __str__(self):
        return str(self.phone_number)


class Otp(models.Model):

    class OtpType(DjangoChoices):
        LOGIN = ChoiceItem("login")
        SIGNUP = ChoiceItem("signup")
        FORGOT_PASSWORD = ChoiceItem("forgot_password")

    otp = models.IntegerField()
    phone_number = models.CharField(max_length=20, null=True)
    email = models.EmailField(null=True)
    is_verified = models.BooleanField(default=False)
    otp_type = models.CharField(max_length=128, choices=OtpType.choices)
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(null=True, auto_now=True)
