Checklist Status Report
❌ Critical Bugs (5/5 FIXED ✅)
Bug	Status	Evidence
1. jwt.encode() receiving Pydantic model	✅ FIXED	jwt_service.py line 117: jwt.encode(payload.model_dump(), ...)
2. /token wrong kwarg names to JWT methods	✅ FIXED	auth.py calls: create_access_token(user.id, email=user.email, scopes=...) matches signature
3. RefreshToken constructor field mismatches	✅ FIXED	Stores: user_id, authorization_code, token_hash, issued_at, expires_at (no token/created_at/client_id)
4. User.find_by_id() doesn't exist	✅ FIXED	auth.py step 8: await User.get(auth_code_doc.user_id)
5. slowapi limiter not registered on app	✅ FIXED	Created app/core/limiter.py, imported in main.py, registered on app
⚠️ Significant Issues (7/10 status mixed)
Issue	Status	Notes
6. Lazy imports inside functions	✅ FIXED	JwtTokenPayload imported at module top, no lazy imports in token_exchange()
7. No response_model on /token	❌ NOT FIXED	Endpoint returns bare dict, should have response_model=TokenResponse
8. /token has include_in_schema=False	❌ NOT FIXED	Should be removed — /token is a public RFC 6749 JSON endpoint
9. Unused imports in main.py	❓ UNKNOWN	Not recently checked; needs verification
10. jwt_algorithm configurable via .env	❌ NOT FIXED	jwt_service.py line 62 still loads from settings.jwt_algorithm; TODO comment remains
📁 Folder Structure (0/3 improvements)
Recommendation	Status
Create app/dependencies/ for auth guards	❌ Missing
Create app/middleware/ for request concerns	❌ Missing
Separate DB documents (models/) from API schemas (schemas/)	❌ Mixed in auth.py
📋 What's Left to Implement (0/6 plus additions)
Feature	RFC	Status	Impact
POST /token exchange	6749 §4.1.3	✅ Working (buggy issues fixed)	High
POST /refresh token rotation	6749 §6	❌ Missing	High
POST /revoke token revocation	7009	❌ Missing	Medium
JWT bearer auth dependency	6750 §2.1	❌ Missing	High (blocks protected routes)
Scope enforcement	6749 §3.3	❌ Missing	Medium
POST /logout	—	❌ Missing	Low
code_challenge validation	7636 §4.2	❌ Missing	Low
✨ ADDED Since Initial Review (not in original list)
Addition	Status	Reason
Authorization code replay attack detection	✅ Added	RFC 6749 §10.5 compliance — revoke all tokens if code reused
Usage tracking on AuthorizationCode	✅ Added	Support replay detection (used/'used_at fields)
authorization_code ref on RefreshToken	✅ Added	Link tokens to code for revocation chain
Typed error handling (AuthErrors/ErrorInfo)	✅ Added	Type-safe, extendable error system
Next Steps (Recommended Priority)
Quick wins (30 min):

Remove include_in_schema=False from /token
Add response_model=TokenResponse to /token (create model if missing)
Remove unused imports from main.py
Hardcode algorithm = "HS256" in JWTService __init__
High-impact (2–3 hrs):

Build auth.py with get_current_user() dependency
Implement POST /refresh endpoint
Add a simple protected route to test auth dependency
Medium-term (1–2 hrs):

Folder restructuring (dependencies/, middleware/, schemas/)
POST /revoke endpoint
Scope enforcement helper
Ready to tackle any of these?