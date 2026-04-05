from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User
from .serializers import (
    LoginSerializer,
    UserSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
)


def _token_pair(user) -> dict:
    """Return access + refresh token dict for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


# ─── Login ────────────────────────────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    POST /api/auth/login/
    Body: { "email": "...", "password": "..." }
    Returns: { "access": "...", "refresh": "...", "user": {...} }
    """
    serializer = LoginSerializer(data=request.data, context={"request": request})
    if not serializer.is_valid():
        # Flatten validation errors into a single "detail" string
        errors = serializer.errors
        detail = next(iter(errors.get("non_field_errors", errors.values())), "Invalid credentials.")
        if isinstance(detail, list):
            detail = detail[0]
        return Response({"detail": str(detail)}, status=status.HTTP_401_UNAUTHORIZED)

    user = serializer.validated_data["user"]

    # Update last_login
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    return Response(
        {**_token_pair(user), "user": UserSerializer(user).data},
        status=status.HTTP_200_OK,
    )


# ─── Refresh ──────────────────────────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([AllowAny])
def refresh(request):
    """
    POST /api/auth/refresh/
    Body: { "refresh": "..." }
    Returns: { "access": "..." }
    """
    token = request.data.get("refresh")
    if not token:
        return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh_token = RefreshToken(token)
        return Response(
            {"access": str(refresh_token.access_token)},
            status=status.HTTP_200_OK,
        )
    except TokenError as e:
        return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


# ─── Logout ───────────────────────────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    POST /api/auth/logout/
    Body: { "refresh": "..." }   (optional — blacklists the token if provided)
    """
    token = request.data.get("refresh")
    if token:
        try:
            RefreshToken(token).blacklist()
        except Exception:
            pass  # token already invalid — that's fine
    return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


# ─── Current user (me) ────────────────────────────────────────────────────────
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    """
    GET  /api/auth/me/  → current user profile
    PATCH /api/auth/me/ → update full_name
    """
    if request.method == "GET":
        return Response(UserSerializer(request.user).data)

    # Only full_name may be updated via this endpoint. UserSerializer is
    # read-only by design (safe for GET responses), so we update directly.
    if "full_name" in request.data:
        user = request.user
        user.full_name = request.data["full_name"]
        user.save(update_fields=["full_name"])
    return Response(UserSerializer(request.user).data)


# ─── Change password ──────────────────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    POST /api/auth/change-password/
    Body: { "current_password", "new_password", "new_password_confirm" }
    """
    serializer = ChangePasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if not user.check_password(serializer.validated_data["current_password"]):
        return Response({"detail": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(serializer.validated_data["new_password"])
    user.save(update_fields=["password"])
    return Response({"detail": "Password updated successfully."})


# ─── Register (admin-only) ────────────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAdminUser])
def register(request):
    """
    POST /api/auth/register/
    Admin-only: create a new user account.
    """
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# ─── SSO placeholder ─────────────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([AllowAny])
def sso_redirect(request):
    """
    GET /api/auth/sso/
    Placeholder — replace with your actual SAML/OIDC redirect.
    """
    return Response(
        {"detail": "SSO not configured. Implement SAML/OIDC redirect here."},
        status=status.HTTP_501_NOT_IMPLEMENTED,
    )
