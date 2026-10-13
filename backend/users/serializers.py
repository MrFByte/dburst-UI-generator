import ipaddress
import unicodedata
from urllib.parse import urlsplit

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import User

AVATAR_URL_MAX_LENGTH = 2048
NAME_MAX_LENGTH = User._meta.get_field("name").max_length
_url_validator = URLValidator(schemes=["http", "https"])


class UserSerializer(serializers.ModelSerializer):
    """Serializer for returning user profile details."""

    class Meta:
        model = User
        fields = ["id", "email", "name", "avatar_url", "role"]


def _is_internal_host(host):
    """localhost names and loopback/private/link-local/reserved IP literals.

    Hostnames are not resolved (that would be a server-side fetch) — the URL is
    only ever loaded by the user's own browser, so this is hygiene, not SSRF
    protection.
    """
    host = host.strip("[]").rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost"):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return not ip.is_global


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """PATCH /users/profile/. Only `name` and `avatar_url` are writable; any
    other field in the payload (email, role, is_staff, ...) is ignored."""

    # Length is enforced on the cleaned value in validate_name; the raw cap
    # only bounds the payload.
    name = serializers.CharField(max_length=1000, trim_whitespace=False)
    avatar_url = serializers.CharField(
        max_length=AVATAR_URL_MAX_LENGTH, allow_blank=True, allow_null=True,
        required=False, trim_whitespace=True,
    )

    class Meta:
        model = User
        fields = ["name", "avatar_url"]

    def validate_name(self, value):
        # Drop control/format characters (newlines, NUL, bidi overrides...)
        value = "".join(ch for ch in value if unicodedata.category(ch) not in ("Cc", "Cf"))
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        if len(value) > NAME_MAX_LENGTH:
            raise serializers.ValidationError(f"Ensure this field has no more than {NAME_MAX_LENGTH} characters.")
        if "<" in value or ">" in value:
            raise serializers.ValidationError("Name cannot contain < or >.")
        return value

    def validate_avatar_url(self, value):
        if not value:
            return None  # blank clears the avatar
        if any(ch.isspace() for ch in value):
            raise serializers.ValidationError("Enter a valid http(s) URL.")
        try:
            _url_validator(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Enter a valid http(s) URL.")

        parts = urlsplit(value)
        if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
            raise serializers.ValidationError("Enter a valid http(s) URL.")
        if parts.username is not None or parts.password is not None:
            raise serializers.ValidationError("URL must not contain credentials.")
        if _is_internal_host(parts.hostname):
            raise serializers.ValidationError("URL must point to a public host.")
        return value
