from django.urls import path
from .views import GetOTPView, ValidateOTPView

urlpatterns = [
    path('get_otp/<str:sh_id>/', GetOTPView.as_view()),
    path('validate_otp/<str:sh_id>/<str:otpCode>/', ValidateOTPView.as_view()),
]