"""
Server-side OAuth state for the Google/GitHub authorization-code flow.

`start` mints a random state + PKCE verifier and stores them, together with
the whitelisted redirect_uri, in a signed httponly cookie scoped to
/users/auth/. The callback must present the same state from the same browser
(the cookie), the redirect_uri used for the code exchange comes from that
cookie rather than the client, and each state is accepted once.
"""
import base64
import hashlib
import secrets
from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.core.cache import cache

SIGNING_SALT = "users.oauth.state"
USED_STATE_CACHE_PREFIX = "oauth_state_used:"

PROVIDERS = {
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "scope": "openid email profile",
        "client_id_setting": "GOOGLE_CLIENT_ID",
        "redirect_uris_setting": "GOOGLE_ALLOWED_REDIRECT_URIS",
        "extra_params": {"access_type": "online", "prompt": "select_account"},
    },
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "scope": "read:user user:email",
        "client_id_setting": "GITHUB_CLIENT_ID",
        "redirect_uris_setting": "GITHUB_ALLOWED_REDIRECT_URIS",
        "extra_params": {"allow_signup": "true"},
    },
}


class OAuthStateError(Exception):
    """State missing, tampered with, expired, reused, or for another provider."""


def allowed_redirect_uris(provider):
    return getattr(settings, PROVIDERS[provider]["redirect_uris_setting"], [])


def _pkce_challenge(verifier):
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def begin(provider, redirect_uri):
    """Returns (authorization_url, signed_cookie_value). Caller validated inputs."""
    config = PROVIDERS[provider]
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)

    params = {
        "client_id": getattr(settings, config["client_id_setting"]),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": config["scope"],
        "state": state,
        "code_challenge": _pkce_challenge(verifier),
        "code_challenge_method": "S256",
        **config["extra_params"],
    }
    cookie_value = signing.dumps(
        {"p": provider, "s": state, "v": verifier, "r": redirect_uri},
        salt=SIGNING_SALT,
    )
    return f"{config['authorize_url']}?{urlencode(params)}", cookie_value


def consume(provider, returned_state, cookie_value):
    """Validates the callback's state against the browser's cookie.

    Returns (redirect_uri, code_verifier). Raises OAuthStateError otherwise.
    """
    if not returned_state or not cookie_value:
        raise OAuthStateError()
    try:
        data = signing.loads(
            cookie_value, salt=SIGNING_SALT, max_age=settings.OAUTH_STATE_MAX_AGE
        )
    except signing.BadSignature:  # includes SignatureExpired
        raise OAuthStateError()

    if data.get("p") != provider or not secrets.compare_digest(
        str(data.get("s", "")), str(returned_state)
    ):
        raise OAuthStateError()

    # One-time use even if the same cookie is replayed before it's cleared.
    if not cache.add(
        f"{USED_STATE_CACHE_PREFIX}{data['s']}", 1, timeout=settings.OAUTH_STATE_MAX_AGE
    ):
        raise OAuthStateError()

    if data.get("r") not in allowed_redirect_uris(provider):
        raise OAuthStateError()
    return data["r"], data["v"]
