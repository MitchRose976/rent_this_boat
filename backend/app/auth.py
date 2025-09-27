from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
COOKIE_NAME = "access_token"


# Helper
def verify_password(plain: str, hashed: str) -> bool:
return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
to_encode = data.copy()
expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
to_encode.update({"exp": expire})
return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Register
@router.post("/register", response_model=UserOut)
async def register(user: UserCreate):
existing = await db.users.find_one({"email": user.email.lower()})
if existing:
raise HTTPException(status_code=400, detail="Email already registered")


hashed = get_password_hash(user.password)
doc = {"email": user.email.lower(), "password": hashed, "full_name": user.full_name}
res = await db.users.insert_one(doc)
return UserOut(id=str(res.inserted_id), email=user.email.lower(), full_name=user.full_name)


# Login
@router.post("/login", response_model=Token)
async def login(response: Response, user: UserCreate):
db_user = await db.users.find_one({"email": user.email.lower()})
if not db_user:
raise HTTPException(status_code=401, detail="Invalid credentials")
if not verify_password(user.password, db_user.get("password")):
raise HTTPException(status_code=401, detail="Invalid credentials")


token = create_access_token({"sub": str(db_user.get("_id")), "email": db_user.get("email")})


# Set cookie (httpOnly)
secure = os.environ.get("COOKIE_SECURE", "False").lower() == "true"
response.set_cookie(
key=COOKIE_NAME,
value=token,
httponly=True,
secure=secure,
samesite="lax",
max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
path='/'
)


return {"access_token": token, "token_type": "bearer"}


# Logout
@router.post("/logout")
async def logout(response: Response):
response.delete_cookie(COOKIE_NAME, path='/')
return {"ok": True}


# Protected endpoint: /auth/me
@router.get("/me", response_model=UserOut)
async def me(request: Request):
token = request.cookies.get(COOKIE_NAME)
if not token:
raise HTTPException(status_code=401, detail="Not authenticated")
try:
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
user_id = payload.get("sub")
if not user_id:
raise HTTPException(status_code=401, detail="Invalid token")
except Exception:
raise HTTPException(status_code=401, detail="Invalid token")


found = await db.users.find_one({"_id": ObjectId(user_id)})
if not found:
raise HTTPException(status_code=404, detail="User not found")


return UserOut(id=str(found.get("_id")), email=found.get("email"), full_name=found.get("full_name"))