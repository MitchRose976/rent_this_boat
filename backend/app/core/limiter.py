"""Rate limiter initialization for slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Single limiter instance — shared across all routers
limiter = Limiter(key_func=get_remote_address)
