from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ErrorInfo:
    type: str
    description: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to a dict with keys matching template expectations."""
        return {"error": self.type, "detail": self.description}


# ============================================================================
# OAuth2 Error Types & Descriptions
# Defined according to RFC 6749 Section 4.1.2.1
# https://datatracker.ietf.org/doc/html/rfc6749#section-4.1.2.1
# ============================================================================
class AuthErrors:
    def __init__(self):
        self.invalid_request = ErrorInfo(
            "invalid_request",
            "The request is missing a required parameter, includes an invalid parameter value, includes a parameter more than once, or is otherwise malformed.",
        )
        self.unauthorized_client = ErrorInfo(
            "unauthorized_client",
            "The client is not authorized to request an authorization code using this method.",
        )
        self.access_denied = ErrorInfo(
            "access_denied",
            "The resource owner or authorization server denied the request.",
        )
        self.unsupported_response_type = ErrorInfo(
            "unsupported_response_type",
            "The authorization server does not support obtaining an authorization code using this method.",
        )
        self.unsupported_grant_type = ErrorInfo(
            "unsupported_grant_type",
            "The authorization grant type is not supported by the authorization server.",
        )
        self.invalid_scope = ErrorInfo(
            "invalid_scope",
            "The requested scope is invalid, unknown, or malformed.",
        )
        self.server_error = ErrorInfo(
            "server_error",
            "The authorization server encountered an unexpected condition that prevented it from fulfilling the request.",
        )
        self.temporarily_unavailable = ErrorInfo(
            "temporarily_unavailable",
            "The authorization server is currently unable to handle the request due to a temporary overloading or maintenance of the server.",
        )

        # map for dict-like access
        self._map: Dict[str, ErrorInfo] = {
            "invalid_request": self.invalid_request,
            "unauthorized_client": self.unauthorized_client,
            "access_denied": self.access_denied,
            "unsupported_response_type": self.unsupported_response_type,
            "unsupported_grant_type": self.unsupported_grant_type,
            "invalid_scope": self.invalid_scope,
            "server_error": self.server_error,
            "temporarily_unavailable": self.temporarily_unavailable,
        }

    def __getitem__(self, key: str) -> ErrorInfo:
        return self._map[key]


# single shared instance
AUTH_ERRORS: AuthErrors = AuthErrors()
