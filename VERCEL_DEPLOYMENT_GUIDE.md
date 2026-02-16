# 🚀 Deploy to Vercel - Full Stack Setup Complete!

## ✅ Your Project Structure is Ready

```
self-speak/
├── frontend/           # All frontend files (HTML, CSS, JS)
├── backend/           # FastAPI backend
├── api/
│   └── index.py      # Vercel serverless entry point
├── vercel.json       # Vercel configuration
└── requirements.txt  # Python dependencies
```

---

## 🎯 How to Deploy on Vercel

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Configure Vercel deployment with frontend/backend separation"
git push
```

### Step 2: Connect to Vercel

1. Go to https://vercel.com
2. Click "Add New Project"
3. Import your GitHub repository
4. Vercel will auto-detect the configuration

### Step 3: Configure Environment Variables

In Vercel dashboard, add these environment variables:

**Critical - Add ALL of these:**

```
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_api_key
LEMON_SQUEEZY_API_KEY=your_lemon_squeezy_api_key
LEMON_SQUEEZY_WEBHOOK_SECRET=your_webhook_secret
LEMON_SQUEEZY_STORE_ID=your_store_id
LEMON_MONTHLY_VARIANT_ID=your_monthly_variant_id
LEMON_ANNUAL_VARIANT_ID=your_annual_variant_id
PYTHON_VERSION=3.11
```

### Step 4: Deploy

Click "Deploy" - Vercel will:
1. Install Python dependencies from `requirements.txt`
2. Build frontend static files
3. Create serverless function from `api/index.py`
4. Deploy everything

**Deployment time: 2-3 minutes**

### Step 5: Get Your URL

Vercel gives you: `https://your-app.vercel.app`

---

## 🔧 How It Works

### Request Flow:

```
User Request
    ↓
1. Static Files: /landing.html, /index.html, /style.css
   → Served from /frontend/ folder
   
2. API Calls: /journal/*, /dashboard/*, /billing/*
   → Routed to api/index.py (serverless)
   → Calls backend/main.py (FastAPI)
```

### Architecture:

```
Vercel Deployment
├── Frontend (Static CDN)
│   ├── landing.html
│   ├── index.html
│   ├── dashboard.html
│   └── *.css, *.js
│
└── Backend (Serverless Functions)
    └── api/index.py → backend/main.py
```

---

## ✅ What's Already Configured

1. **`vercel.json`** - Routes and builds configured
2. **`api/index.py`** - Serverless entry point with Mangum
3. **`requirements.txt`** - Python dependencies including mangum
4. **Frontend API URLs** - Already using `window.location.origin`
5. **`.vercelignore`** - Excludes unnecessary files

---

## 🧪 Testing After Deployment

### Test Checklist:

1. **Frontend:**
   - [ ] Visit `https://your-app.vercel.app`
   - [ ] Landing page loads
   - [ ] CSS/JS files load correctly
   - [ ] No 404 errors in console

2. **Authentication:**
   - [ ] Click "Sign In"
   - [ ] Google OAuth works
   - [ ] Redirects back to app

3. **Backend API:**
   - [ ] Journal save works
   - [ ] Analyze button works
   - [ ] Dashboard loads
   - [ ] No CORS errors

4. **Check Console:**
   - [ ] API Base URL shows: `https://your-app.vercel.app`
   - [ ] No localhost errors

---

## ⚠️ Important: Update Supabase

After deployment, update Supabase redirect URLs:

1. Go to Supabase Dashboard
2. Authentication → URL Configuration
3. Add Redirect URLs:

```
https://your-app.vercel.app/*
https://your-app.vercel.app/index.html
https://your-app.vercel.app/dashboard.html
http://localhost:3000/*
```

4. Set Site URL:
```
https://your-app.vercel.app
```

---

## ⚠️ Update Lemon Squeezy Webhook

Update webhook URL to:
```
https://your-app.vercel.app/billing/webhook
```

---

## 🐛 Troubleshooting

### Issue: API routes return 404

**Solution:** Check Vercel Function Logs
- Vercel Dashboard → Your Project → "Functions" tab
- Look for errors in serverless function

### Issue: Import errors in backend

**Solution:** Verify `api/index.py` path configuration
- Make sure backend path is correctly added to sys.path

### Issue: Frontend files not loading

**Solution:** Check vercel.json routes
- Static files should route to `/frontend/`

### Issue: CORS errors

**Solution:** Should not happen (same origin)
- But if it does, check `backend/main.py` CORS settings

---

## 📊 Vercel Limits (Free Tier)

- ✅ Serverless Function Timeout: 10 seconds
- ✅ Deployments: Unlimited
- ✅ Bandwidth: 100GB/month
- ✅ Build Time: 6000 minutes/month

**Your app should stay well within these limits!**

---

## 🚀 Local Development

### Run Frontend:
```bash
cd frontend
python -m http.server 3000
```

### Run Backend:
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

### Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

---

## 📝 Deployment Checklist

Before deploying:

- [ ] All frontend files in `frontend/` folder
- [ ] Backend files in `backend/` folder
- [ ] `api/index.py` exists and configured
- [ ] `vercel.json` exists
- [ ] `requirements.txt` in root
- [ ] `.vercelignore` configured
- [ ] Committed and pushed to GitHub
- [ ] Environment variables ready

After deploying:

- [ ] Test all pages load
- [ ] Test authentication
- [ ] Test API calls
- [ ] Update Supabase URLs
- [ ] Update Lemon Squeezy webhook
- [ ] Monitor Vercel logs

---

## 🎉 You're Ready to Deploy!

Your project structure is perfect and configured correctly for Vercel deployment.

**Next steps:**
1. `git push` to GitHub
2. Connect to Vercel
3. Add environment variables
4. Click Deploy

**Your app will be live in 3 minutes!** 🚀

---

## 📚 Additional Resources

- Vercel Docs: https://vercel.com/docs
- Vercel Python: https://vercel.com/docs/functions/serverless-functions/runtimes/python
- Mangum (ASGI adapter): https://github.com/jordaneremieff/mangum
- FastAPI: https://fastapi.tiangolo.com/

---

## 💰 Cost

**Current Setup:** $0/month (Vercel free tier)

**If you need more:**
- Vercel Pro: $20/month (longer timeouts, more bandwidth)
- Consider Railway/Render for backend if you hit limits

**For most hobby/small projects: Free tier is perfect!** ✅
