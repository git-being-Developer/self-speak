# Selfspeak Testing Guide

## Prerequisites

1. ✅ Backend server running (`python main.py` or `.\start.ps1`)
2. ✅ .env file configured with Supabase credentials
3. ✅ Supabase database tables created

---

## Option 1: Test Complete Flow with Frontend (Recommended)

This is the **most realistic** way to test because it includes actual Google authentication.

### Step 1: Configure Frontend Supabase Credentials

Edit `auth.js` and replace placeholders:

```javascript
const SUPABASE_URL = 'https://qlmxusbpbjfcyihjqmow.supabase.co';
const SUPABASE_ANON_KEY = 'YOUR_ANON_KEY_HERE'; // NOT service role!
```

**Important**: Use the `anon/public` key (not service_role) for frontend.

### Step 2: Add Supabase JavaScript CDN

Add this to `login.html` before closing `</body>`:

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script src="auth.js"></script>
```

### Step 3: Serve Frontend Files

You need a local web server. Choose one:

**Option A: Python HTTP Server**
```powershell
# In root directory (C:\Personal\self-speak)
python -m http.server 3000
```

**Option B: Node.js http-server**
```powershell
npx http-server -p 3000
```

**Option C: VS Code Live Server Extension**
- Install "Live Server" extension
- Right-click `login.html` → "Open with Live Server"

### Step 4: Configure Google OAuth in Supabase

1. Go to Supabase Dashboard → Authentication → Providers
2. Enable Google
3. Add redirect URL: `http://localhost:3000/index.html`

### Step 5: Test the Flow

1. Open browser: `http://localhost:3000/login.html`
2. Click "Continue with Google"
3. Sign in with Google
4. You should be redirected to `index.html`
5. Open browser console (F12) - you should see the access token
6. The app will make API calls to your backend with the JWT

### Step 6: Test API Integration

Once logged in on `index.html`:

1. Type in the journal textarea
2. Click "Save" - should call `/journal/save`
3. Click "Analyze" - should call `/journal/analyze`
4. Refresh page - should call `/journal/today`

Check:
- Browser Network tab (F12 → Network)
- Backend terminal logs
- Supabase database tables

---

## Option 2: Test Backend API Only (Without Frontend)

This is faster for testing just the backend, but you need to manually get a JWT token first.

### Step 1: Get a Real JWT Token

You have 3 options:

#### Option A: Use Supabase Dashboard
1. Go to Supabase Dashboard → Authentication → Users
2. Click on a user (or create one manually)
3. Copy the JWT from the "User JWT" field

#### Option B: Create a Quick Test User via Supabase SQL
```sql
-- In Supabase SQL Editor
SELECT auth.uid(), auth.jwt();
```

#### Option C: Use the test script (below)

### Step 2: Create Test Script

Run the provided `test_auth_flow.py` script:

```powershell
python backend/test_auth_flow.py
```

This will:
1. Create a mock JWT token
2. Test all endpoints
3. Show you the responses

---

## Option 3: Quick Manual API Tests (Using curl or Postman)

### Get a JWT Token First

```powershell
# You'll need a real token from Supabase
# For now, we'll create a test endpoint
```

### Test Endpoints

**1. Test Health Check (No Auth)**
```powershell
curl http://localhost:8000/
```

**2. Get Today's Journal (Requires Auth)**
```powershell
$token = "YOUR_JWT_TOKEN_HERE"
curl -H "Authorization: Bearer $token" http://localhost:8000/journal/today
```

**3. Save Journal Entry**
```powershell
$token = "YOUR_JWT_TOKEN_HERE"
$body = '{"content": "Today I feel grateful and calm. Reflecting on my goals."}'
curl -X POST -H "Authorization: Bearer $token" -H "Content-Type: application/json" -d $body http://localhost:8000/journal/save
```

**4. Analyze Journal**
```powershell
$token = "YOUR_JWT_TOKEN_HERE"
curl -X POST -H "Authorization: Bearer $token" http://localhost:8000/journal/analyze
```

---

## Recommended Testing Flow

**For Development**: Use **Option 1** (Frontend + Backend)
- Most realistic
- Tests complete user experience
- Validates authentication flow

**For Quick Backend Tests**: Use **Option 2** (Test Script)
- Faster iteration
- Focus on API logic
- No frontend needed

---

## Troubleshooting

### "Unable to read the keys" Error
- Check `.env` file exists in `backend/` directory
- Ensure no spaces around `=` signs
- Try restarting the server

### "401 Unauthorized" Error
- JWT token expired (Supabase tokens expire after 1 hour)
- Wrong token used
- Token not in `Authorization: Bearer` format

### CORS Error in Browser
- Backend CORS is configured to allow all origins
- If issue persists, check browser console for exact error

### "Database error" or "User not found"
- User profile not created in Supabase
- Check if trigger exists to auto-create profiles
- Manually insert profile in `profiles` table

---

## What's Next?

Once everything works:

1. ✅ Test Google login flow
2. ✅ Test save journal entry
3. ✅ Test analyze journal
4. ✅ Test weekly usage limits
5. 🔄 Integrate real AI analysis (replace mock data)
6. 🔄 Add audio playback features
7. 🔄 Add visualization charts

---

## Quick Reference

| What | Command |
|------|---------|
| Start Backend | `cd backend; python main.py` |
| Start Frontend | `python -m http.server 3000` |
| View Backend Logs | Check terminal where backend is running |
| View API Docs | `http://localhost:8000/docs` |
| View Database | Supabase Dashboard → Table Editor |
| View Auth Users | Supabase Dashboard → Authentication → Users |

