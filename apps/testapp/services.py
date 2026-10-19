import os

import requests
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def google_login(code):
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    if not all((client_id, client_secret, redirect_uri)):
        raise AuthenticationFailed(
            "Google OAuth не настроен в переменных окружения."
        )

    try:
        token_response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )

        if not token_response.ok:
            raise AuthenticationFailed("Не удалось авторизоваться через Google.")

        google_access_token = token_response.json().get("access_token")

        if not google_access_token:
            raise AuthenticationFailed("Google не вернул access token.")

        profile_response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={
                "Authorization": f"Bearer {google_access_token}",
            },
            timeout=10,
        )

        if not profile_response.ok:
            raise AuthenticationFailed(
                "Не удалось получить профиль Google."
            )

        profile = profile_response.json()

    except requests.RequestException as exc:
        raise AuthenticationFailed(
            "Ошибка соединения с Google."
        ) from exc

    email = profile.get("email")

    if not email or not profile.get("verified_email"):
        raise AuthenticationFailed(
            "Google не подтвердил адрес электронной почты."
        )

    user = User.objects.filter(email__iexact=email).first()
    is_new_user = user is None

    if is_new_user:
        user = User.objects.create_user(
            email=email,
            password=None,
            first_name=profile.get("given_name", ""),
            last_name=profile.get("family_name", ""),
            role=User.Role.STUDENT,
        )

    if not user.is_active:
        raise AuthenticationFailed("Аккаунт пользователя отключён.")

    refresh = RefreshToken.for_user(user)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "is_new_user": is_new_user,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
        },
    }