# JWT Authentication - Testing Guide

## 🎯 Overview
SmartHome now supports full REST API authentication using JWT (JSON Web Tokens). This allows for stateless authentication and enables API usage from external clients (curl, Postman, mobile apps, etc.).

## 📝 What Was Done

### 1. Backend Changes

#### JWT Authentication Module (`jwt_auth.py`)
- ✅ Token generation with 24-hour expiration
- ✅ Token verification with error handling
- ✅ Header parsing (Bearer token extraction)
- ✅ Environment-based secret key (JWT_SECRET)

#### JWT API Endpoints (`auth_jwt_api.py`)
- ✅ `POST /api/auth/jwt/login` - Login and get JWT token
- ✅ `POST /api/auth/jwt/register` - Register and get JWT token

#### Authentication Middleware
- ✅ Updated `BaseAPIHandler.get_current_user()` to support JWT
- ✅ Backward compatible with cookie-based auth
- ✅ JWT takes priority over cookies when both present

#### Decorators (`decorators.py`)
- ✅ `@jwt_required` - Require authentication
- ✅ `@jwt_optional` - Optional authentication

### 2. Frontend Changes

#### JWT Helper Library (`jwt-auth.js`)
- ✅ Token storage in localStorage
- ✅ `loginWithJWT()` - Login with email/password
- ✅ `registerWithJWT()` - Register new user
- ✅ `authFetch()` - Fetch wrapper with automatic JWT header
- ✅ `addAuthHeader()` - Add Authorization header to requests
- ✅ `requireAuth()` - Redirect to login if not authenticated
- ✅ Auto logout on 401 (token expired)

#### New Pages
- ✅ `login-jwt.html` - JWT-based login page
- ✅ `register-jwt.html` - JWT-based registration page

### 3. Dependencies
- ✅ Added `PyJWT>=2.8` to requirements.txt
- ✅ Installed in virtual environment

## 🧪 Testing Instructions

### Test 1: Register via JWT API (Terminal)

```bash
curl -X POST http://127.0.0.1:8001/api/auth/jwt/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "phone": "0612345678"
  }'
```

**Expected Response:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "phone_number": "0612345678",
    "profile_image": null,
    "is_active": true,
    "date_joined": "2025-01-28T12:00:00"
  }
}
```

### Test 2: Login via JWT API (Terminal)

```bash
curl -X POST http://127.0.0.1:8001/api/auth/jwt/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Expected Response:** Same as registration (token + user info)

### Test 3: Use JWT Token to Access Protected Endpoint

```bash
# Save the token from login/register
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Access protected endpoint
curl http://127.0.0.1:8001/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "phone_number": "0612345678",
  "profile_image": null,
  "is_active": true,
  "date_joined": "2025-01-28T12:00:00"
}
```

### Test 4: Upload Profile Image with JWT

```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
USER_ID=1

curl -X POST http://127.0.0.1:8001/api/users/$USER_ID/upload-image \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@/path/to/image.jpg"
```

**Expected Response:**
```json
{
  "profile_image": "/media/profile_images/user_1_1738156789.jpg",
  "message": "Profile image uploaded successfully"
}
```

### Test 5: Frontend JWT Login

1. Start the server:
   ```bash
   cd /Users/davidyala/Documents/Etudes/Cours\ Master/M2/S1/Base\ de\ Données\ et\ Pro/Projet/SmartHome/smarthome
   python3 -m smarthome.tornado_app.app
   ```

2. Open browser: http://127.0.0.1:8001/app/login-jwt.html

3. Fill in email and password

4. Check browser console (F12):
   - Token should be saved in localStorage
   - User info should be stored
   - Redirect to dashboard should occur

5. Open browser DevTools > Application > Local Storage:
   - `smarthome_jwt_token` should contain the JWT
   - `smarthome_user` should contain user JSON

### Test 6: Frontend JWT Register

1. Open browser: http://127.0.0.1:8001/app/register-jwt.html

2. Fill in registration form

3. Submit and verify same behavior as login

### Test 7: Test Token Expiration

```bash
# Use an invalid/expired token
curl http://127.0.0.1:8001/api/auth/me \
  -H "Authorization: Bearer invalid_token"
```

**Expected Response:**
```json
{
  "error": "Authentication required"
}
```
Status: 401 Unauthorized

### Test 8: Test Backward Compatibility

The old cookie-based authentication should still work:

1. Open http://127.0.0.1:8001/app/login.html (old login)
2. Login with username/password
3. Verify dashboard access works
4. Cookie-based auth still functional

## 🔍 Verification Checklist

- [ ] JWT tokens are generated successfully
- [ ] JWT tokens can be verified
- [ ] JWT tokens expire after 24 hours
- [ ] Login endpoint returns token + user info
- [ ] Register endpoint returns token + user info
- [ ] Protected endpoints accept JWT in Authorization header
- [ ] Invalid tokens return 401 error
- [ ] File upload works with JWT authentication
- [ ] Frontend stores tokens in localStorage
- [ ] Frontend adds Authorization header to API calls
- [ ] Auto-logout works on 401 response
- [ ] Old cookie-based auth still works (backward compatible)

## 🐛 Debugging

### Check JWT Token Content
```bash
# Decode JWT (first two parts are base64)
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
echo $TOKEN | cut -d. -f2 | base64 -d | python3 -m json.tool
```

### Check Server Logs
```bash
cd /Users/davidyala/Documents/Etudes/Cours\ Master/M2/S1/Base\ de\ Données\ et\ Pro/Projet/SmartHome/smarthome
python3 -m smarthome.tornado_app.app
```

### Check localStorage in Browser
```javascript
// In browser console (F12)
console.log('Token:', localStorage.getItem('smarthome_jwt_token'));
console.log('User:', JSON.parse(localStorage.getItem('smarthome_user')));
```

## 🎉 Success Criteria

✅ **REST API Compliance**: 100% REST API for authentication
✅ **Stateless Auth**: No server-side sessions needed
✅ **External Client Support**: Can authenticate from curl, Postman, mobile apps
✅ **File Upload**: Profile image upload works with JWT
✅ **Backward Compatible**: Old cookie-based auth still works
✅ **Security**: Tokens expire after 24 hours
✅ **Frontend Integration**: Complete JWT flow in browser

## 📝 Next Steps (Optional Improvements)

1. Add refresh tokens for extended sessions
2. Add token blacklist for logout
3. Add password reset with JWT
4. Add email verification with JWT
5. Add rate limiting on auth endpoints
6. Add HTTPS requirement for production
7. Move JWT_SECRET to environment variable
8. Add JWT expiry configuration option
9. Create API documentation with OpenAPI/Swagger
10. Add integration tests for auth flow
