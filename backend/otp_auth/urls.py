from django.urls import path

from .views import RequestOTPView, VerifyOTPView

urlpatterns = [
    path("request/", RequestOTPView.as_view(), name="otp-request"),
    path("verify/", VerifyOTPView.as_view(), name="otp-verify"),
]
