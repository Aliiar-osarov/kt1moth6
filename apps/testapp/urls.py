from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.testapp.views import (
    EmailTokenObtainPairView,
    GoogleAuthView,
    LessonsView,
)

urlpatterns = [
    path(
        "auth/jwt/create/",
        EmailTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "auth/jwt/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "auth/google/",
        GoogleAuthView.as_view(),
        name="google_auth",
    ),
    path(
        "lessons/",
        LessonsView.as_view(),
        name="lessons",
    ),
]