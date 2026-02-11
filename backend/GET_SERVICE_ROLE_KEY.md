# 🔑 How to Get Your Supabase Service Role Key

## ⚠️ Current Issue

Your `.env` file has the **WRONG** Supabase key. You're using:
```
sb_publishable_XAKRtkael0pRQ35NLWQ6gA_Ea4aoRwW
```

This is the **publishable/anon key** (starts with `sb_publishable_`).

You need the **service_role key** (starts with `eyJ...` and is much longer).

---

## ✅ How to Get the Correct Key

### Step 1: Go to Supabase Dashboard

1. Open: https://app.supabase.com/
2. Select your project: **qlmxusbpbjfcyihjqmow**

### Step 2: Navigate to API Settings

1. Click **Settings** (gear icon in left sidebar)
2. Click **API**

### Step 3: Find the Service Role Key

You'll see three API keys on this page:

#### ❌ Project API keys → anon / public
```
sb_publishable_XXXXX...
```
**DO NOT USE THIS** - This is for frontend only!

#### ✅ Project API keys → service_role
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFsbXh1c2JwYmpmY3lpaGpxbW93Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY0...
```
**USE THIS ONE** - This is what you need!

### Step 4: Copy the Service Role Key

1. Click the **Copy** button next to `service_role` key
2. It will be a very long string starting with `eyJ...`
3. Keep it secret - this has admin access to your database!

### Step 5: Update Your .env File

Replace this line in `backend/.env`:

**Current (WRONG):**
```env
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.REPLACE_WITH_YOUR_SERVICE_ROLE_KEY
```

**Correct (after copying):**
```env
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFsbXh1c2JwYmpmY3lpaGpxbW93Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY0... (very long)
```

---

## 📋 Visual Guide

In Supabase Dashboard → Settings → API, you'll see:

```
Project API keys

┌─────────────────────────────────────────┐
│ anon                                     │
│ public                                   │
│ sb_publishable_XXXXX...          [Copy] │ ← ❌ Don't use this
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ service_role                             │
│ secret                                   │
│ eyJhbGciOiJIUzI1NiIsInR...      [Copy] │ ← ✅ Use this one!
└─────────────────────────────────────────┘
```

---

## ⚙️ Also Get Your JWT Secret

While you're on the same page (Settings → API):

1. Scroll down to **JWT Settings**
2. Find **JWT Secret**
3. Copy the value (looks like: `56376459-c1c6-4731-abfd-eb924f4302f0`)
4. This should already be in your `.env` file (it looks correct)

---

## ✅ Quick Test

After updating the `.env` file, test if it works:

```powershell
cd C:\Personal\self-speak\backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Service Key (first 20 chars):', os.getenv('SUPABASE_SERVICE_KEY')[:20])"
```

**Expected output:**
```
Service Key (first 20 chars): eyJhbGciOiJIUzI1NiIsI
```

**If you see:**
```
Service Key (first 20 chars): sb_publishable_XAKRt
```
**Then it's still wrong!**

---

## 🚀 After Fixing

Once you've updated the service_role key:

```powershell
cd C:\Personal\self-speak\backend
python main.py
```

Should start successfully!

---

## 🔒 Security Note

**⚠️ NEVER commit the service_role key to git!**

The `.env` file is already in `.gitignore`, so it won't be committed.

The service_role key has **FULL ACCESS** to your database and bypasses Row Level Security (RLS). Keep it secret!

---

## 📝 Summary

**What you need to do:**
1. ✅ Go to Supabase Dashboard → Settings → API
2. ✅ Copy the **service_role** key (the long one starting with `eyJ...`)
3. ✅ Paste it in `backend/.env` replacing the placeholder
4. ✅ Save the file
5. ✅ Run `python main.py`

**Your `.env` should look like:**
```env
SUPABASE_URL=https://qlmxusbpbjfcyihjqmow.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOi... (very long)
SUPABASE_JWT_SECRET=56376459-c1c6-4731-abfd-eb924f4302f0
```

That's it! 🎉
