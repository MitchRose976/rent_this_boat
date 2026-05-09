import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from .core.config import settings
from starlette.middleware.base import BaseHTTPMiddleware


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


def configure_middleware(app: FastAPI):
    """
    Configure all middleware for the FastAPI app.
    This includes process time header, CORS, HTTPS redirect, and TrustedHost.
    """

    # 1. ProcessTimeMiddleware to add X-Process-Time header
    app.add_middleware(ProcessTimeMiddleware)

    # 2. TrustedHostMiddleware to prevent Host header attacks
    app.add_middleware(
        TrustedHostMiddleware,
        # TODO(deploy): add production API hostnames here (NO scheme, NO path),
        # e.g. ["api.rentthisboat.com", "rentthisboat.com"].
        allowed_hosts=["localhost", "127.0.0.1", "::1"],
    )

    # 3. Protocol-aware HTTPS redirect middleware
    # Environment-aware middleware behavior
    # - Local development: no forced HTTPS redirect (avoids local cert friction)
    # - Staging/Production: enable HTTPS redirect
    app_env = settings.app_env.lower()
    force_https = settings.force_https
    enable_https_redirect = force_https or app_env in {"staging", "production"}
    if enable_https_redirect:
        app.add_middleware(HTTPSRedirectMiddleware)
    else:
        print("HTTPS redirect disabled for local development.")

    # 4. CORS middleware to allow requests from frontend origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://localhost:3000",
            "https://localhost:3000",
            "https://127.0.0.1:3000",
            # TODO(deploy): add production frontend origins here.
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
