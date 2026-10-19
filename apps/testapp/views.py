from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.testapp.permissions import IsTeacherOrReadOnly
from apps.testapp.serializers import EmailTokenObtainPairSerializer
from apps.testapp.services import google_login


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class GoogleAuthView(APIView):
    permission_classes = []

    def post(self, request):
        code = request.data.get("code")

        if not isinstance(code, str) or not code.strip():
            return Response(
                {"detail": "Поле code обязательно."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from rest_framework.exceptions import APIException

        try:
            result = google_login(code.strip())
        except APIException as exc:
            return Response(
                {"detail": exc.detail},
                status=exc.status_code,
            )

        return Response(result, status=status.HTTP_200_OK)


class LessonsView(APIView):
    permission_classes = [IsAuthenticated, IsTeacherOrReadOnly]

    def get(self, request):
        return Response({
            "message": "Список уроков",
            "user_role": request.user.role,
            "lessons": [],
        })

    def post(self, request):
        return Response(
            {
                "message": "Доступ преподавателя подтверждён.",
                "data": request.data,
            },
            status=status.HTTP_201_CREATED,
        )