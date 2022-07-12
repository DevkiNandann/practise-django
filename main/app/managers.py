from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):

    def create_superuser(
        self,
        phone_number,
        password,
        email,
        is_superuser,
        **extra_fields
    ):
        if not phone_number or not password or not email:
            raise ValueError(
                "phone_number, password, email must be set"
            )

        user = self.model(
            phone_number=phone_number, email=email, is_superuser=is_superuser, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user