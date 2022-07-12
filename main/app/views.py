from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import make_password, check_password
from sqlalchemy import desc

from app.models import Users, Otp
from app import constants, helpers
from app.serializers import (
    LoginSerializer,
    UserSerializer,
    SendOtpSerializer,
    ValidateOtpSerializer,
    ForgotPasswordSerializer
)
from django.db.models import Q


class SendOtp(APIView):
    """
    this class sends the otp to phone

    """
    def post(self, request):
        serializer = SendOtpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data = serializer.errors,
                status = status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        operation_type = data.get("operation_type")
        phone_number = data.get("phone_number")
        email = data.get("email")

        try:
            otp = helpers.generate_otp()
            if operation_type == constants.SIGN_IN_PHONE:
                Otp.objects.create(
                    phone_number=phone_number,
                    otp=otp,
                    otp_type=Otp.OtpType.SIGNUP
                )
                client = helpers.MessageClient()
                client.send_message(otp, phone_number)

            elif operation_type == constants.FORGOT_PASSWORD_PHONE:
                Otp.objects.create(
                    phone_number=phone_number,
                    otp=otp,
                    otp_type=Otp.OtpType.FORGOT_PASSWORD
                )
                client = helpers.MessageClient()
                client.send_message(otp, phone_number)

            elif operation_type == constants.FORGOT_PASSWORD_EMAIL:
                Otp.objects.create(
                    email=email,
                    otp=otp,
                    otp_type=Otp.OtpType.FORGOT_PASSWORD
                )
                client = helpers.MessageClient()
                client.send_mail(
                    to=email,
                    subject=constants.FORGOT_PASSWORD_MAIL_SUBJECT,
                    message=constants.FORGOT_PASSWORD_MAIL_MESSAGE.format(otp)
                )

            else:
                Otp.objects.create(
                    email=email,
                    otp=otp,
                    otp_type=Otp.OtpType.SIGNUP
                )
                client = helpers.MessageClient()
                client.send_mail(
                    to=email,
                    subject=constants.SIGN_IN_MAIL_SUBJECT,
                    message=constants.SIGN_IN_MAIL_MESSAGE.format(otp)
                )

            return Response(
                data = {
                    "message": constants.OTP_SENT_SUCCESSFULLY,
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as ex:
            return Response(data=str(ex), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ValidateOtp(APIView):
    """
    this class validates the otp

    """
    def post(self, request):
        serializer = ValidateOtpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data = serializer.errors,
                status = status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        operation_type = data.get("operation_type")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        password = data.get("password")
        email = data.get("email")
        otp_code = data.get("otp")
        phone_number = data.get("phone_number")

        check_otp = Otp.objects.filter(
            otp=otp_code,
            is_verified=False,
            otp_type=Otp.OtpType.SIGNUP
        )

        if operation_type == constants.SIGN_IN_PHONE:
            check_otp = check_otp.filter(
                phone_number=phone_number
            )

        else:
            check_otp = check_otp.filter(
                email=email
            )

        if not check_otp.exists():
            return Response(
                data = {"error": constants.RECORD_NOT_FOUND},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            check_otp = check_otp.order_by("-created_at").first()
            check_otp.is_verified = True
            check_otp.save()

            password_hash = make_password(password)

            Users.objects.create(
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                email=email,
                password=password_hash
            )

            return Response(
                data = {
                    "message": constants.USER_CREATED,
                    "user": UserSerializer(request.data).data,
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as ex:
            return Response(data=str(ex), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Login(APIView):
    """
    this class is used to login

    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data = serializer.errors,
                status = status.HTTP_400_BAD_REQUEST
            )

        phone_number = serializer.validated_data.get("phone_number")
        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        user = Users.objects.filter(
            Q(phone_number=phone_number) | Q(email=email)
        )
        if not user.exists():
            return Response(
                data = {"error": constants.USER_DOES_NOT_EXISTS},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = user.first()
        if not check_password(password, user.password):
            return Response(
                data = {"error": constants.INCORRECT_PASSWORD},
                status = status.HTTP_400_BAD_REQUEST
            )

        try:
            # creating a new token or getting it if already exists for a user
            new_token, _ = Token.objects.get_or_create(user=user)
            if new_token:
                user.last_login = timezone.now()
                user.save()
                response = {
                    "token": str(new_token),
                    "user": UserSerializer(user).data,
                }
                return Response(response, status=status.HTTP_201_CREATED)

            return Response(request.data, status=status.HTTP_400_BAD_REQUEST)

        except Exception as ex:
            return Response(data=str(ex), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfile(APIView):
    """
    this class is used to get user profile

    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = Users.objects.get(phone_number=request.user)
            if user:
                return Response(
                    data = UserSerializer(user).data,
                    status = status.HTTP_201_CREATED,
                )
            return Response(
                data = {
                    "message": constants.USER_NOT_FOUND
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as ex:
            return Response(
                data = str(ex),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class Logout(APIView):
    """
    this class logs user out

    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(
            data = {"message": constants.USER_LOGGED_OUT},
            status = status.HTTP_200_OK,
        )


class ForgotPassword(APIView):
    """
    this class updated the password on otp validation.

    """
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data = serializer.errors,
                status = status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        operation_type = data.get("operation_type")
        phone_number = data.get("phone_number")
        email = data.get("email")
        otp_code = data.get("otp")
        new_password = data.get("new_password")

        check_otp = Otp.objects.filter(
            otp=otp_code,
            is_verified=False,
            otp_type=Otp.OtpType.FORGOT_PASSWORD
        )

        if operation_type == constants.FORGOT_PASSWORD_PHONE:
            check_otp = check_otp.filter(
                phone_number=phone_number
            )

        else:
            check_otp = check_otp.filter(
                email=email
            )

        if not check_otp.exists():
            return Response(
                data = {"error": constants.RECORD_NOT_FOUND},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = None
        if phone_number:
            user = Users.objects.filter(phone_number=phone_number)

        if email:
            user = Users.objects.filter(email=email)

        if not user or not user.exists():
            return Response(
                data = {"error": constants.USER_NOT_FOUND},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = user.first()

        try:
            check_otp = check_otp.order_by("-created_at").first()
            check_otp.is_verified = True
            check_otp.save()

            password_hash = make_password(new_password)

            user.password = password_hash
            user.save()

            return Response(
                data = {
                    "message": constants.USER_UPDATED,
                    "user": UserSerializer(request.data).data,
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as ex:
            return Response(data=str(ex), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
