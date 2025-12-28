from typing_extensions import Annotated
from beanie import Document, Indexed, Replace, Save, before_event
from pydantic import ConfigDict, EmailStr, Field
from pydantic.functional_validators import BeforeValidator
from datetime import datetime, date, timezone
from typing import Optional, Literal
from enum import Enum

from backend.models.address import Address, CountryCode


class UserRole(str, Enum):
    CUSTOMER = "customer"
    OWNER = "owner"
    ADMIN = "admin"


class User(Document):
    email: Annotated[
        EmailStr,
        Field(description="User email address"),
        Indexed(unique=True),
    ]
    password_hash: str
    first_name: Annotated[
        str, Field(min_length=1, max_length=50, description="First name")
    ]
    last_name: Annotated[
        str, Field(min_length=1, max_length=50, description="Last name")
    ]
    # TODO: perhaps remove the default role of CUSTOMER?
    role: Annotated[UserRole, Field(description="Role of the user in the system")] = (
        UserRole.CUSTOMER
    )
    is_active: Annotated[bool, Field(description="Is the user active?"), Indexed()] = (
        True
    )
    is_verified: Annotated[
        bool, Field(description="Is the user verified?"), Indexed()
    ] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Annotated[
        Optional[datetime], Field(description="Last login timestamp")
    ] = None

    # Profile information
    phone: Annotated[
        Optional[str], Field(max_length=20, description="Phone number")
    ] = None
    date_of_birth: Annotated[date | None, Field(description="Date of birth")] = None
    profile_picture_url: Annotated[
        Optional[str], Field(description="Profile picture URL")
    ] = None

    # Address information
    address: Annotated[Optional[Address], Field(description="User address")] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "jdoe@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "role": UserRole.CUSTOMER,
                "is_active": True,
                "is_verified": True,
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z",
                "last_login": "2023-01-10T08:30:00Z",
                "phone": "416-555-1234",
                "date_of_birth": "1990-05-15",
                "profile_picture_url": "https://example.com/profiles/jdoe.jpg",
                "address": {
                    "street_address": "123 Main St",
                    "city": "Toronto",
                    "state_province": "ON",
                    "postal_code": "M4B 1B3",
                    "country": CountryCode.CA,
                },
            }
        },
    )

    class Settings:
        name = "users"  # Collection name in MongoDB

    def __str__(self):
        return f"User(email={self.email}, name={self.first_name} {self.last_name})"

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def update_last_login(self):
        now = datetime.now(timezone.utc)
        self.last_login = now
        self.updated_at = now

    @before_event([Replace, Save])
    def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)
