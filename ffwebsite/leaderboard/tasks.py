from rest_framework.permissions import BasePermission
from django.conf import settings

class HasAPIToken(BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get("Authorization", "")
        return token == f"{settings.API_AUTH_TOKEN}"