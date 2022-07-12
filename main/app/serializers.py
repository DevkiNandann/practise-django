from app import constants
from rest_framework import serializers
from app.models import Users


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "email"
        ]


class SignupSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=256)
    last_name = serializers.CharField(max_length=256)
    password = serializers.CharField(max_length=256)

    def validate(self, data):
        if data.get("first_name"):
            data["first_name"] = data["first_name"].strip().title()
        if data.get("last_name"):
            data["last_name"] = data["last_name"].strip().title()

        return data


class SendOtpSerializer(serializers.Serializer):
    operation_type = serializers.CharField(max_length=128)
    phone_number = serializers.CharField(required=False, max_length=20, allow_null=True)
    email = serializers.EmailField(required=False, allow_null=True)

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        email = attrs.get("email")
        operation_type = attrs.get("operation_type")

        if operation_type not in (
            constants.SIGN_IN_EMAIL,
            constants.SIGN_IN_PHONE,
            constants.FORGOT_PASSWORD_PHONE,
            constants.FORGOT_PASSWORD_EMAIL,
            constants.LOGIN_WITH_OTP,
            constants.LOGIN_WITH_PASSWORD
        ):
            raise serializers.ValidationError(constants.INVALID_OPERATION_TYPE)

        if operation_type in (constants.SIGN_IN_EMAIL, constants.FORGOT_PASSWORD_EMAIL) and not email:
            raise serializers.ValidationError(constants.EMAIL_MANDATORY)

        if (
            operation_type in (constants.SIGN_IN_PHONE, constants.FORGOT_PASSWORD_PHONE, constants.LOGIN_WITH_OTP)
            and not phone_number
        ):
            raise serializers.ValidationError(constants.PHONE_MANDATORY)

        if phone_number and operation_type == constants.SIGN_IN_PHONE:
            existing_user = Users.objects.filter(phone_number=phone_number)
            if existing_user.exists():
                raise serializers.ValidationError(constants.PHONE_NUMBER_ALREADY_EXISTS)

        if email and operation_type == constants.SIGN_IN_EMAIL:
            existing_user = Users.objects.filter(email=email)
            if existing_user.exists():
                raise serializers.ValidationError(constants.EMAIL_ALREADY_EXISTS)

        return super().validate(attrs)


class ValidateOtpSerializer(SendOtpSerializer, SignupSerializer):
    otp = serializers.IntegerField()
    
    def validate(self, attrs):
        if not attrs.get("phone_number"):
            raise serializers.ValidationError(constants.PHONE_MANDATORY)

        if not attrs.get("email"):
            raise serializers.ValidationError(constants.EMAIL_MANDATORY)

        return super().validate(attrs)


class LoginSerializer(SendOtpSerializer):
    password = serializers.CharField(max_length=256, required=False, allow_null=True)
    otp = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        operation_type = attrs.get("operation_type")
        if operation_type == constants.LOGIN_WITH_OTP:
            if not attrs.get("otp") or not attrs.get("phone_number"):
                raise serializers.ValidationError(constants.PHONE_NUMBER_OR_OTP_NOT_PROVIDED)
        elif operation_type == constants.LOGIN_WITH_PASSWORD:
            if not attrs.get("password"):
                raise serializers.ValidationError(constants.PASSWORD_NOT_PROVIDED)
            if not attrs.get("phone_number") and not attrs.get("email"):
                raise serializers.ValidationError(constants.PHONE_OR_EMAIL_NOT_PROVIDED)
        else:
            raise serializers.ValidationError(constants.INVALID_OPERATION_TYPE)
        return super().validate(attrs)


class ForgotPasswordSerializer(SendOtpSerializer):
    otp = serializers.IntegerField()
    new_password = serializers.CharField(max_length=256)
    confirm_new_password = serializers.CharField(max_length=256)

    def validate(self, attrs):
        if attrs.get("confirm_new_password") != attrs.get("new_password"):
            raise serializers.ValidationError(constants.PASSWORD_DOES_NOT_MATCH)

        if attrs.get("operation_type") not in (
            constants.FORGOT_PASSWORD_PHONE,
            constants.FORGOT_PASSWORD_EMAIL
        ):
            raise serializers.ValidationError(constants.INVALID_OPERATION_TYPE)

        return super().validate(attrs)
