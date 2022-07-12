from django.urls import path
from app.views import (
    Login,
    UserProfile,
    Logout,
    SendOtp,
    ValidateOtp,
    ForgotPassword,
)

urlpatterns = [
   path("login", Login.as_view(), name="login"),
   path("profile", UserProfile.as_view(), name="profile"),
   path("logout", Logout.as_view(), name="logout"),
   path("send-otp", SendOtp.as_view(), name="send-otp"),
   path("validate-otp", ValidateOtp.as_view(), name="validate-otp"),
   path("forgot-password", ForgotPassword.as_view(), name="forgot-password")
]
