from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

urlpatterns = [
    path("token/", TokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
    path("logout/", TokenBlacklistView.as_view()),
    path("register/", views.RegisterView.as_view()),
    path("me/", views.MeView.as_view()),
]
