from typing_extensions import Annotated
from beanie import Document, Indexed
from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator
from pydantic.functional_validators import BeforeValidator
from datetime import datetime
from typing import Optional, Literal
from enum import Enum

from backend.models.address import Address, CountryCode

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]


class UserRole(str, Enum):
    CUSTOMER = "customer"
    OWNER = "owner"
    ADMIN = "admin"


class User(Document):
    # The primary key for the StudentModel, stored as a `str` on the instance.
    # This will be aliased to ``_id`` when sent to MongoDB,
    # but provided as ``id`` in the API requests and responses.
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    role: UserRole = UserRole.CUSTOMER
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    # Profile information
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None
    profile_picture_url: Optional[str] = None

    # Address information
    address: Optional[Address] = None

    # populate_by_name - allows the model to be initialized with 'id' OR '_id'
    # arbitrary_types_allowed - allows the use of custom types like PyObjectId
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "Jane Doe",
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
        indexes = [
            "email",  # Already indexed above
            "role",
            "is_active",
            "is_verified",
            "created_at",
        ]

    def __str__(self):
        return f"User(email={self.email}, name={self.first_name} {self.last_name})"

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
